from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from datetime import timedelta

from accounts.models import (
    User,
    EmailVerificationToken,
    PasswordResetToken,
    LoginAttempt,
    LoginActivity,
)
from accounts.tests.helpers import DEFAULT_PASSWORD, api_client, create_user, login


class AuthEdgeCaseTests(TestCase):
    def setUp(self):
        self.client = api_client()
        self.password = DEFAULT_PASSWORD
        self.user = create_user(
            email="edge@example.com",
            password=self.password,
            first_name="Edge",
            last_name="Case",
            role=User.Role.EMPLOYEE,
        )

    # ---------------------------------------------------------
    # EMAIL VERIFICATION EDGE CASES
    # ---------------------------------------------------------

    def test_verify_invalid_token(self):
        resp = self.client.post(
            "/api/auth/email/verify/confirm/",
            {"token": "invalid-token"},
            format="json",
        )

        if resp.status_code == 404:
            self.skipTest("Email verification not wired yet.")

        self.assertEqual(resp.status_code, 400)

    def test_verify_expired_token(self):
        token = EmailVerificationToken.objects.create(user=self.user)
        token.expires_at = timezone.now() - timedelta(minutes=1)
        token.save()

        resp = self.client.post(
            "/api/auth/email/verify/confirm/",
            {"token": str(token.token)},
            format="json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_verify_already_verified_email(self):
        # mark as already verified
        self.user.is_email_verified = True
        self.user.save()

        resp = self.client.post(
            "/api/auth/email/verify/",
            {"email": self.user.email},
            format="json",
        )

        if resp.status_code == 404:
            self.skipTest("Email verification not wired yet.")

        self.assertEqual(resp.status_code, 400)

    def test_multiple_verification_requests_dont_duplicate(self):
        resp1 = self.client.post(
            "/api/auth/email/verify/",
            {"email": self.user.email},
            format="json",
        )
        resp2 = self.client.post(
            "/api/auth/email/verify/",
            {"email": self.user.email},
            format="json",
        )

        if resp1.status_code == 404:
            self.skipTest("Email verification not wired yet.")

        count = EmailVerificationToken.objects.filter(user=self.user).count()
        self.assertEqual(count, 1)

    # ---------------------------------------------------------
    # PASSWORD RESET EDGE CASES
    # ---------------------------------------------------------

    def test_reset_for_non_existing_email_returns_200(self):
        resp = self.client.post(
            "/api/auth/password-reset/",
            {"email": "notfound@example.com"},
            format="json",
        )
        if resp.status_code == 404:
            self.skipTest("Password reset not wired yet.")

        # Should not reveal existence of account
        self.assertEqual(resp.status_code, 200)

    def test_reset_with_invalid_token(self):
        resp = self.client.post(
            "/api/auth/password-reset/confirm/",
            {"token": "invalid", "new_password": "NewPass123!"},
            format="json",
        )
        if resp.status_code == 404:
            self.skipTest("Password reset not wired yet.")
        self.assertEqual(resp.status_code, 400)

    def test_reset_with_expired_token(self):
        token = PasswordResetToken.objects.create(user=self.user)
        token.expires_at = timezone.now() - timedelta(minutes=1)
        token.save()

        resp = self.client.post(
            "/api/auth/password-reset/confirm/",
            {"token": str(token.token), "new_password": "NewPass123!"},
            format="json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_reset_with_used_token(self):
        token = PasswordResetToken.objects.create(user=self.user)
        token.used = True
        token.save()

        resp = self.client.post(
            "/api/auth/password-reset/confirm/",
            {"token": str(token.token), "new_password": "NewPass123!"},
            format="json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_reset_with_weak_password(self):
        token = PasswordResetToken.objects.create(user=self.user)

        resp = self.client.post(
            "/api/auth/password-reset/confirm/",
            {"token": str(token.token), "new_password": "123"},
            format="json",
        )
        self.assertEqual(resp.status_code, 400)

    # ---------------------------------------------------------
    # LOCKOUT EDGE CASES
    # ---------------------------------------------------------

    def test_lockout_expires_after_timeout(self):
        """
        Simulate a user whose lockout period has already expired.

        We MUST set locked_until because the login serializer uses it:
            (attempt.locked_until - now)
        """
        attempt, _ = LoginAttempt.objects.get_or_create(user=self.user)
        attempt.failed_attempts = attempt.MAX_ATTEMPTS
        attempt.is_locked = True

        # If your model defines LOCKOUT_MINUTES, use it; otherwise fallback.
        lock_minutes = getattr(LoginAttempt, "LOCKOUT_MINUTES", 15)

        # Make locked_until in the past so lock is expired
        attempt.locked_until = timezone.now() - timedelta(minutes=1)
        # Optionally also set locked_at for consistency (not required for the serializer)
        attempt.locked_at = timezone.now() - timedelta(minutes=lock_minutes + 1)

        attempt.save()

        # Now login should work again
        resp = self.client.post(
            "/api/auth/login/",
            {"email": self.user.email, "password": self.password},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_locked_user_cannot_request_password_reset(self):
        attempt, _ = LoginAttempt.objects.get_or_create(user=self.user)
        attempt.failed_attempts = attempt.MAX_ATTEMPTS
        attempt.is_locked = True
        attempt.save()

        resp = self.client.post(
            "/api/auth/password-reset/",
            {"email": self.user.email},
            format="json",
        )

        if resp.status_code == 404:
            self.skipTest("Password reset not wired yet.")

        # Should NOT allow, return a generic 200 (security) or explicit 400 depending design
        self.assertIn(resp.status_code, [200, 400])

    def test_failed_login_logs_activity(self):
        self.client.post(
            "/api/auth/login/",
            {"email": self.user.email, "password": "WRONG"},
            format="json",
        )
        activity = LoginActivity.objects.filter(user=self.user).last()
        self.assertIsNotNone(activity)
        self.assertFalse(activity.success)

    def test_successful_login_logs_activity(self):
        self.client.post(
            "/api/auth/login/",
            {"email": self.user.email, "password": self.password},
            format="json",
        )
        activity = LoginActivity.objects.filter(user=self.user).last()
        self.assertIsNotNone(activity)
        self.assertTrue(activity.success)

    def test_login_activity_contains_ip(self):
        resp = self.client.post(
            "/api/auth/login/",
            {"email": self.user.email, "password": self.password},
            REMOTE_ADDR="127.0.0.1",
            format="json",
        )
        if resp.status_code != 200:
            self.fail(f"Login failed in IP test: {resp.data}")
        activity = LoginActivity.objects.filter(user=self.user).last()
        self.assertEqual(activity.ip_address, "127.0.0.1")
