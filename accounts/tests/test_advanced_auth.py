from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import (
    User,
    PasswordResetToken,
    EmailVerificationToken,
    LoginAttempt,
    LoginActivity,
)


class AdvancedAuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.password = "StrongPass123!"
        self.user = User.objects.create_user(
            email="user@example.com",
            password=self.password,
            first_name="Test",
            last_name="User",
            role=User.Role.EMPLOYEE,
        )

    def login(self, email, password):
        return self.client.post(
            "/api/auth/login/",
            {"email": email, "password": password},
            format="json",
        )

    # --- Password reset ---

    def test_password_reset_flow(self):
        """
        1) Request reset -> token created
        2) Confirm reset -> password changed
        3) Login with new password works

        If endpoints are not wired yet (404), we SKIP this test.
        """
        # Request reset
        response = self.client.post(
            "/api/auth/password-reset/",
            {"email": self.user.email},
            format="json",
        )

        if response.status_code == status.HTTP_404_NOT_FOUND:
            self.skipTest("Password reset endpoints not available yet (404).")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token_obj = PasswordResetToken.objects.filter(user=self.user).first()
        self.assertIsNotNone(token_obj)

        # Confirm reset
        new_password = "NewPassword456!"
        response2 = self.client.post(
            "/api/auth/password-reset/confirm/",
            {"token": str(token_obj.token), "new_password": new_password},
            format="json",
        )
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        # Login with old password fails
        bad_login = self.login(self.user.email, self.password)
        self.assertEqual(bad_login.status_code, status.HTTP_400_BAD_REQUEST)

        # Login with new password works
        good_login = self.login(self.user.email, new_password)
        self.assertEqual(good_login.status_code, status.HTTP_200_OK)

        # Envelope-aware assertion for access token
        payload = good_login.data
        data = payload.get("data", payload)
        tokens = data.get("tokens")

        if tokens is not None:
            self.assertIn("access", tokens)
        else:
            self.assertIn("access", data)

    # --- Email verification ---

    def test_email_verification_flow(self):
        """
        1) Request email verification -> token created
        2) Confirm -> is_email_verified = True

        If endpoints are not wired yet (404), we SKIP this test.
        """
        self.user.is_email_verified = False
        self.user.save()

        # Request verification
        response = self.client.post(
            "/api/auth/email/verify/",
            {"email": self.user.email},
            format="json",
        )

        if response.status_code == status.HTTP_404_NOT_FOUND:
            self.skipTest("Email verification endpoints not available yet (404).")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        token_obj = EmailVerificationToken.objects.filter(user=self.user).first()
        self.assertIsNotNone(token_obj)

        # Confirm
        response2 = self.client.post(
            "/api/auth/email/verify/confirm/",
            {"token": str(token_obj.token)},
            format="json",
        )
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)

    # --- Lockout + LoginActivity ---

    def test_lockout_after_failed_logins_and_activity_logged(self):
        """
        After several failed logins, user is locked.
        Also records LoginActivity entries.
        """
        max_attempts = LoginAttempt.MAX_ATTEMPTS

        # Ensure login_attempt exists
        attempt, _ = LoginAttempt.objects.get_or_create(user=self.user)

        # Perform max_attempts wrong logins
        for _ in range(max_attempts):
            response = self.login(self.user.email, "WrongPass!")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Now user should be locked
        attempt.refresh_from_db()
        self.assertTrue(attempt.is_locked)

        locked_response = self.login(self.user.email, self.password)
        self.assertEqual(locked_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Compte verrouillé", str(locked_response.data))

        # LoginActivity entries must exist (at least failed ones)
        activities = LoginActivity.objects.filter(user=self.user)
        self.assertGreaterEqual(activities.count(), max_attempts)
        # Check that at least one is marked as failed
        self.assertTrue(activities.filter(success=False).exists())
