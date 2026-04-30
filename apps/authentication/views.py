from django.shortcuts import render
from django.contrib.auth import authenticate
from rest_framework import viewsets, serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied

# Models import 
from datetime import timedelta
from secrets import randbelow

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import PendingUserRegistration, User
from .emailServices import EmailService, OTPService
from .validators import validate_password_strength

# Serializers import
from .serializers import (
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
    VerifyOTPSerializer,
    ResendOTPSerializer,
)

# Create your views here.

class AuthViewSet(viewsets.GenericViewSet):

    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action == 'register':
            return RegisterSerializer
        if self.action == 'verify_otp':
            return VerifyOTPSerializer
        if self.action == 'resend_otp':
            return ResendOTPSerializer
        return UserSerializer
    
    def get_permissions(self):
        if self.action in ['register', 'student_login', 'teacher_login', 'verify_otp', 'resend_otp']:
            return [AllowAny()]
        return [IsAuthenticated()]
    
    @action(detail=False, methods=['post'])
    def student_login(self, request):
        """Student login endpoint."""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        user = authenticate(request, username=email, password=password)

        if not user:
            raise AuthenticationFailed('Invalid email or password')
        if not user.is_active:
            raise AuthenticationFailed('Account not verified. Please verify email OTP.')
        if not user.is_student():
            raise PermissionDenied('Use the teacher login page for teacher accounts')

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)

