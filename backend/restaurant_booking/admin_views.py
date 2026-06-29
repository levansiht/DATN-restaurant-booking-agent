from datetime import datetime, timedelta
from decimal import Decimal

from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models.user import User
from common.permissions.permission import IsAdminPortalUser
from restaurant_booking.models import (
    Booking,
    BookingPayment,
    Order,
    OrderItem,
    Payment,
    Table,
    TableSession,
)
from restaurant_booking.serializers import (
    AdminBookingStatusSerializer,
    AdminTableWriteSerializer,
    BookingSerializer,
    TableSerializer,
)
from restaurant_booking.services.availability import BookingValidationError
from restaurant_booking.services.table_operations import release_table


def _missing_permission_response():
    return Response(
        {"detail": "Tài khoản này chưa được cấp quyền cho chức năng này."},
        status=status.HTTP_403_FORBIDDEN,
    )


def _require_permission(request, permission_key):
    if request.user.role == User.UserRole.SUPER_ADMIN:
        return None
    if request.user.has_permission(permission_key):
        return None
    return _missing_permission_response()


def _require_any_permission(request, permission_keys):
    if request.user.role == User.UserRole.SUPER_ADMIN:
        return None
    if any(request.user.has_permission(permission_key) for permission_key in permission_keys):
        return None
    return _missing_permission_response()


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminPortalUser])
def admin_dashboard_summary(request):
    booking_permission_error = _require_permission(request, "manage_bookings")
    table_permission_error = _require_permission(request, "manage_tables")
    order_permission_error = _require_permission(request, "manage_orders")
    payment_permission_error = _require_permission(request, "manage_payments")

    bookings = Booking.objects.filter(is_deleted=False)
    tables = Table.objects.filter(is_deleted=False)
    sessions = TableSession.objects.filter(is_deleted=False)
    payments = Payment.objects.filter(is_deleted=False)
    orders = Order.objects.filter(is_deleted=False)
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
                "busy": tables.filter(
                    status__in=[Table.TableStatus.RESERVED, Table.TableStatus.OCCUPIED]
                ).count()
                if table_permission_error is None
                else 0,
                "maintenance": tables.filter(status=Table.TableStatus.MAINTENANCE).count()
                if table_permission_error is None
                else 0,
            },
            "operations": {
                "enabled": order_permission_error is None,
                "open_sessions": sessions.filter(
                    status__in=[
                        TableSession.SessionStatus.OPEN,
                        TableSession.SessionStatus.PAYMENT_PENDING,
                    ]
                ).count()
                if order_permission_error is None
                else 0,
                "open_orders": orders.filter(
                    status__in=[
                        Order.OrderStatus.OPEN,
                        Order.OrderStatus.SENT_TO_KITCHEN,
                        Order.OrderStatus.PARTIALLY_SERVED,
                    ]
                ).count()
                if order_permission_error is None
                else 0,
            },
            "payments": {
                "enabled": payment_permission_error is None,
                "completed_today": payments.filter(
                    paid_at__date=today,
                    status=Payment.PaymentStatus.PAID,
                ).count()
                if payment_permission_error is None
                else 0,
            },
        }
    )


def _parse_report_range(request):
    """Resolve the (start, end) local-date window for a report request.

    Defaults to the last 30 days. The range is clamped to one year to keep the
    daily time series bounded.
    """
    today = timezone.localdate()

    def parse(value, default):
        if not value:
            return default
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return default

    end = parse(request.GET.get("end"), today)
    start = parse(request.GET.get("start"), end - timedelta(days=29))
    if start > end:
        start, end = end, start
    if (end - start).days > 366:
        start = end - timedelta(days=366)
    return start, end


