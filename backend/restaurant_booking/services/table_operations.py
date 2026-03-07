from __future__ import annotations

from datetime import datetime

from django.db import transaction
from django.utils import timezone

from restaurant_booking.models import Booking, Table
from restaurant_booking.services.availability import BookingValidationError


def _current_local_datetime(current_datetime=None):
    return current_datetime or timezone.localtime()


def get_current_active_booking(table, current_datetime=None, *, for_update=False):
    local_now = _current_local_datetime(current_datetime)
    current_date = local_now.date()
    current_moment = datetime.combine(
        current_date,
        local_now.time().replace(second=0, microsecond=0, tzinfo=None),
    )

    bookings = Booking.objects.filter(
        table=table,
        booking_date=current_date,
        status__in=[Booking.BookingStatus.PENDING, Booking.BookingStatus.CONFIRMED],
    ).order_by("-booking_time", "-created_at")

    if for_update:
        bookings = bookings.select_for_update()

    for booking in bookings:
        booking_start = datetime.combine(current_date, booking.booking_time)
        booking_end = booking_start + timezone.timedelta(hours=float(booking.duration_hours))
        if booking_start <= current_moment < booking_end:
            return booking, booking_end

    return None, None


def release_table(table_id):
    with transaction.atomic():
        table = (
            Table.objects.select_for_update()
            .filter(id=table_id, is_deleted=False)
            .first()
        )

        if not table:
            raise BookingValidationError({"table_id": "Bàn không tồn tại."})

        current_booking, _ = get_current_active_booking(
            table,
            timezone.localtime(),
            for_update=True,
        )

        if current_booking:
            current_booking.status = Booking.BookingStatus.COMPLETED
            current_booking.save(update_fields=["status", "updated_at"])

        if table.status != Table.TableStatus.AVAILABLE:
            table.status = Table.TableStatus.AVAILABLE
            table.save(update_fields=["status", "updated_at"])

        return table, current_booking
