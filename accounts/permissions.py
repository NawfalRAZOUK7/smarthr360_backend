from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import User
from hr.models import EmployeeProfile  # add this import at the top of the file


class IsAdminRole(BasePermission):
    """
    Allow access only to users with role ADMIN.
    """

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.role == User.Role.ADMIN
        )


class IsHRRole(BasePermission):
    """
    Allow access to HR and ADMIN users.
    """

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.has_role(User.Role.HR, User.Role.ADMIN)
        )


class IsManagerOrAbove(BasePermission):
    """
    Allow access to MANAGER, HR, ADMIN.
    """

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.is_at_least(User.Role.MANAGER)
        )


class ReadOnlyOrAdmin(BasePermission):
    """
    Allow read-only (GET, HEAD, OPTIONS) to authenticated users,
    but write operations only to ADMIN role.
    """

    def has_permission(self, request, view):
        user = request.user

        if not (user and user.is_authenticated):
            return False

        if request.method in SAFE_METHODS:
            return True

        # write methods
        return user.role == User.Role.ADMIN

class EmployeeProfileAccessPermission(BasePermission):
    """
    Object-level permission for EmployeeProfile:

    - HR / ADMIN: full access
    - Employee: only their own profile
    - Manager: only their direct team members
    """

    def has_object_permission(self, request, view, obj: EmployeeProfile):
        user = request.user
        if not (user and user.is_authenticated):
            return False

        # HR & Admin → full access
        if user.has_role(user.Role.HR, user.Role.ADMIN):
            return True

        # Employee → only their own profile
        if hasattr(user, "employee_profile") and obj.user_id == user.id:
            return True

        # Manager → their direct team (employee_profile.manager == manager_profile)
        if user.role == user.Role.MANAGER and hasattr(user, "employee_profile"):
            manager_profile = user.employee_profile
            return obj.manager_id == manager_profile.id

        return False
