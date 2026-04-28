from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.http import HttpResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from restaurant_booking.models import Booking, BookingPayment, Table
from restaurant_booking.serializers import (
    BookingSerializer,
    PublicBookingCreateSerializer,
    RestaurantBookingChatRequestSerializer,
    TableSerializer,
)
from restaurant_booking.services.availability import booking_has_conflict
from restaurant_booking.services.booking_payments import (
    BookingPaymentConfigurationError,
    build_sepay_checkout_context,
    serialize_booking_payment,
    process_sepay_ipn,
)
from restaurant_booking.services.chat import RestaurantBookingChatService
from restaurant_booking.services.public_links import build_booking_search_url


@api_view(["POST"])
@permission_classes([AllowAny])
def restaurant_chat_stream(request):
    serializer = RestaurantBookingChatRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    chat_service = RestaurantBookingChatService()

    response = StreamingHttpResponse(
        chat_service.chat(request, serializer.validated_data),
        content_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache"
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Headers"] = "Cache-Control"
    return response


@api_view(["GET"])
@permission_classes([AllowAny])
def table_list(request):
    tables = Table.objects.filter(is_deleted=False).order_by("floor", "id")
    booking_date = request.GET.get("date")
    booking_time = request.GET.get("booking_time")
    duration_hours = request.GET.get("duration_hours", "2.0")
    booking_date_obj = None
    booking_time_obj = None

    if booking_date:
        try:
            booking_date_obj = datetime.strptime(booking_date, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    if booking_time:
        try:
            booking_time_obj = datetime.strptime(booking_time, "%H:%M").time()
        except ValueError:
            return Response(
                {"error": "Invalid time format. Use HH:MM."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    try:
        duration_hours_value = Decimal(duration_hours)
    except (InvalidOperation, TypeError):
        return Response(
            {"error": "Invalid duration_hours value."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    floors = {}
    for table in tables:
        table_status = table.get_status_display()
        is_available_for_booking = table.is_available_for_booking

        if table.status == Table.TableStatus.AVAILABLE and booking_date_obj:
            if booking_time_obj:
                has_booking = booking_has_conflict(
                    table=table,
                    booking_date=booking_date_obj,
                    booking_time=booking_time_obj,
                    duration_hours=duration_hours_value,
                )
            else:
                has_booking = Booking.objects.filter(
                    table=table,
                    booking_date=booking_date_obj,
                    status=Booking.BookingStatus.CONFIRMED,
                ).exists()

            if has_booking:
                table_status = "Reserved"
                is_available_for_booking = False
            else:
                table_status = "Available"
                is_available_for_booking = True
        elif table.status != Table.TableStatus.AVAILABLE:
            is_available_for_booking = False

        floor_key = f"Floor {table.floor}"
        floors.setdefault(floor_key, []).append(
            {
                "id": table.id,
                "table_type": table.get_table_type_display(),
                "capacity": table.capacity,
                "floor": table.floor,
                "status": table_status,
                "is_available_for_booking": is_available_for_booking,
                "created_at": table.created_at.isoformat(),
                "notes": table.notes,
            }
        )

    return Response(
        [{"name": floor_name, "tables": table_rows} for floor_name, table_rows in floors.items()]
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def table_search(request):
    data = request.data
    booking_date = data.get("booking_date")
    booking_time = data.get("booking_time")
    party_size = data.get("party_size")
    table_type = data.get("table_type")
    floor = data.get("floor")

    if not all([booking_date, booking_time, party_size]):
        return Response(
            {"error": "booking_date, booking_time và party_size là bắt buộc."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        booking_date_obj = datetime.strptime(booking_date, "%Y-%m-%d").date()
        booking_time_obj = datetime.strptime(booking_time, "%H:%M").time()
    except ValueError:
        return Response(
            {"error": "Sai định dạng ngày hoặc giờ."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    tables = Table.objects.filter(
        is_deleted=False,
        status=Table.TableStatus.AVAILABLE,
        capacity__gte=party_size,
    ).order_by("capacity", "floor", "id")

    if table_type:
        tables = tables.filter(table_type=table_type)
    if floor:
        tables = tables.filter(floor=floor)

    available_tables = [
        table
        for table in tables
        if not booking_has_conflict(table, booking_date_obj, booking_time_obj)
    ]

    return Response(
        {
            "available_tables": [
                {
                    "id": table.id,
                    "table_type": table.get_table_type_display(),
                    "capacity": table.capacity,
                    "floor": table.floor,
                    "status": table.get_status_display(),
                    "is_available_for_booking": table.is_available_for_booking,
                    "notes": table.notes,
                }
                for table in available_tables
            ],
            "search_criteria": {
                "booking_date": booking_date,
                "booking_time": booking_time,
                "party_size": party_size,
                "table_type": table_type,
                "floor": floor,
            },
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def table_detail(request, table_id):
    table = get_object_or_404(Table, id=table_id, is_deleted=False)
    return Response(TableSerializer(table).data)


@api_view(["POST"])
@permission_classes([AllowAny])
def booking_create(request):
    serializer = PublicBookingCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    booking = serializer.save()
    try:
        payment = booking.payment
    except BookingPayment.DoesNotExist:
        payment = None

    if payment:
        message = (
            "Yêu cầu thanh toán cọc đã được tạo. Chỉ khi SePay báo thanh toán thành công thì booking mới được xác nhận."
        )
    else:
        message = "Đặt bàn thành công. Thông tin xác nhận đã được gửi tới email của bạn."

    return Response(
        {
            "message": message,
            "booking": BookingSerializer(booking, context={"request": request}).data,
            "payment": serialize_booking_payment(payment, request=request),
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def booking_search_by_code(request):
    code = (request.GET.get("code") or "").strip().upper()
    if not code:
        return Response(
            {"error": "code parameter is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    booking = (
        Booking.objects.filter(code=code, is_deleted=False)
        .select_related("table", "payment")
        .first()
    )
    if not booking:
        return Response(
            {"error": "No booking found with this confirmation code"},
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response(BookingSerializer(booking, context={"request": request}).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def booking_payment_checkout(request, booking_code):
    normalized_code = (booking_code or "").strip().upper()
    booking = get_object_or_404(
        Booking.objects.select_related("payment"),
        code=normalized_code,
        is_deleted=False,
    )

    try:
        payment = booking.payment
    except BookingPayment.DoesNotExist:
        return Response(
            {"error": "Booking này hiện chưa có giao dịch thanh toán."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if payment.status == BookingPayment.PaymentStatus.PAID:
        return redirect(build_booking_search_url(booking.code))

    try:
        checkout_context = build_sepay_checkout_context(payment)
    except BookingPaymentConfigurationError as exc:
        return Response(
            {"error": str(exc)},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    html = render_to_string(
        "payment/sepay_checkout.html",
        {
            "action_url": checkout_context["action_url"],
            "fields": list(checkout_context["fields"].items()),
            "signature": checkout_context["signature"],
            "booking_code": booking.code,
            "search_url": build_booking_search_url(booking.code),
        },
    )
    return HttpResponse(html)


@api_view(["POST"])
@permission_classes([AllowAny])
def sepay_payment_ipn(request):
    expected_secret_key = settings.SEPAY_SECRET_KEY
    received_secret_key = request.headers.get("X-Secret-Key")

    if expected_secret_key and received_secret_key != expected_secret_key:
        return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

    payload = request.data if isinstance(request.data, dict) else {}

    try:
        result = process_sepay_ipn(payload, received_secret_key)
    except BookingPaymentConfigurationError as exc:
        return Response(
            {"error": str(exc)},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    return Response(result, status=status.HTTP_200_OK)
