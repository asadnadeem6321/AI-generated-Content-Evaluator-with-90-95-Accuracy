from rest_framework import serializers
from .models import Result, ParagraphResult

class ParagraphResultSerializer(serializers.ModelSerializer):
    """Serializer for paragraph level results"""
    grammer_error_count = serializers.ReadOnlyField()

    class Meta:
        model = ParagraphResult
        fields = [
            'id', 'paragraph_number', 'text_content', 'ai_probability',
            'ai_level', 'is_flagged', 'confidence', 'grammar_issues',
            'grammar_error_count', 'features'
        ]


class ResultSerializer(serializers.ModelSerializer):
    """Serializer for overall results"""

    paragraphs = ParagraphResultSerializer(many=True, read_only=True)
    report_url = serializers.SerializerMethodField()
    student_name = serializers.SerializerMethodField()
    student_email = serializers.ReadOnlyField(source='submission.user.email')
    assignment_name = serializers.ReadOnlyField(source='submission.assignment_name')

    class Meta:
        model = Result
        fields = [
            'id', 'submission', 'student_name', 'student_email',
            'assignment_name', 'ai_percentage', 'human_percentage',
            'grammar_score', 'total_paragraphs', 'ai_paragraphs',
            'report_pdf', 'report_url', 'processing_time', 'created_at',
            'paragraphs'
        ]
        read_only_fields = ['id', 'created_at']

    def get_report_url(self, obj):
        if obj.report_pdf:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.report_pdf.url)
        return None

    def get_student_name(self, obj):
        user = getattr(obj.submission, 'user', None)
        if user:
            full_name = user.get_full_name()
            return full_name if full_name else user.username
        return None


class ResultSummarySerializer(serializers.ModelSerializer):
    """Serializer for result summary without paragraph details"""

    report_url = serializers.SerializerMethodField()
    student_name = serializers.SerializerMethodField()
    student_email = serializers.ReadOnlyField(source='submission.user.email')
    assignment_name = serializers.ReadOnlyField(source='submission.assignment_name')
    
    class Meta:
        model = Result
        fields = [
            'id', 'submission', 'student_name', 'student_email',
            'assignment_name', 'ai_percentage', 'human_percentage',
            'grammar_score', 'total_paragraphs', 'ai_paragraphs',
            'report_url', 'processing_time', 'created_at'
        ]
    
    def get_report_url(self, obj):
        if obj.report_pdf:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.report_pdf.url)
        return None

    def get_student_name(self, obj):
        user = getattr(obj.submission, 'user', None)
        if user:
            full_name = user.get_full_name()
            return full_name if full_name else user.username
        return None