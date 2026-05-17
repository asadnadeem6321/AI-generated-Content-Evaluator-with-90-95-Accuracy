# from celery import shared_task
# from django.utils import timezone
# from django.conf import settings
# import requests
# import re
# import base64
# from django.core.files.base import ContentFile
# from .models import Submission
# from apps.results.models import Result, ParagraphResult
# import logging
#
# logger = logging.getLogger(__name__)
#
#
# #
# # PDF report helpers  (unchanged)
# #
#
# def extract_pdf_bytes(payload):
#     if payload is None:
#         return None
#     if isinstance(payload, bytes):
#         return payload if payload.startswith(b'%PDF') else None
#     if isinstance(payload, str):
#         payload = payload.strip()
#         if not payload:
#             return None
#         if payload.startswith('http'):
#             response = requests.get(payload, timeout=600)
#             if response.status_code == 200 and response.content.startswith(b'%PDF'):
#                 return response.content
#             return None
#         try:
#             decoded = base64.b64decode(payload, validate=False)
#             if decoded.startswith(b'%PDF'):
#                 return decoded
#         except Exception:
#             return None
#         return None
#     if isinstance(payload, dict):
#         for candidate_key in [
#             'pdf_report_base64', 'report_pdf_base64', 'pdf_base64', 'report_base64',
#             'report_pdf', 'pdf_report', 'report', 'pdf'
#         ]:
#             if candidate_key in payload:
#                 report_bytes = extract_pdf_bytes(payload[candidate_key])
#                 if report_bytes:
#                     return report_bytes
#         for value in payload.values():
#             report_bytes = extract_pdf_bytes(value)
#             if report_bytes:
#                 return report_bytes
#         return None
#     if isinstance(payload, (list, tuple)):
#         for value in payload:
#             report_bytes = extract_pdf_bytes(value)
#             if report_bytes:
#                 return report_bytes
#     return None
#
#
# def save_report_pdf(result, report_payload):
#     if not report_payload:
#         logger.warning("No PDF report payload received for submission %s", result.submission.id)
#         return
#     report_bytes = extract_pdf_bytes(report_payload)
#     if not report_bytes:
#         logger.warning("Could not extract PDF bytes for submission %s", result.submission.id)
#         return
#     filename = f"report_{result.submission.id}.pdf"
#     result.report_pdf.save(filename, ContentFile(report_bytes), save=True)
#     logger.info("✅ PDF report saved for submission %s", result.submission.id)
#
#
# #
# # Paragraph helpers (unchanged)
# #
#
# def _split_single_paragraph(paragraphs: list) -> list:
#     if len(paragraphs) != 1:
#         return paragraphs
#     raw_text = paragraphs[0].get('paragraph_text', '')
#     split_paras = re.split(r'\n\s*\n+', raw_text.strip())
#     if len(split_paras) <= 1:
#         return paragraphs
#     logger.warning(
#         'ML service returned 1 paragraph but text contains %d sub-paragraphs; splitting locally.',
#         len(split_paras),
#     )
#     base_para = paragraphs[0]
#     return [
#         {
#             **{k: v for k, v in base_para.items() if k != 'paragraph_text'},
#             'paragraph_text': text.strip(),
#         }
#         for text in split_paras
#         if text.strip()
#     ]
#
#
# def _build_result_and_paragraphs(submission, ml_data: dict):
#     paragraphs = ml_data.get('paragraphs', [])
#     paragraphs = _split_single_paragraph(paragraphs)
#     paragraph_count = len(paragraphs)
#
#     if paragraph_count == 0:
#         raise ValueError('ML service returned no paragraph data')
#
#     logger.info("Received analysis for %d paragraphs", paragraph_count)
#
#     document_summary = ml_data['document_summary']
#
#     result = Result.objects.create(
#         submission=submission,
#         ai_percentage=document_summary['average_ai_percentage'],
#         human_percentage=document_summary['average_human_percentage'],
#         grammar_score=(
#             document_summary.get('average_grammar_score')
#             or document_summary.get('grammar_score', 0)
#         ),
#         total_paragraphs=paragraph_count,
#         ai_paragraphs=document_summary['paragraphs_flagged_as_ai'],
#         is_complete=True,
#         completed_paragraphs=paragraph_count,
#     )
#
#     paragraph_records = [
#         ParagraphResult(
#             result=result,
#             paragraph_number=idx,
#             text_content=para_data['paragraph_text'],
#             ai_probability=para_data['ai_percentage'] / 100.0,
#             confidence=0.90,
#             status='completed',
#             grammar_issues=[],
#             sentence_highlights=[],
#             highlighted_html='',
#             features={
#                 'bert_score': para_data.get('bert'),
#                 'perplexity': para_data.get('perplexity'),
#             },
#         )
#         for idx, para_data in enumerate(paragraphs, start=1)
#     ]
#
#     ParagraphResult.objects.bulk_create(paragraph_records)
#     return result, paragraph_count
#
#
#
# # Fallback helper  ← NEW
#
#
# def _defer_and_process_next(self, submission_id, exc):
#     """
#     Called when a submission fails mid-processing.
#
#     Logic:
#     - Find the oldest other 'pending' submission and kick it off immediately.
#     - Schedule the failed submission for retry after a delay.
#     - If no other submission exists, just retry this one after the delay.
#     """
#     RETRY_DELAY = 60  # seconds before retrying the failed submission
#
#     # Find another pending submission that isn't this one
#     next_submission = (
#         Submission.objects
#         .filter(status='pending')
#         .exclude(id=submission_id)
#         .order_by('created_at')   # oldest first — fair queue
#         .first()
#     )
#
#     if next_submission:
#         logger.info(
#             "Submission %s failed — processing next submission %s first, "
#             "will retry %s in %ds",
#             submission_id, next_submission.id, submission_id, RETRY_DELAY,
#         )
#         # Kick off the next one immediately
#         extract_paragraphs_from_pdf.apply_async(
#             args=[next_submission.id],
#             queue='default',
#         )
#     else:
#         logger.info(
#             "Submission %s failed and no other submissions pending — "
#             "retrying in %ds",
#             submission_id, RETRY_DELAY,
#         )
#
#     # Re-queue the failed submission after a delay regardless
#     raise self.retry(exc=exc, countdown=RETRY_DELAY)
#
#
# # Celery tasks
#
# @shared_task(bind=True, max_retries=3, default_retry_delay=60)
# def extract_paragraphs_from_pdf(self, submission_id):
#     submission = None
#     try:
#         submission = Submission.objects.get(id=submission_id)
#         submission.status = 'processing'
#         submission.save(update_fields=['status'])
#
#         logger.info("📄 Processing submission %s", submission_id)
#
#         pdf_file = submission.file.open('rb')
#         ml_service_url = f"{settings.ML_SERVICE_URL}/api/analyze_pdf"
#         headers = {
#             'X-API-Key': settings.ML_SERVICE_API_KEY or 'ai-content-evaluator-by-salman-and-ali'
#         }
#
#         response = requests.post(
#             ml_service_url,
#             files={'file': (submission.original_filename, pdf_file, 'application/pdf')},
#             headers=headers,
#             timeout=600,
#         )
#         pdf_file.close()
#
#         if response.status_code != 200:
#             raise Exception(f"ML service error {response.status_code}: {response.text}")
#
#         ml_data = response.json()
#
#         result, paragraph_count = _build_result_and_paragraphs(submission, ml_data)
#         save_report_pdf(result, ml_data.get('pdf_report_base64'))
#
#         submission.total_paragraphs = paragraph_count
#         submission.processed_paragraphs = paragraph_count
#         submission.status = 'completed'
#         submission.processed_at = timezone.now()
#         submission.save(update_fields=[
#             'total_paragraphs', 'processed_paragraphs', 'status', 'processed_at'
#         ])
#
#         logger.info("✅ Submission %s completed (%d paragraphs)", submission_id, paragraph_count)
#
#         return {
#             'status': 'success',
#             'submission_id': str(submission_id),
#             'paragraphs': paragraph_count,
#         }
#
#     except Submission.DoesNotExist:
#         logger.error("Submission %s not found", submission_id)
#         return {'status': 'error', 'message': 'Submission not found'}
#
#     except Exception as exc:
#         logger.exception("Submission %s failed: %s", submission_id, exc)
#
#         # Reset status to pending so it can be retried cleanly
#         if submission is not None:
#             submission.status = 'pending'
#             submission.save(update_fields=['status'])
#
#         # ← Skip to next submission, come back to this one later
#         _defer_and_process_next(self, submission_id, exc)
#
#
# # @shared_task
# # def queue_submission_processing(submission_id, user_role, is_teacher_view=False):
# #     if is_teacher_view:
# #         priority = 10
# #     elif user_role == 'student':
# #         priority = 5
# #     else:
# #         priority = 1
# #
# #     extract_paragraphs_from_pdf.apply_async(
# #         args=[submission_id],
# #         priority=priority,
# #         queue='default',
# #     )
#
# @shared_task
# def queue_submission_processing(submission_id, user_role, is_teacher_view=False):
#     if is_teacher_view:
#         priority = 10
#     elif user_role == 'student':
#         priority = 5
#     else:
#         priority = 1
#
#     task_result = extract_paragraphs_from_pdf.apply_async(  # 👈 renamed
#         args=[submission_id],
#         priority=priority,
#         queue='submissions',
#     )
#     Submission.objects.filter(id=submission_id).update(task_id=str(task_result.id))  # 👈
#
#
# def queue_paragraph_tasks(submission_id, user_role, is_teacher_view=False):
#     return queue_submission_processing(
#         submission_id=submission_id,
#         user_role=user_role,
#         is_teacher_view=is_teacher_view,
#     )


