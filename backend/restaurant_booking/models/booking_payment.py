from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from common.models.base import DateTimeModel, SoftDeleteModel


class BookingPayment(DateTimeModel, SoftDeleteModel):
    class Provider(models.TextChoices):
        SEPAY = "SEPAY", "SePay"

    class PaymentStatus(models.TextChoices):
        PENDING = "PENDING", "Chờ thanh toán"
        PAID = "PAID", "Đã thanh toán"
        VOID = "VOID", "Đã hủy giao dịch"
        FAILED = "FAILED", "Thanh toán thất bại"

    class BookingFlow(models.TextChoices):
        WEBSITE = "WEBSITE", "Đặt bàn trực tiếp"
        CHATBOT = "CHATBOT", "Đặt bàn qua chatbot"

    booking = models.OneToOneField(
        "restaurant_booking.Booking",
        on_delete=models.CASCADE,
        related_name="payment",
        verbose_name="Booking",
    )
    provider = models.CharField(
        max_length=20,
        choices=Provider.choices,
        default=Provider.SEPAY,
        verbose_name="Cổng thanh toán",
    )
    flow = models.CharField(
        max_length=20,
        choices=BookingFlow.choices,
        default=BookingFlow.WEBSITE,
        verbose_name="Luồng đặt bàn",
    )
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        verbose_name="Trạng thái thanh toán",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=Decimal("0"),
        verbose_name="Số tiền",
    )
    currency = models.CharField(
        max_length=10,
        default="VND",
        verbose_name="Tiền tệ",
    )
    order_invoice_number = models.CharField(
        max_length=64,
        unique=True,
        verbose_name="Mã hóa đơn SePay",
    )
    order_description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Mô tả thanh toán",
    )
    payment_method = models.CharField(
        max_length=32,
        blank=True,
        null=True,
        verbose_name="Phương thức thanh toán",
    )
    sepay_order_id = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name="Order ID từ SePay",
    )
    sepay_transaction_id = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        verbose_name="Transaction ID từ SePay",
    )
    provider_transaction_status = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name="Trạng thái giao dịch từ cổng thanh toán",
    )
    notification_type = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name="Loại IPN gần nhất",
    )
    paid_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Thời điểm thanh toán",
    )
    raw_ipn_payload = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Payload IPN thô",
    )

    class Meta:
        db_table = "restaurant_booking_payments"
        verbose_name = "Booking payment"
        verbose_name_plural = "Booking payments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.booking.code} - {self.get_status_display()}"

    @property
    def requires_payment(self):
        return self.amount > 0

    def mark_paid(self, *, notification_type=None, transaction_status=None, paid_at=None):
        self.status = self.PaymentStatus.PAID
        self.notification_type = notification_type or self.notification_type
        self.provider_transaction_status = transaction_status or self.provider_transaction_status
        self.paid_at = paid_at or self.paid_at or timezone.now()
        self.save(
            update_fields=[
                "status",
                "notification_type",
                "provider_transaction_status",
                "paid_at",
                "updated_at",
            ]
        )
        return self

    def mark_void(self, *, notification_type=None, transaction_status=None):
        self.status = self.PaymentStatus.VOID
        self.notification_type = notification_type or self.notification_type
        self.provider_transaction_status = transaction_status or self.provider_transaction_status
        self.save(
            update_fields=[
                "status",
                "notification_type",
                "provider_transaction_status",
                "updated_at",
            ]
        )
        return self
