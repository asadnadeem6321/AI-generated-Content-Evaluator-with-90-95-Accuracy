"""
Results app URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ResultViewSet

router = DefaultRouter()
router.register('', ResultViewSet, basename='result')
app_name = 'results'

urlpatterns = [
    path('', include(router.urls))
]