from django.contrib.auth import authenticate
from rest_framework import serializers
# + the new import we just added:
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework import exceptions

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

class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer used for /change-password/
    """
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Ancien mot de passe incorrect.")
        return value

    def validate(self, attrs):
        if attrs["old_password"] == attrs["new_password"]:
            raise serializers.ValidationError(
                "Le nouveau mot de passe doit être différent de l'ancien."
            )
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user


class LogoutSerializer(serializers.Serializer):
    """
    Serializer used for /logout/ to blacklist the refresh token.
    """
    refresh = serializers.CharField()

    def validate(self, attrs):
        self.token = attrs["refresh"]
        return attrs

    def save(self, **kwargs):
        try:
            token = RefreshToken(self.token)
            token.blacklist()
        except TokenError:
            raise exceptions.ValidationError("Token invalide ou déjà blacklisté.")
