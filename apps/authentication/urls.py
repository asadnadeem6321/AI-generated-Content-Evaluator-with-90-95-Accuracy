"""
Authentication app URLs
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import AuthViewSet

router = DefaultRouter()
router.register("", AuthViewSet, basename='auth')
app_name = 'authentication'


urlpatterns = [
    path('', include(router.urls)),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]


# END POINTS OF THIS APP

# POST /api/auth/register/
# GET /api/auth/profile/
# PUT /api/auth/profile/
# POST /api/auth/token/refresh/