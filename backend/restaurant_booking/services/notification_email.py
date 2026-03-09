import logging

from django.conf import settings
from django.utils.formats import date_format, time_format

from common.services.mail_service import MailService
from restaurant_booking.models import Booking
from restaurant_booking.services.public_links import build_booking_search_url

logger = logging.getLogger(__name__)


def _format_duration_hours(duration_hours):
    if duration_hours == duration_hours.to_integral():
        return str(int(duration_hours))
    return format(duration_hours.normalize(), "f")


def send_booking_confirmation_email(booking_id):
    booking = (
        Booking.objects.select_related("table")
        .filter(id=booking_id, is_deleted=False)
        .first()
    )
    if not booking or not booking.guest_email:
        return

    if not settings.EMAIL_HOST or not settings.EMAIL_HOST_USER:
        logger.warning(
            "Skip booking confirmation email because SMTP is not configured. booking_id=%s",
            booking_id,
        )
        return

    restaurant_name = settings.WEBSITE_NAME or "PSCD Japanese Dining"
    lookup_url = build_booking_search_url(booking.code)
    duration_hours_label = _format_duration_hours(booking.duration_hours)

    context = {
        "url_site": restaurant_name,
        "restaurant_name": restaurant_name,
        "guest_name": booking.guest_name or "Quý khách",
        "booking_code": booking.code,
        "booking_date": date_format(booking.booking_date, "d/m/Y"),
        "booking_time": time_format(booking.booking_time, "H:i"),
        "duration_hours": duration_hours_label,
        "party_size": booking.party_size,
        "table_id": booking.table.id,
        "table_type": booking.table.get_table_type_display(),
        "table_floor": booking.table.floor,
        "booking_status": booking.get_status_display(),
        "guest_phone": booking.guest_phone,
        "guest_email": booking.guest_email,
        "notes": booking.notes,
        "lookup_url": lookup_url,
    }

    try:
        MailService().send_email_template(
            subject=f"[{restaurant_name}] Xác nhận tiếp nhận đặt bàn {booking.code}",
            recipient_mails=[booking.guest_email],
            html_template_path="email/booking_confirmation.html",
            context=context,
            fail_silently=False,
        )
    except Exception:
        logger.exception(
            "Unable to send booking confirmation email. booking_id=%s",
            booking_id,
        )
