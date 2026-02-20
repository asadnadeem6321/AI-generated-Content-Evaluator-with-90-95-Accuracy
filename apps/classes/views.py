from rest_framework import viewsets, status
from django.shortcuts import render
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from authentication.permissions import IsTeacher, IsStudent
# Models import 
from .models import Class, Enrollment
# Serializers
from .serializers import (
    ClassSerializer,
    ClassCreateSerializer,
    EnrollmentSerializer,
    EnrolledStudentSerializer
)

# Create your views here.

class ClassViewSet(viewsets.ModelViewSet):
    """Viewset fot class CURD operations"""

    queryset = Class.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return ClassCreateSerializer
        elif self.action == 'enroll':
            return EnrollmentSerializer
        elif self.action == 'students':
            return EnrolledStudentSerializer
        else:
            return ClassSerializer
        

    def get_permissions(self):
        """Setting up role base access"""
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'student']:
            return [IsTeacher()]
        elif self.action in ['enroll']:
            return [IsStudent()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        """Guest can't see or access classes"""
        user = self.request.user
        if user.is_teacher():
            return Class.objects.filter(teacher=user)
        elif user.is_student():
            return Class.objects.filter(students=user)
        else:
            Class.objects.none() # Guest can't see classes
    

    @action(detail=True, methods=['post'])
    def enroll(self, request, pk=None):
        """Student enrolled in class using class code (student's api)
        
        POST /api/classes/{CODE}/enroll/
        """
        serializer = EnrollmentSerializer(data={'code':pk})
        serializer.is_valid(raise_exception=True)

        class_obj = Class.objects.get(code = serializer.validated_data['code'])

        # Check if student is already enrolled in class
        if Enrollment.objects.filter(student=request.user, class_obj=class_obj).exists():
            return Response({'error':'Already enrolled'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Enroll student
        Enrollment.objects.create(student=request.user, class_obj=class_obj)
        return Response({'message':'Successfully enrolled', 'class':ClassSerializer(class_obj).data})
    

    @action(detail=True, methods=['get'])
    def students(self, request, pk=None):
        """
        Get all enrolled students in the class (teacher's api)
        """
        class_obj = self.get_object()
        enrollments = class_obj.enrollemant.all()
        serializer = EnrolledStudentSerializers(enrollments, many=True)
        return Response(serializer.data)

