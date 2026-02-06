"""
Settings package initialization
Automatically loads appropriate settings based on environment
"""

from decouple import config

# Determine which settings to use
ENVIRONMENT = config('ENVIRONMENT', default='development')

if ENVIRONMENT == 'production':
    from .production import *
elif ENVIRONMENT == 'development':
    from .development import *
else:
    from .development import *