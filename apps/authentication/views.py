import os
from django.shortcuts import render
from django.contrib.auth import authenticate
from rest_framework import viewsets, serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, BasePermission
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


class IsSuperUser(BasePermission):
    """Allow access only to superusers."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)


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
        if self.action in [
            'register', 'student_login', 'teacher_login', 'guest_login',
            'verify_otp', 'resend_otp', 'change_password_otp_logout',
            'confirm_password_otp', 'admin_login',
        ]:
            return [AllowAny()]
        if self.action in ['admin_list_users', 'admin_delete_user']:
            return [IsSuperUser()]
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

    @action(detail=False, methods=['post'])
    def guest_login(self, request):
        """Guest login endpoint."""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        user = authenticate(request, username=email, password=password)

        if not user:
            raise AuthenticationFailed('Invalid email or password')
        if not user.is_active:
            raise AuthenticationFailed('Account not verified. Please verify email OTP.')
        if not user.is_guest():
            raise PermissionDenied('Use the student login page for student accounts')

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)

    #  ADMIN LOGIN 
    @action(detail=False, methods=['post'])
    def admin_login(self, request):
        """Admin login — superusers only. Returns JWT tokens."""
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'error': 'Email and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=email, password=password)

        if not user:
            raise AuthenticationFailed('Invalid email or password')
        if not user.is_superuser:
            raise PermissionDenied('Admin access only')

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)

    #  LIST ALL USERS ─
    @action(detail=False, methods=['get'], url_path='admin/users')
    def admin_list_users(self, request):
        """Return all users with their details. Superuser only."""
        users = User.objects.all().values(
            'id', 'email', 'username',
            'first_name', 'last_name',
            'role', 'is_active', 'date_joined'
        )
        return Response(list(users), status=status.HTTP_200_OK)
    
    #  Total student teachers and guests count
    @action(detail=False, methods=['get'], url_path='admin/stats')
    def admin_stats(self, request):
        """Return total count of each role. Superuser only."""
        return Response({
            'total_students': User.objects.filter(role='student').count(),
            'total_teachers': User.objects.filter(role='teacher').count(),
            'total_guests':   User.objects.filter(role='guest').count(),
            'total_users':    User.objects.count(),
        }, status=status.HTTP_200_OK)

    #  DELETE USER BY ID 
    @action(detail=False, methods=['delete'], url_path='admin/users/(?P<user_id>[^/.]+)')
    def admin_delete_user(self, request, user_id=None):
        """Delete any user by ID. Superuser only."""
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        user.delete()
        return Response({'message': 'User deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

    #  CHANGE PASSWORD (logged in) 
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        user = request.user

        if not current_password or not new_password or not confirm_password:
            return Response({"error": "Fill all fields"}, status=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_password:
            return Response({"error": "Passwords don't match"}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(current_password):
            return Response({"error": "Current password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)

        if current_password == new_password:
            return Response({"error": "New password must be different"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password_strength(new_password)
        except serializers.ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        EmailService.send_password_change_notification(user)
        return Response({"message": "Password successfully updated"}, status=status.HTTP_200_OK)

    #  CHANGE PASSWORD VIA OTP (logged in) 
    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def change_password_otp(self, request):
        user = request.user
        email = request.user.email
        try:
            return OTPService.generate_send_otp(email, user.first_name, user.last_name)
        except Exception:
            return Response({'error': 'Failed to send OTP'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    #  CHANGE PASSWORD VIA OTP (logged out) 
    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def change_password_otp_logout(self, request):
        email = request.data.get("email")
        if not email:
            return Response({'error': 'Email required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'User does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            return OTPService.generate_send_otp(email, user.first_name, user.last_name)
        except Exception:
            return Response({'error': 'Failed to send OTP'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    #  CONFIRM OTP TO CHANGE PASSWORD ─
    @action(detail=False, methods=["post"])
    def confirm_password_otp(self, request):
        email = request.data.get('email')
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")
        otp_code = request.data.get("otp_code")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Email does not exist"}, status=status.HTTP_400_BAD_REQUEST)

        if not new_password or not confirm_password or not otp_code:
            return Response({"error": "Fields are not filled"}, status=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_password:
            return Response({"error": "New password and confirm password are not same"}, status=status.HTTP_400_BAD_REQUEST)

        otp, error_response = OTPService.verify_otp(email, otp_code)
        if error_response:
            return error_response

        try:
            validate_password_strength(new_password)
        except serializers.ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        otp.is_used = True
        otp.save()
        user.set_password(new_password)
        user.save()
        EmailService.send_password_change_notification(user)
        return Response({"message": "Password successfully updated"}, status=status.HTTP_200_OK)

    #  LOGOUT ─
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'Refresh token required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'{e}, token is not valid'}, status=status.HTTP_400_BAD_REQUEST)

    #  DELETE OWN ACCOUNT ─
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def delete_account(self, request):
        user = request.user
        try:
            user.delete()
            return Response({'message': 'User deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    #  REGISTER ─
    def _send_otp_email(self, email, otp_code):
        subject = 'OTP verification for AI Content Evaluator'
        message = (
            'Here is your OTP to confirm login to AI Content Evaluator\n\n'
            f'{otp_code}\n\n'
            'Expires in 20 minutes.'
        )
        from_email = settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER
        send_mail(subject, message, from_email, [email], fail_silently=False)

    def _generate_otp(self):
        return f"{randbelow(10000):04d}"

    @action(detail=False, methods=['post'])
    def register(self, request):
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

    #  VERIFY OTP ─
    @action(detail=False, methods=['post'])
    def verify_otp(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp']

        try:
            pending = PendingUserRegistration.objects.get(email=email)
        except PendingUserRegistration.DoesNotExist:
            raise AuthenticationFailed('Invalid email or OTP')

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

    #  RESEND OTP ─
    @action(detail=False, methods=['post'])
    def resend_otp(self, request):
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

    #  PROFILE 
    @action(detail=False, methods=['get', 'put', 'patch'])
    def profile(self, request):
        if request.method == 'GET':
            serializer = UserSerializer(request.user)
            return Response(serializer.data)

        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)