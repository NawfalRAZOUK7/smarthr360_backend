from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import (
    UserSerializer,
    RegisterSerializer,
    LoginSerializer,
    ChangePasswordSerializer,  # ⬅️ NEW
    LogoutSerializer,  # ⬅️ NEW
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
