from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User

DEFAULT_PASSWORD = "StrongPass123!"


def api_client():
    """Return a DRF APIClient instance for convenience."""
    return APIClient()


def create_user(
    *,
    email: str = "user@example.com",
    password: str = DEFAULT_PASSWORD,
    first_name: str = "Test",
    last_name: str = "User",
    role: User.Role = User.Role.EMPLOYEE,
    **extra,
):
    """Create a user with sensible defaults for tests."""
    return User.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        role=role,
        **extra,
    )


def login(client: APIClient, email: str, password: str, expect_success: bool = True):
    """Post to the login endpoint; optionally assert success."""
    response = client.post(
        "/api/auth/login/",
        {"email": email, "password": password},
        format="json",
    )
    if expect_success and response.status_code != status.HTTP_200_OK:
        raise AssertionError(
            f"Login failed for {email}: {response.status_code} {response.data}"
        )
    return response


def extract_tokens(response):
    """Return (access, refresh) tokens from envelope-aware login/refresh responses."""
    payload = response.data
    data = payload.get("data", payload)
    tokens = data.get("tokens") or {}
    access = tokens.get("access") or data.get("access")
    refresh = tokens.get("refresh") or data.get("refresh")
    return access, refresh


def authenticate(client: APIClient, email: str, password: str) -> str:
    """Login and set Authorization header; returns access token."""
    response = login(client, email, password, expect_success=True)
    access, _ = extract_tokens(response)
    if not access:
        raise AssertionError(f"No access token for {email}: {response.status_code} {response.data}")
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    return access