from celery import shared_task
from django.utils import timezone
from django.conf import settings
import requests
import re
import base64
from django.core.files.base import ContentFile
from .models import Submission
from apps.results.models import Result, ParagraphResult
import logging

logger = logging.getLogger(__name__)


#
# PDF report helpers
#

def extract_pdf_bytes(payload):
    if payload is None:
        return None
    if isinstance(payload, bytes):
        return payload if payload.startswith(b'%PDF') else None
    if isinstance(payload, str):
        payload = payload.strip()
        if not payload:
            return None
        if payload.startswith('http'):
            response = requests.get(payload, timeout=600)
            if response.status_code == 200 and response.content.startswith(b'%PDF'):
                return response.content
            return None
        try:
            decoded = base64.b64decode(payload, validate=False)
            if decoded.startswith(b'%PDF'):
                return decoded
        except Exception:
            return None
        return None
    if isinstance(payload, dict):
        for candidate_key in [
            'pdf_report_base64', 'report_pdf_base64', 'pdf_base64', 'report_base64',
            'report_pdf', 'pdf_report', 'report', 'pdf'
        ]:
            if candidate_key in payload:
                report_bytes = extract_pdf_bytes(payload[candidate_key])
                if report_bytes:
                    return report_bytes
        for value in payload.values():
            report_bytes = extract_pdf_bytes(value)
            if report_bytes:
                return report_bytes
        return None
    if isinstance(payload, (list, tuple)):
        for value in payload:
            report_bytes = extract_pdf_bytes(value)
            if report_bytes:
                return report_bytes
    return None


