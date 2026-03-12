from django.db import models
from apps.authentication.models import User  
from apps.classes.models import Class
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

    # processing tracking
    total_paragraphs = models.IntegerField(default=0, help_text='Total paragraphs extracted from PDF')
    processed_paragraphs = models.IntegerField(default=0, help_text='Paragraphs analyzed so far')

    # Teacher controls for processing
    is_paused = models.BooleanField(default=False, help_text='Teacher paused this submission')
    paused_at = models.DateTimeField(blank=True, null=True)
    paused_by =models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='paused_submission')

    submitted_at = models.DateTimeField(auto_now_add=True)
    processed_at =  models.DateTimeField(null=True, blank=True)

    extension_requested = models.BooleanField(default=False)
    extension_granted = models.BooleanField(default=False)
    extension_reason = models.TextField(blank=True)

    class Meta:
        db_table = 'submissions'
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['user', '-submitted_at']),
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
    
    def processing_percentage(self):
        '''Calculate Processing Progress'''
        if self.total_paragraphs == 0:
            return 0
        return round((self.processed_paragraphs / self.total_paragraphs) * 100, 2)

    def pause(self, user):
        '''Pause submission processing'''
        self.is_paused = True
        self.paused_at = timezone.now()
        self.paused_by = user
        self.save()

    def resume(self, user):
        '''Pause submission processing'''
        self.is_paused = False
        self.paused_at = None
        self.paused_by = None
        self.save()