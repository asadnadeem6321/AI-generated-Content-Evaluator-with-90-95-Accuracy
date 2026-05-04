from django.shortcuts import render
from rest_framework import viewsets, status 
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.http import Http404
from django.utils import timezone
from django.db.models import Q
from apps.dashboard import serializers
from apps.authentication.permissions import IsStudent, IsTeacher
from .tasks import queue_paragraph_tasks, queue_submission_processing

# Modes
from .models import Submission
from apps.classes.models import Assignment
# Serializers
from .serializers import (
    SubmissionSerializer, 
    SubmissionCreateSerializer, 
    ExtensionRequestSerializer
)

# Create your views here.

class SubmissionViewSet(viewsets.ModelViewSet):
    """ViewSet for Submissions CURD operations"""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return SubmissionCreateSerializer
        elif self.action == 'request_extension':
            return ExtensionRequestSerializer
        return SubmissionSerializer

    def get_queryset(self):
        user = self.request.user
        assignment_id = self.request.query_params.get('assignment')
        class_id = self.request.query_params.get('class_id') or self.request.query_params.get('class')
        
        # Teachers see all submissions in their classes
        if user.is_teacher():
            queryset = Submission.objects.filter(
                assignment__class_obj__teacher=user
            )
        # Students see only their own
        elif user.is_student():
            queryset = Submission.objects.filter(user=user)
        # Guests see only their own
        else:
            queryset = Submission.objects.filter(user=user, assignment__isnull=True)
        
        # Filter by assignment if provided
        if assignment_id:
            queryset = queryset.filter(assignment_id=assignment_id)

        # Filter by class if provided
        if class_id:
            queryset = queryset.filter(assignment__class_obj_id=class_id)
        
        return queryset.select_related('user', 'assignment').order_by('-submitted_at')

    def get_object(self):
        try:
            return super().get_object()
        except Http404:
            user = self.request.user
            if not user.is_teacher():
                raise

            lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
            lookup_value = self.kwargs.get(lookup_url_kwarg)
            if not lookup_value:
                raise

            submission = Submission.objects.filter(id=lookup_value).first()
            if not submission:
                raise

            if submission.assignment and submission.assignment.class_obj.teacher == user:
                return submission

            if submission.assignment is None and submission.assignment_name:
                teacher_titles = Assignment.objects.filter(
                    class_obj__teacher=user
                ).values_list('title', flat=True)
                if any(title.lower() in submission.assignment_name.lower() for title in teacher_titles):
                    return submission

            raise

    @action(detail=False, methods=['get'], permission_classes=[IsTeacher], url_path='assignment')
    def teacher_assignment(self, request):
        """Teacher: get all submissions for a specific assignment."""
        assignment_id = request.query_params.get('assignment')
        if not assignment_id:
            return Response(
                {'detail': 'assignment query parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        assignment = Assignment.objects.filter(id=assignment_id).first()
        if not assignment or assignment.class_obj.teacher != request.user:
            return Response(
                {'detail': 'Assignment not found or access denied.'},
                status=status.HTTP_404_NOT_FOUND
            )

        submissions = Submission.objects.filter(
            Q(assignment_id=assignment_id) |
            Q(assignment__isnull=True, assignment_name__icontains=assignment.title)
        ).select_related('user', 'assignment').order_by('-submitted_at')

        page = self.paginate_queryset(submissions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(submissions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsStudent], url_path='my-assignment')
    def student_assignment(self, request):
        """Student: get own submissions for a specific assignment."""
        assignment_id = request.query_params.get('assignment')
        if not assignment_id:
            return Response(
                {'detail': 'assignment query parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        assignment = Assignment.objects.filter(id=assignment_id).first()
        if not assignment:
            return Response(
                {'detail': 'Assignment not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        submissions = Submission.objects.filter(
            Q(assignment_id=assignment_id) |
            Q(assignment__isnull=True, assignment_name__icontains=assignment.title),
            user=request.user
        ).select_related('user', 'assignment').order_by('-submitted_at')

        page = self.paginate_queryset(submissions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(submissions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsTeacher], url_path='by-class')
    def by_class(self, request):
        """Return submissions for all assignments in a class for the logged-in teacher."""
        class_id = request.query_params.get('class_id') or request.query_params.get('class')
        if not class_id:
            return Response(
                {'detail': 'class_id query parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        submissions = Submission.objects.filter(
            assignment__class_obj_id=class_id,
            assignment__class_obj__teacher=request.user
        ).select_related('user', 'assignment').order_by('-submitted_at')

        page = self.paginate_queryset(submissions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(submissions, many=True)
        return Response(serializer.data)
        
    def perform_create(self, serializer):
        """Create submission and queue for processing"""
        
        # Validate deadline
        if serializer.validated_data.get('assignment'):
            assignment = serializer.validated_data['assignment']
            if assignment.is_past_deadline and not assignment.allow_late_submissions:
                if not serializer.validated_data.get('extension_granted'):
                    raise serializers.ValidationError("Deadline has passed. Request an extension.")
        
        # Save submission
        submission = serializer.save(
            user=self.request.user,
            original_filename=serializer.validated_data['file'].name,
            file_size=serializer.validated_data['file'].size,
            status='queued'
        )
        
        # Queue for processing
        queue_submission_processing(
            submission_id=str(submission.id),
            user_role=self.request.user.role,
            is_teacher_view=False
        )



    @action(detail=True, methods=['post'], permission_classes=[IsStudent])
    def request_extension(self, request, pk=None):
        """Student request for deadline extension"""
        submission = self.get_object()

        if submission.extension_requested:
            return Response({'error':'Extension already requested'}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = ExtensionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        submission.extension_requested = True
        submission.extension_reason = serializer.validated_data['reason']
        submission.save()

        return Response({'message':'Extension request submitted'}, status=status.HTTP_200_OK)


    @action(detail=True, methods=['post'], permission_classes=[IsTeacher])
    def approve_extension(self, request, pk=None):
        """Teacher approve extension request"""
        submission = self.get_object()

        if not submission.extension_requested:
            return Response({'error':'No extension request found'}, status=status.HTTP_400_BAD_REQUEST)

        submission.extension_granted=True
        submission.save()

        return Response({'message':'Extension approved'})


    @action(detail=True, methods=['post'], permission_classes=[IsTeacher])
    def reject_extension(self, request, pk=None):
        """Teacher reject extension request"""
        submission = self.get_object()
        
        submission.extension_requested=False
        submission.extension_reason=''
        submission.save()

        return Response({'message':"Extension Rejected"})
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get submission processing status"""
        submission = self.get_object()
        
        return Response({
            'id': str(submission.id),
            'status': submission.status,
            'total_paragraphs': submission.total_paragraphs,
            'processed_paragraphs': submission.processed_paragraphs,
            'processing_percentage': submission.processing_percentage,
            'is_complete': submission.status == 'completed'
        })


    # API for teachers to pause replay submission processing 
    @action(detail=True, methods=['post'], permission_classes=[IsTeacher])
    def pause(self, request, pk=None):
        """
        Teacher pauses submission's processing
        POST /api/submission/{id}/pause
        """
        submission = self.get_object()

        # Verify teacher owns this submission
        if submission.class_obj and submission.class_obj.teacher != request.user:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if submission.is_paused:
            return Response({'message': 'Already paused'})
        submission.pause(request.user)

        return Response({
            'message': 'Submission paused',
            'paused_at': submission.paused_at
        })
    
    @action(detail=True, methods=['post'], permission_classes = [IsTeacher])
    def resume(self, request, pk=None):
        """
        Teacher resume submission processing
        POST /api/submissions/{id}/resume/
        """
        submission = self.get_object()
        
        if submission.class_obj and submission.class_obj.teacher != request.user:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not submission.is_paused:
            return Response({'message': 'Not paused'})
        
        submission.resume()
        
        # Re-queue pending paragraphs
        if hasattr(submission, 'result'):
            pending_count = submission.result.paragraphs.filter(status='pending').count()
            if pending_count > 0:
                queue_paragraph_tasks(str(submission.id), submission.user.role)
        
        return Response({
            'message': 'Submission resumed',
            'pending_paragraphs': pending_count
        })

    
    @action(detail=False, methods=['post'], permission_classes=[IsTeacher])
    def bulk_pause(self, request):
        """
        Teacher can pause multiple submissions

        POST /api/submissions/bulk_pause/
        request body : {"submission_ids": ["id1", "id2", "id3"]}
        """
        submission_ids = request.data.get('submission_ids', [])

        submissions = Submission.objects.filter(
            id__in = submission_ids,
            class_obj__teacher = request.user
        )

        paused_count = 0
        for submission in submissions:
            if not submission.is_paused:
                submission.pause(request.user)
                paused_count += 1
            
        return Response({
            'message': f'Paused {paused_count} submissions',
            'paused_count': paused_count
        })
    

    @action(detail=False, methods=['post'], permission_classes=[IsTeacher])
    def bulk_resume(self, request):
        """
        Teacher can resumes multiple submissions

        POST /api/submissions/bulk_resume/
        request body : {"submission_ids": ["id1", "id2", "id3"]}
        """

        submission_ids = request.data.get('submission_ids', [])

        submissions = Submission.objects.filter(
             id__in=submission_ids,
            class_obj__teacher=request.user,
            is_paused=True
        )

        resumed_count = 0
        for submission in submissions:
            submission.resume()
            if hasattr(submission, 'result'):
                queue_paragraph_tasks(str(submission.id), submission.user.role)
            resumed_count += 1
        
        return Response({
            'message': f'Resumed {resumed_count} submissions',
            'resumed_count': resumed_count
        })

#  seperate point for teachers and guests to evaluate documents without creating assignments, so they can use the same interface for quick checks without needing to set up an assignment.
    @action(detail=False, methods=['post'])
    def evaluate_document(self, request):
        """
        Teacher/Guest evaluates their own document (no assignment)
        
        POST /api/submissions/evaluate_document/
        """
        if not request.FILES.get('file'):
            return Response(
                {'error': 'PDF file is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        file = request.FILES['file']
        assignment_name = request.data.get('assignment_name', 'Document Evaluation')
        
        # Validate file type
        if not file.name.endswith('.pdf'):
            return Response(
                {'error': 'Only PDF files are allowed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create submission without assignment
        submission = Submission.objects.create(
            user=request.user,
            assignment=None,
            assignment_name=assignment_name,
            file=file,
            original_filename=file.name,
            file_size=file.size,
            status='queued'
        )
        
        # Queue for processing
        from .tasks import queue_submission_processing
        queue_submission_processing(
            submission_id=str(submission.id),
            user_role=request.user.role,
            is_teacher_view=False
        )
        
        serializer = self.get_serializer(submission)
        return Response(serializer.data, status=status.HTTP_201_CREATED)