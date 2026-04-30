'''
User model for authentication 
Support three roles Teachers, Students, Guest users
'''

import random
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone  
from datetime import timedelta
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


class OTP(models.Model):
        email = models.EmailField()
        otp = models.CharField(max_length=4)
        created_at = models.DateTimeField(auto_now_add=True)
        is_used = models.BooleanField(default=False)

#function to validate the token if it was used 
        def is_valid(self):
                return not self.is_used and timezone.now() < self.created_at + timedelta(minutes=10)

        @staticmethod
        def generate_otp():
                return str(random.randint(1000, 9999))


class PendingUserRegistration(models.Model):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    role = models.CharField(
        max_length=10,
        choices=User.ROLE_CHOICE,
        default=User.GUEST,
        help_text='User role: teacher, student, or guest'
    )
    password = models.CharField(max_length=128)
    otp = models.CharField(max_length=4)
    otp_created_at = models.DateTimeField(auto_now_add=True)
    otp_expires_at = models.DateTimeField()
    otp_is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pending_user_registrations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['otp_expires_at']),
            models.Index(fields=['otp_is_used']),
        ]

    def __str__(self):
        return f"Pending registration for {self.email}"

    def is_valid_otp(self, code):
        return (
            self.otp == code
            and not self.otp_is_used
            and self.otp_expires_at >= timezone.now()
        )

    def mark_otp_used(self):
        self.otp_is_used = True
        self.save(update_fields=['otp_is_used'])

    def refresh_otp(self, otp_code, expires_at):
        self.otp = otp_code
        self.otp_created_at = timezone.now()
        self.otp_expires_at = expires_at
        self.otp_is_used = False
        self.save(update_fields=['otp', 'otp_created_at', 'otp_expires_at', 'otp_is_used'])


class OTPVerification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='otp_verifications'
    )
    code = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        db_table = 'otp_verifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'code']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['is_used']),
        ]

    def __str__(self):
        return f"OTPVerification for {self.user.email}"

    def is_valid(self):
        return not self.is_used and self.expires_at >= timezone.now()
