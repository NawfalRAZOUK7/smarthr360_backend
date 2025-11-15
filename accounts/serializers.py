from django.contrib.auth import authenticate
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Public user data returned to the frontend."""
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "role"]


class RegisterSerializer(serializers.ModelSerializer):
    """Used for /register endpoint."""
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "password", "role"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        # we use our custom manager (UserManager)
        user = User.objects.create_user(
            password=password,
            **validated_data,
        )
        return user


class LoginSerializer(serializers.Serializer):
    """Used for /login endpoint."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        # Because AUTH_USER_MODEL has USERNAME_FIELD = 'email',
        # authenticate can accept 'email' as kwarg.
        user = authenticate(email=email, password=password)
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")

        attrs["user"] = user
        return attrs
