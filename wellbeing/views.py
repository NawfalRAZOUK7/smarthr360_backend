# wellbeing/views.py
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from hr.models import EmployeeProfile
from .models import WellbeingSurvey, SurveyQuestion, SurveyResponse
from .serializers import (
    WellbeingSurveySerializer,
    SurveyQuestionSerializer,
    SurveySubmissionSerializer,
    SurveyStatsSerializer,
    TeamStatsSerializer,
)

class WellbeingSurveyListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/wellbeing/surveys/      → list surveys (any authenticated)
    POST /api/wellbeing/surveys/      → create survey (HR / ADMIN)
    """
    queryset = WellbeingSurvey.objects.all()
    serializer_class = WellbeingSurveySerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        if not user.has_role(user.Role.HR, user.Role.ADMIN):
            raise PermissionDenied("Only HR or Admin can create wellbeing surveys.")
        serializer.save(created_by=user)

class WellbeingSurveyDetailView(generics.RetrieveUpdateAPIView):
    """
    GET   /api/wellbeing/surveys/<id>/
    PATCH /api/wellbeing/surveys/<id>/   → HR / ADMIN only
    """
    queryset = WellbeingSurvey.objects.all()
    serializer_class = WellbeingSurveySerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_update(self, serializer):
        user = self.request.user
        if not user.has_role(user.Role.HR, user.Role.ADMIN):
            raise PermissionDenied("Only HR or Admin can update wellbeing surveys.")
        serializer.save()

class SurveyQuestionListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/wellbeing/surveys/<survey_id>/questions/
    POST /api/wellbeing/surveys/<survey_id>/questions/   → HR / ADMIN
    """
    serializer_class = SurveyQuestionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_survey(self):
        survey_id = self.kwargs.get("survey_id")
        return get_object_or_404(WellbeingSurvey, pk=survey_id)

    def get_queryset(self):
        survey = self.get_survey()
        return SurveyQuestion.objects.filter(survey=survey)

    def perform_create(self, serializer):
        user = self.request.user
        if not user.has_role(user.Role.HR, user.Role.ADMIN):
            raise PermissionDenied("Only HR or Admin can add questions.")
        survey = self.get_survey()
        serializer.save(survey=survey)

class SurveyQuestionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PATCH/DELETE /api/wellbeing/questions/<id>/   → HR / ADMIN only for write
    """
    queryset = SurveyQuestion.objects.select_related("survey")
    serializer_class = SurveyQuestionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_update(self, serializer):
        user = self.request.user
        if not user.has_role(user.Role.HR, user.Role.ADMIN):
            raise PermissionDenied("Only HR or Admin can update questions.")
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if not user.has_role(user.Role.HR, user.Role.ADMIN):
            raise PermissionDenied("Only HR or Admin can delete questions.")
        super().perform_destroy(instance)

class SurveySubmitView(APIView):
    """
    POST /api/wellbeing/surveys/<survey_id>/submit/
    Body:
    {
      "answers": {
        "3": "4",
        "4": "yes",
        "5": "Feeling tired lately"
      }
    }

    ⚠ We do NOT link to User or EmployeeProfile.
    Only store:
      - survey
      - random response_id (UUID)
      - answers JSON
      - department (if user has one)
      - submitted_at
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, survey_id):
        survey = get_object_or_404(WellbeingSurvey, pk=survey_id, is_active=True)

        serializer = SurveySubmissionSerializer(
            data=request.data,
            context={"survey": survey},
        )
        serializer.is_valid(raise_exception=True)
        answers = serializer.validated_data["answers"]

        # derive department from employee profile, if exists
        department = None
        user = request.user
        if hasattr(user, "employee_profile") and user.employee_profile.department:
            department = user.employee_profile.department

        response = SurveyResponse.objects.create(
            survey=survey,
            answers=answers,
            department=department,
        )

        return Response(
            {
                "detail": "Survey submitted successfully.",
                "response_id": str(response.response_id),
            },
            status=status.HTTP_201_CREATED,
        )

