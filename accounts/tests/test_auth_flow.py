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

        # Envelope-aware: {"data": {"user": ..., "tokens": {...}}, "meta": {...}}
        envelope = response.data
        data = envelope.get("data", envelope)

        tokens = data.get("tokens") or {}
        access = tokens.get("access")
        refresh = tokens.get("refresh")

        self.assertIsNotNone(
            access,
            f"No access token in login response: {response.data}",
        )
        self.assertIsNotNone(
            refresh,
            f"No refresh token in login response: {response.data}",
        )

        return access, refresh

    def login_with_username(self, username, password):
        response = self.client.post(
            self.login_url,
            {"username": username, "password": password},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        envelope = response.data
        data = envelope.get("data", envelope)

        tokens = data.get("tokens") or {}
        access = tokens.get("access")
        refresh = tokens.get("refresh")

        self.assertIsNotNone(
            access,
            f"No access token in login response: {response.data}",
        )
        self.assertIsNotNone(
            refresh,
            f"No refresh token in login response: {response.data}",
        )

        return access, refresh

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

        # Envelope-aware
        envelope = response.data
        data = envelope.get("data", envelope)

        self.assertIn("user", data)
        user = data["user"]
        self.assertEqual(user["email"], payload["email"])
        self.assertEqual(user["role"], "EMPLOYEE")
        self.assertEqual(user["username"], payload["email"])
        self.assertIn("tokens", data)

    def test_register_with_username_sets_username(self):
        payload = {
            "email": "userwithname@example.com",
            "username": "userwithname",
            "first_name": "User",
            "last_name": "WithName",
            "password": "UserName123!",
            "role": "EMPLOYEE",
        }
        response = self.client.post(self.register_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        envelope = response.data
        data = envelope.get("data", envelope)
        user = data["user"]
        self.assertEqual(user["email"], payload["email"])
        self.assertEqual(user["username"], payload["username"])

    def test_login_returns_tokens(self):
        access, refresh = self.login("emp@example.com", "EmpPass123!")
        self.assertTrue(isinstance(access, str) and len(access) > 10)
        self.assertTrue(isinstance(refresh, str) and len(refresh) > 10)

    def test_login_with_username_returns_tokens(self):
        payload = {
            "email": "username_login@example.com",
            "username": "username_login",
            "first_name": "User",
            "last_name": "Name",
            "password": "UserName123!",
            "role": "EMPLOYEE",
        }
        response = self.client.post(self.register_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        access, refresh = self.login_with_username("username_login", "UserName123!")
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

        envelope = response.data
        data = envelope.get("data", envelope)
        self.assertEqual(data["email"], "emp@example.com")

    def test_refresh_token_returns_new_access(self):
        _, refresh = self.login("emp@example.com", "EmpPass123!")
        response = self.client.post(
            self.refresh_url,
            {"refresh": refresh},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        envelope = response.data
        data = envelope.get("data", envelope)

        # Support either {"access": "..."} or {"tokens": {"access": "..."}}
        tokens = data.get("tokens")
        if tokens is not None:
            access = tokens.get("access")
        else:
            access = data.get("access")

        self.assertIsNotNone(
            access,
            f"No access token in refresh response: {response.data}",
        )
        self.assertTrue(isinstance(access, str) and len(access) > 10)

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

        # Envelope + pagination: expect a dict with "results"
        envelope = response_hr.data
        data = envelope.get("data", envelope)
        self.assertIsInstance(data, dict)
        self.assertIn("results", data)
        self.assertGreaterEqual(len(data["results"]), 2)
