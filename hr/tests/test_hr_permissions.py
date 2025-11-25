# hr/tests/test_hr_permissions.py

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from hr.models import Department, EmployeeProfile


class HRPermissionsTests(APITestCase):
    """
    Tests HR + manager + employee permissions on HR endpoints.
    All users are created fresh via REGISTER + ORM.
    """

    def setUp(self):
        self.employees_url = "/api/hr/employees/"
        self.employee_me_url = "/api/hr/employees/me/"
        self.my_team_url = "/api/hr/employees/my-team/"
        self.login_url = "/api/auth/login/"
        self.register_url = "/api/auth/register/"

        # ---- Create users via REGISTER endpoint ----

        # HR user
        hr_payload = {
            "email": "hr@example.com",
            "first_name": "HR",
            "last_name": "User",
            "password": "HrPass123!",
            "role": "HR",
        }
        resp_hr = self.client.post(self.register_url, hr_payload, format="json")
        self.assertEqual(resp_hr.status_code, status.HTTP_201_CREATED)

        # Manager user
        manager_payload = {
            "email": "manager@example.com",
            "first_name": "Mona",
            "last_name": "Manager",
            "password": "ManagerPass123!",
            "role": "MANAGER",
        }
        resp_manager = self.client.post(self.register_url, manager_payload, format="json")
        self.assertEqual(resp_manager.status_code, status.HTTP_201_CREATED)

        # Employee (team member)
        team_emp_payload = {
            "email": "teamemp@example.com",
            "first_name": "Team",
            "last_name": "Employee",
            "password": "EmpPass123!",
            "role": "EMPLOYEE",
        }
        resp_team_emp = self.client.post(self.register_url, team_emp_payload, format="json")
        self.assertEqual(resp_team_emp.status_code, status.HTTP_201_CREATED)

        # Employee (non-team)
        other_emp_payload = {
            "email": "otheremp@example.com",
            "first_name": "Other",
            "last_name": "Employee",
            "password": "EmpPass123!",
            "role": "EMPLOYEE",
        }
        resp_other_emp = self.client.post(self.register_url, other_emp_payload, format="json")
        self.assertEqual(resp_other_emp.status_code, status.HTTP_201_CREATED)

        # Retrieve User instances from DB
        self.hr_user = User.objects.get(email="hr@example.com")
        self.manager_user = User.objects.get(email="manager@example.com")
        self.emp_team_user = User.objects.get(email="teamemp@example.com")
        self.emp_other_user = User.objects.get(email="otheremp@example.com")

        # Department
        self.dept = Department.objects.create(
            name="IT",
            code="IT",
            description="IT Department",
        )

        # Employee profiles
        self.hr_profile = EmployeeProfile.objects.create(
            user=self.hr_user,
            department=self.dept,
            job_title="HR Manager",
        )

        self.manager_profile = EmployeeProfile.objects.create(
            user=self.manager_user,
            department=self.dept,
            job_title="Team Lead",
        )

        self.team_emp_profile = EmployeeProfile.objects.create(
            user=self.emp_team_user,
            department=self.dept,
            job_title="Developer",
            manager=self.manager_profile,
        )

        self.other_emp_profile = EmployeeProfile.objects.create(
            user=self.emp_other_user,
            department=self.dept,
            job_title="Designer",
        )

    # ---------- Helpers ----------

    def login(self, email, password):
        response = self.client.post(
            self.login_url,
            {"email": email, "password": password},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Envelope-aware
        envelope = response.data
        data = envelope.get("data", envelope)
        tokens = data.get("tokens", {})
        access = tokens.get("access")
        self.assertIsNotNone(access, f"No access token in login response: {response.data}")
        return access

    # ---------- Tests ----------

    def test_hr_can_list_all_employees(self):
        access = self.login("hr@example.com", "HrPass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        response = self.client.get(self.employees_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        envelope = response.data
        data = envelope.get("data", envelope)
        results = data.get("results", [])
        # hr + manager + 2 employees = 4 profiles
        self.assertEqual(len(results), 4)

    def test_employee_cannot_list_all_employees(self):
        access = self.login("teamemp@example.com", "EmpPass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        response = self.client.get(self.employees_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_employee_me_get_and_patch(self):
        access = self.login("teamemp@example.com", "EmpPass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        # GET own profile
        response_get = self.client.get(self.employee_me_url)
        self.assertEqual(response_get.status_code, status.HTTP_200_OK)
        envelope = response_get.data
        data = envelope.get("data", envelope)
        self.assertEqual(data["user"]["email"], "teamemp@example.com")

        # PATCH allowed fields
        response_patch = self.client.patch(
            self.employee_me_url,
            {"phone_number": "+212600000000"},
            format="json",
        )
        self.assertEqual(response_patch.status_code, status.HTTP_200_OK)
        envelope_patch = response_patch.data
        data_patch = envelope_patch.get("data", envelope_patch)
        self.assertEqual(data_patch["phone_number"], "+212600000000")

    def test_manager_my_team_returns_only_direct_reports(self):
        access = self.login("manager@example.com", "ManagerPass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        response = self.client.get(self.my_team_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        envelope = response.data
        data = envelope.get("data", envelope)
        results = data.get("results", [])
        emails = [item["user"]["email"] for item in results]
        self.assertIn("teamemp@example.com", emails)
        self.assertNotIn("otheremp@example.com", emails)
        self.assertNotIn("hr@example.com", emails)

    def test_manager_can_access_team_member_but_not_other_employee(self):
        access = self.login("manager@example.com", "ManagerPass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        # team member → allowed
        url_team = f"/api/hr/employees/{self.team_emp_profile.id}/"
        response_team = self.client.get(url_team)
        self.assertEqual(response_team.status_code, status.HTTP_200_OK)
        env_team = response_team.data
        data_team = env_team.get("data", env_team)

        # non-team employee → forbidden
        url_other = f"/api/hr/employees/{self.other_emp_profile.id}/"
        response_other = self.client.get(url_other)
        self.assertEqual(response_other.status_code, status.HTTP_403_FORBIDDEN)

    def test_hr_can_access_any_employee_detail(self):
        access = self.login("hr@example.com", "HrPass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        url = f"/api/hr/employees/{self.other_emp_profile.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        envelope = response.data
        data = envelope.get("data", envelope)
        self.assertEqual(data["user"]["email"], "otheremp@example.com")
