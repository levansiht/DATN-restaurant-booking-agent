from __future__ import annotations

import logging
from decimal import Decimal

import requests
from django.conf import settings

from restaurant_booking.models import Booking, BookingPayment

logger = logging.getLogger(__name__)


def _iso_datetime(value):
    return value.isoformat() if value else None


def _format_time(value):
    return value.strftime("%H:%M") if value else None


def _decimal_to_number(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return value


def _serialize_booking(booking: Booking) -> dict[str, object]:
    table = getattr(booking, "table", None)
    return {
        "id": booking.id,
        "code": booking.code,
        "status": booking.status,
        "status_label": booking.get_status_display(),
        "source": booking.source,
        "source_label": booking.get_source_display(),
        "guest_name": booking.guest_name,
        "guest_phone": booking.guest_phone,
        "guest_email": booking.guest_email,
        "booking_date": booking.booking_date.isoformat() if booking.booking_date else None,
        "booking_time": _format_time(booking.booking_time),
        "duration_hours": _decimal_to_number(booking.duration_hours),
        "party_size": booking.party_size,
        "notes": booking.notes,
        "cancellation_reason": booking.cancellation_reason,
        "confirmed_at": _iso_datetime(booking.confirmed_at),
        "cancelled_at": _iso_datetime(booking.cancelled_at),
        "created_at": _iso_datetime(booking.created_at),
        "updated_at": _iso_datetime(booking.updated_at),
        "table": {
            "id": table.id,
            "floor": table.floor,
            "capacity": table.capacity,
            "table_type": table.table_type,
            "table_type_label": table.get_table_type_display(),
        }
        if table
        else None,
    }


def _serialize_payment(payment: BookingPayment | None) -> dict[str, object] | None:
    if not payment:
        return None

    return {
        "id": payment.id,
        "provider": payment.provider,
        "provider_label": payment.get_provider_display(),
        "flow": payment.flow,
        "flow_label": payment.get_flow_display(),
        "status": payment.status,
        "status_label": payment.get_status_display(),
        "amount": _decimal_to_number(payment.amount),
        "currency": payment.currency,
        "order_invoice_number": payment.order_invoice_number,
        "payment_method": payment.payment_method,
        "sepay_order_id": payment.sepay_order_id,
        "sepay_transaction_id": payment.sepay_transaction_id,
        "provider_transaction_status": payment.provider_transaction_status,
        "notification_type": payment.notification_type,
        "paid_at": _iso_datetime(payment.paid_at),
        "created_at": _iso_datetime(payment.created_at),
        "updated_at": _iso_datetime(payment.updated_at),
    }


def _get_booking_payment(booking: Booking) -> BookingPayment | None:
    try:
        return booking.payment
    except BookingPayment.DoesNotExist:
        return None


def notify_admin_booking_event(
    *,
    event: str,
    booking: Booking,
    action: str,
    payment: BookingPayment | None = None,
) -> None:
    webhook_url = (settings.N8N_ADMIN_WEBHOOK_URL or "").strip()
    if not webhook_url or not settings.N8N_ADMIN_NOTIFICATIONS_ENABLED:
        return

    payload = {
        "event": event,
        "action": action,
        "restaurant": {
            "name": settings.WEBSITE_NAME or "PSCD Japanese Dining",
            "website_url": settings.WEBSITE_URL,
        },
        "booking": _serialize_booking(booking),
        "payment": _serialize_payment(payment or _get_booking_payment(booking)),
    }

    headers = {"Content-Type": "application/json"}
    if settings.N8N_ADMIN_WEBHOOK_SECRET:
        headers["X-N8N-Secret"] = settings.N8N_ADMIN_WEBHOOK_SECRET

    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers=headers,
            timeout=settings.N8N_ADMIN_WEBHOOK_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.RequestException:
        logger.exception(
            "Failed to send admin notification webhook to n8n. event=%s booking_id=%s",
            event,
            booking.id,
        )
