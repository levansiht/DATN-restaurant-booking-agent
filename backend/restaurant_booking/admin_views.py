from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models.user import User
from common.permissions.permission import IsAdminPortalUser
from restaurant_booking.models import Booking, Table
from restaurant_booking.serializers import (
    AdminBookingStatusSerializer,
    AdminTableWriteSerializer,
    BookingSerializer,
    TableSerializer,
)


def _missing_permission_response():
    return Response(
        {"detail": "Tài khoản này chưa được cấp quyền cho chức năng này."},
        status=status.HTTP_403_FORBIDDEN,
    )


def _require_permission(request, permission_key):
    if request.user.role == User.UserRole.SUPER_ADMIN:
        return None
    if request.user.has_admin_permission(permission_key):
        return None
    return _missing_permission_response()


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminPortalUser])
def admin_dashboard_summary(request):
    booking_permission_error = _require_permission(request, "manage_bookings")
    table_permission_error = _require_permission(request, "manage_tables")

    bookings = Booking.objects.filter(is_deleted=False)
    tables = Table.objects.filter(is_deleted=False)
    today = timezone.localdate()

    return Response(
        {
            "bookings": {
                "enabled": booking_permission_error is None,
                "total": bookings.count() if booking_permission_error is None else 0,
                "pending": bookings.filter(status=Booking.BookingStatus.PENDING).count()
                if booking_permission_error is None
                else 0,
                "confirmed_today": bookings.filter(
                    booking_date=today,
                    status=Booking.BookingStatus.CONFIRMED,
                ).count()
                if booking_permission_error is None
                else 0,
            },
            "tables": {
                "enabled": table_permission_error is None,
                "total": tables.count() if table_permission_error is None else 0,
                "available": tables.filter(status=Table.TableStatus.AVAILABLE).count()
                if table_permission_error is None
                else 0,
                "maintenance": tables.filter(status=Table.TableStatus.MAINTENANCE).count()
                if table_permission_error is None
                else 0,
            },
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminPortalUser])
def admin_booking_list(request):
    permission_error = _require_permission(request, "manage_bookings")
    if permission_error:
        return permission_error

    bookings = Booking.objects.filter(is_deleted=False).select_related("table").order_by(
        "-booking_date", "-booking_time", "-created_at"
    )

    query = request.GET.get("query", "").strip()
    booking_date = request.GET.get("booking_date")
    status_filter = request.GET.get("status")

    if query:
        bookings = bookings.filter(
            Q(guest_name__icontains=query)
            | Q(guest_email__icontains=query)
            | Q(guest_phone__icontains=query)
            | Q(code__icontains=query)
        )

    if booking_date:
        bookings = bookings.filter(booking_date=booking_date)

    if status_filter:
        bookings = bookings.filter(status=status_filter)

    page = int(request.GET.get("page", 1))
    page_size = min(int(request.GET.get("page_size", 20)), 100)
    paginator = Paginator(bookings, page_size)
    page_obj = paginator.get_page(page)

    serializer = BookingSerializer(page_obj.object_list, many=True)
    return Response(
        {
            "results": serializer.data,
            "pagination": {
                "page": page_obj.number,
                "pages": paginator.num_pages,
                "total": paginator.count,
                "has_next": page_obj.has_next(),
                "has_previous": page_obj.has_previous(),
            },
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminPortalUser])
def admin_booking_detail(request, booking_id):
    permission_error = _require_permission(request, "manage_bookings")
    if permission_error:
        return permission_error

    booking = get_object_or_404(
        Booking.objects.select_related("table"), id=booking_id, is_deleted=False
    )
    serializer = BookingSerializer(booking)
    return Response(serializer.data)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated, IsAdminPortalUser])
def admin_booking_status_update(request, booking_id):
    permission_error = _require_permission(request, "manage_bookings")
    if permission_error:
        return permission_error

    booking = get_object_or_404(Booking, id=booking_id, is_deleted=False)
    serializer = AdminBookingStatusSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    new_status = serializer.validated_data["status"]
    cancellation_reason = serializer.validated_data.get("cancellation_reason", "") or ""

    if new_status == Booking.BookingStatus.CONFIRMED:
        booking.mark_confirmed(request.user)
    elif new_status == Booking.BookingStatus.CANCELLED:
        booking.mark_cancelled(request.user, cancellation_reason)
    else:
        booking.status = new_status
        if new_status != Booking.BookingStatus.CANCELLED:
            booking.cancellation_reason = ""
        booking.save(update_fields=["status", "cancellation_reason", "updated_at"])

    return Response(BookingSerializer(booking).data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsAdminPortalUser])
def admin_table_list_create(request):
    permission_error = _require_permission(request, "manage_tables")
    if permission_error:
        return permission_error

    if request.method == "GET":
        tables = Table.objects.filter(is_deleted=False).order_by("floor", "id")
        floor = request.GET.get("floor")
        status_filter = request.GET.get("status")

        if floor:
            tables = tables.filter(floor=floor)
        if status_filter:
            tables = tables.filter(status=status_filter)

        serializer = TableSerializer(tables, many=True)
        return Response(serializer.data)

    serializer = AdminTableWriteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    table = serializer.save()
    return Response(TableSerializer(table).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated, IsAdminPortalUser])
def admin_table_detail(request, table_id):
    permission_error = _require_permission(request, "manage_tables")
    if permission_error:
        return permission_error

    table = get_object_or_404(Table, id=table_id, is_deleted=False)

    if request.method == "GET":
        return Response(TableSerializer(table).data)

    if request.method == "DELETE":
        table.is_deleted = True
        table.save(update_fields=["is_deleted", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = AdminTableWriteSerializer(instance=table, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    table = serializer.save()
    return Response(TableSerializer(table).data)
