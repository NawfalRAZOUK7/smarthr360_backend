from rest_framework import serializers
from django.utils import timezone

from .models import Department, EmployeeProfile, Skill, EmployeeSkill, FutureCompetency
from accounts.models import User
from accounts.serializers import UserSerializer


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

class EmployeeSelfUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer used when an EMPLOYEE updates their own profile.
    Only allows "safe" personal fields.
    """

    class Meta:
        model = EmployeeProfile
        fields = [
            "phone_number",
            "date_of_birth",
        ]

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = [
            "id",
            "name",
            "code",
            "description",
            "category",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

class EmployeeSkillSerializer(serializers.ModelSerializer):
    employee_id = serializers.IntegerField(write_only=True, required=False)
    skill_id = serializers.IntegerField(write_only=True, required=False)

    employee = serializers.SerializerMethodField(read_only=True)
    skill = SkillSerializer(read_only=True)
    last_evaluated_by = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = EmployeeSkill
        fields = [
            "id",
            "employee_id",
            "skill_id",
            "employee",
            "skill",
            "level",
            "target_level",
            "last_evaluated_by",
            "last_evaluated_at",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "employee",
            "skill",
            "last_evaluated_by",
            "last_evaluated_at",
            "created_at",
            "updated_at",
        ]

    def get_employee(self, obj):
        # return minimal view of employee
        return {
            "id": obj.employee.id,
            "user": {
                "id": obj.employee.user.id,
                "email": obj.employee.user.email,
                "first_name": obj.employee.user.first_name,
                "last_name": obj.employee.user.last_name,
            },
            "department": obj.employee.department.name if obj.employee.department else None,
        }

    def get_last_evaluated_by(self, obj):
        if not obj.last_evaluated_by:
            return None
        return {
            "id": obj.last_evaluated_by.id,
            "email": obj.last_evaluated_by.email,
        }

class FutureCompetencySerializer(serializers.ModelSerializer):
    skill_id = serializers.IntegerField(write_only=True, required=False)
    department_id = serializers.IntegerField(write_only=True, required=False)

    skill = SkillSerializer(read_only=True)
    department = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = FutureCompetency
        fields = [
            "id",
            "skill_id",
            "department_id",
            "skill",
            "department",
            "timeframe",
            "importance",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["skill", "department", "created_at", "updated_at"]

    def get_department(self, obj):
        if not obj.department:
            return None
        return {
            "id": obj.department.id,
            "name": obj.department.name,
            "code": obj.department.code,
        }
