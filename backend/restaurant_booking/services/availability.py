from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from restaurant_booking.models import Booking, Table
from restaurant_booking.services.notification_email import (
    send_booking_confirmation_email,
)


TABLE_CONFLICT_MESSAGE = (
    "Bàn này vừa được khách khác giữ chỗ trong khung giờ đã chọn."
)


class BookingValidationError(Exception):
    def __init__(self, detail):
        super().__init__(str(detail))
        self.detail = detail


def normalize_booking_date(value):
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value), "%Y-%m-%d").date()


def normalize_booking_time(value):
    if isinstance(value, time):
        return value
    return datetime.strptime(str(value), "%H:%M").time()


def normalize_duration_hours(value):
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def booking_has_conflict(
    table,
    booking_date,
    booking_time,
    duration_hours=Decimal("2.0"),
    exclude_booking_id=None,
):
    booking_date_value = normalize_booking_date(booking_date)
    booking_time_value = normalize_booking_time(booking_time)
    duration_hours_value = normalize_duration_hours(duration_hours)

    requested_start = datetime.combine(booking_date_value, booking_time_value)
    requested_end = requested_start + timezone.timedelta(hours=float(duration_hours_value))

    conflicting_bookings = Booking.objects.filter(
        table=table,
        booking_date=booking_date_value,
        status__in=[Booking.BookingStatus.PENDING, Booking.BookingStatus.CONFIRMED],
    )

    if exclude_booking_id:
        conflicting_bookings = conflicting_bookings.exclude(id=exclude_booking_id)

    for booking in conflicting_bookings:
        booking_start = datetime.combine(booking_date_value, booking.booking_time)
        booking_end = booking_start + timezone.timedelta(hours=float(booking.duration_hours))
        if requested_start < booking_end and requested_end > booking_start:
            return True

    return False


def get_available_tables(
    *,
    booking_date,
    booking_time,
    party_size,
    duration_hours=Decimal("2.0"),
    table_type=None,
    floor=None,
    table_id=None,
):
    booking_date_value = normalize_booking_date(booking_date)
    booking_time_value = normalize_booking_time(booking_time)
    duration_hours_value = normalize_duration_hours(duration_hours)

    tables = Table.objects.filter(
        is_deleted=False,
        status=Table.TableStatus.AVAILABLE,
        capacity__gte=party_size,
    ).order_by("capacity", "floor", "id")

    if table_type:
        tables = tables.filter(table_type=table_type)

    if floor:
        tables = tables.filter(floor=floor)

    if table_id:
        tables = tables.filter(id=table_id)

    return [
        table
        for table in tables
        if not booking_has_conflict(
            table=table,
            booking_date=booking_date_value,
            booking_time=booking_time_value,
            duration_hours=duration_hours_value,
        )
    ]


def create_pending_booking(
    *,
    table_id,
    guest_name,
    guest_phone,
    guest_email,
    booking_date,
    booking_time,
    party_size,
    duration_hours=Decimal("2.0"),
    notes="",
    source=Booking.BookingSource.WEBSITE,
):
    booking_date_value = normalize_booking_date(booking_date)
    booking_time_value = normalize_booking_time(booking_time)
    duration_hours_value = normalize_duration_hours(duration_hours)

    if booking_date_value < timezone.localdate():
        raise BookingValidationError(
            {"booking_date": "Không thể đặt bàn cho ngày trong quá khứ."}
        )

    with transaction.atomic():
        table = (
            Table.objects.select_for_update()
            .filter(id=table_id, is_deleted=False)
            .first()
        )

        if not table:
            raise BookingValidationError({"table_id": "Bàn không tồn tại."})

        if party_size > table.capacity:
            raise BookingValidationError(
                {"party_size": "Số lượng khách vượt quá sức chứa của bàn đã chọn."}
            )

        if table.status != Table.TableStatus.AVAILABLE:
            raise BookingValidationError(
                {"table_id": f"Bàn này hiện không khả dụng ({table.get_status_display()})."}
            )

        if booking_has_conflict(
            table=table,
            booking_date=booking_date_value,
            booking_time=booking_time_value,
            duration_hours=duration_hours_value,
        ):
            raise BookingValidationError(
                {"table_id": TABLE_CONFLICT_MESSAGE}
            )

        booking = Booking.objects.create(
            table=table,
            guest_name=guest_name,
            guest_phone=guest_phone,
            guest_email=guest_email,
            booking_date=booking_date_value,
            booking_time=booking_time_value,
            duration_hours=duration_hours_value,
            party_size=party_size,
            status=Booking.BookingStatus.PENDING,
            source=source,
            notes=notes,
        )

        transaction.on_commit(
            lambda booking_id=booking.id: send_booking_confirmation_email(booking_id)
        )

        return booking
