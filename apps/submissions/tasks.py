from celery import shared_task
from django.utils import timezone
from django.conf import settings
import requests
import re
from .models import Submission
from apps.results.models import Result, ParagraphResult
import logging

logger = logging.getLogger(__name__)


@shared_task
def extract_paragraphs_from_pdf(submission_id):
    """
    Stage 1: Extract paragraphs from PDF and create records
    """
    try:
        submission = Submission.objects.get(id=submission_id)
        submission.status = 'processing'
        submission.save()
        
        logger.info(f"📄 Extracting paragraphs from submission {submission_id}")
        
        # Get PDF file from MinIO
        pdf_file = submission.file.open('rb')
        
        # Call FastAPI to extract and analyze PDF
        ml_service_url = f"{settings.ML_SERVICE_URL}/api/analyze_pdf"
        
        files = {'file': (submission.original_filename, pdf_file, 'application/pdf')}
        headers = {
            'X-API-Key': settings.ML_SERVICE_API_KEY or 'ai-content-evaluator-by-salman-and-ali'
        }
        
        response = requests.post(
            ml_service_url,
            files=files,
            headers=headers,
            timeout=300  # 5 minutes timeout
        )
        
        pdf_file.close()
        
        if response.status_code != 200:
            raise Exception(f"ML service error: {response.text}")
        
        ml_data = response.json()
        paragraphs = ml_data.get('paragraphs', [])
        paragraph_count = len(paragraphs)

        if paragraph_count == 0:
            raise Exception('ML service returned no paragraph data')

        # Handle cases where the service reports a single paragraph but the text contains multiple paragraphs
        if paragraph_count == 1:
            raw_text = paragraphs[0].get('paragraph_text', '')
            split_paras = re.split(r'\n\s*\n+', raw_text.strip())
            if len(split_paras) > 1:
                logger.warning(
                    'ML service returned 1 paragraph but text contains %s paragraphs; splitting locally.',
                    len(split_paras)
                )
                base_para = paragraphs[0]
                paragraphs = [
                    {
                        **{k: v for k, v in base_para.items() if k != 'paragraph_text'},
                        'paragraph_text': text.strip()
                    }
                    for text in split_paras if text.strip()
                ]
                paragraph_count = len(paragraphs)

        logger.info(f"✅ Received analysis for {paragraph_count} paragraphs")
        
        # Create Result record
        document_summary = ml_data['document_summary']
        
        result = Result.objects.create(
            submission=submission,
            ai_percentage=document_summary['average_ai_percentage'],
            human_percentage=document_summary['average_human_percentage'],
            grammar_score=0.0,  # Not calculated in BERT approach
            total_paragraphs=paragraph_count,
            ai_paragraphs=document_summary['paragraphs_flagged_as_ai'],
            is_complete=True,
            completed_paragraphs=paragraph_count
        )
        
        # Create ParagraphResult records
        for idx, para_data in enumerate(paragraphs, start=1):
            ai_prob = para_data['ai_percentage'] / 100.0  # Convert to 0-1
            paragraph_index = idx
            
            ParagraphResult.objects.create(
                result=result,
                paragraph_number=paragraph_index,
                text_content=para_data['paragraph_text'],
                ai_probability=ai_prob,
                confidence=0.90,  # BERT typically has high confidence
                status='completed',
                grammar_issues=[],  # Empty for now
                sentence_highlights=[],  # Empty for now
                highlighted_html='',  # Empty for now
                features={
                    'bert_score': para_data.get('bert'),
                    'perplexity': para_data.get('perplexity')
                }
            )
        
        # Update submission
        submission.total_paragraphs = paragraph_count
        submission.processed_paragraphs = paragraph_count
        submission.status = 'completed'
        submission.processed_at = timezone.now()
        submission.save()
        
        logger.info(f"✅ Submission {submission_id} completed successfully")
        
        return {
            'status': 'success',
            'submission_id': str(submission_id),
            'paragraphs': paragraph_count
        }
        
    except Submission.DoesNotExist:
        logger.error(f"Submission {submission_id} not found")
        return {'status': 'error', 'message': 'Submission not found'}
        
    except Exception as e:
        logger.error(f"Failed to process submission {submission_id}: {str(e)}")
        submission.status = 'failed'
        submission.save()
        raise


@shared_task
def queue_submission_processing(submission_id, user_role, is_teacher_view=False):
    """
    Queue submission for processing with appropriate priority
    """
    # Determine priority
    if is_teacher_view:
        priority = 10  # HIGH - Teacher wants to see specific student NOW
    elif user_role == 'student':
        priority = 5   # MEDIUM - Class submission
    else:  # guest
        priority = 1   # LOW - Individual upload
    
    # Queue task with priority
    extract_paragraphs_from_pdf.apply_async(
        args=[submission_id],
        priority=priority,
        queue='default'
    )


def queue_paragraph_tasks(submission_id, user_role, is_teacher_view=False):
    """
    Alias for resuming paused submissions using the same queueing behavior.
    """
    return queue_submission_processing(
        submission_id=submission_id,
        user_role=user_role,
        is_teacher_view=is_teacher_view
    )