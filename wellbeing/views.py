# wellbeing/views.py (UPDATED WITH ENVELOPE)
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from hr.models import EmployeeProfile
from smarthr360_backend.api_mixins import ApiResponseMixin
from .models import WellbeingSurvey, SurveyQuestion, SurveyResponse
from .serializers import (
    WellbeingSurveySerializer,
    SurveyQuestionSerializer,
    SurveySubmissionSerializer,
    SurveyStatsSerializer,
    TeamStatsSerializer,
)


class WellbeingSurveyListCreateView(ApiResponseMixin, generics.ListCreateAPIView):
    queryset = WellbeingSurvey.objects.all()
    serializer_class = WellbeingSurveySerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        if not user.has_role(user.Role.HR, user.Role.ADMIN):
            raise PermissionDenied("Only HR or Admin can create wellbeing surveys.")
        serializer.save(created_by=user)


class WellbeingSurveyDetailView(ApiResponseMixin, generics.RetrieveUpdateAPIView):
    queryset = WellbeingSurvey.objects.all()
    serializer_class = WellbeingSurveySerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_update(self, serializer):
        user = self.request.user
        if not user.has_role(user.Role.HR, user.Role.ADMIN):
            raise PermissionDenied("Only HR or Admin can update wellbeing surveys.")
        serializer.save()


class SurveyQuestionListCreateView(ApiResponseMixin, generics.ListCreateAPIView):
    serializer_class = SurveyQuestionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_survey(self):
        survey_id = self.kwargs.get("survey_id")
        return get_object_or_404(WellbeingSurvey, pk=survey_id)

    def get_queryset(self):
        return SurveyQuestion.objects.filter(survey=self.get_survey())

    def perform_create(self, serializer):
        user = self.request.user
        if not user.has_role(user.Role.HR, user.Role.ADMIN):
            raise PermissionDenied("Only HR or Admin can add questions.")
        serializer.save(survey=self.get_survey())


class SurveyQuestionDetailView(ApiResponseMixin, generics.RetrieveUpdateDestroyAPIView):
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


class SurveySubmitView(ApiResponseMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, survey_id):
        survey = get_object_or_404(WellbeingSurvey, pk=survey_id, is_active=True)

        serializer = SurveySubmissionSerializer(
            data=request.data,
            context={"survey": survey},
        )
        serializer.is_valid(raise_exception=True)
        answers = serializer.validated_data["answers"]

        department = None
        if hasattr(request.user, "employee_profile"):
            department = request.user.employee_profile.department

        response = SurveyResponse.objects.create(
            survey=survey,
            answers=answers,
            department=department,
        )

        return self.success_response(
            {
                "detail": "Survey submitted successfully.",
                "response_id": str(response.response_id),
            },
            status=status.HTTP_201_CREATED,
        )


class SurveyStatsView(ApiResponseMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, survey_id):
        user = request.user
        if not user.has_role(user.Role.HR, user.Role.ADMIN):
            raise PermissionDenied("Only HR or Admin can view global wellbeing stats.")

        survey = get_object_or_404(WellbeingSurvey, pk=survey_id)
        responses = SurveyResponse.objects.filter(survey=survey)

        questions_data = []
        for q in survey.questions.all():
            qid = str(q.id)
            q_data = {"id": q.id, "text": q.text, "type": q.type}

            values = [r.answers.get(qid) for r in responses if qid in r.answers]

            if q.type == SurveyQuestion.QuestionType.SCALE_1_5:
                nums = []
                dist = {str(i): 0 for i in range(1, 6)}
                for v in values:
                    try:
                        n = int(v)
                        if 1 <= n <= 5:
                            nums.append(n)
                            dist[str(n)] += 1
                    except:
                        continue
                q_data["avg"] = sum(nums) / len(nums) if nums else None
                q_data["distribution"] = dist

            elif q.type == SurveyQuestion.QuestionType.YES_NO:
                yes = sum(str(v).lower() in ["yes", "oui"] for v in values)
                no = sum(str(v).lower() in ["no", "non"] for v in values)
                q_data["yes"] = yes
                q_data["no"] = no

            else:  # TEXT
                q_data["count_text"] = len(values)

            questions_data.append(q_data)

        payload = {
            "count_responses": responses.count(),
            "questions": questions_data,
        }

        s = SurveyStatsSerializer(data=payload)
        s.is_valid(raise_exception=True)

        return self.success_response(s.data)


class TeamStatsView(ApiResponseMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, survey_id):
        user = request.user
        survey = get_object_or_404(WellbeingSurvey, pk=survey_id)

        # Team filtering
        if user.has_role(user.Role.HR, user.Role.ADMIN):
            team_profiles = EmployeeProfile.objects.all()
        elif user.role == User.Role.MANAGER and hasattr(user, "employee_profile"):
            team_profiles = EmployeeProfile.objects.filter(manager=user.employee_profile)
        else:
            raise PermissionDenied("Only managers (or HR/Admin) can view team stats.")

        team_size = team_profiles.count()
        dept_ids = {p.department_id for p in team_profiles if p.department_id}

        if not dept_ids:
            return self.success_response(
                {"team_size": team_size, "responses": 0, "aggregates": {}}
            )

        responses = SurveyResponse.objects.filter(
            survey=survey,
            department_id__in=dept_ids,
        )

        # Aggregates
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
                    except:
                        continue
            aggregates[qid] = sum(nums) / len(nums) if nums else None

        payload = {
            "team_size": team_size,
            "responses": responses.count(),
            "aggregates": aggregates,
        }

        s = TeamStatsSerializer(data=payload)
        s.is_valid(raise_exception=True)

        return self.success_response(s.data)
