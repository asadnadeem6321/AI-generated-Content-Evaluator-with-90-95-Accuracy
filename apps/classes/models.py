from django.db import models
from django.utils.crypto import get_random_string
from authentication.models import User
# Create your models here.

def generate_class_code():
    """Generates a unique class code consisting of 6 uppercase letters and digits.
    """
    return get_random_string(length=6, allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789').upper()

class Class(models.Model):
    """Class model for teachers to create and manage classes"""
    name = models.CharField(
        max_length=200,
        help_text='Class name (eg. BSCS sem 1 morning)'
    )
    code = models.CharField(
        max_length=6,
        unique=True,
        default=generate_class_code,
        editable=False
    )
    description = models.TextField(blank=True)
    teacher = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='classes_teaching'
    )
    students = models.ManyToManyField(
        User,
        through="Enrollment",
        related_name='classes_enrolled'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'classes'
        verbose_name = 'Class'
        verbose_name_plural = 'Classes'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.code}"
    
    def __str__(self):
        return f"{self.students.count()}"
    

class Enrollment(models.Model):
    """Student enrolled in classes"""

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    class_obj = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='enrollement'
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'enrollemant'
        unique_together = ['student', 'class_obj'] # So student can not enrolled twise
        ordering = ['-enrolled_at']

    def __str__(self):
        return f"{self.student.username} enrolled in {self.class_obj.name}"