# Update password using old password ------------------------------------------------------------
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        user = request.user
        
        # validating all fields 
        if not current_password or not new_password or not confirm_password:
            return Response({"error": "Fill all fields"}, status=status.HTTP_400_BAD_REQUEST)
        
        # checking new and confirm passwords if they are same
        if new_password != confirm_password:
            return Response({"error": "Passwords don't match"}, status=status.HTTP_400_BAD_REQUEST)
        
        # checking the current password if exist in the database
        if not user.check_password(current_password):
            return Response({"error": "Current password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)
        
        if current_password == new_password:  # Add this check
            return Response({"error": "New password must be different"}, status=status.HTTP_400_BAD_REQUEST)
        
        # validating password 
        try:
            validate_password_strength(new_password)
        except serializers.ValidationError as e:  # Add 'as e'
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        # Change password
        user.set_password(new_password)
        user.save()
        
        # Send notification (don't return it)
        EmailService.send_password_change_notification(user)
        
        # Return success response
        return Response({"message": "Password successfully updated"}, status=status.HTTP_200_OK)

# Update password using email OTP if he user is login
    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def change_password_otp(self, request):
        user = request.user # current user
        email = request.user.email # current user's email
        
        try:
            return OTPService.generate_send_otp(email, user.first_name, user.last_name)
        except Exception as e:
            return Response({'error': 'Failed to send OTP'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
# Update password using email OTP if he user is not login
    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def change_password_otp_logout(self, request):

        email = request.data.get("email") # current user's email
        if not email:
            return Response({'error':'Email required'}, status=status.HTTP_400_BAD_REQUEST)
        try: 
            user = User.objects.get(email=email) 
        except User.DoesNotExist:
            return Response({'error':'User does not exists'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            return OTPService.generate_send_otp(email, user.first_name, user.last_name)
        except Exception:
            return Response({'error': 'Failed to send OTP'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

# confirm otp to change password
    @action(detail=False, methods=["post"])
    def confirm_password_otp(self, request):
        email = request.data.get('email') # current user's email
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")
        otp_code = request.data.get("otp_code")


        # check that the user with this email exists or not
        try:
            user = User.objects.get(email=email) #current user
        except:
            return Response({"error":"Email does not exist"}, status=status.HTTP_400_BAD_REQUEST)

        # checking for blank fields
        if not new_password or not confirm_password or not otp_code:
            return Response ({"error":"Fields are not filled"}, status=status.HTTP_400_BAD_REQUEST)
        
        # checking new and confirm passwords if they are same
        if new_password != confirm_password:
            return Response ({"error":"New password and confirm password are not same"}, status=status.HTTP_400_BAD_REQUEST)


        otp, error_response = OTPService.verify_otp(email, otp_code)
        if error_response:
           return error_response

        try:
            validate_password_strength(new_password)
        except serializers.ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # saving otp as used 
        otp.is_used = True
        otp.save()
        # saving new password of user
        user.set_password(new_password)
        user.save()


        #change password
        
        EmailService.send_password_change_notification(user)
        return Response({"message": "Password successfully updated"}, status=status.HTTP_200_OK)

        

#logout user ----------------------------------------------------------------------------
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response ({'error':'Refresh token required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response ({'message':'logout successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response ({'error':f'{e}, token is not valid'}, status=status.HTTP_400_BAD_REQUEST)
        


# delete the user account -----------------------------------------------------------------------

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def delete_account(self, request):
        user = request.user
        try:
            user.delete()
            return Response ({'message':'User delete successfully'}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response ({'error':f'{e}, token is not valid'}, status=status.HTTP_400_BAD_REQUEST)



    @action(detail=False, methods=['post'])
    def teacher_login(self, request):
        """Teacher login endpoint."""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        user = authenticate(request, username=email, password=password)

        if not user:
            raise AuthenticationFailed('Invalid email or password')
        if not user.is_active:
            raise AuthenticationFailed('Account not verified. Please verify email OTP.')
        if not user.is_teacher():
            raise PermissionDenied('Use the student login page for student accounts')

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)

    def _send_otp_email(self, email, otp_code):
        subject = 'OTP verification for AI Content Evaluator'
        message = (
            'Here is your OTP to confirm login to ai content evaluator\n\n'
            f'{otp_code}\n\n'
            'expires in 20 min'
        )
        from_email = settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER
        recipient_list = [email]
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)

    def _generate_otp(self):
        return f"{randbelow(10000):04d}"

    @action(detail=False, methods=['post'])
    def register(self, request):
        '''
        User Registration

        Endpoints:
        POST /api/auth/register/
        '''
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        email = validated_data['email']
        if User.objects.filter(email=email).exists():
            return Response(
                {'email': ['A user with this email already exists.']},
                status=status.HTTP_400_BAD_REQUEST,
            )

        otp_code = self._generate_otp()
        expires_at = timezone.now() + timedelta(minutes=20)

        pending, created = PendingUserRegistration.objects.get_or_create(
            email=email,
            defaults={
                'username': validated_data['username'],
                'first_name': validated_data['first_name'],
                'last_name': validated_data['last_name'],
                'role': validated_data['role'],
                'password': validated_data['password'],
                'otp': otp_code,
                'otp_expires_at': expires_at,
            }
        )

        if not created:
            pending.username = validated_data['username']
            pending.first_name = validated_data['first_name']
            pending.last_name = validated_data['last_name']
            pending.role = validated_data['role']
            pending.password = validated_data['password']
            pending.refresh_otp(otp_code, expires_at)
            pending.save(update_fields=['username', 'first_name', 'last_name', 'role', 'password'])

        self._send_otp_email(pending.email, pending.otp)

        return Response({
            'detail': 'OTP sent to provided email. Complete verification to activate your account.'
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def verify_otp(self, request):
        """Verify the OTP and create the account after successful OTP verification."""
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp']

        try:
            pending = PendingUserRegistration.objects.get(email=email)
        except PendingUserRegistration.DoesNotExist:
            raise AuthenticationFailed('Invalid email or otp')

        if not pending.is_valid_otp(otp_code):
            raise AuthenticationFailed('Invalid or expired OTP')

        if User.objects.filter(email=email).exists():
            raise AuthenticationFailed('A user with this email already exists.')

        pending.mark_otp_used()

        user = User(
            email=pending.email,
            username=pending.username,
            first_name=pending.first_name,
            last_name=pending.last_name,
            role=pending.role,
            is_active=True,
        )
        user.password = pending.password
        user.save()
        pending.delete()

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def resend_otp(self, request):
        """Resend a new OTP for pending registration."""
        serializer = ResendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']

        try:
            pending = PendingUserRegistration.objects.get(email=email)
        except PendingUserRegistration.DoesNotExist:
            raise AuthenticationFailed('Invalid email')

        if pending.otp_is_used:
            return Response({'detail': 'OTP already used. Please register again.'}, status=status.HTTP_400_BAD_REQUEST)

        otp_code = self._generate_otp()
        expires_at = timezone.now() + timedelta(minutes=20)
        pending.refresh_otp(otp_code, expires_at)
        self._send_otp_email(pending.email, otp_code)

        return Response({'detail': 'A new OTP was sent to your email.'}, status=status.HTTP_200_OK)
    

    @action(detail=False, methods=['get', 'put', 'patch'])
    def profile(self, request):
        '''
        Get or update user profile

        used in dashboard to show user profile and update it

        Endpoints:
        GET /api/auth/profile/
        PUT /api/auth/profile/
        '''
        if request.method == 'get':
            serializer = UserSerializer(request.user)
            return Response(serializer.data)
        
        serializer = UserSerializer(request.user, data = request.data, partial=True )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
        