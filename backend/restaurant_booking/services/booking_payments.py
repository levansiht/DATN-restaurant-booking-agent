from __future__ import annotations

import base64
import hashlib
import hmac
import logging
from collections import OrderedDict
from datetime import datetime
from decimal import Decimal
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from restaurant_booking.models import Booking, BookingPayment, RestaurantProfile
from restaurant_booking.services.availability import booking_has_conflict, create_pending_booking
from restaurant_booking.services.public_links import build_booking_search_url

logger = logging.getLogger(__name__)

DEFAULT_BOOKING_FEE_AMOUNT = Decimal("100000")
PAYMENT_CONFLICT_REASON = (
    "Khoản cọc đã được thanh toán nhưng bàn không còn trống ở khung giờ này. "
    "Nhà hàng sẽ liên hệ để hỗ trợ đổi bàn hoặc xử lý hoàn cọc."
)
SEPAY_CHECKOUT_URLS = {
    "sandbox": "https://pay-sandbox.sepay.vn/v1/checkout/init",
    "production": "https://pay.sepay.vn/v1/checkout/init",
}
SEPAY_SIGNED_FIELDS = [
    "order_amount",
    "merchant",
    "currency",
    "operation",
    "order_description",
    "order_invoice_number",
    "customer_id",
    "payment_method",
    "success_url",
    "error_url",
    "cancel_url",
]


class BookingPaymentConfigurationError(Exception):
    pass


def _quantize_amount(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.01"))


def _format_sepay_amount(value: Decimal) -> str:
    amount = _quantize_amount(value)
    if amount == amount.to_integral():
        return str(int(amount))
    return format(amount.normalize(), "f")


def _append_query_params(url: str, **params) -> str:
    if not url:
        return url

    parsed = urlsplit(url)
    current = OrderedDict(parse_qsl(parsed.query, keep_blank_values=True))
    current.update({key: value for key, value in params.items() if value not in [None, ""]})
    return urlunsplit(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            urlencode(current),
            parsed.fragment,
        )
    )


def _get_payment_callback_url(base_url: str, booking_code: str, result: str) -> str:
    fallback_url = build_booking_search_url(booking_code)
    target_url = (base_url or fallback_url).strip() or fallback_url
    return _append_query_params(target_url, booking_code=booking_code, payment=result)


def _build_backend_absolute_url(path: str, request=None) -> str:
    if request is not None:
        return request.build_absolute_uri(path)

    backend_url = (settings.BACKEND_URL or "").rstrip("/")
    if backend_url:
        return f"{backend_url}{path}"
    return path


def build_booking_payment_checkout_path(booking_code: str) -> str:
    return reverse(
        "restaurant_booking:booking_payment_checkout",
        kwargs={"booking_code": booking_code},
    )


def build_booking_payment_checkout_url(booking_code: str, request=None) -> str:
    return _build_backend_absolute_url(
        build_booking_payment_checkout_path(booking_code),
        request=request,
    )


def get_booking_fee_amount(flow: str) -> Decimal:
    profile = RestaurantProfile.get_active_profile()
    if not profile:
        return DEFAULT_BOOKING_FEE_AMOUNT

    if flow == BookingPayment.BookingFlow.CHATBOT:
        amount = (
            profile.chatbot_booking_fee_amount
            if profile.chatbot_booking_fee_amount is not None
            else DEFAULT_BOOKING_FEE_AMOUNT
        )
        return _quantize_amount(amount)

    amount = (
        profile.public_booking_fee_amount
        if profile.public_booking_fee_amount is not None
        else DEFAULT_BOOKING_FEE_AMOUNT
    )
    return _quantize_amount(amount)


def get_sepay_checkout_action_url() -> str:
    environment = (settings.SEPAY_ENVIRONMENT or "sandbox").lower()
    return SEPAY_CHECKOUT_URLS.get(environment, SEPAY_CHECKOUT_URLS["sandbox"])


def ensure_sepay_is_configured() -> None:
    if not settings.SEPAY_MERCHANT_ID or not settings.SEPAY_SECRET_KEY:
        raise BookingPaymentConfigurationError(
            "SePay chưa được cấu hình đầy đủ. Vui lòng kiểm tra MERCHANT ID và SECRET KEY."
        )


