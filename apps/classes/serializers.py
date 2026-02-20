from rest_framework import serializers
from .models import Class, Enrollment
from authentication.serializers import UserSerializer

class ClassSerializer(serializers.ModelSerializer):
    """serializer for class model"""
    teacher = UserSerializer(readonly=True)
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
        