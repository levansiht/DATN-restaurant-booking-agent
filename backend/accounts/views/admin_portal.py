from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models.user import User
from accounts.serializers.admin_portal import (
    AdminPortalUserSerializer,
    AdminUserCreateSerializer,
    AdminUserUpdateSerializer,
)
from common.permissions.permission import IsAdminPortalUser, IsSuperAdmin


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminPortalUser])
def admin_session(request):
    serializer = AdminPortalUserSerializer(request.user)
    return Response(serializer.data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def admin_user_list_create(request):
    if request.method == "GET":
        users = User.objects.filter(
            role__in=[User.UserRole.ADMIN, User.UserRole.SUPER_ADMIN]
        ).order_by("role", "full_name", "email")
        serializer = AdminPortalUserSerializer(users, many=True)
        return Response(serializer.data)

    serializer = AdminUserCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    return Response(
        AdminPortalUserSerializer(user).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def admin_user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if user.role != User.UserRole.ADMIN:
        return Response(
            {"detail": "Chỉ có thể chỉnh sửa tài khoản admin thường."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if request.method == "DELETE":
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = AdminUserUpdateSerializer(instance=user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    updated_user = serializer.save()
    return Response(AdminPortalUserSerializer(updated_user).data)
