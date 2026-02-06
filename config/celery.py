"""
Celery configuration for AI Detection Backend
"""
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Create Celery app
app = Celery('ai_detection')

# Load config from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed apps
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Optional: Configure task routes
app.conf.task_routes = {
    'apps.submissions.tasks.process_submission': {'queue': 'submissions'},
    'apps.core.tasks.cleanup_old_files': {'queue': 'maintenance'},
}

# Optional: Configure periodic tasks (beat schedule)
app.conf.beat_schedule = {
    'cleanup-old-files-daily': {
        'task': 'apps.core.tasks.cleanup_old_files',
        'schedule': 86400.0,  # Run daily (24 hours)
    },
}

@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery"""
    print(f'Request: {self.request!r}')