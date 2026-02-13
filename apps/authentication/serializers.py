from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password

class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model.
    """
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'role', 'created_at')
        read_only_fields = ('id', 'created_at')

    
    class RegistrationSerializer(serializers.ModelSerializer):
        '''Serializer for user registration'''

        password = serializers.CharField(write_only=True, validators=[validate_password])
        confirm_password = serializers.CharField(write_only=True)

        class Meta:
            model = User
            fields = ['email', 'username', 'first_name', 'last_name', 'password', 'confirm_password', 'role', ]

        def validate(self, attrs):
            if attrs['password'] != attrs['confirm_password']:
                raise serializers.ValidationError({"Password : Password and confirm password did not match"})
            return attrs
        
        def create(self, validated_data):
            validated_data.pop('confirm_password')
            user = User.objects.create(**validated_data)
            return user