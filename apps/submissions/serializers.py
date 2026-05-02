from rest_framework import serializers
from django.conf import settings

from .models import Submission
from apps.classes.models import Assignment
from apps.authentication.serializers import UserSerializer


# 🔹 Submission Detail Serializer
class SubmissionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    file_url = serializers.SerializerMethodField()
    assignment_deadline = serializers.SerializerMethodField()

    class Meta:
        model = Submission
        fields = [
            'id',
            'user',
            'assignment',
            'class_obj',
            'assignment_name',
            'assignment_deadline',
            'file',
            'file_url',
            'original_filename',
            'file_size',
            'status',
            'submitted_at',
            'processed_at',
            'extension_requested',
            'extension_granted'
        ]
        read_only_fields = [
            'id',
            'user',
            'status',
            'submitted_at',
            'processed_at'
        ]

    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.file.url) if request else None
        return None

    def get_assignment_deadline(self, obj):
        """
        Get deadline from related assignment
        """
        if obj.assignment:
            return obj.assignment.deadline
        return None

    def get_class_obj(self, obj):
        if obj.assignment and obj.assignment.class_obj:
            return str(obj.assignment.class_obj.id)
        return None


# 🔹 Create Submission Serializer
class SubmissionCreateSerializer(serializers.ModelSerializer):
    assignment = serializers.PrimaryKeyRelatedField(
        queryset=Assignment.objects.all(),
        required=False,
        allow_null=True
    )
    assignment_name = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Submission
        fields = [
            'assignment',
            'assignment_name',
            'file'
        ]

    def validate_file(self, file):
        # Only PDF allowed
        if not file.name.lower().endswith('.pdf'):
            raise serializers.ValidationError("Only PDF files are allowed")

        # File size check
        if file.size > settings.MAX_UPLOAD_SIZE:
            raise serializers.ValidationError("File size must be less than 50MB")

        return file

    def validate(self, attrs):
        """
        Ensure assignment-linked submissions have an assignment and save the title.
        """
        assignment = attrs.get('assignment')
        assignment_name = attrs.get('assignment_name')

        if not assignment and not assignment_name:
            raise serializers.ValidationError(
                'Either assignment or assignment_name must be provided.'
            )

        if assignment and not assignment_name:
            attrs['assignment_name'] = assignment.title

        return attrs


# 🔹 Extension Request Serializer
class ExtensionRequestSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=500)