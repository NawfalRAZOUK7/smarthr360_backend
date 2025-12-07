# accounts/views.py (updated with ApiResponseMixin)

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from smarthr360_backend.api_mixins import ApiResponseMixin

from .models import LoginActivity, User
from .permissions import IsHRRole
from .schemas import (
    change_password_schema,
    email_verification_schema,
    login_schema,
    logout_schema,
    me_schema,
    password_reset_schema,
    register_schema,
    request_email_verification_schema,
    request_password_reset_schema,
    user_list_schema,
)
from .serializers import (
    ChangePasswordSerializer,
    EmailVerificationSerializer,
    LoginSerializer,
    LogoutSerializer,
    PasswordResetSerializer,
    RegisterSerializer,
    RequestEmailVerificationSerializer,
    RequestPasswordResetSerializer,
    UserSerializer,
)


def get_tokens_for_user(user: User):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


@register_schema
class RegisterView(ApiResponseMixin, generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = get_tokens_for_user(user)
        payload = {
            "user": UserSerializer(user).data,
            "tokens": tokens,
        }
        return Response(payload, status=status.HTTP_201_CREATED)


@login_schema
class LoginView(ApiResponseMixin, APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        tokens = get_tokens_for_user(user)
        return Response({
            "user": UserSerializer(user).data,
            "tokens": tokens,
        }, status=status.HTTP_200_OK)


@change_password_schema
class ChangePasswordView(ApiResponseMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Mot de passe modifié avec succès."}, status=200)


@logout_schema
class LogoutView(ApiResponseMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        LoginActivity.objects.create(
            user=request.user,
            action=LoginActivity.Action.LOGOUT,
            success=True,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        return Response({"detail": "Déconnexion réussie."}, status=200)


@me_schema
class MeView(ApiResponseMixin, generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


@user_list_schema
class UserListView(ApiResponseMixin, generics.ListAPIView):
    queryset = User.objects.all().order_by("email")
    serializer_class = UserSerializer
    permission_classes = [IsHRRole]


@request_password_reset_schema
class RequestPasswordResetView(ApiResponseMixin, APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RequestPasswordResetSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        token_obj = serializer.save()

        data = {"detail": "Si un compte existe, un lien de réinitialisation a été envoyé."}

        from django.conf import settings as dj_settings
        if dj_settings.DEBUG:
            data["debug_token"] = token_obj.token

        return Response(data, status=200)


@password_reset_schema
class PasswordResetView(ApiResponseMixin, APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Mot de passe réinitialisé avec succès."}, status=200)


@request_email_verification_schema
class RequestEmailVerificationView(ApiResponseMixin, APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RequestEmailVerificationSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        token_obj = serializer.save()

        data = {"detail": "Un email de vérification a été envoyé."}
        from django.conf import settings as dj_settings
        if dj_settings.DEBUG:
            data["debug_token"] = token_obj.token

        return Response(data, status=200)


@email_verification_schema
class EmailVerificationView(ApiResponseMixin, APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Adresse email vérifiée avec succès."}, status=200)
