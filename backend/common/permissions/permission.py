from accounts.models.user import User
from rest_framework import permissions


class IsAdminPortalUser(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.has_portal_access
        )


class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.status == User.UserStatus.ACTIVE
            and user.role == User.UserRole.SUPER_ADMIN
        )
