'''
User model for authentication 
Support three roles Teachers, Students, Guest users
'''

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone  
# Create your models here.

class User(AbstractUser):
    '''
    Custom user model with roles 
    Teacher - can create classes post assignments and view submissions and results
    Student - can join class and post assignment or any deliverable
    Guest user - can use ai detection without having any class
    '''    

    # Role choice
    TEACHER = "teacher"
    STUDENT = "student"
    GUEST = "guest"

    ROLE_CHOICE =[
        (TEACHER , "teacher"),
        (STUDENT , "student"),
        (GUEST , "guest")
        
    ]

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICE,
        default=GUEST,
        help_text='User role: teacher, student, or guest'
    )
    email = models.EmailField(
        unique=True,
        help_text='Email address for login'
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)   
    updated_at = models.DateTimeField(auto_now=True)   

    class Meta:
        db_table = 'users'
        verbose_name = 'Users'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"
    
    def is_teacher(self):
        return self.role == self.TEACHER
    
    def is_student(self):
        return self.role == self.STUDENT
    
    def is_guest(self):
        return self.role == self.GUEST
    

    def can_create_class(self):
        return self.is_teacher()

    def can_join_class(self):
        return self.is_student()
    
    def can_use_detection(self):
        return self.is_guest()

