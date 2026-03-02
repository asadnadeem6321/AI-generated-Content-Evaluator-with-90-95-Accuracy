from celery import shared_task
from django.utils import timezone
import requests
from .models import Submission
from apps.results.models import Result, ParagraphResult
from django.conf import settings

@shared_task(bind=True, max_retries=3)
def process_submission(self, submission_id):
    """
    Process pdf submission through ML service

    1. Update submission result to 'processing'
    2. call fast api for ML service
    3. store results in database
    4. update submission status to 'complete'
    """

    try:
        # Get submission
        submission = Submission.objects.get(id = submission_id)
        submission.status = 'processing'
        submission.save()

        # Call ML Service 
        ml_service_url = f'{settings.ML_SERVICE_URL}/api/analyze'

        with submission.file.open('rb') as f:
            file = {'file': (submission.original_filename, f, 'application/pdf')}
            headers = {'X-API-KEY': settings.ML_SERVICE_API_KEY}

            response = requests.post(
                ml_service_url,
                files=file,
                headers=headers,
                timeout=300 # 5 min
            )

            if response.status_code != 200:
                raise Exception(f"ML service error: {response.text}")
            
            # Parse ML response
            ml_data = response.json()

            # Result object
            result = Result.objects.create(
                submission=submission,
                ai_percentage=ml_data['ai_percentage'],
                human_percentage=ml_data['human_percentage'],
                grammar_score=ml_data['grammar_score'],
                total_paragraphs=ml_data['total_paragraphs'],
                ai_paragraphs=ml_data['ai_paragraphs'],
                processing_time=ml_data['processing_time']
            )

            # Pragraph result object
            for para_data in ml_data['paragraphs']:
                ParagraphResult.objects.create(
                    result=result,
                    paragraph_number=para_data['paragraph_number'],
                    text_content=para_data['text_content'],
                    ai_probability=para_data['ai_probability'],
                    confidence=para_data['confidence'],
                    grammar_issues=para_data['grammar_issues'],
                    features=para_data['features']
                )

            # Update submission status
            submission.status = 'completed'
            submission.processed_at = timezone.now()
            submission.save()

            return {'status': 'success', 'submission_id': str(submission_id)}
        
    except Submission.DoesNotExist:
        return {'status': 'error', 'message': 'Submission not found'}
        
    except Exception as e:
        # Retry on failure
        submission.status = 'failed'
        submission.save()
        
        # Retry task
        raise self.retry(exc=e, countdown=60)  # Retry after 60 seconds