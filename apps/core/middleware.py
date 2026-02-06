"""
Custom middleware for the application
"""
import logging
import time
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all incoming requests and responses
    """
    
    def process_request(self, request):
        """Log the incoming request"""
        request.start_time = time.time()
        
        logger.info(
            f"Request: {request.method} {request.path} "
            f"from {request.META.get('REMOTE_ADDR', 'unknown')}"
        )
        
        return None
    
    def process_response(self, request, response):
        """Log the response"""
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            logger.info(
                f"Response: {request.method} {request.path} "
                f"[{response.status_code}] - {duration:.3f}s"
            )
        
        return response


def request_logging_middleware(get_response):
    """
    Functional middleware for request logging
    """
    
    def middleware(request):
        # Log request
        start_time = time.time()
        logger.info(
            f"Request: {request.method} {request.path} "
            f"from {request.META.get('REMOTE_ADDR', 'unknown')}"
        )
        
        # Process request
        response = get_response(request)
        
        # Log response
        duration = time.time() - start_time
        logger.info(
            f"Response: {request.method} {request.path} "
            f"[{response.status_code}] - {duration:.3f}s"
        )
        
        return response
    
    return middleware