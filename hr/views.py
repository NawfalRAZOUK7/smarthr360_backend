from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

from accounts.permissions import IsHRRole, IsManagerOrAbove, EmployeeProfileAccessPermission
from accounts.models import User
from .models import Department, EmployeeProfile
from .serializers import (
    DepartmentSerializer,
    EmployeeProfileSerializer,
    EmployeeSelfUpdateSerializer,
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
