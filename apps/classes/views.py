from rest_framework import viewsets, status, serializers
from django.shortcuts import render
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.authentication.permissions import IsTeacher, IsStudent
# Models import 
from .models import Class, Enrollment, Assignment
# Serializers
from .serializers import (
    ClassSerializer,
    ClassCreateSerializer,
    EnrollmentSerializer,
    EnrolledStudentSerializer,
    AssignmentCreateSerializer,
    AssignmentSerializer,
    AssignmentUpdateSerializer
)

# Create your views here.

class ClassViewSet(viewsets.ModelViewSet):
    """Viewset fot class CURD operations"""

    queryset = Class.objects.all()
    lookup_field = 'code'
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
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'students']:
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
            return Class.objects.none()  # Guest can't see classes

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)


    @action(detail=True, methods=['post'])
    def enroll(self, request, code=None):
        """Student enrolled in class using class code (student's api)
        
        POST /api/classes/{FE16VM}/enroll/
        """
        serializer = EnrollmentSerializer(data={'code':code})
        serializer.is_valid(raise_exception=True)

        class_obj = Class.objects.get(code = serializer.validated_data['code'])

        # Check if student is already enrolled in class
        if Enrollment.objects.filter(student=request.user, class_obj=class_obj).exists():
            return Response({'error':'Already enrolled'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Enroll student
        Enrollment.objects.create(student=request.user, class_obj=class_obj)
        return Response({'message':'Successfully enrolled', 'class':ClassSerializer(class_obj).data})

    @action(detail=False, methods=['get'], permission_classes=[IsStudent])
    def enrolled(self, request):
        """Return all classes the authenticated student is enrolled in."""
        classes = self.get_queryset()
        serializer = self.get_serializer(classes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def assignments(self, request, code=None):
        """Create an assignment inside a specific class."""
        class_obj = self.get_object()
        serializer = AssignmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        assignment = Assignment.objects.create(
            class_obj=class_obj,
            title=serializer.validated_data['title'],
            description=serializer.validated_data.get('description', ''),
            deadline=serializer.validated_data['deadline'],
            max_score=serializer.validated_data['max_score'],
            allow_late_submissions=serializer.validated_data.get('allow_late_submissions', False),
            created_by=request.user,
        )

        return Response(AssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)
    @action(detail=True, methods=['get'])
    # get all assignments in a class (teacher's and student's api)
    def assignment(self, request, code=None):
        class_obj = self.get_object()
        assignments = Assignment.objects.filter(class_obj=class_obj)

        serializer = AssignmentSerializer(assignments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def students(self, request, code=None):
        """
        Get all enrolled students in the class (teacher's api)
        """
        class_obj = self.get_object()
        enrollments = class_obj.enrollement.all()
        serializer = EnrolledStudentSerializer(enrollments, many=True)
        return Response(serializer.data)

        
    @action(detail=True, methods=['post'], permission_classes=[IsStudent])
    # Student leaves the class (student's api)
    def leave(self, request, code=None):
        class_obj = self.get_object()

        enrollment = Enrollment.objects.filter(
            student=request.user,
            class_obj=class_obj
        ).first()

        if not enrollment:
            return Response(
                {"error": "You are not enrolled in this class"},
                status=status.HTTP_400_BAD_REQUEST
            )

        enrollment.delete()

        return Response(
            {"message": "You left the class successfully"}
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsTeacher])
    # Teacher removes a student from the class (teacher's api)
    def remove_student(self, request, code=None):
        class_obj = self.get_object()
        student_id = request.data.get("student_id")

        if not student_id:
            return Response(
                {"error": "student_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        enrollment = Enrollment.objects.filter(
            student_id=student_id,
            class_obj=class_obj
        ).first()

        if not enrollment:
            return Response(
                {"error": "Student not found in this class"},
                status=status.HTTP_404_NOT_FOUND
            )

        enrollment.delete()

        return Response(
            {"message": "Student removed from class successfully"}
        )

# Assignment view sset
class AssignmentViewSet(viewsets.ModelViewSet):
    """Assignment curd operations"""

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return AssignmentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AssignmentUpdateSerializer
        return AssignmentSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'extend_deadline']:
            return [IsTeacher()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        user = self.request.user
        class_id = self.request.query_params.get('class_id')
        
        if user.is_teacher():
            queryset = Assignment.objects.filter(created_by=user)
        elif user.is_student():
            queryset = Assignment.objects.filter(class_obj__students=user)
        else:
            return Assignment.objects.none()
        
        if class_id:
            queryset = queryset.filter(class_obj_id=class_id)
        
        return queryset
    
    def perform_create(self, serializer):
        class_id = serializer.validated_data.get('class_id')
        if not class_id:
            raise serializers.ValidationError({'class_id': 'This field is required.'})

        try:
            class_obj = Class.objects.get(id=class_id, teacher=self.request.user)
        except Class.DoesNotExist:
            raise serializers.ValidationError({'class_id': 'Class not found or you are not the teacher for this class.'})

        serializer.save(created_by=self.request.user, class_obj=class_obj)

    @action(detail=True, methods=['post'])
    def extend_deadline(self, request, pk=None):
        """Teacher extends assignment deadline"""
        assignment = self.get_object()
        new_deadline = request.data.get('new_deadline')
        
        if not new_deadline:
            return Response({'error': 'new_deadline required'}, status=status.HTTP_400_BAD_REQUEST)
        
        assignment.extend_deadline(new_deadline)
        
        return Response({
            'message': 'Deadline extended',
            'new_deadline': assignment.deadline
        })