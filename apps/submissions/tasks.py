from celery import shared_task, group
from django.utils import timezone
import requests
from .models import Submission
from apps.results.models import Result, ParagraphResult
from django.conf import settings
import PyPDF2
import io


@shared_task
def extract_paragraphs_from_pdf(submission_id):
    """
    Stage 1: Extract text and create paragraph records
    """
    try:
        submission = Submission.objects.get(id=submission_id)
        submission.status = 'processing'
        submission.save()

        # Extract text from pdf
        pdf_file = submission.file.open('rb')
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        full_text = ""
        for pages in pdf_reader.pages:
            full_text += pages.extract_text()

        pdf_file.close()

        # Split in to peragraphs
        paragraphs = [p.strip() for p in full_text.split('\n\n') if p.strip()]

        # Create result object
        result = Result.objects.create(
            submission = submission,
            total_paragraphs = len(paragraphs)
        )

        # Create ParagraphResult records (status = pending)
        for idx, para_text in enumerate(paragraphs, 1):
            ParagraphResult.objects.create(
                result=result,
                paragraph_number=idx,
                text_content=para_text,
                status='pending',
            )

        # Update submission
        submission.total_paragraphs = len(paragraphs)
        submission.save()

        # Queue paragraph processing tasks
        queue_paragraph_tasks(submission_id, submission.user.role)

        return {'status': 'extracted', 'paragraphs': len(paragraphs)}
    except Exception as e:
        submission.status = 'failed'
        submission.save()
        raise e
    

def queue_paragraph_tasks(submission_id, user_role):
    """
    Queue individual paragraph processing tasks
    """
    submission = Submission.objects.get(id=submission_id)
    result = submission.result

    # Determinr priority
    priority_map = {
        'teacher':10,
        'student':5,
        'guest':1,
    }
    priority = priority_map.get(user_role, 1)

    # Get all pending paragraphs
    pending_paragraphs = result.paragraphs.filter(status='pending')

    # Queue each paragraph
    for paragraph in pending_paragraphs:
        process_paragraph.apply_async(
            args=[paragraph.id],
            priority=priority,
            queue='default'
        )

@shared_task(bind=True, max_retries=3)
def process_paragraph(self, paragraph_id):
    """
    Stage 2: process individal paragraphs through ML
    and we will consider each paragraph as individual task
    """
    try:
        paragraph = ParagraphResult.objects.get(id=paragraph_id)
        paragraph.status = 'processing'
        paragraph.processing_started_at = timezone.now()
        paragraph.save()

        # Call ML service for this paragraph
        ml_service_url =f"{settings.ML_SERVICE_URL}/api/analyze_paragraph"

        response = response.post(
            ml_service_url,
            json = {'text':paragraph.text_content},
            headers = {'X-API-KEY':settings.ML_SERVICE_API_KEY},
            timeout = 30,
        )

        if response.status_code != 200:
            raise Exception(f"ML service error: {response.text}")

        ml_data = response.json()

        # Update paragraphs with results
        paragraph.ai_probability = ml_data['ai_probability']
        paragraph.confidence = ml_data['confidence']
        paragraph.grammar_issues = ml_data['grammar_issues']
        paragraph.sentence_highlights = ml_data['sentence_highlights']
        paragraph.features = ml_data['features']
        paragraph.status = 'completed'
        paragraph.processing_completed_at = timezone.now()
        paragraph.save()

        # Update submission process
        submission = paragraph.result.submission
        submission.processed_paragraphs = submission.result.paragraphs.filter(status='completed').count()
        submission.save()

        # Update result completion
        paragraph.result.update_completion()

        # If all ok then generate report
        if paragraph.result.is_complete:
            generate_report.delay(paragraph.result.id)

        return {'status': 'success', 'paragraph': paragraph_id}
    
    except ParagraphResult.DoesNotExist:
        return {'status': 'error', 'message': 'Paragraph not found'}
    
    except Exception as e:
        paragraph.status = 'failed'
        paragraph.retry_count += 1
        paragraph.save()
        
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=30 * (2 ** paragraph.retry_count))


@shared_task
def generate_report(result_id):
    """
    Stage 3 : Generate pdf report after all paragraphs processed
    """

    try:
        result = Result.objects.get(id=result_id)

        # Here we will call report generation service
        # and implement pdf generation

        result.submission.status = 'completed'
        result.submission.processed_at = timezone.now()
        result.submission.save()

        return{'status':'report_generated'}
    except Exception as e:
        return {'status':'error', 'message':str(e)}
    