from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import User
from hr.models import Department, EmployeeProfile
from wellbeing.models import WellbeingSurvey, SurveyQuestion, SurveyResponse


class WellbeingModuleTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Users
        self.hr_user = User.objects.create_user(
            email="hr@example.com",
            password="HrPass123!",
            role=User.Role.HR,
            first_name="HR",
            last_name="User",
        )
        self.manager_user = User.objects.create_user(
            email="manager@example.com",
            password="ManagerPass123!",
            role=User.Role.MANAGER,
            first_name="Mona",
            last_name="Manager",
        )
        self.emp1_user = User.objects.create_user(
            email="emp1@example.com",
            password="EmpPass123!",
            role=User.Role.EMPLOYEE,
            first_name="Emp",
            last_name="One",
        )
        self.emp2_user = User.objects.create_user(
            email="emp2@example.com",
            password="EmpPass123!",
            role=User.Role.EMPLOYEE,
            first_name="Emp",
            last_name="Two",
        )

        self.department = Department.objects.create(
            name="IT",
            code="IT",
            description="IT Department",
        )

        # Manager & employees
        self.manager_profile = EmployeeProfile.objects.create(
            user=self.manager_user,
            department=self.department,
            job_title="Team Lead",
        )
        self.emp1_profile = EmployeeProfile.objects.create(
            user=self.emp1_user,
            department=self.department,
            job_title="Developer",
            manager=self.manager_profile,
        )
        self.emp2_profile = EmployeeProfile.objects.create(
            user=self.emp2_user,
            department=self.department,
            job_title="QA",
            manager=self.manager_profile,
        )

        # Survey + questions
        self.survey = WellbeingSurvey.objects.create(
            title="Stress & Satisfaction",
            description="Weekly wellbeing check",
            is_active=True,
            created_by=self.hr_user,
        )
        self.q1 = SurveyQuestion.objects.create(
            survey=self.survey,
            text="How stressed do you feel this week?",
            type=SurveyQuestion.QuestionType.SCALE_1_5,
            order=1,
        )
        self.q2 = SurveyQuestion.objects.create(
            survey=self.survey,
            text="Do you feel supported by your manager?",
            type=SurveyQuestion.QuestionType.YES_NO,
            order=2,
        )

    def auth_as(self, user):
        # Pick the right password based on user
        password = (
            "HrPass123!"
            if user == self.hr_user
            else "ManagerPass123!"
            if user == self.manager_user
            else "EmpPass123!"
        )

        res = self.client.post(
            "/api/auth/login/",
            {"email": user.email, "password": password},
            format="json",
        )

        if res.status_code != status.HTTP_200_OK:
            self.fail(f"Login failed for {user.email}: {res.status_code}, {res.data}")

        data = res.data
        token = None

        # Case 1: flat response { "access": "...", ... }
        if isinstance(data, dict) and "access" in data:
            token = data["access"]

        # Case 2: flat but grouped tokens { "tokens": { "access": "..." } }
        if token is None and isinstance(data, dict):
            tokens = data.get("tokens")
            if isinstance(tokens, dict):
                token = tokens.get("access")

        # Case 3: enveloped { "data": { "access": "..." } }
        if token is None and isinstance(data, dict):
            inner = data.get("data")
            if isinstance(inner, dict):
                if "access" in inner:
                    token = inner["access"]
                else:
                    tokens = inner.get("tokens")
                    if isinstance(tokens, dict):
                        token = tokens.get("access")

        if token is None:
            self.fail(f"No access token in login response for {user.email}: {res.data}")

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_employee_can_submit_anonymous_response(self):
        self.auth_as(self.emp1_user)

        payload = {
            "answers": {
                str(self.q1.id): "4",
                str(self.q2.id): "yes",
            }
        }
        resp = self.client.post(
            f"/api/wellbeing/surveys/{self.survey.id}/submit/",
            payload,
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        # Envelope: { "data": { "response_id": "..." }, "meta": {...} }
        self.assertIn("response_id", resp.data["data"])

        stored = SurveyResponse.objects.filter(survey=self.survey).first()
        self.assertIsNotNone(stored)
        self.assertEqual(stored.answers[str(self.q1.id)], "4")
        self.assertEqual(stored.department, self.emp1_profile.department)
        # No direct link to user
        self.assertFalse(hasattr(stored, "user"))

    def test_hr_can_view_global_stats(self):
        # Create a couple of responses
        self.auth_as(self.emp1_user)
        self.client.post(
            f"/api/wellbeing/surveys/{self.survey.id}/submit/",
            {
                "answers": {
                    str(self.q1.id): "4",
                    str(self.q2.id): "yes",
                }
            },
            format="json",
        )
        self.auth_as(self.emp2_user)
        self.client.post(
            f"/api/wellbeing/surveys/{self.survey.id}/submit/",
            {
                "answers": {
                    str(self.q1.id): "2",
                    str(self.q2.id): "no",
                }
            },
            format="json",
        )

        self.auth_as(self.hr_user)
        stats_resp = self.client.get(
            f"/api/wellbeing/surveys/{self.survey.id}/stats/"
        )
        self.assertEqual(stats_resp.status_code, status.HTTP_200_OK)
        # Envelope: stats_resp.data["data"]["..."]
        self.assertEqual(stats_resp.data["data"]["count_responses"], 2)
        self.assertEqual(len(stats_resp.data["data"]["questions"]), 2)

    def test_manager_team_stats_filtered_by_department(self):
        # Two employees in same department submit
        self.auth_as(self.emp1_user)
        self.client.post(
            f"/api/wellbeing/surveys/{self.survey.id}/submit/",
            {
                "answers": {
                    str(self.q1.id): "4",
                    str(self.q2.id): "yes",
                }
            },
            format="json",
        )
        self.auth_as(self.emp2_user)
        self.client.post(
            f"/api/wellbeing/surveys/{self.survey.id}/submit/",
            {
                "answers": {
                    str(self.q1.id): "3",
                    str(self.q2.id): "yes",
                }
            },
            format="json",
        )

        self.auth_as(self.manager_user)
        team_resp = self.client.get(
            f"/api/wellbeing/surveys/{self.survey.id}/team-stats/"
        )
        self.assertEqual(team_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(team_resp.data["data"]["team_size"], 2)
        self.assertEqual(team_resp.data["data"]["responses"], 2)
        self.assertIn(
            str(self.q1.id),
            team_resp.data["data"]["aggregates"],
        )

    def test_non_manager_cannot_access_team_stats(self):
        self.auth_as(self.emp1_user)
        resp = self.client.get(
            f"/api/wellbeing/surveys/{self.survey.id}/team-stats/"
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
