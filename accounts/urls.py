from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    ChangePasswordView,  # ⬅️ NEW
    EmailVerificationView,
    LoginView,
    LogoutView,  # ⬅️ NEW
    MeView,
    PasswordResetView,
    RegisterView,
    RequestEmailVerificationView,
    RequestPasswordResetView,
    UserListView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("me/", MeView.as_view(), name="auth-me"),

    # New: list all users (HR & Admin only)
    path("users/", UserListView.as_view(), name="auth-user-list"),

    path("change-password/", ChangePasswordView.as_view(), name="auth-change-password"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),

    path(
        "password-reset/request/",
        RequestPasswordResetView.as_view(),
        name="auth-password-reset-request",
    ),
    path(
        "password-reset/",
        RequestPasswordResetView.as_view(),
        name="auth-password-reset-request-legacy",
    ),
    path(
        "password-reset/confirm/",
        PasswordResetView.as_view(),
        name="auth-password-reset-confirm",
    ),

    path(
        "email/verify/request/",
        RequestEmailVerificationView.as_view(),
        name="auth-email-verify-request",
    ),
    path(
        "email/verify/",
        RequestEmailVerificationView.as_view(),
        name="auth-email-verify-request-legacy",
    ),
    path(
        "email/verify/confirm/",
        EmailVerificationView.as_view(),
        name="auth-email-verify-confirm",
    ),
]