def _money(value):
    return float(value or Decimal("0"))


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminPortalUser])
def admin_revenue_report(request):
    permission_error = _require_any_permission(request, ["view_reports", "manage_payments"])
    if permission_error:
        return permission_error

    start, end = _parse_report_range(request)
    today = timezone.localdate()
    month_start = today.replace(day=1)

    paid_payments = Payment.objects.filter(
        is_deleted=False,
        status=Payment.PaymentStatus.PAID,
        paid_at__isnull=False,
    )
    paid_deposits = BookingPayment.objects.filter(
        is_deleted=False,
        status=BookingPayment.PaymentStatus.PAID,
        paid_at__isnull=False,
    )

    def revenue_window(begin, finish):
        dine = paid_payments.filter(
            paid_at__date__gte=begin, paid_at__date__lte=finish
        ).aggregate(total=Sum("total_amount"))["total"] or Decimal("0")
        deposit = paid_deposits.filter(
            paid_at__date__gte=begin, paid_at__date__lte=finish
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
        return dine, deposit

    range_payments = paid_payments.filter(paid_at__date__gte=start, paid_at__date__lte=end)
    range_deposits = paid_deposits.filter(paid_at__date__gte=start, paid_at__date__lte=end)

    dine_in_total = range_payments.aggregate(total=Sum("total_amount"))["total"] or Decimal("0")
    dine_in_count = range_payments.count()
    deposit_total = range_deposits.aggregate(total=Sum("amount"))["total"] or Decimal("0")
    deposit_count = range_deposits.count()
    average_dine_in = (dine_in_total / dine_in_count) if dine_in_count else Decimal("0")
    total_revenue = dine_in_total + deposit_total

    today_dine, today_deposit = revenue_window(today, today)
    month_dine, month_deposit = revenue_window(month_start, today)

    # Previous period of the same length (immediately before the selected range).
    period_days = (end - start).days + 1
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=period_days - 1)
    prev_dine, prev_deposit = revenue_window(prev_start, prev_end)
    prev_total = prev_dine + prev_deposit
    if prev_total > 0:
        total_change_pct = round(float((total_revenue - prev_total) / prev_total * 100), 1)
    else:
        total_change_pct = None

    # Daily time series (dense — zero-filled for missing days).
    payments_by_day = {
        row["day"]: row["total"]
        for row in range_payments.annotate(day=TruncDate("paid_at"))
        .values("day")
        .annotate(total=Sum("total_amount"))
    }
    deposits_by_day = {
        row["day"]: row["total"]
        for row in range_deposits.annotate(day=TruncDate("paid_at"))
        .values("day")
        .annotate(total=Sum("amount"))
    }
    timeseries = []
    cursor = start
    while cursor <= end:
        dine = payments_by_day.get(cursor) or Decimal("0")
        deposit = deposits_by_day.get(cursor) or Decimal("0")
        timeseries.append(
            {
                "date": cursor.isoformat(),
                "dine_in_revenue": _money(dine),
                "deposit_revenue": _money(deposit),
                "total_revenue": _money(dine + deposit),
            }
        )
        cursor += timedelta(days=1)

    # Deposit revenue split by booking flow (website vs chatbot).
    deposit_flow_rows = {
        row["flow"]: row
        for row in range_deposits.values("flow").annotate(
            amount=Sum("amount"), count=Count("id")
        )
    }
    deposit_by_flow = [
        {
            "flow": value,
            "label": label,
            "amount": _money(deposit_flow_rows.get(value, {}).get("amount")),
            "count": deposit_flow_rows.get(value, {}).get("count", 0),
        }
        for value, label in BookingPayment.BookingFlow.choices
    ]

    # Dine-in revenue split by payment method.
    method_rows = {
        row["method"]: row
        for row in range_payments.values("method").annotate(
            amount=Sum("total_amount"), count=Count("id")
        )
    }
    payment_by_method = [
        {
            "method": value,
            "label": label,
            "amount": _money(method_rows.get(value, {}).get("amount")),
            "count": method_rows.get(value, {}).get("count", 0),
        }
        for value, label in Payment.PaymentMethod.choices
    ]

    # Top selling items across sessions that were paid within the range.
    paid_session_ids = list(
        range_payments.values_list("table_session_id", flat=True).distinct()
    )
    top_items = []
    if paid_session_ids:
        top_items = [
            {
                "name": row["item_name"],
                "quantity": int(row["total_quantity"] or 0),
                "revenue": _money(row["revenue"]),
            }
            for row in (
                OrderItem.objects.filter(
                    is_deleted=False,
                    order__is_deleted=False,
                    order__table_session_id__in=paid_session_ids,
                )
                .exclude(kitchen_status=OrderItem.KitchenStatus.CANCELLED)
                .exclude(order__status=Order.OrderStatus.CANCELLED)
                .values("item_name")
                .annotate(
                    total_quantity=Sum("quantity"),
                    revenue=Sum(
                        ExpressionWrapper(
                            F("quantity") * F("unit_price"),
                            output_field=DecimalField(max_digits=14, decimal_places=2),
                        )
                    ),
                )
                .order_by("-total_quantity")[:10]
            )
        ]

    # Booking volume (by reservation date) within the range.
    range_bookings = Booking.objects.filter(
        is_deleted=False, booking_date__gte=start, booking_date__lte=end
    )
    booking_status_rows = {
        row["status"]: row["count"]
        for row in range_bookings.values("status").annotate(count=Count("id"))
    }
    booking_source_rows = {
        row["source"]: row["count"]
        for row in range_bookings.values("source").annotate(count=Count("id"))
    }

    return Response(
        {
            "range": {
                "start": start.isoformat(),
                "end": end.isoformat(),
                "days": (end - start).days + 1,
            },
            "currency": "VND",
            "summary": {
                "dine_in_revenue": _money(dine_in_total),
                "deposit_revenue": _money(deposit_total),
                "total_revenue": _money(total_revenue),
                "dine_in_count": dine_in_count,
                "deposit_count": deposit_count,
                "average_dine_in_value": _money(average_dine_in),
            },
            "comparison": {
                "previous_start": prev_start.isoformat(),
                "previous_end": prev_end.isoformat(),
                "previous_total_revenue": _money(prev_total),
                "previous_dine_in_revenue": _money(prev_dine),
                "previous_deposit_revenue": _money(prev_deposit),
                "total_change_pct": total_change_pct,
            },
            "today": {
                "dine_in_revenue": _money(today_dine),
                "deposit_revenue": _money(today_deposit),
                "total_revenue": _money(today_dine + today_deposit),
            },
            "this_month": {
                "dine_in_revenue": _money(month_dine),
                "deposit_revenue": _money(month_deposit),
                "total_revenue": _money(month_dine + month_deposit),
            },
            "timeseries": timeseries,
            "deposit_by_flow": deposit_by_flow,
            "payment_by_method": payment_by_method,
            "top_items": top_items,
            "bookings": {
                "total": range_bookings.count(),
                "by_status": [
                    {"status": value, "label": label, "count": booking_status_rows.get(value, 0)}
                    for value, label in Booking.BookingStatus.choices
                ],
                "by_source": [
                    {"source": value, "label": label, "count": booking_source_rows.get(value, 0)}
                    for value, label in Booking.BookingSource.choices
                ],
            },
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminPortalUser])
def admin_booking_list(request):
    permission_error = _require_permission(request, "manage_bookings")
    if permission_error:
        return permission_error

    bookings = Booking.objects.filter(is_deleted=False).select_related("table", "payment").order_by(
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

    serializer = BookingSerializer(page_obj.object_list, many=True, context={"request": request})
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
        Booking.objects.select_related("table", "payment"), id=booking_id, is_deleted=False
    )
    serializer = BookingSerializer(booking, context={"request": request})
    return Response(serializer.data)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated, IsAdminPortalUser])
