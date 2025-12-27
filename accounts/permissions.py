from rest_framework.permissions import SAFE_METHODS, BasePermission

from hr.models import EmployeeProfile  # add this import at the top of the file

from .grouping import HR_GROUPS, MANAGER_GROUPS
from .models import User


def _is_admin(user) -> bool:
    return bool(
        user
        and user.is_authenticated
        and (user.is_superuser or user.role == User.Role.ADMIN)
    )


def _in_groups(user, group_names) -> bool:
    if _is_admin(user):
        return True
    return bool(
        user
        and user.is_authenticated
        and user.groups.filter(name__in=group_names).exists()
    )


class IsAdminRole(BasePermission):
    """
    Allow access only to users with role ADMIN.
    """

    def has_permission(self, request, view):
        return _is_admin(request.user)


class IsHRRole(BasePermission):
    """
    Allow access to HR and ADMIN users.
    """

    def has_permission(self, request, view):
        user = request.user
        if _is_admin(user):
            return True
        if user and user.is_authenticated and user.role == User.Role.HR:
            return True
        return _in_groups(user, HR_GROUPS)


class IsManagerOrAbove(BasePermission):
    """
    Allow access to MANAGER, HR, ADMIN.
    """

    def has_permission(self, request, view):
        user = request.user
        if _is_admin(user):
            return True
        if user and user.is_authenticated and user.is_at_least(User.Role.MANAGER):
            return True
        return _in_groups(user, MANAGER_GROUPS | HR_GROUPS)


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
        return _is_admin(user)

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
        if _is_admin(user) or user.has_role(user.Role.HR):
            return True
        if _in_groups(user, HR_GROUPS):
            return True

        # Employee → only their own profile
        if hasattr(user, "employee_profile") and obj.user_id == user.id:
            return True

        # Manager → their direct team (employee_profile.manager == manager_profile)
        if (
            (user.role == user.Role.MANAGER or _in_groups(user, MANAGER_GROUPS))
            and hasattr(user, "employee_profile")
        ):
            manager_profile = user.employee_profile
            return obj.manager_id == manager_profile.id

        return False
