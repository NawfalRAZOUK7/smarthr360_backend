from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, LoginActivity
from .serializers import (
    UserSerializer,
    RegisterSerializer,
    LoginSerializer,
    ChangePasswordSerializer,  # ⬅️ NEW
    LogoutSerializer,  # ⬅️ NEW
    RequestPasswordResetSerializer,
    PasswordResetSerializer,
    RequestEmailVerificationSerializer,
    EmailVerificationSerializer,
    )
from .permissions import IsHRRole  # ⬅️ add this


def get_tokens_for_user(user: User):
    """Helper: create refresh + access tokens for a given user."""
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register/

    Creates a new user and returns:
    {
      "user": {...},
      "tokens": {"refresh": "...", "access": "..."}
    }
    """
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = get_tokens_for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": tokens,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """
    POST /api/auth/login/

    Expects email + password
    Returns same structure as register.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        tokens = get_tokens_for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": tokens,
            },
            status=status.HTTP_200_OK,
        )

class ChangePasswordView(APIView):
    """
    POST /api/auth/change-password/

    Body:
    {
      "old_password": "...",
      "new_password": "..."
    }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Mot de passe modifié avec succès."},
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """
    POST /api/auth/logout/

    Blacklists the refresh token so it can't be used again.

    Body:
    {
      "refresh": "<refresh_token_here>"
    }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Log logout activity
        ip = request.META.get("REMOTE_ADDR")
        ua = request.META.get("HTTP_USER_AGENT", "")
        LoginActivity.objects.create(
            user=request.user,
            action=LoginActivity.Action.LOGOUT,
            success=True,
            ip_address=ip,
            user_agent=ua,
        )

        return Response(
            {"detail": "Déconnexion réussie."},
            status=status.HTTP_200_OK,
        )


class MeView(generics.RetrieveAPIView):
    """
    GET /api/auth/me/

    Returns the current authenticated user.
    Requires Authorization: Bearer <access_token>
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

class UserListView(generics.ListAPIView):
    """
    GET /api/auth/users/

    Visible only to HR and ADMIN roles.
    Used for SmartHR360 to let HR see employees list.
    """
    queryset = User.objects.all().order_by("email")
    serializer_class = UserSerializer
    permission_classes = [IsHRRole]

class RequestPasswordResetView(APIView):
    """
    POST /api/auth/password-reset/request/

    Body:
    {
      "email": "user@example.com"
    }

    Sends a reset link via email (console backend in dev).
    In DEBUG mode, we also return the token in the response for easier testing.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RequestPasswordResetSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        token_obj = serializer.save()

        data = {
            "detail": "Si un compte existe pour cet email, un lien de réinitialisation a été envoyé."
        }

        # In development, expose token for quick testing
        from django.conf import settings as dj_settings

        if dj_settings.DEBUG:
            data["debug_token"] = token_obj.token

        return Response(data, status=status.HTTP_200_OK)


class PasswordResetView(APIView):
    """
    POST /api/auth/password-reset/confirm/

    Body:
    {
      "token": "...",
      "new_password": "NewPass123!"
    }

    Uses the token to set a new password.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Mot de passe réinitialisé avec succès."},
            status=status.HTTP_200_OK,
        )

class RequestEmailVerificationView(APIView):
    """
    POST /api/auth/email/verify/request/

    Body:
    {
      "email": "user@example.com"
    }

    Sends a verification link by email.
    In DEBUG, we can also send back the token (optional).
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RequestEmailVerificationSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        token_obj = serializer.save()

        data = {
            "detail": "Un email de vérification a été envoyé si ce compte existe.",
        }

        from django.conf import settings as dj_settings
        if dj_settings.DEBUG:
            data["debug_token"] = token_obj.token

        return Response(data, status=status.HTTP_200_OK)


class EmailVerificationView(APIView):
    """
    POST /api/auth/email/verify/confirm/

    Body:
    {
      "token": "..."
    }

    Marks the user as email-verified.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Adresse email vérifiée avec succès."},
            status=status.HTTP_200_OK,
        )
