# reviews/serializers.py
from django.utils import timezone
from rest_framework import serializers

from hr.models import EmployeeProfile
from .models import ReviewCycle, PerformanceReview, ReviewItem, Goal
from accounts.models import User


class ReviewCycleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewCycle
        fields = [
            "id",
            "name",
            "start_date",
            "end_date",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

class ReviewItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewItem
        fields = [
            "id",
            "criteria",
            "score",
            "comment",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

class PerformanceReviewSerializer(serializers.ModelSerializer):
    """
    Main serializer for performance reviews.
    - accepts employee_id, cycle_id on create
    - returns nested employee, manager, cycle, items
    """

    employee_id = serializers.IntegerField(write_only=True, required=False)
    cycle_id = serializers.IntegerField(write_only=True, required=False)

    employee = serializers.SerializerMethodField(read_only=True)
    manager = serializers.SerializerMethodField(read_only=True)
    cycle = ReviewCycleSerializer(read_only=True)
    items = ReviewItemSerializer(many=True, read_only=True)

    class Meta:
        model = PerformanceReview
        fields = [
            "id",
            "employee_id",
            "cycle_id",
            "employee",
            "manager",
            "cycle",
            "status",
            "overall_score",
            "employee_comment",
            "manager_comment",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "status",
            "overall_score",
            "employee",
            "manager",
            "cycle",
            "items",
            "created_at",
            "updated_at",
        ]

    def get_employee(self, obj):
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

    def get_manager(self, obj):
        if not obj.manager:
            return None
        return {
            "id": obj.manager.id,
            "user": {
                "id": obj.manager.user.id,
                "email": obj.manager.user.email,
                "first_name": obj.manager.user.first_name,
                "last_name": obj.manager.user.last_name,
            },
        }

class GoalSerializer(serializers.ModelSerializer):
    employee_id = serializers.IntegerField(write_only=True, required=False)
    cycle_id = serializers.IntegerField(write_only=True, required=False)

    employee = serializers.SerializerMethodField(read_only=True)
    cycle = ReviewCycleSerializer(read_only=True)

    class Meta:
        model = Goal
        fields = [
            "id",
            "employee_id",
            "cycle_id",
            "employee",
            "cycle",
            "title",
            "description",
            "status",
            "progress_percent",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "employee",
            "cycle",
            "created_at",
            "updated_at",
        ]

    def get_employee(self, obj):
        return {
            "id": obj.employee.id,
            "user": {
                "id": obj.employee.user.id,
                "email": obj.employee.user.email,
                "first_name": obj.employee.user.first_name,
                "last_name": obj.employee.user.last_name,
            },
        }
