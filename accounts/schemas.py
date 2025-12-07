# accounts/schemas.py
"""
OpenAPI schema extensions for authentication endpoints.
"""

from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema

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

# Register endpoint schemas
register_schema = extend_schema(
    summary="Register a new user",
    description=(
        "Create a new user account. Returns user data and JWT tokens upon successful "
        "registration."
    ),
    request=RegisterSerializer,
    responses={
        201: OpenApiResponse(
            description="User successfully registered",
            response=UserSerializer,
        ),
        400: OpenApiResponse(description="Bad request - validation errors"),
    },
    tags=["Authentication"],
    examples=[
        OpenApiExample(
            "Register Example",
            value={
                "email": "john.doe@company.com",
                "password": "SecurePass123!",
                "first_name": "John",
                "last_name": "Doe",
                "role": "EMPLOYEE"
            },
            request_only=True,
        ),
    ],
)

# Login endpoint schemas
login_schema = extend_schema(
    summary="User login",
    description=(
        "Authenticate user and receive JWT tokens. Returns user data and access/refresh tokens."
    ),
    request=LoginSerializer,
    responses={
        200: OpenApiResponse(
            description="Login successful",
            response=UserSerializer,
        ),
        401: OpenApiResponse(description="Invalid credentials"),
        423: OpenApiResponse(description="Account locked due to too many failed attempts"),
    },
    tags=["Authentication"],
    examples=[
        OpenApiExample(
            "Login Example",
            value={
                "email": "john.doe@company.com",
                "password": "SecurePass123!"
            },
            request_only=True,
        ),
    ],
)

# Change password schema
change_password_schema = extend_schema(
    summary="Change password",
    description="Change password for authenticated user. Requires old password verification.",
    request=ChangePasswordSerializer,
    responses={
        200: OpenApiResponse(description="Password changed successfully"),
        400: OpenApiResponse(description="Invalid old password or validation error"),
    },
    tags=["Authentication"],
    examples=[
        OpenApiExample(
            "Change Password Example",
            value={
                "old_password": "OldPass123!",
                "new_password": "NewSecurePass456!"
            },
            request_only=True,
        ),
    ],
)

# Logout schema
logout_schema = extend_schema(
    summary="User logout",
    description="Logout user by blacklisting their refresh token.",
    request=LogoutSerializer,
    responses={
        200: OpenApiResponse(description="Logout successful"),
        400: OpenApiResponse(description="Invalid or missing refresh token"),
    },
    tags=["Authentication"],
    examples=[
        OpenApiExample(
            "Logout Example",
            value={
                "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
            },
            request_only=True,
        ),
    ],
)

# Me endpoint schema
me_schema = extend_schema(
    summary="Get current user profile",
    description="Retrieve the profile information of the currently authenticated user.",
    responses={
        200: OpenApiResponse(
            description="User profile retrieved successfully",
            response=UserSerializer,
        ),
    },
    tags=["User Profile"],
)

# User list schema
user_list_schema = extend_schema(
    summary="List all users",
    description="Get a list of all users in the system. Requires HR role.",
    responses={
        200: OpenApiResponse(
            description="List of users",
            response=UserSerializer(many=True),
        ),
        403: OpenApiResponse(description="Permission denied - HR role required"),
    },
    tags=["User Management"],
)

# Password reset request schema
request_password_reset_schema = extend_schema(
    summary="Request password reset",
    description="Request a password reset link. An email will be sent if the account exists.",
    request=RequestPasswordResetSerializer,
    responses={
        200: OpenApiResponse(description="Reset link sent (if account exists)"),
    },
    tags=["Authentication"],
    examples=[
        OpenApiExample(
            "Request Password Reset",
            value={
                "email": "john.doe@company.com"
            },
            request_only=True,
        ),
    ],
)

# Password reset schema
password_reset_schema = extend_schema(
    summary="Reset password with token",
    description="Reset password using the token received via email.",
    request=PasswordResetSerializer,
    responses={
        200: OpenApiResponse(description="Password reset successful"),
        400: OpenApiResponse(description="Invalid or expired token"),
    },
    tags=["Authentication"],
    examples=[
        OpenApiExample(
            "Password Reset",
            value={
                "token": "abc123def456",
                "new_password": "NewSecurePass789!"
            },
            request_only=True,
        ),
    ],
)

# Email verification request schema
request_email_verification_schema = extend_schema(
    summary="Request email verification",
    description="Request an email verification link.",
    request=RequestEmailVerificationSerializer,
    responses={
        200: OpenApiResponse(description="Verification email sent"),
    },
    tags=["Authentication"],
    examples=[
        OpenApiExample(
            "Request Email Verification",
            value={
                "email": "john.doe@company.com"
            },
            request_only=True,
        ),
    ],
)

# Email verification schema
email_verification_schema = extend_schema(
    summary="Verify email with token",
    description="Verify email address using the token received via email.",
    request=EmailVerificationSerializer,
    responses={
        200: OpenApiResponse(description="Email verified successfully"),
        400: OpenApiResponse(description="Invalid or expired token"),
    },
    tags=["Authentication"],
    examples=[
        OpenApiExample(
            "Email Verification",
            value={
                "token": "xyz789abc123"
            },
            request_only=True,
        ),
    ],
)
