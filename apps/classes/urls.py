"""
Classes app URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClassViewSet


router = DefaultRouter()
router.register('',ClassViewSet, basename='class')
app_name = 'classes'

urlpatterns = [
    path('', include(router.urls))
    
]