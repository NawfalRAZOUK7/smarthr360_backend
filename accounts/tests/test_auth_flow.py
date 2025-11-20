# accounts/tests/test_auth_flow.py

from rest_framework import status
from rest_framework.test import APITestCase


class AuthFlowTests(APITestCase):
    """
    Tests for:
    - register
    - login
    - me
    - refresh
    - change-password
    - logout (blacklist)
    - /users/ visibility by role
    """

    def setUp(self):
        self.register_url = "/api/auth/register/"
        self.login_url = "/api/auth/login/"
        self.refresh_url = "/api/auth/refresh/"
        self.me_url = "/api/auth/me/"
        self.change_password_url = "/api/auth/change-password/"
        self.logout_url = "/api/auth/logout/"
        self.user_list_url = "/api/auth/users/"

        # Create HR user via REGISTER endpoint
        hr_payload = {
            "email": "hr@example.com",
            "first_name": "HR",
            "last_name": "User",
            "password": "HrPass123!",
            "role": "HR",
        }
        resp_hr = self.client.post(self.register_url, hr_payload, format="json")
        self.assertEqual(resp_hr.status_code, status.HTTP_201_CREATED)

        # Create EMPLOYEE user via REGISTER endpoint
        emp_payload = {
            "email": "emp@example.com",
            "first_name": "Emp",
            "last_name": "User",
            "password": "EmpPass123!",
            "role": "EMPLOYEE",
        }
        resp_emp = self.client.post(self.register_url, emp_payload, format="json")
        self.assertEqual(resp_emp.status_code, status.HTTP_201_CREATED)

    # ---------- Helpers ----------

    def login(self, email, password):
        response = self.client.post(
            self.login_url,
            {"email": email, "password": password},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data["tokens"]["access"], response.data["tokens"]["refresh"]

    # ---------- Tests ----------

    def test_register_employee_success(self):
        payload = {
            "email": "newemp@example.com",
            "first_name": "New",
            "last_name": "Employee",
            "password": "NewPass123!",
            "role": "EMPLOYEE",
        }
        response = self.client.post(self.register_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["email"], payload["email"])
        self.assertEqual(response.data["user"]["role"], "EMPLOYEE")
        self.assertIn("tokens", response.data)

    def test_login_returns_tokens(self):
        access, refresh = self.login("emp@example.com", "EmpPass123!")
        self.assertTrue(isinstance(access, str) and len(access) > 10)
        self.assertTrue(isinstance(refresh, str) and len(refresh) > 10)

    def test_me_requires_authentication(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_with_valid_token(self):
        access, _ = self.login("emp@example.com", "EmpPass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "emp@example.com")

    def test_refresh_token_returns_new_access(self):
        _, refresh = self.login("emp@example.com", "EmpPass123!")
        response = self.client.post(
            self.refresh_url,
            {"refresh": refresh},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertTrue(len(response.data["access"]) > 10)

    def test_change_password_flow(self):
        # login with old password
        access, _ = self.login("emp@example.com", "EmpPass123!")

        # call change-password
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = self.client.post(
            self.change_password_url,
            {
                "old_password": "EmpPass123!",
                "new_password": "EmpNewPass123!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # old password no longer works
        response_old = self.client.post(
            self.login_url,
            {"email": "emp@example.com", "password": "EmpPass123!"},
            format="json",
        )
        # Depending on implementation, invalid credentials may return 400 or 401
        self.assertIn(
            response_old.status_code,
            (status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED),
        )

        # new password works
        response_new = self.client.post(
            self.login_url,
            {"email": "emp@example.com", "password": "EmpNewPass123!"},
            format="json",
        )
        self.assertEqual(response_new.status_code, status.HTTP_200_OK)

    def test_logout_blacklists_refresh_token(self):
        access, refresh = self.login("emp@example.com", "EmpPass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        # logout → blacklist refresh
        response = self.client.post(
            self.logout_url,
            {"refresh": refresh},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # using same refresh again must fail (401 or 400 depending on JWT setup)
        response2 = self.client.post(
            self.refresh_url,
            {"refresh": refresh},
            format="json",
        )
        self.assertIn(
            response2.status_code,
            (status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED),
        )

    def test_user_list_only_visible_to_hr(self):
        # employee tries to list users → forbidden
        emp_access, _ = self.login("emp@example.com", "EmpPass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {emp_access}")
        response_emp = self.client.get(self.user_list_url)
        self.assertEqual(response_emp.status_code, status.HTTP_403_FORBIDDEN)

        # HR can list users
        hr_access, _ = self.login("hr@example.com", "HrPass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {hr_access}")
        response_hr = self.client.get(self.user_list_url)
        self.assertEqual(response_hr.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response_hr.data), 2)
