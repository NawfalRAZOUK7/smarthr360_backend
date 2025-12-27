from rest_framework.permissions import SAFE_METHODS, BasePermission

from hr.models import EmployeeProfile  # add this import at the top of the file

from .access import (
    has_hr_access,
    has_manager_access,
    is_admin,
    is_auditor,
    is_manager,
    is_security_admin,
    is_support,
)
from .models import User


class IsAdminRole(BasePermission):
    """
    Allow access only to users with role ADMIN.
    """

    def has_permission(self, request, view):
        return is_admin(request.user)


class IsHRRole(BasePermission):
    """
    Allow access to HR and ADMIN users.
    """

    def has_permission(self, request, view):
        return has_hr_access(request.user)


class IsManagerOrAbove(BasePermission):
    """
    Allow access to MANAGER, HR, ADMIN.
    """

    def has_permission(self, request, view):
        return has_manager_access(request.user)


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
        return is_admin(user)

class EmployeeProfileAccessPermission(BasePermission):
    """
    Object-level permission for EmployeeProfile:

    - HR / ADMIN: full access
    - Employee: only their own profile
    - Manager: only their direct team members
    - Auditor: read-only access
    """

    def has_object_permission(self, request, view, obj: EmployeeProfile):
        user = request.user
        if not (user and user.is_authenticated):
            return False

        if request.method in SAFE_METHODS and is_auditor(user):
            return True

        # HR & Admin → full access
        if has_hr_access(user):
            return True

        # Employee → only their own profile
        if hasattr(user, "employee_profile") and obj.user_id == user.id:
            return True

        # Manager → their direct team (employee_profile.manager == manager_profile)
        if is_manager(user) and hasattr(user, "employee_profile"):
            manager_profile = user.employee_profile
            return obj.manager_id == manager_profile.id

        return False


class IsAuditorReadOnly(BasePermission):
    """
    Allow read-only access for auditors or admins.
    """

    def has_permission(self, request, view):
        if request.method not in SAFE_METHODS:
            return False
        return is_auditor(request.user)


class IsSecurityAdmin(BasePermission):
    """
    Allow access to security admins or global admins.
    """

    def has_permission(self, request, view):
        return is_security_admin(request.user)


class IsSupport(BasePermission):
    """
    Allow access to support group or global admins.
    """

    def has_permission(self, request, view):
        return is_support(request.user)


class IsHROrAuditorReadOnly(BasePermission):
    """
    Allow HR/Admin to write, and auditors to read-only.
    """

    def has_permission(self, request, view):
        user = request.user
        if request.method in SAFE_METHODS:
            return has_hr_access(user) or is_auditor(user)
        return has_hr_access(user)


class IsManagerOrAuditorReadOnly(BasePermission):
    """
    Allow Manager/HR/Admin to write, and auditors to read-only.
    """

    def has_permission(self, request, view):
        user = request.user
        if request.method in SAFE_METHODS:
            return has_manager_access(user) or is_auditor(user)
        return has_manager_access(user)


class IsHRRoleOrSupport(BasePermission):
    """
    Allow HR/Admin or Support access.
    """

    def has_permission(self, request, view):
        user = request.user
        return has_hr_access(user) or is_support(user)
