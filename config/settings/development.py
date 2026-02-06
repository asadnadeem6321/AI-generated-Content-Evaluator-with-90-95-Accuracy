"""
Development settings
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Development-specific installed apps
INSTALLED_APPS += [
    'django_extensions',  # Provides shell_plus and other utilities
]

# Development middleware
MIDDLEWARE += [
    'apps.core.middleware.request_logging_middleware',  # Log all requests in dev
]

# Console email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable HTTPS redirect in development
SECURE_SSL_REDIRECT = False

# Less strict CORS in development
CORS_ALLOW_ALL_ORIGINS = True

# Django Debug Toolbar (optional - install with: pip install django-debug-toolbar)
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
# INTERNAL_IPS = ['127.0.0.1']

# Show detailed error pages
DEBUG_PROPAGATE_EXCEPTIONS = True

# Less restrictive Content Security Policy in development
# CSP_DEFAULT_SRC = ("'self'", "'unsafe-inline'", "'unsafe-eval'")

# Development-specific logging (more verbose)
LOGGING['loggers']['django']['level'] = 'DEBUG'
LOGGING['loggers']['apps']['level'] = 'DEBUG'
LOGGING['handlers']['console']['level'] = 'DEBUG'

print("🚀 Running in DEVELOPMENT mode")