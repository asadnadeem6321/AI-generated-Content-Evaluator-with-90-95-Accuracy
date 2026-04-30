import random

from rest_framework import serializers
from .models import PendingUserRegistration, User
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from datetime import timedelta
from .validators import validate_password_strength


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model.
    """
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'role', 'created_at')
        read_only_fields = ('id', 'created_at')

    
class LoginSerializer(serializers.Serializer):
    """Serializer for login requests."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class RegisterSerializer(serializers.Serializer):
    """Serializer for user registration input."""
    email = serializers.EmailField()
    username = serializers.CharField()
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password, validate_password_strength]
    )
    confirm_password = serializers.CharField(write_only=True)
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    role = serializers.ChoiceField(choices=User.ROLE_CHOICE)

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords don't match"})

        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "A user with this email already exists."})

        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError({"username": "This username is already taken."})

        if PendingUserRegistration.objects.filter(username=attrs['username']).exclude(email=attrs['email']).exists():
            raise serializers.ValidationError({"username": "This username is already taken."})

        attrs['password'] = make_password(attrs['password'])
        attrs.pop('confirm_password')
        return attrs

    def create(self, validated_data):
        otp_code = str(random.randint(1000, 9999)).zfill(4)
        expires_at = timezone.now() + timedelta(minutes=20)
        return PendingUserRegistration.objects.create(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            role=validated_data['role'],
            password=validated_data['password'],
            otp=otp_code,
            otp_expires_at=expires_at,
        )


# serializers for OTP verification
class SendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=4)


class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()