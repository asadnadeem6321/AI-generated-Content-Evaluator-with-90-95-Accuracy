from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Avg, Q
from apps.authentication.models import User
from apps.authentication.permissions import IsTeacher
from apps.classes.models import Class, Assignment
from apps.submissions.models import Submission
from apps.results.models import Result
from .serializers import (
    ClassStatisticsSerializer,
    AssignmentStatisticsSerializer,
    StudentPerformanceSerializer,
    SubmissionOverviewSerializer
)
# Create your views here.

class DashboardViewSet(viewsets.ModelViewSet):
    """Teacher Dashboard statics"""
    permission_classes = [IsTeacher]

    @action(detail=False, methods=['get'])
    def class_statistics(self, request):
        """get statics for all teacher's classes"""
        teacher = request.user
        classes = Class.object.filter(teacher=teacher)
        
        stats = []
        for class_obj in classes:
            submissions = Submission.objects.filter(assignment__class_obj=class_obj)
            completed = submissions.filter(status='completed')
            results = Result.objects.filter(submissions__in=completed)

            stats.append({
                'class_id': class_obj.id,
                'class_name': class_obj.name,
                'total_students': class_obj.students.count(),
                'total_assignments': class_obj.assignments.count(),
                'total_submissions': submissions.count(),
                'completed_submissions': completed.count(),
                'pending_submissions': submissions.filter(status__in=['queued', 'processing']).count(),
                'average_ai_percentage': results.aggregate(Avg('ai_percentage'))['ai_percentage__avg'] or 0,
                'average_grammar_score': results.aggregate(Avg('grammar_score'))['grammar_score__avg'] or 0,
                'high_ai_count': results.filter(ai_percentage__gte=70).count()
            })

        serializer = ClassStatisticsSerializer(stats, many=True)
        return Response(serializer.data)
    

    @action(detail=True, methods=['get'])
    def assignment_statistics(self, request, pk=None):
        """To get statics of assignment in class"""
        class_obj = Class.objects.get(id=pk, teacher=request.user)
        assignments = class_obj.assignments.all()

        stats = []
        total_students = class_obj.students.count()

        for assignment in assignments:
            submissions = assignment.submission.all()
            completed = submissions.filter(status='completed')
            results = Result.objects.filter(submission__in=completed)

            stats.append({
                'assignment_id': assignment.id,
                'assignment_title': assignment.title,
                'deadline': assignment.deadline,
                'is_past_deadline': assignment.is_past_deadline,
                'total_students': total_students,
                'submitted_count': submissions.count(),
                'pending_count': total_students - submissions.count(),
                'average_ai_percentage': results.aggregate(Avg('ai_percentage'))['ai_percentage__avg'] or 0,
                'high_ai_submissions': results.filter(ai_percentage__gte=70).count()
            })
        
        serializer = AssignmentStatisticsSerializer(stats, many=True)
        return Response(serializer.data)
    


    @action(detail=True, methods=['get'])
    def student_performance(self, request, pk=None):
        """Get student performance for a class"""
        class_obj = Class.objects.get(id=pk, teacher=request.user)
        students = class_obj.students.all()

        performance = []

        for student in students:
            submissions = Submission.objects.filter(
                user=student,
                assignment__class_obj=class_obj
            )
            completed = submissions.filter(status='completed')
            results = Result.objects.filter(submission__in=completed)
            
            performance.append({
                'student_id': student.id,
                'student_name': f"{student.first_name} {student.last_name}",
                'student_email': student.email,
                'total_submissions': submissions.count(),
                'completed_submissions': completed.count(),
                'average_ai_percentage': results.aggregate(Avg('ai_percentage'))['ai_percentage__avg'] or 0,
                'average_grammar_score': results.aggregate(Avg('grammar_score'))['grammar_score__avg'] or 0,
                'flagged_submissions': results.filter(ai_percentage__gte=70).count()
            })
        
        serializer = StudentPerformanceSerializer(performance, many=True)
        return Response(serializer.data)


    @action(detail=True, methods=['get'])
    def assignment_submissions(self, request, pk=None):
        """Get all submissions for an assignment"""
        assignment = Assignment.objects.get(id=pk, created_by=request.user)
        submissions = assignment.submissions.filter(
            user__role='student'
        )
        
        overview = []
        for submission in submissions:
            result = None
            if hasattr(submission, 'result'):
                result = submission.result
            
            overview.append({
                'submission_id': submission.id,
                'student_name': f"{submission.user.first_name} {submission.user.last_name}",
                'student_email': submission.user.email,
                'submitted_at': submission.submitted_at,
                'status': submission.status,
                'processing_percentage': submission.processing_percentage,
                'ai_percentage': result.ai_percentage if result else None,
                'grammar_score': result.grammar_score if result else None,
                'is_flagged': result.ai_percentage >= 70 if result else False
            })
        
        serializer = SubmissionOverviewSerializer(overview, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['delete'], permission_classes=[IsTeacher])
    def delete_submission(self, request, pk=None):
        """Teacher deletes a student's submission"""
        submission = Submission.objects.get(id=pk)
        
        # Verify teacher owns the class
        if submission.assignment.class_obj.teacher != request.user:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        submission.delete()
        
        return Response({'message': 'Submission deleted'})
    


    @action(detail=False, methods=['get'])
    def teacher_overview(self, request):
        """Get teacher's overall statistics"""
        teacher = request.user
        
        # Total classes created
        total_classes = Class.objects.filter(teacher=teacher).count()
        
        # Total students (fix: use 'enrollment' not 'enrollments')
        total_students = User.objects.filter(
            enrollment__class_obj__teacher=teacher
        ).distinct().count()
        
        # Total assignments created
        total_assignments = Assignment.objects.filter(created_by=teacher).count()
        
        # Total submissions received
        total_submissions = Submission.objects.filter(
            assignment__class_obj__teacher=teacher
        ).count()
        
        return Response({
            'total_classes': total_classes,
            'total_students': total_students,
            'total_assignments': total_assignments,
            'total_submissions': total_submissions
        })