def save_report_pdf(result, report_payload):
    if not report_payload:
        logger.warning("No PDF report payload received for submission %s", result.submission.id)
        return
    report_bytes = extract_pdf_bytes(report_payload)
    if not report_bytes:
        logger.warning("Could not extract PDF bytes for submission %s", result.submission.id)
        return
    filename = f"report_{result.submission.id}.pdf"
    result.report_pdf.save(filename, ContentFile(report_bytes), save=True)
    logger.info("PDF report saved for submission %s", result.submission.id)


#
# Paragraph helpers
#

def _split_single_paragraph(paragraphs: list) -> list:
    if len(paragraphs) != 1:
        return paragraphs
    raw_text = paragraphs[0].get('paragraph_text', '')
    split_paras = re.split(r'\n\s*\n+', raw_text.strip())
    if len(split_paras) <= 1:
        return paragraphs
    logger.warning(
        'ML service returned 1 paragraph but text contains %d sub-paragraphs; splitting locally.',
        len(split_paras),
    )
    base_para = paragraphs[0]
    return [
        {
            **{k: v for k, v in base_para.items() if k != 'paragraph_text'},
            'paragraph_text': text.strip(),
        }
        for text in split_paras
        if text.strip()
    ]


def _build_result_and_paragraphs(submission, ml_data: dict):
    paragraphs = ml_data.get('paragraphs', [])
    paragraphs = _split_single_paragraph(paragraphs)
    paragraph_count = len(paragraphs)

    if paragraph_count == 0:
        raise ValueError('ML service returned no paragraph data')

    logger.info("Received analysis for %d paragraphs", paragraph_count)

    document_summary = ml_data['document_summary']

    result = Result.objects.create(
        submission=submission,
        ai_percentage=document_summary['average_ai_percentage'],
        human_percentage=document_summary['average_human_percentage'],
        grammar_score=(
            document_summary.get('average_grammar_score')
            or document_summary.get('grammar_score', 0)
        ),
        total_paragraphs=paragraph_count,
        ai_paragraphs=document_summary['paragraphs_flagged_as_ai'],
        is_complete=True,
        completed_paragraphs=paragraph_count,
    )

    paragraph_records = [
        ParagraphResult(
            result=result,
            paragraph_number=idx,
            text_content=para_data['paragraph_text'],
            ai_probability=para_data['ai_percentage'] / 100.0,
            confidence=0.90,
            status='completed',
            grammar_issues=[],
            sentence_highlights=[],
            highlighted_html='',
            features={
                'bert_score': para_data.get('bert'),
                'perplexity': para_data.get('perplexity'),
            },
        )
        for idx, para_data in enumerate(paragraphs, start=1)
    ]

    ParagraphResult.objects.bulk_create(paragraph_records)
    return result, paragraph_count


