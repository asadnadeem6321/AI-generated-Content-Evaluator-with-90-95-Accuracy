from django.db import models
from authentication.models import User  
from classes.models import Class
import uuid
from django.utils import timezone
# Create your models here.

class Submission(models.Model):
    """
    Pdf submission for AI detection"""

    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('Failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='submissions', null=True, blank=True)

    assignment_name = models.CharField(max_length=225)
    assignment_deadline = models.DateTimeField(null=True, blank=True, help_text='Deadline for submission')
    file = models.FileField(upload_to='submissions/%y/%m/%d')
    original_filename = models.CharField(max_length=225)
    file_size = models.IntegerField(help_text='file size in bytes')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')

    submitted_at = models.DateTimeField(auto_now_add=True)
    processed_at =  models.DateTimeField(null=True, blank=True)

    extension_requested = models.BooleanField(default=False)
    extension_granted = models.BooleanField(default=False)
    extension_reason = models.TextField(blank=True)

    class Meta:
        db_name = 'submissions'
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['user', '-submission_at']),
            models.Index(fields=['status']),
            models.Index(fields=['assignment_deadline'])
        ]

    def __str__(self):
        return f"{self.assignment_name} - {self.user.email}"
    
    def is_past_deadline(self):
        """check if past deadline"""
        if not self.assignment_deadline:
            return False
        return timezone.now() > self.assignment_deadline
    
    def can_submit(self):
        """Check if submission is allowed"""
        if not self.assignment_deadline:
            return True
        if self.extension_granted:
            return True
        return not self.is_past_deadline()