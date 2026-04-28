from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from common.models.base import DateTimeModel, SoftDeleteModel
import random
import string


def generate_booking_code(length=8):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


class Booking(DateTimeModel, SoftDeleteModel):
    """
    Booking model to store restaurant booking information
    """

    class BookingStatus(models.TextChoices):
        PENDING = "PENDING", "Chờ thanh toán"
        CONFIRMED = "CONFIRMED", "Đã xác nhận"
        CANCELLED = "CANCELLED", "Đã hủy"
        COMPLETED = "COMPLETED", "Hoàn thành"
        NO_SHOW = "NO_SHOW", "Không đến"

    class BookingSource(models.TextChoices):
        WEBSITE = "WEBSITE", "Website"
        PHONE = "PHONE", "Điện thoại"
        WALK_IN = "WALK_IN", "Đến trực tiếp"
        MOBILE_APP = "MOBILE_APP", "Ứng dụng di động"
        THIRD_PARTY = "THIRD_PARTY", "Bên thứ ba"

    # Basic booking information
    table = models.ForeignKey(
        'restaurant_booking.Table',
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name="Bàn"
    )

    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Mã đặt bàn",
        editable=False,
        default=generate_booking_code,
    )

    # Guest information (for non-registered users)
    guest_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Tên khách"
    )
    guest_email = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Email khách"
    )
    guest_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Số điện thoại khách"
    )

    # Booking details
    booking_date = models.DateField(verbose_name="Ngày đặt bàn")
    booking_time = models.TimeField(verbose_name="Giờ đặt bàn")
    duration_hours = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=Decimal("2.0"),
        validators=[
            MinValueValidator(Decimal("0.5")),
            MaxValueValidator(Decimal("8.0")),
        ],
        verbose_name="Thời gian (giờ)"
    )

    # Party information
    party_size = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        verbose_name="Số người"
    )

    # Booking status and source
    status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING,
        verbose_name="Trạng thái"
    )
    source = models.CharField(
        max_length=20,
        choices=BookingSource.choices,
        default=BookingSource.WEBSITE,
        verbose_name="Nguồn đặt bàn"
    )

    # Confirmation and notes
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Ghi chú nội bộ"
    )
    
    # Cancellation information
    cancellation_reason = models.TextField(
        blank=True,
        null=True,
        verbose_name="Lý do hủy"
    )
    confirmed_at = models.DateTimeField(blank=True, null=True, verbose_name="Thời gian xác nhận")
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="confirmed_bookings",
        blank=True,
        null=True,
        verbose_name="Người xác nhận",
    )
    cancelled_at = models.DateTimeField(blank=True, null=True, verbose_name="Thời gian hủy")
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="cancelled_bookings",
        blank=True,
        null=True,
        verbose_name="Người hủy",
    )

    class Meta:
        db_table = 'restaurant_bookings'
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"
        ordering = ['-created_at']

    def __str__(self):
        guest_name = self.guest_name or "Guest"
        return f"Table {self.table.id} - {guest_name} - {self.booking_date} {self.booking_time}"

    def save(self, *args, **kwargs):
        # Generate unique booking code if not exists
        if not self.code:
            self.code = self._generate_unique_code('code')

        self._validate_confirmation_requires_payment()
        super().save(*args, **kwargs)

    def _generate_unique_code(self, field, length=8):
        """
        Generate a unique code for the specified field.
        """
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
            if not Booking.objects.filter(**{field: code}).exists():
                return code

    def _get_active_payment(self):
        from .booking_payment import BookingPayment

        if not self.pk:
            return None

        return (
            BookingPayment.objects.filter(booking_id=self.pk, is_deleted=False)
            .order_by("-created_at")
            .first()
        )

    def _validate_confirmation_requires_payment(self):
        if self.status != self.BookingStatus.CONFIRMED:
            return

        from .booking_payment import BookingPayment

        payment = self._get_active_payment()
        if (
            payment
            and payment.requires_payment
            and payment.status != BookingPayment.PaymentStatus.PAID
        ):
            raise ValidationError(
                {"status": "Booking chỉ được xác nhận sau khi khách đã thanh toán cọc."}
            )

    def mark_confirmed(self, actor=None):
        self.status = self.BookingStatus.CONFIRMED
        self.confirmed_at = timezone.now()
        self.confirmed_by = actor
        self.save(update_fields=["status", "confirmed_at", "confirmed_by", "updated_at"])
        return self

    def mark_cancelled(self, actor=None, reason=""):
        self.status = self.BookingStatus.CANCELLED
        self.cancellation_reason = reason
        self.cancelled_at = timezone.now()
        self.cancelled_by = actor
        self.save(
            update_fields=[
                "status",
                "cancellation_reason",
                "cancelled_at",
                "cancelled_by",
                "updated_at",
            ]
        )
        return self
