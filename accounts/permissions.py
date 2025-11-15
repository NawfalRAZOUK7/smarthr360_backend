from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import User


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
