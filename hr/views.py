from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from accounts.permissions import EmployeeProfileAccessPermission, IsHRRole, IsManagerOrAbove
from smarthr360_backend.api_mixins import ApiResponseMixin

from .models import Department, EmployeeProfile, EmployeeSkill, FutureCompetency, Skill
from .serializers import (
    DepartmentSerializer,
    EmployeeProfileSerializer,
    EmployeeSelfUpdateSerializer,
    EmployeeSkillSerializer,
    FutureCompetencySerializer,
    SkillSerializer,
)

# --------------------------------------------------------------------------------------
#   DEPARTMENTS
# --------------------------------------------------------------------------------------

class DepartmentListCreateView(ApiResponseMixin, generics.ListCreateAPIView):
    queryset = Department.objects.all().order_by("name")
    serializer_class = DepartmentSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsHRRole()]
        return [permissions.IsAuthenticated()]


class DepartmentDetailView(ApiResponseMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsHRRole]


# --------------------------------------------------------------------------------------
#   EMPLOYEE ME
# --------------------------------------------------------------------------------------

class EmployeeMeView(ApiResponseMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, request):
        profile, _ = EmployeeProfile.objects.get_or_create(user=request.user)
        return profile

    def get(self, request):
        profile = self.get_object(request)
        serializer = EmployeeProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        profile = self.get_object(request)
        serializer = EmployeeSelfUpdateSerializer(
            profile,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            EmployeeProfileSerializer(profile).data,
            status=status.HTTP_200_OK,
        )


# --------------------------------------------------------------------------------------
#   EMPLOYEE LIST + FILTERS ADDED HERE
# --------------------------------------------------------------------------------------

class EmployeeListCreateView(ApiResponseMixin, generics.ListCreateAPIView):
    serializer_class = EmployeeProfileSerializer
    permission_classes = [IsHRRole]

    def get_queryset(self):
        qs = EmployeeProfile.objects.select_related("user", "department")

        params = self.request.query_params

        # ------------------------
        # FILTER: department=IT
        # ------------------------
        department_code = params.get("department")
        if department_code:
            qs = qs.filter(department__code__iexact=department_code)

        # ------------------------
        # FILTER: is_active=true/false
        # ------------------------
        is_active_param = params.get("is_active")
        if is_active_param is not None:
            v = is_active_param.lower()
            if v in ("true", "1", "yes", "y"):
                qs = qs.filter(is_active=True)
            elif v in ("false", "0", "no", "n"):
                qs = qs.filter(is_active=False)

        # ------------------------
        # FILTER: manager=<id>
        # ------------------------
        manager_id = params.get("manager")
        if manager_id:
            qs = qs.filter(manager_id=manager_id)

        return qs

    def perform_create(self, serializer):
        user_id = self.request.data.get("user_id")
        if not user_id:
            raise ValidationError({"user_id": "This field is required."})

        user = get_object_or_404(User, pk=user_id)
        serializer.save(user=user)


class EmployeeDetailView(ApiResponseMixin, generics.RetrieveUpdateAPIView):
    queryset = EmployeeProfile.objects.select_related("user", "department").all()
    serializer_class = EmployeeProfileSerializer
    permission_classes = [permissions.IsAuthenticated, EmployeeProfileAccessPermission]


# --------------------------------------------------------------------------------------
#   MANAGER TEAM
# --------------------------------------------------------------------------------------

class MyTeamListView(ApiResponseMixin, generics.ListAPIView):
    serializer_class = EmployeeProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAbove]

    def get_queryset(self):
        user = self.request.user

        if user.has_role(user.Role.HR, user.Role.ADMIN):
            return EmployeeProfile.objects.select_related("user", "department").all()

        if hasattr(user, "employee_profile"):
            manager_profile = user.employee_profile
            return EmployeeProfile.objects.select_related("user", "department").filter(
                manager=manager_profile
            )

        return EmployeeProfile.objects.none()


# --------------------------------------------------------------------------------------
#   SKILLS
# --------------------------------------------------------------------------------------