#
# Fallback helper
#

def _defer_and_process_next(self, submission_id, exc):
    RETRY_DELAY = 60

    next_submission = (
        Submission.objects
        .filter(status='pending')
        .exclude(id=submission_id)
        .order_by('created_at')
        .first()
    )

    if next_submission:
        logger.info(
            "Submission %s failed — processing next submission %s first, "
            "will retry %s in %ds",
            submission_id, next_submission.id, submission_id, RETRY_DELAY,
        )
        extract_paragraphs_from_pdf.apply_async(
            args=[next_submission.id],
            queue='submissions',
        )
    else:
        logger.info(
            "Submission %s failed and no other submissions pending — "
            "retrying in %ds",
            submission_id, RETRY_DELAY,
        )

    raise self.retry(exc=exc, countdown=RETRY_DELAY)


#
# Celery tasks
#

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def extract_paragraphs_from_pdf(self, submission_id):
    submission = None
    try:
        submission = Submission.objects.get(id=submission_id)

        # ── Check if terminated BEFORE starting ──────────────────────
        submission.refresh_from_db()
        if submission.status == 'terminated':
            logger.info("Submission %s was terminated — skipping", submission_id)
            return {'status': 'terminated', 'submission_id': str(submission_id)}

        submission.status = 'processing'
        submission.save(update_fields=['status'])

        logger.info("Processing submission %s", submission_id)

        pdf_file = submission.file.open('rb')
        ml_service_url = f"{settings.ML_SERVICE_URL}/api/analyze_pdf"
        headers = {
            'X-API-Key': settings.ML_SERVICE_API_KEY or 'ai-content-evaluator-by-salman-and-ali'
        }

        response = requests.post(
            ml_service_url,
            files={'file': (submission.original_filename, pdf_file, 'application/pdf')},
            headers=headers,
            timeout=600,
        )
        pdf_file.close()

        # ── Check if terminated AFTER ML call returns ─────────────────
        submission.refresh_from_db()
        if submission.status == 'terminated':
            logger.info("Submission %s terminated during ML call — discarding result", submission_id)
            return {'status': 'terminated', 'submission_id': str(submission_id)}

        if response.status_code != 200:
            raise Exception(f"ML service error {response.status_code}: {response.text}")

        ml_data = response.json()

        result, paragraph_count = _build_result_and_paragraphs(submission, ml_data)
        save_report_pdf(result, ml_data.get('pdf_report_base64'))

        submission.total_paragraphs = paragraph_count
        submission.processed_paragraphs = paragraph_count
        submission.status = 'completed'
        submission.processed_at = timezone.now()
        submission.save(update_fields=[
            'total_paragraphs', 'processed_paragraphs', 'status', 'processed_at'
        ])

        logger.info("Submission %s completed (%d paragraphs)", submission_id, paragraph_count)

        return {
            'status': 'success',
            'submission_id': str(submission_id),
            'paragraphs': paragraph_count,
        }

    except Submission.DoesNotExist:
        logger.error("Submission %s not found", submission_id)
        return {'status': 'error', 'message': 'Submission not found'}

    except Exception as exc:
        logger.exception("Submission %s failed: %s", submission_id, exc)

        if submission is not None:
            submission.refresh_from_db()
            # ── Don't overwrite terminated status ────────────────────
            if submission.status != 'terminated':
                submission.status = 'pending'
                submission.save(update_fields=['status'])

        _defer_and_process_next(self, submission_id, exc)


@shared_task
def queue_submission_processing(submission_id, user_role, is_teacher_view=False):
    if is_teacher_view:
        priority = 10
    elif user_role == 'student':
        priority = 5
    else:
        priority = 1

    task_result = extract_paragraphs_from_pdf.apply_async(
        args=[submission_id],
        priority=priority,
        queue='submissions',
    )
    # ✅ Save the REAL processing task id (extract_paragraphs_from_pdf)
    Submission.objects.filter(id=submission_id).update(task_id=str(task_result.id))


def queue_paragraph_tasks(submission_id, user_role, is_teacher_view=False):
    return queue_submission_processing(
        submission_id=submission_id,
        user_role=user_role,
        is_teacher_view=is_teacher_view,
    )