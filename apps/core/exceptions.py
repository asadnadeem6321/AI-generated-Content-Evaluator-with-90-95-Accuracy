"""
Custom exception handler for Django REST Framework
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error responses
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # Log the exception
    logger.error(f"Exception occurred: {exc}", exc_info=True)
    
    # If response is None, it's not a DRF exception
    if response is None:
        return Response(
            {
                'error': 'Internal server error',
                'detail': str(exc),
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Customize the response data
    custom_response = {
        'error': response.data.get('detail', 'An error occurred'),
        'status_code': response.status_code
    }
    
    # Add additional error details if available
    if isinstance(response.data, dict):
        custom_response.update(response.data)
    
    response.data = custom_response
    
    return response


class ValidationError(Exception):
    """Custom validation error"""
    pass


class FileUploadError(Exception):
    """Custom file upload error"""
    pass


class MLServiceError(Exception):
    """Custom ML service error"""
    pass