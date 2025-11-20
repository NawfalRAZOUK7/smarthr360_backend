from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsHRRole
from .models import Department, EmployeeProfile
from .serializers import DepartmentSerializer, EmployeeProfileSerializer


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
    GET /api/hr/employees/me/
    Returns (or auto-creates) the profile of the current user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile, _ = EmployeeProfile.objects.get_or_create(user=request.user)
        serializer = EmployeeProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)


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
        user = self.request.data.get("user_id")
        if not user:
            raise ValueError("user_id is required to create an employee profile.")
        serializer.save(user_id=user)


class EmployeeDetailView(generics.RetrieveUpdateAPIView):
    """
    GET/PUT/PATCH /api/hr/employees/<id>/
    HR/Admin only.
    """
    queryset = EmployeeProfile.objects.select_related("user", "department").all()
    serializer_class = EmployeeProfileSerializer
    permission_classes = [IsHRRole]
