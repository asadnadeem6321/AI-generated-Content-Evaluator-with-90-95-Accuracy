from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import FileResponse
from apps.authentication.permissions import IsTeacher

# Model import
from .models import Result, ParagraphResult
# Serializer import
from .serializers import ResultSerializer, ResultSummarySerializer, ParagraphResultSerializer

# Create your views here.


class ResultViewSet(viewsets.ReadOnlyModelViewSet):
    """View set for viewing analysis results"""

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return ResultSummarySerializer
        return ResultSerializer
    
    def get_queryset(self):
        user = self.request.user
        assignment_id = self.request.query_params.get('assignment')

        if user.is_teacher():
            # Teacher can see results from assignments they own
            queryset = Result.objects.filter(
                submission__assignment__class_obj__teacher=user
            )
            if assignment_id:
                queryset = queryset.filter(submission__assignment_id=assignment_id)
            return queryset

        # Students and guest can only see their own results
        queryset = Result.objects.filter(submission__user=user)
        if assignment_id:
            queryset = queryset.filter(submission__assignment_id=assignment_id)
        return queryset


    @action(detail=True, methods=['get'])
    def report(self, request, pk=None):
        """Download pdf report"""
        result = self.get_object()
        
        if not result.report_pdf:
            return Response(
                {'error': 'Report not generated yet'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return FileResponse(
            result.report_pdf.open('rb'),
            as_attachment=True,
            filename=f'report_{result.submission.assignment_name}.pdf'
        )
    
    @action(detail=True, methods=['get'])
    def paragraphs(self, request, pk=None):
        """Get detailed paragraph-level results"""
        result = self.get_object()
        paragraphs = result.paragraphs.all()
        serializer = ParagraphResultSerializer(paragraphs, many=True)
        return Response(serializer.data)