class SkillListCreateView(ApiResponseMixin, generics.ListCreateAPIView):
    queryset = Skill.objects.filter(is_active=True).order_by("name")
    serializer_class = SkillSerializer

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()]
        return [IsManagerOrAbove()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class SkillDetailView(ApiResponseMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()]
        return [IsManagerOrAbove()]


# --------------------------------------------------------------------------------------
#   EMPLOYEE SKILLS
# --------------------------------------------------------------------------------------

class EmployeeSkillListCreateView(ApiResponseMixin, generics.ListCreateAPIView):
    serializer_class = EmployeeSkillSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = EmployeeSkill.objects.select_related(
            "employee__user", "employee__department", "skill"
        )

        if user.has_role(user.Role.HR, user.Role.ADMIN):
            return qs

        if user.role == user.Role.MANAGER and hasattr(user, "employee_profile"):
            manager_profile = user.employee_profile
            return qs.filter(employee__manager=manager_profile)

        if hasattr(user, "employee_profile"):
            return qs.filter(employee__user=user)

        return qs.none()

    def perform_create(self, serializer):
        user = self.request.user

        if not user.has_role(user.Role.MANAGER, user.Role.HR, user.Role.ADMIN):
            raise PermissionDenied("Only HR, Manager or Admin can create skill evaluations.")

        employee_id = self.request.data.get("employee_id")
        skill_id = self.request.data.get("skill_id")

        if not employee_id or not skill_id:
            raise ValidationError({"detail": "employee_id and skill_id are required."})

        employee = get_object_or_404(EmployeeProfile, pk=employee_id)
        skill = get_object_or_404(Skill, pk=skill_id)

        if user.role == user.Role.MANAGER and hasattr(user, "employee_profile"):
            manager_profile = user.employee_profile
            if employee.manager_id != manager_profile.id:
                raise PermissionDenied("You can only rate skills of your team members.")

        serializer.save(
            employee=employee,
            skill=skill,
            last_evaluated_by=user,
            last_evaluated_at=timezone.now(),
        )


class EmployeeSkillDetailView(ApiResponseMixin, generics.RetrieveUpdateAPIView):
    serializer_class = EmployeeSkillSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = EmployeeSkill.objects.select_related(
            "employee__user", "employee__department", "skill"
        )

        if user.has_role(user.Role.HR, user.Role.ADMIN):
            return qs

        if user.role == user.Role.MANAGER and hasattr(user, "employee_profile"):
            manager_profile = user.employee_profile
            return qs.filter(employee__manager=manager_profile)

        if hasattr(user, "employee_profile"):
            return qs.filter(employee__user=user)

        return qs.none()

    def perform_update(self, serializer):
        user = self.request.user
        if not user.has_role(user.Role.MANAGER, user.Role.HR, user.Role.ADMIN):
            raise PermissionDenied("Only HR, Manager or Admin can update skill evaluations.")
        serializer.save(
            last_evaluated_by=user,
            last_evaluated_at=timezone.now(),
        )


# --------------------------------------------------------------------------------------
#   FUTURE COMPETENCIES
# --------------------------------------------------------------------------------------

class FutureCompetencyListCreateView(ApiResponseMixin, generics.ListCreateAPIView):
    queryset = FutureCompetency.objects.select_related("skill", "department")
    serializer_class = FutureCompetencySerializer

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()]
        return [IsManagerOrAbove()]

    def perform_create(self, serializer):
        user = self.request.user

        skill_id = self.request.data.get("skill_id")
        department_id = self.request.data.get("department_id")

        if not skill_id:
            raise ValidationError({"detail": "skill_id is required."})

        skill = get_object_or_404(Skill, pk=skill_id)
        department = None
        if department_id:
            department = get_object_or_404(Department, pk=department_id)

        serializer.save(
            skill=skill,
            department=department,
            created_by=user,
        )


class FutureCompetencyDetailView(ApiResponseMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = FutureCompetency.objects.select_related("skill", "department")
    serializer_class = FutureCompetencySerializer

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()]
        return [IsManagerOrAbove()]
