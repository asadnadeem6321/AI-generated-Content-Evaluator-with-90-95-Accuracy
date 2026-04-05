from rest_framework import serializers
from .models import Class, Enrollment, Assignment
from apps.authentication.serializers import UserSerializer
from django.utils import timezone

class ClassSerializer(serializers.ModelSerializer):
    """serializer for class model"""
    teacher = UserSerializer(read_only=True)
    student_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Class
        fields =['id', 'name', 'code', 'description', 'teacher', 'student_count', 'is_active', 'created_at']
        read_only_fields = ['id', 'code', 'teacher', 'created_at']


class ClassCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating class"""
    class Meta:
        model = Class
        fields = ['name', 'description']


class EnrollmentSerializer(serializers.ModelSerializer):
    """Serializer for enrolling in class with code """
    
    code = serializers.CharField(max_length = 6)

    def validate_code(self, value):
        try:
            Class.objects.get(code=value.upper(), is_active=True)
        except:
            raise serializers.ValidationError("Invalid code")
        return value.upper()

class EnrolledStudentSerializer(serializers.ModelSerializer):
    """Serializers for enrolled students"""
    student = UserSerializer()
    class Meta:
        model = Enrollment
        fields = ['id','student', 'enrolled_at']


class AssignmentSerializer(serializers.ModelSerializer):
    """Serializer for assignments"""
    created_by = UserSerializer(read_only=True)
    submission_count = serializers.IntegerField(read_only=True)
    is_past_deadline = serializers.BooleanField(read_only=True)

    class Meta:
        model = Assignment
        fields = [
            'id', 'class_obj', 'title', 'description', 'deadline', 
            'max_score', 'created_by', 'created_at', 'updated_at',
            'is_active', 'allow_late_submissions', 'submission_count',
            'is_past_deadline'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

class AssignmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating assignment"""
    class Meta:
        model = Assignment
        fieds = ['title', 'description', 'deadline', 'max_score', 'allow_late_submissions']

    def validate_deadline(self, value):
        if value > timezone.now():
            raise serializers.ValidationError("Deadline cannot be in the past")
        return value

class AssignmentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating assignment"""
    class Meta:
        model = Assignment
        fields = ['title', 'description', 'deadline', 'max_score', 'is_active', 'allow_late_submissions']