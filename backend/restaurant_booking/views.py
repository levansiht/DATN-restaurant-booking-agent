from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from restaurant_booking.models import Booking, Table
from restaurant_booking.serializers import (
    BookingSerializer,
    PublicBookingCreateSerializer,
    RestaurantBookingChatRequestSerializer,
    TableSerializer,
)
from restaurant_booking.services.availability import booking_has_conflict
from restaurant_booking.services.chat import RestaurantBookingChatService


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
                    status__in=[
                        Booking.BookingStatus.PENDING,
                        Booking.BookingStatus.CONFIRMED,
                    ],
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
    return Response(
        {
            "message": "Đặt bàn thành công. Thông tin xác nhận đã được gửi tới email của bạn.",
            "booking": BookingSerializer(booking).data,
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

    booking = Booking.objects.filter(code=code, is_deleted=False).select_related("table").first()
    if not booking:
        return Response(
            {"error": "No booking found with this confirmation code"},
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response(BookingSerializer(booking).data)
