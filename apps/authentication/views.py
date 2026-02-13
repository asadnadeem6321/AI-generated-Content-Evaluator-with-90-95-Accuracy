from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

# Models import 
from .models import User

# Serializers import
from .serializers import RegisterSerializer, UserSerializer

# Create your views here.

class AuthViewSet(viewsets.GenericViewSet):

    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action == 'register':
            return RegisterSerializer
        return UserSerializer
    
    def get_permissions(self):
        if self.action == ['register', 'login']:
            return [AllowAny()]
        return [IsAuthenticated()]
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        '''
        User Registration
        
        request: 
            email, 'email', 'username', 'password', 'confirm_password', 'first_name', 'last_name', 'role'

        response:
            user, token{refresh, access}
        '''
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Creating token for this user
        refresh = RefreshToken.for_user(user)

        return Response({
            'user':UserSerializer(user).data,
            'tokens':{
                'refresh':str(refresh),
                'access':str(refresh.access_token),
            }
            }, status=status.HTTP_200_OK)
    

    @action(detail=False, methods=['get', 'put', 'patch'])
    def profile(self, request):
        '''
        Get or update user profile

        used in dashboard to show user profile and update it
        '''
        if request.method == 'get':
            serializer = UserSerializer(request.user)
            return Response(serializer.data)
        
        serializer = UserSerializer(request.user, data = request.data, partial=True )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
        