from django.db import models
from apps.submissions.models import Submission
# Create your models here.


class Result(models.Model):
    """Stores overall analysis result of a submission"""
    submission = models.OneToOneField(Submission, on_delete=models.CASCADE, related_name='result')

    ai_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text='AI content percentage')
    human_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text='Human content percentage')
    grammar_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text='Grammer score out of 100')

    total_paragraphs = models.IntegerField(default=0)
    ai_paragraphs = models.IntegerField(default=0 , help_text='Number of AI-flagged paragraphs')

    # COmpletion tracking
    is_complete = models.BooleanField(default=False, help_text='All paragraphs analyzed')
    completed_paragraphs = models.IntegerField(default=0, help_text='Paragraphs with results')

    report_pdf = models.FileField(upload_to='reports/%Y/%m/%d/', null=True, blank= True)
    processing_time = models.FloatField(help_text='Processing time in seconds', null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'results'
        ordering = ['-created_at']

    def __str__(self):
        return f'Result for {self.submission.assignment_name}'
    
    @property
    def completion_percentage(self):
        """Calculate result completion progress"""
        if self.total_paragraphs == 0:
            return 0
        return round((self.completed_paragraphs / self.total_paragraphs) * 100, 2)
    
    def update_completion(self):
        """Update completion status and calculate final scores"""
        completed = self.paragraphs.filter(status='completed').count()
        self.completed_paragraphs = completed
        
        if completed == self.total_paragraphs and self.total_paragraphs > 0:
            self.is_complete = True
            self.calculate_final_scores()
        
        self.save()
    
    def calculate_final_scores(self):
        """Calculate overall AI percentage and grammar score"""
        paragraphs = self.paragraphs.filter(status='completed')
        
        if paragraphs.exists():
            # Calculate average AI percentage
            total_ai = sum(float(p.ai_probability) for p in paragraphs)
            self.ai_percentage = round((total_ai / paragraphs.count()) * 100, 2)
            self.human_percentage = round(100 - self.ai_percentage, 2)
            
            # Count AI-flagged paragraphs
            self.ai_paragraphs = paragraphs.filter(is_flagged=True).count()
            
            # Calculate grammar score (100 - error rate)
            total_errors = sum(p.grammar_error_count for p in paragraphs)
            total_words = sum(p.features.get('word_count', 0) for p in paragraphs)
            if total_words > 0:
                error_rate = (total_errors / total_words) * 100
                self.grammar_score = max(0, round(100 - error_rate, 2))
            
            self.save()

    

class ParagraphResult(models.Model):
    """Store paragraph level detection result"""

    AI_LEVEL_CHOICES = [
        ('human','Human'),                  # 0 - 30%
        ('low_ai','Low AI'),                # 30 - 50%
        ('moderate_ai','Moderate AI'),      # 50 - 70%
        ('high_ai','High AI'),              # 70 - 100%
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    result = models.ForeignKey(Result, on_delete=models.CASCADE, related_name='paragraphs')
    paragraph_number = models.IntegerField(default=0)
    text_content = models.TextField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    ai_probability = models.DecimalField(max_digits=5, decimal_places=4, help_text='AI probability 0-1')
    ai_level = models.CharField(max_length=20, choices=AI_LEVEL_CHOICES)
    is_flagged = models.BooleanField(default=False, help_text='Flagged as AI if >0.6')
    confidence = models.DecimalField(max_digits=5, decimal_places=4, help_text='Model confidence')

    features = models.JSONField(help_text='All 43 extracted features')
    grammar_issues = models.JSONField(default=list,help_text='List of grammar errors with positions')

    # Sentence highlight
    sentence_highlights = models.JSONField(
        default=list,
        help_text='Sentence positions and types for highlighting'
    )

    # Pre-generated highlighted HTML
    highlighted_html = models.TextField(
        blank=True,
        help_text='HTML with highlighted AI and grammar sections'
    )

    # Processing meta data
    processing_started_at = models.DateTimeField(null=True, blank=True)
    processing_completed_at = models.DateTimeField(null=True, blank=True)
    retry_count = models.IntegerField(default=0)


    class Meta:
        db_table = 'paragraph_results'
        ordering = ['paragraph_number']
        unique_together = ['result', 'paragraph_number']

    def __str__(self):
        return f'paragraph {self.paragraph_number} - {self.ai_level} ({self.status})'

    def save(self, *args, **kwargs):
        """Auto calculate AI level"""
        ai_prob = float(self.ai_probability)
        if ai_prob >= 0.70:
            self.ai_level = 'high_ai'
            self.is_flagged = True
        elif ai_prob >= 0.50:
            self.ai_level = 'moderate_ai'
            self.is_flagged = True
        elif ai_prob >= 0.30:
            self.ai_level = 'low_ai'
        else:
            self.ai_level = 'human'

        super().save(*args, **kwargs)
    
    @property
    def grammar_error_count(self):
        """Count grammar errors in this paragraph"""
        return len(self.grammar_issues)

