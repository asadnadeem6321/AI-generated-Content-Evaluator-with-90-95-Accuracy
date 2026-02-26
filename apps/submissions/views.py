from django.shortcuts import render
from rest_framework import viewsets, status 
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from authentication.permissions import IsStudent, IsTeacher
# Modes
from .models import Submission
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
        user = user.request.user
        if user.is_teacher():
            # Teacher can see all submissions in there classes
            return Submission.objects.filter(class_obj__teacher=user)
        else:
        # Students and guest users can see only there submissions
            return Submission.objects.filter(user=user)
        
    def perform_create(self, serializer):
        # Check deadline if class submission
        class_obj = serializer.validated_data.get('class_obj')
        deadline = serializer.validated_data.get('assignment_deadline')

        if deadline and timezone.now() > deadline:
            # Check if extension granted
            if not serializer.validate_data.get('extension_granted'):
                raise serializer.ValidationError("Deadline has passed request an extension")
            
        submission = serializer.save(
            user = self.request.user,
            orignal_filename = serializer.validated_data['file'].name,
            file_size = serializer.validated_data['file'].size
        )

        # TODO : Queue for ML processing
        # from .task import process_submission
        # process_submission.delay(str(submission.id))



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
        """Check submission processing status"""
        submission = self.get_object()
        return Response(
            {
                'status': submission.status,
                'submitted_at': submission.submitted_at,
                'processed_at': submission.processed_at
            }
        )




        #i want you to in every api write a doc string with its request and expected respoce sample so that in future developer knows that what api accepr what and return what is not it a best practice? and also write all the end points of that file include custom ones in the end of file as comment