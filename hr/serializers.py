from rest_framework import serializers
from accounts.serializers import UserSerializer
from .models import Department, EmployeeProfile


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "name", "code", "description"]


class EmployeeProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        source="department",
        queryset=Department.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    manager_id = serializers.PrimaryKeyRelatedField(
        source="manager",
        queryset=EmployeeProfile.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = EmployeeProfile
        fields = [
            "id",
            "user",
            "department",
            "department_id",
            "manager_id",
            "job_title",
            "employment_type",
            "hire_date",
            "date_of_birth",
            "phone_number",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
