from django.db import models
from submissions.models import Submission
# Create your models here.


class Result(models.Model):
    """Stores overall analysis result of a submission"""
    submission = models.OneToOneField(Submission, on_delete=models.CASCADE, related_name='result')

    ai_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text='AI content percentage')