def admin_booking_status_update(request, booking_id):
    permission_error = _require_permission(request, "manage_bookings")
    if permission_error:
        return permission_error

    booking = get_object_or_404(
        Booking.objects.select_related("table", "payment"),
        id=booking_id,
        is_deleted=False,
    )
    serializer = AdminBookingStatusSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    new_status = serializer.validated_data["status"]
    cancellation_reason = serializer.validated_data.get("cancellation_reason", "") or ""

    if new_status == Booking.BookingStatus.CONFIRMED:
        try:
            payment = booking.payment
        except BookingPayment.DoesNotExist:
            payment = None
        if payment and payment.requires_payment and payment.status != payment.PaymentStatus.PAID:
            return Response(
                {"status": "Booking chỉ được xác nhận sau khi khách đã thanh toán cọc."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            booking.mark_confirmed(request.user)
        except ValidationError as exc:
            return Response(exc.message_dict, status=status.HTTP_400_BAD_REQUEST)
    elif new_status == Booking.BookingStatus.CANCELLED:
        booking.mark_cancelled(request.user, cancellation_reason)
    else:
        booking.status = new_status
        if new_status != Booking.BookingStatus.CANCELLED:
            booking.cancellation_reason = ""
        booking.save(update_fields=["status", "cancellation_reason", "updated_at"])

    return Response(BookingSerializer(booking, context={"request": request}).data)


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


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdminPortalUser])
def admin_table_release(request, table_id):
    permission_error = _require_permission(request, "manage_tables")
    if permission_error:
        return permission_error

    try:
        table, booking = release_table(table_id)
    except BookingValidationError as exc:
        return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        {
            "message": "Bàn đã được mở lại để phục vụ khách tiếp theo.",
            "table": TableSerializer(table).data,
            "booking": (
                BookingSerializer(booking, context={"request": request}).data
                if booking
                else None
            ),
        }
    )
