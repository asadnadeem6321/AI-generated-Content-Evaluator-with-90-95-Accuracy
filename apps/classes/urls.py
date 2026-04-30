"""
Classes app URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClassViewSet, AssignmentViewSet


router = DefaultRouter()
router.register('', ClassViewSet, basename='class')
router.register('assignments', AssignmentViewSet, basename='assignment')

app_name = 'classes'

urlpatterns = [
    path('', include(router.urls))
    
]