def sign_sepay_fields(fields: dict[str, str]) -> str:
    ensure_sepay_is_configured()
    signed_payload = ",".join(
        f"{field}={fields[field]}"
        for field in SEPAY_SIGNED_FIELDS
        if fields.get(field) not in [None, ""]
    )
    digest = hmac.new(
        settings.SEPAY_SECRET_KEY.encode("utf-8"),
        signed_payload.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.b64encode(digest).decode("utf-8")


def create_booking_payment_for_booking(
    booking: Booking,
    *,
    flow: str,
    payment_method: str | None = None,
) -> BookingPayment | None:
    amount = get_booking_fee_amount(flow)
    if amount <= 0:
        return None

    ensure_sepay_is_configured()

    profile = RestaurantProfile.get_active_profile()
    restaurant_name = profile.name if profile else (settings.WEBSITE_NAME or "PSCD Japanese Dining")
    description = f"Phi giu cho booking {booking.code} - {restaurant_name}"

    payment, _ = BookingPayment.objects.update_or_create(
        booking=booking,
        defaults={
            "provider": BookingPayment.Provider.SEPAY,
            "flow": flow,
            "status": BookingPayment.PaymentStatus.PENDING,
            "amount": amount,
            "currency": "VND",
            "order_invoice_number": f"BK-{booking.code}",
            "order_description": description[:255],
            "payment_method": payment_method or "",
        },
    )
    return payment


def create_booking_with_payment(
    *,
    flow: str,
    table_id,
    guest_name,
    guest_phone,
    guest_email,
    booking_date,
    booking_time,
    party_size,
    duration_hours,
    notes="",
    source=Booking.BookingSource.WEBSITE,
):
    with transaction.atomic():
        booking = create_pending_booking(
            table_id=table_id,
            guest_name=guest_name,
            guest_phone=guest_phone,
            guest_email=guest_email,
            booking_date=booking_date,
            booking_time=booking_time,
            party_size=party_size,
            duration_hours=duration_hours,
            notes=notes,
            source=source,
        )
        payment = create_booking_payment_for_booking(booking, flow=flow)
        return booking, payment


def build_sepay_checkout_context(payment: BookingPayment) -> dict[str, object]:
    ensure_sepay_is_configured()
    booking = payment.booking
    form_fields = OrderedDict()
    form_fields["order_amount"] = _format_sepay_amount(payment.amount)
    form_fields["merchant"] = settings.SEPAY_MERCHANT_ID
    form_fields["currency"] = payment.currency or "VND"
    form_fields["operation"] = "PURCHASE"
    form_fields["order_description"] = payment.order_description or f"Phi giu cho booking {booking.code}"
    form_fields["order_invoice_number"] = payment.order_invoice_number
    form_fields["customer_id"] = booking.code

    if payment.payment_method:
        form_fields["payment_method"] = payment.payment_method

    form_fields["success_url"] = _get_payment_callback_url(
        settings.SEPAY_SUCCESS_URL,
        booking.code,
        "success",
    )
    form_fields["error_url"] = _get_payment_callback_url(
        settings.SEPAY_ERROR_URL,
        booking.code,
        "error",
    )
    form_fields["cancel_url"] = _get_payment_callback_url(
        settings.SEPAY_CANCEL_URL,
        booking.code,
        "cancel",
    )

    return {
        "action_url": get_sepay_checkout_action_url(),
        "fields": form_fields,
        "signature": sign_sepay_fields(form_fields),
    }


def serialize_booking_payment(payment: BookingPayment | None, request=None):
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
        "amount": payment.amount,
        "currency": payment.currency,
        "order_invoice_number": payment.order_invoice_number,
        "checkout_url": (
            build_booking_payment_checkout_url(payment.booking.code, request=request)
            if payment.status != BookingPayment.PaymentStatus.PAID
            else None
        ),
        "paid_at": payment.paid_at,
        "transaction_id": payment.sepay_transaction_id,
        "transaction_status": payment.provider_transaction_status,
        "notification_type": payment.notification_type,
        "requires_payment": payment.requires_payment,
    }


