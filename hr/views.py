from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.utils import timezone

from accounts.permissions import IsHRRole, IsManagerOrAbove, EmployeeProfileAccessPermission
from accounts.models import User
from .models import Department, EmployeeProfile, Skill, EmployeeSkill, FutureCompetency
from .serializers import (
    DepartmentSerializer,
    EmployeeProfileSerializer,
    EmployeeSelfUpdateSerializer,
    SkillSerializer,
    EmployeeSkillSerializer,
    FutureCompetencySerializer,
)



class DepartmentListCreateView(generics.ListCreateAPIView):
    """
    GET /api/hr/departments/
    POST /api/hr/departments/
    Only HR/Admin can create departments.
    All authenticated can list (you can tighten later if needed).
    """
    queryset = Department.objects.all().order_by("name")
    serializer_class = DepartmentSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsHRRole()]
        return [permissions.IsAuthenticated()]


class DepartmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/PATCH/DELETE /api/hr/departments/<id>/
    Only HR/Admin.
    """
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsHRRole]


class EmployeeMeView(APIView):
    """
    GET  /api/hr/employees/me/   → view own profile (auto-create if needed)
    PATCH /api/hr/employees/me/ → update allowed personal fields only
    """
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
        # return full profile with all fields:
        return Response(
            EmployeeProfileSerializer(profile).data,
            status=status.HTTP_200_OK,
        )



class EmployeeListCreateView(generics.ListCreateAPIView):
    """
    GET /api/hr/employees/
    POST /api/hr/employees/
    HR/Admin only.

    For POST, you must provide user_id (existing user),
    then HR can fill HR fields.
    """
    queryset = EmployeeProfile.objects.select_related("user", "department").all()
    serializer_class = EmployeeProfileSerializer
    permission_classes = [IsHRRole]

    def perform_create(self, serializer):
        user_id = self.request.data.get("user_id")
        if not user_id:
            raise ValidationError({"user_id": "This field is required."})

        user = get_object_or_404(User, pk=user_id)
        serializer.save(user=user)


class EmployeeDetailView(generics.RetrieveUpdateAPIView):
    """
    GET/PUT/PATCH /api/hr/employees/<id>/

    - HR / Admin: any employee
    - Manager: only their team members
    - Employee: only themselves
    """
    queryset = EmployeeProfile.objects.select_related("user", "department").all()
    serializer_class = EmployeeProfileSerializer
    permission_classes = [permissions.IsAuthenticated, EmployeeProfileAccessPermission]

class MyTeamListView(generics.ListAPIView):
    """
    GET /api/hr/employees/my-team/

    - Manager → their direct reports (employees whose manager == current user's employee_profile)
    - HR / Admin → all employees (you can later restrict if you want)
    """
    serializer_class = EmployeeProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAbove]

    def get_queryset(self):
        user = self.request.user

        # HR / Admin see all (for now)
        if user.has_role(user.Role.HR, user.Role.ADMIN):
            return EmployeeProfile.objects.select_related("user", "department").all()

        # Manager: only their team
        if hasattr(user, "employee_profile"):
            manager_profile = user.employee_profile
            return EmployeeProfile.objects.select_related("user", "department").filter(
                manager=manager_profile
            )

        # fallback: empty queryset
        return EmployeeProfile.objects.none()

class SkillListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/hr/skills/         → list all skills
    POST /api/hr/skills/         → create skill (HR / Manager / Admin)
    """
    queryset = Skill.objects.filter(is_active=True).order_by("name")
    serializer_class = SkillSerializer

    def get_permissions(self):
        # Everyone authenticated can READ; only manager+ can WRITE
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()]
        return [IsManagerOrAbove()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class SkillDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/hr/skills/<id>/
    PUT    /api/hr/skills/<id>/   (HR / Manager / Admin)
    PATCH  /api/hr/skills/<id>/
    DELETE /api/hr/skills/<id>/
    """
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()]
        return [IsManagerOrAbove()]

class EmployeeSkillListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/hr/employee-skills/
        - HR / Admin: all employee skills
        - Manager: only team employees
        - Employee: only self skills

    POST /api/hr/employee-skills/
        - HR / Manager / Admin: create or update skill rating for an employee
    """
    serializer_class = EmployeeSkillSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = EmployeeSkill.objects.select_related(
            "employee__user", "employee__department", "skill"
        )

        # HR & Admin → all
        if user.has_role(user.Role.HR, user.Role.ADMIN):
            return qs

        # Manager → only team (employees whose manager == my employee_profile)
        if user.role == user.Role.MANAGER and hasattr(user, "employee_profile"):
            manager_profile = user.employee_profile
            return qs.filter(employee__manager=manager_profile)

        # Employee → only self
        if hasattr(user, "employee_profile"):
            return qs.filter(employee__user=user)

        return qs.none()

    def perform_create(self, serializer):
        user = self.request.user

        # Only HR / Manager / Admin can create ratings
        if not user.has_role(user.Role.MANAGER, user.Role.HR, user.Role.ADMIN):
            raise PermissionDenied("Only HR, Manager or Admin can create skill evaluations.")

        employee_id = self.request.data.get("employee_id")
        skill_id = self.request.data.get("skill_id")

        if not employee_id or not skill_id:
            raise ValidationError({"detail": "employee_id and skill_id are required."})

        employee = get_object_or_404(EmployeeProfile, pk=employee_id)
        skill = get_object_or_404(Skill, pk=skill_id)

        # If manager, ensure this employee is in their team
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

class EmployeeSkillDetailView(generics.RetrieveUpdateAPIView):
    """
    GET   /api/hr/employee-skills/<id>/
          - HR/Admin: any
          - Manager: only team member skills
          - Employee: only own skills

    PATCH /api/hr/employee-skills/<id>/
          - HR/Manager/Admin only
    """
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
        # Only HR / Manager / Admin can update
        if not user.has_role(user.Role.MANAGER, user.Role.HR, user.Role.ADMIN):
            raise PermissionDenied("Only HR, Manager or Admin can update skill evaluations.")
        serializer.save(
            last_evaluated_by=user,
            last_evaluated_at=timezone.now(),
        )

class FutureCompetencyListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/hr/future-competencies/
        - all authenticated users can read (to show in dashboards)

    POST /api/hr/future-competencies/
        - HR / Manager / Admin can define future competency needs
    """
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

class FutureCompetencyDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/hr/future-competencies/<id>/
    PATCH  /api/hr/future-competencies/<id>/  (HR / Manager / Admin)
    DELETE /api/hr/future-competencies/<id>/
    """
    queryset = FutureCompetency.objects.select_related("skill", "department")
    serializer_class = FutureCompetencySerializer

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()]
        return [IsManagerOrAbove()]
