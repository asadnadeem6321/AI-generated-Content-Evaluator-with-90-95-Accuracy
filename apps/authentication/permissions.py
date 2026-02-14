from rest_framework import permissions


class IsTeacher(permissions.BasePermission):
    """Only teachers can access"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_teacher()


class IsStudent(permissions.BasePermission):
    """Only students can access"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_student()


class IsGuest(permissions.BasePermission):
    """Only guests can access"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_guest()


class IsTeacherOrReadOnly(permissions.BasePermission):
    """Teachers can edit, others can only read"""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:  
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.is_teacher()