class SurveyStatsView(APIView):
    """
    GET /api/wellbeing/surveys/<survey_id>/stats/
    HR / ADMIN only.

    Returns:
    {
      "count_responses": 14,
      "questions": [
        {
          "id": 3,
          "text": "...",
          "type": "SCALE_1_5",
          "avg": 3.7,
          "distribution": {"1": 1, "2": 2, "3": 4, "4": 5, "5": 2}
        },
        {
          "id": 4,
          "type": "YES_NO",
          "yes": 10,
          "no": 4
        },
        {
          "id": 5,
          "type": "TEXT",
          "count_text": 14
        }
      ]
    }
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, survey_id):
        user = request.user
        if not user.has_role(user.Role.HR, user.Role.ADMIN):
            raise PermissionDenied("Only HR or Admin can view global wellbeing stats.")

        survey = get_object_or_404(WellbeingSurvey, pk=survey_id)
        responses = SurveyResponse.objects.filter(survey=survey)
        count_responses = responses.count()

        questions_data = []

        for q in survey.questions.all():
            qid = str(q.id)
            q_data = {
                "id": q.id,
                "text": q.text,
                "type": q.type,
            }

            # collect all answers for this question
            values = []
            for r in responses:
                if qid in r.answers:
                    values.append(r.answers[qid])

            if q.type == SurveyQuestion.QuestionType.SCALE_1_5:
                nums = []
                dist = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
                for v in values:
                    try:
                        n = int(v)
                        if 1 <= n <= 5:
                            nums.append(n)
                            dist[str(n)] += 1
                    except (ValueError, TypeError):
                        continue
                if nums:
                    avg = sum(nums) / len(nums)
                else:
                    avg = None
                q_data["avg"] = avg
                q_data["distribution"] = dist

            elif q.type == SurveyQuestion.QuestionType.YES_NO:
                yes = 0
                no = 0
                for v in values:
                    s = str(v).lower()
                    if s in ["yes", "oui"]:
                        yes += 1
                    elif s in ["no", "non"]:
                        no += 1
                q_data["yes"] = yes
                q_data["no"] = no

            else:  # TEXT
                q_data["count_text"] = len(values)

            questions_data.append(q_data)

        payload = {
            "count_responses": count_responses,
            "questions": questions_data,
        }

        stats_serializer = SurveyStatsSerializer(data=payload)
        stats_serializer.is_valid(raise_exception=True)
        return Response(stats_serializer.data, status=status.HTTP_200_OK)

class TeamStatsView(APIView):
    """
    GET /api/wellbeing/surveys/<survey_id>/team-stats/

    Manager:
      - identifies their employees (EmployeeProfile.manager == manager_profile)
      - collects their departments
      - aggregates responses for those departments

    HR/Admin can also call it (they'll see same aggregate as manager would for his teams).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, survey_id):
        user = request.user
        survey = get_object_or_404(WellbeingSurvey, pk=survey_id)

        # HR/Admin → full org stats, but still using this structure
        if user.has_role(user.Role.HR, user.Role.ADMIN):
            team_profiles = EmployeeProfile.objects.all()
        else:
            # Manager only
            if not (user.role == user.Role.MANAGER and hasattr(user, "employee_profile")):
                raise PermissionDenied("Only managers (or HR/Admin) can view team stats.")
            manager_profile = user.employee_profile
            team_profiles = EmployeeProfile.objects.filter(manager=manager_profile)

        team_size = team_profiles.count()
        dept_ids = {
            ep.department_id for ep in team_profiles if ep.department_id is not None
        }

        if not dept_ids:
            payload = {
                "team_size": team_size,
                "responses": 0,
                "aggregates": {},
            }
            s = TeamStatsSerializer(data=payload)
            s.is_valid(raise_exception=True)
            return Response(s.data, status=status.HTTP_200_OK)

        responses = SurveyResponse.objects.filter(
            survey=survey,
            department_id__in=dept_ids,
        )
        responses_count = responses.count()

        # compute average for SCALE_1_5 questions
        aggregates = {}
        for q in survey.questions.all():
            if q.type != SurveyQuestion.QuestionType.SCALE_1_5:
                continue

            qid = str(q.id)
            nums = []
            for r in responses:
                if qid in r.answers:
                    try:
                        n = int(r.answers[qid])
                        if 1 <= n <= 5:
                            nums.append(n)
                    except (ValueError, TypeError):
                        continue

            if nums:
                avg = sum(nums) / len(nums)
            else:
                avg = None

            # key by question id (string), can be mapped to labels in frontend
            aggregates[qid] = avg

        payload = {
            "team_size": team_size,
            "responses": responses_count,
            "aggregates": aggregates,
        }

        s = TeamStatsSerializer(data=payload)
        s.is_valid(raise_exception=True)
        return Response(s.data, status=status.HTTP_200_OK)
