from django.db import models
from apps.authentication.models import User  
from apps.classes.models import Class
import uuid
from django.utils import timezone


class Submission(models.Model):
    """PDF submission for AI detection"""

    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),  
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    
    # here i link this to assignment model in class app
    assignment = models.ForeignKey(
        'classes.Assignment', 
        on_delete=models.CASCADE, 
        related_name='submissions',
        null=True,
        blank=True,
        help_text='Assignment this submission belongs to (null for guest uploads)'
    )

    # For guest 
    assignment_name = models.CharField(max_length=255, help_text='Assignment name for guest submissions')
    
    
    file = models.FileField(upload_to='submissions/%Y/%m/%d/')
    original_filename = models.CharField(max_length=255)
    file_size = models.IntegerField(help_text='File size in bytes')

    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')

    total_paragraphs = models.IntegerField(default=0, help_text='Total paragraphs extracted from PDF')
    processed_paragraphs = models.IntegerField(default=0, help_text='Paragraphs analyzed so far')

    # Teacher controls
    is_paused = models.BooleanField(default=False, help_text='Teacher paused this submission')
    paused_at = models.DateTimeField(null=True, blank=True)
    paused_by = models.ForeignKey(
        User, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='paused_submissions'
    )

    submitted_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    # Extension request from student 
    extension_requested = models.BooleanField(default=False)
    extension_granted = models.BooleanField(default=False)
    extension_reason = models.TextField(blank=True)

    class Meta:
        db_table = 'submissions'
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['user', '-submitted_at']),
            models.Index(fields=['status']),
            models.Index(fields=['assignment']),
        ]

    def __str__(self):
        if self.assignment:
            return f"{self.assignment.title} - {self.user.email}"
        return f"{self.assignment_name} - {self.user.email}"
    
    @property
    def deadline(self):
        """Get deadline from assignment or None for guest submissions"""
        if self.assignment:
            return self.assignment.deadline
        return None
    
    def is_past_deadline(self):
        """Check if past deadline"""
        deadline = self.deadline
        if not deadline:
            return False  
        return timezone.now() > deadline
    
    def can_submit(self):
        """Check if submission is allowed"""
        if not self.assignment:
            return True
        
        # Check if assignment allows late submissions
        if self.assignment.allow_late_submissions:
            return True
        
        # Check if extension granted
        if self.extension_granted:
            return True
        
        # Check deadline
        return not self.is_past_deadline()
    
    @property
    def processing_percentage(self):
        """Calculate processing progress"""
        if self.total_paragraphs == 0:
            return 0
        return round((self.processed_paragraphs / self.total_paragraphs) * 100, 2)

    def pause(self, user):
        """Pause submission processing (teacher only)"""
        self.is_paused = True
        self.paused_at = timezone.now()
        self.paused_by = user
        self.save()

    def resume(self):
        """Resume submission processing"""
        self.is_paused = False
        self.paused_at = None
        self.paused_by = None
        self.save()
    
    @property
    def class_obj(self):
        """Get class from assignment (for backward compatibility)"""
        if self.assignment:
            return self.assignment.class_obj
        return None