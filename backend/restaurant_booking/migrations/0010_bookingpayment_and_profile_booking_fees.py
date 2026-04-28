from decimal import Decimal

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("restaurant_booking", "0009_seed_demo_restaurant_menu"),
    ]

    operations = [
        migrations.AddField(
            model_name="restaurantprofile",
            name="chatbot_booking_fee_amount",
            field=models.DecimalField(
                decimal_places=2,
                default=100000,
                max_digits=12,
                validators=[django.core.validators.MinValueValidator(0)],
                verbose_name="Phí giữ chỗ đặt bàn qua chatbot",
            ),
        ),
        migrations.AddField(
            model_name="restaurantprofile",
            name="public_booking_fee_amount",
            field=models.DecimalField(
                decimal_places=2,
                default=100000,
                max_digits=12,
                validators=[django.core.validators.MinValueValidator(0)],
                verbose_name="Phí giữ chỗ đặt bàn trực tiếp",
            ),
        ),
        migrations.CreateModel(
            name="BookingPayment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        editable=False,
                        verbose_name="Ngày tạo",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        editable=False,
                        verbose_name="Ngày cập nhật",
                    ),
                ),
                (
                    "is_deleted",
                    models.BooleanField(
                        default=False,
                        help_text="Đã xóa",
                        verbose_name="Đã xóa",
                    ),
                ),
                (
                    "provider",
                    models.CharField(
                        choices=[("SEPAY", "SePay")],
                        default="SEPAY",
                        max_length=20,
                        verbose_name="Cổng thanh toán",
                    ),
                ),
                (
                    "flow",
                    models.CharField(
                        choices=[
                            ("WEBSITE", "Đặt bàn trực tiếp"),
                            ("CHATBOT", "Đặt bàn qua chatbot"),
                        ],
                        default="WEBSITE",
                        max_length=20,
                        verbose_name="Luồng đặt bàn",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Chờ thanh toán"),
                            ("PAID", "Đã thanh toán"),
                            ("VOID", "Đã hủy giao dịch"),
                            ("FAILED", "Thanh toán thất bại"),
                        ],
                        default="PENDING",
                        max_length=20,
                        verbose_name="Trạng thái thanh toán",
                    ),
                ),
                (
                    "amount",
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal("0"),
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(0)],
                        verbose_name="Số tiền",
                    ),
                ),
                (
                    "currency",
                    models.CharField(
                        default="VND",
                        max_length=10,
                        verbose_name="Tiền tệ",
                    ),
                ),
                (
                    "order_invoice_number",
                    models.CharField(
                        max_length=64,
                        unique=True,
                        verbose_name="Mã hóa đơn SePay",
                    ),
                ),
                (
                    "order_description",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        null=True,
                        verbose_name="Mô tả thanh toán",
                    ),
                ),
                (
                    "payment_method",
                    models.CharField(
                        blank=True,
                        max_length=32,
                        null=True,
                        verbose_name="Phương thức thanh toán",
                    ),
                ),
                (
                    "sepay_order_id",
                    models.CharField(
                        blank=True,
                        max_length=64,
                        null=True,
                        verbose_name="Order ID từ SePay",
                    ),
                ),
                (
                    "sepay_transaction_id",
                    models.CharField(
                        blank=True,
                        max_length=128,
                        null=True,
                        verbose_name="Transaction ID từ SePay",
                    ),
                ),
                (
                    "provider_transaction_status",
                    models.CharField(
                        blank=True,
                        max_length=64,
                        null=True,
                        verbose_name="Trạng thái giao dịch từ cổng thanh toán",
                    ),
                ),
                (
                    "notification_type",
                    models.CharField(
                        blank=True,
                        max_length=64,
                        null=True,
                        verbose_name="Loại IPN gần nhất",
                    ),
                ),
                (
                    "paid_at",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        verbose_name="Thời điểm thanh toán",
                    ),
                ),
                (
                    "raw_ipn_payload",
                    models.JSONField(
                        blank=True,
                        null=True,
                        verbose_name="Payload IPN thô",
                    ),
                ),
                (
                    "booking",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="payment",
                        to="restaurant_booking.booking",
                        verbose_name="Booking",
                    ),
                ),
            ],
            options={
                "verbose_name": "Booking payment",
                "verbose_name_plural": "Booking payments",
                "db_table": "restaurant_booking_payments",
                "ordering": ["-created_at"],
            },
        ),
    ]
