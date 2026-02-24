from rest_framework import serializers
from django.conf import settings
from .models import Submission
from authentication.serializers import UserSerializer

class SubmissionSerializer(serializers.ModelSerializer):
    """Serializers for submissions"""
    user = UserSerializer(read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Submission
        fields = [
            'id', 'user', 'class_obj', 'assignment_name', 'assignment_deadline',
            'file', 'file_url', 'original_filename', 'file_size', 'status',
            'submitted_at', 'processed_at', 'extension_requested', 'extension_granted'
        ]
        read_only_fields = ['id', 'user', 'status', 'submitted_at', 'processed_at']

        def get_file_url(self, obj):
            if obj.file:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(obj.file.url)
            return None
        
    class SubmissionCreateSerializer(serializers.ModelSerializer):
        """Serializer for creating submissions"""
        class Meta:
            model = Submission
            fields = ['assignment_name', 'class_obj', 'assignment_deadline', 'file']

        def validate_file(self, file):
            # Check file extension
            if not file.name.lower().endswith('.pdf'):
                raise serializers.ValidationError("Only PDF files are allowed")
            
            # Check file size
            if file.size > settings.MAX_UPLOAD_SIZE:
                raise serializers.ValidationError("File size must be less then 50MB")

            return file
        
        def validate(self, attrs):
            #  Check if past deadline
            class_obj = attrs.get('class_obj')
            deadline = attrs.get('assignment_deadline')

            if deadline and class_obj:
                pass
            return attrs
        
class ExtensionRequestSerializer(serializers.Serializer):
    """Serializer for extension requests"""
    reason = serializers.CharField(max_length=500)

        