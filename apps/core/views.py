"""
Core app views
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.db import connection
from django.core.cache import cache
import sys


class HealthCheckView(APIView):
    """
    Health check endpoint to verify system status
    GET /health/
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        Check the health of the application
        """
        health_status = {
            'status': 'healthy',
            'database': self._check_database(),
            'cache': self._check_cache(),
            'python_version': sys.version,
        }
        
        # Determine overall status
        if not health_status['database'] or not health_status['cache']:
            health_status['status'] = 'unhealthy'
            return Response(health_status, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        return Response(health_status, status=status.HTTP_200_OK)
    
    def _check_database(self):
        """Check database connection"""
        try:
            connection.ensure_connection()
            return True
        except Exception as e:
            return False
    
    def _check_cache(self):
        """Check Redis cache connection"""
        try:
            cache.set('health_check', 'ok', 10)
            return cache.get('health_check') == 'ok'
        except Exception as e:
            return False