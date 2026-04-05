from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DashboardViewSet

router = DefaultRouter()
router.register('', DashboardViewSet, basename='dashboard')

app_name = 'dashboard'

urlpatterns = [
    path('', include(router.urls)),
]