def _parse_transaction_paid_at(value: str | None):
    if not value:
        return None

    try:
        parsed = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None

    if timezone.is_naive(parsed):
        return timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def process_sepay_ipn(payload: dict, received_secret_key: str | None) -> dict[str, object]:
    ensure_sepay_is_configured()

    expected_secret_key = settings.SEPAY_SECRET_KEY
    if expected_secret_key and received_secret_key != expected_secret_key:
        raise BookingPaymentConfigurationError("Secret key từ SePay không hợp lệ.")

    order_data = payload.get("order") or {}
    transaction_data = payload.get("transaction") or {}
    invoice_number = (order_data.get("order_invoice_number") or "").strip()

    if not invoice_number:
        return {"success": True, "ignored": True, "reason": "missing_invoice_number"}

    payment = (
        BookingPayment.objects.select_related("booking")
        .filter(order_invoice_number=invoice_number, is_deleted=False)
        .first()
    )
    if not payment:
        logger.warning("Ignore SePay IPN because payment was not found. invoice=%s", invoice_number)
        return {"success": True, "ignored": True, "reason": "payment_not_found"}

    received_amount = _quantize_amount(
        order_data.get("order_amount") or transaction_data.get("transaction_amount") or 0
    )
    received_currency = (order_data.get("order_currency") or transaction_data.get("transaction_currency") or "VND").upper()
    notification_type = payload.get("notification_type") or ""
    transaction_status = transaction_data.get("transaction_status") or ""

    payment.payment_method = transaction_data.get("payment_method") or payment.payment_method
    payment.sepay_order_id = order_data.get("order_id") or payment.sepay_order_id
    payment.sepay_transaction_id = transaction_data.get("transaction_id") or payment.sepay_transaction_id
    payment.provider_transaction_status = transaction_status or payment.provider_transaction_status
    payment.notification_type = notification_type or payment.notification_type
    payment.raw_ipn_payload = payload

    if received_amount != _quantize_amount(payment.amount) or received_currency != (payment.currency or "VND").upper():
        payment.save(
            update_fields=[
                "payment_method",
                "sepay_order_id",
                "sepay_transaction_id",
                "provider_transaction_status",
                "notification_type",
                "raw_ipn_payload",
                "updated_at",
            ]
        )
        logger.warning(
            "Ignore SePay IPN due to amount/currency mismatch. invoice=%s expected=%s/%s received=%s/%s",
            invoice_number,
            payment.amount,
            payment.currency,
            received_amount,
            received_currency,
        )
        return {"success": True, "ignored": True, "reason": "amount_or_currency_mismatch"}

    if notification_type == "ORDER_PAID":
        with transaction.atomic():
            payment = (
                BookingPayment.objects.select_for_update()
                .select_related("booking", "booking__table")
                .get(id=payment.id)
            )
            booking = payment.booking
            payment.paid_at = _parse_transaction_paid_at(transaction_data.get("transaction_date")) or timezone.now()
            payment.status = BookingPayment.PaymentStatus.PAID
            payment.payment_method = transaction_data.get("payment_method") or payment.payment_method
            payment.sepay_order_id = order_data.get("order_id") or payment.sepay_order_id
            payment.sepay_transaction_id = transaction_data.get("transaction_id") or payment.sepay_transaction_id
            payment.provider_transaction_status = transaction_status or payment.provider_transaction_status
            payment.notification_type = notification_type or payment.notification_type
            payment.raw_ipn_payload = payload
            payment.save(
                update_fields=[
                    "payment_method",
                    "sepay_order_id",
                    "sepay_transaction_id",
                    "provider_transaction_status",
                    "notification_type",
                    "paid_at",
                    "status",
                    "raw_ipn_payload",
                    "updated_at",
                ]
            )

            if booking.status == Booking.BookingStatus.PENDING:
                has_conflict = booking_has_conflict(
                    table=booking.table,
                    booking_date=booking.booking_date,
                    booking_time=booking.booking_time,
                    duration_hours=booking.duration_hours,
                    exclude_booking_id=booking.id,
                )
                if has_conflict:
                    booking.mark_cancelled(reason=PAYMENT_CONFLICT_REASON)
                    return {
                        "success": True,
                        "ignored": False,
                        "payment_status": payment.status,
                        "booking_status": booking.status,
                    }

                booking.mark_confirmed()

        return {
            "success": True,
            "ignored": False,
            "payment_status": BookingPayment.PaymentStatus.PAID,
            "booking_status": payment.booking.status,
        }

    if notification_type == "TRANSACTION_VOID":
        payment.status = BookingPayment.PaymentStatus.VOID
        payment.save(
            update_fields=[
                "payment_method",
                "sepay_order_id",
                "sepay_transaction_id",
                "provider_transaction_status",
                "notification_type",
                "status",
                "raw_ipn_payload",
                "updated_at",
            ]
        )
        return {"success": True, "ignored": False, "payment_status": payment.status}

    payment.save(
        update_fields=[
            "payment_method",
            "sepay_order_id",
            "sepay_transaction_id",
            "provider_transaction_status",
            "notification_type",
            "raw_ipn_payload",
            "updated_at",
        ]
    )
    return {"success": True, "ignored": True, "reason": "unsupported_notification_type"}
