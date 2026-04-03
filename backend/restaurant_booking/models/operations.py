from decimal import Decimal, ROUND_HALF_UP
import random
import string

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from common.models.base import DateTimeModel, SoftDeleteModel
from restaurant_booking.models.booking import Booking
from restaurant_booking.models.menu import MenuItem
from restaurant_booking.models.table import Table


def generate_reference_code(prefix, length=8):
    return f"{prefix}{''.join(random.choices(string.ascii_uppercase + string.digits, k=length))}"


def quantize_money(amount):
    return Decimal(amount or "0.00").quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class TableSession(DateTimeModel, SoftDeleteModel):
    class SessionStatus(models.TextChoices):
        OPEN = "OPEN", "Đang phục vụ"
        PAYMENT_PENDING = "PAYMENT_PENDING", "Chờ thanh toán"
        PAID = "PAID", "Đã thanh toán"
        CLOSED = "CLOSED", "Đã đóng"
        CANCELLED = "CANCELLED", "Đã hủy"

    booking = models.ForeignKey(
        Booking,
        on_delete=models.SET_NULL,
        related_name="table_sessions",
        blank=True,
        null=True,
        verbose_name="Booking liên quan",
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        blank=True,
        verbose_name="Mã phiên phục vụ",
    )
    guest_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Tên khách",
    )
    guest_phone = models.CharField(
        max_length=32,
        blank=True,
        null=True,
        verbose_name="Số điện thoại khách",
    )
    guest_count = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name="Số khách",
    )
    opened_at = models.DateTimeField(default=timezone.now, verbose_name="Giờ mở phiên")
    closed_at = models.DateTimeField(blank=True, null=True, verbose_name="Giờ đóng phiên")
    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="opened_table_sessions",
        blank=True,
        null=True,
        verbose_name="Nhân viên mở phiên",
    )
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="closed_table_sessions",
        blank=True,
        null=True,
        verbose_name="Nhân viên đóng phiên",
    )
    status = models.CharField(
        max_length=24,
        choices=SessionStatus.choices,
        default=SessionStatus.OPEN,
        verbose_name="Trạng thái",
    )
    notes = models.TextField(blank=True, null=True, verbose_name="Ghi chú")

    class Meta:
        db_table = "restaurant_table_sessions"
        verbose_name = "Table session"
        verbose_name_plural = "Table sessions"
        ordering = ["-opened_at", "-created_at"]

    def __str__(self):
        return self.code or f"SESSION-{self.pk}"

    def save(self, *args, **kwargs):
        if not self.code:
            while True:
                candidate = generate_reference_code("SES")
                if not TableSession.objects.filter(code=candidate).exists():
                    self.code = candidate
                    break
        super().save(*args, **kwargs)


class SessionTable(DateTimeModel, SoftDeleteModel):
    class AssignmentRole(models.TextChoices):
        PRIMARY = "PRIMARY", "Bàn chính"
        MERGED = "MERGED", "Bàn ghép"

    table_session = models.ForeignKey(
        TableSession,
        on_delete=models.CASCADE,
        related_name="session_tables",
        verbose_name="Phiên phục vụ",
    )
    table = models.ForeignKey(
        Table,
        on_delete=models.CASCADE,
        related_name="session_assignments",
        verbose_name="Bàn",
    )
    role = models.CharField(
        max_length=20,
        choices=AssignmentRole.choices,
        default=AssignmentRole.PRIMARY,
        verbose_name="Vai trò bàn",
    )
    is_active = models.BooleanField(default=True, verbose_name="Đang áp dụng")
    assigned_at = models.DateTimeField(default=timezone.now, verbose_name="Giờ gán")
    released_at = models.DateTimeField(blank=True, null=True, verbose_name="Giờ trả bàn")

    class Meta:
        db_table = "restaurant_session_tables"
        verbose_name = "Session table"
        verbose_name_plural = "Session tables"
        ordering = ["-assigned_at", "id"]

    def __str__(self):
        return f"{self.table_session} - Table {self.table_id}"


class Order(DateTimeModel, SoftDeleteModel):
    class OrderStatus(models.TextChoices):
        OPEN = "OPEN", "Đang mở"
        SENT_TO_KITCHEN = "SENT_TO_KITCHEN", "Đã gửi bếp"
        PARTIALLY_SERVED = "PARTIALLY_SERVED", "Đang phục vụ"
        COMPLETED = "COMPLETED", "Hoàn thành"
        CANCELLED = "CANCELLED", "Đã hủy"

    table_session = models.ForeignKey(
        TableSession,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="Phiên phục vụ",
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        blank=True,
        verbose_name="Mã order",
    )
    status = models.CharField(
        max_length=24,
        choices=OrderStatus.choices,
        default=OrderStatus.OPEN,
        verbose_name="Trạng thái",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_orders",
        blank=True,
        null=True,
        verbose_name="Người tạo",
    )
    notes = models.TextField(blank=True, null=True, verbose_name="Ghi chú")
    sent_to_kitchen_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Giờ gửi bếp",
    )
    closed_at = models.DateTimeField(blank=True, null=True, verbose_name="Giờ đóng order")

    class Meta:
        db_table = "restaurant_orders"
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.code or f"ORDER-{self.pk}"

    def save(self, *args, **kwargs):
        if not self.code:
            while True:
                candidate = generate_reference_code("ORD")
                if not Order.objects.filter(code=candidate).exists():
                    self.code = candidate
                    break
        super().save(*args, **kwargs)

    @property
    def subtotal_amount(self):
        return sum((item.line_total for item in self.items.all()), Decimal("0.00"))


class OrderItem(DateTimeModel, SoftDeleteModel):
    class KitchenStatus(models.TextChoices):
        PENDING = "PENDING", "Chờ xử lý"
        SENT_TO_KITCHEN = "SENT_TO_KITCHEN", "Đã gửi bếp"
        PREPARING = "PREPARING", "Đang chuẩn bị"
        READY = "READY", "Sẵn sàng"
        SERVED = "SERVED", "Đã phục vụ"
        CANCELLED = "CANCELLED", "Đã hủy"

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Order",
    )
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.SET_NULL,
        related_name="order_items",
        blank=True,
        null=True,
        verbose_name="Món ăn",
    )
    item_name = models.CharField(max_length=255, verbose_name="Tên món")
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Số lượng",
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Đơn giá",
    )
    kitchen_status = models.CharField(
        max_length=24,
        choices=KitchenStatus.choices,
        default=KitchenStatus.PENDING,
        verbose_name="Trạng thái bếp",
    )
    note = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Ghi chú món",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_order_items",
        blank=True,
        null=True,
        verbose_name="Người thêm món",
    )

    class Meta:
        db_table = "restaurant_order_items"
        verbose_name = "Order item"
        verbose_name_plural = "Order items"
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"{self.item_name} x{self.quantity}"

    def save(self, *args, **kwargs):
        if self.menu_item and not self.item_name:
            self.item_name = self.menu_item.name
        if self.menu_item and quantize_money(self.unit_price) == Decimal("0.00"):
            self.unit_price = self.menu_item.price
        super().save(*args, **kwargs)

    @property
    def line_total(self):
        return quantize_money(self.quantity * self.unit_price)


class Payment(DateTimeModel, SoftDeleteModel):
    class PaymentStatus(models.TextChoices):
        PENDING = "PENDING", "Chờ thanh toán"
        PAID = "PAID", "Đã thanh toán"
        REFUNDED = "REFUNDED", "Hoàn tiền"
        VOIDED = "VOIDED", "Đã hủy"

    class PaymentMethod(models.TextChoices):
        CASH = "CASH", "Tiền mặt"
        BANK_TRANSFER = "BANK_TRANSFER", "Chuyển khoản"
        CARD = "CARD", "Thẻ"

    table_session = models.ForeignKey(
        TableSession,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="Phiên phục vụ",
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        blank=True,
        verbose_name="Mã thanh toán",
    )
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        verbose_name="Trạng thái",
    )
    method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
        verbose_name="Phương thức",
    )
    subtotal_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Tiền món",
    )
    surcharge_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Phụ phí",
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Tổng thanh toán",
    )
    card_surcharge_rate = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        default=Decimal("0.0350"),
        validators=[MinValueValidator(Decimal("0.0000"))],
        verbose_name="Tỷ lệ phụ phí thẻ",
    )
    note = models.TextField(blank=True, null=True, verbose_name="Ghi chú")
    paid_at = models.DateTimeField(blank=True, null=True, verbose_name="Giờ thanh toán")
    paid_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="processed_payments",
        blank=True,
        null=True,
        verbose_name="Thu ngân xử lý",
    )

    class Meta:
        db_table = "restaurant_payments"
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.code or f"PAY-{self.pk}"

    def recalculate_totals(self):
        subtotal = quantize_money(self.subtotal_amount)
        surcharge = quantize_money(self.surcharge_amount)

        if self.method == self.PaymentMethod.CARD:
            surcharge = quantize_money(subtotal * self.card_surcharge_rate)

        self.subtotal_amount = subtotal
        self.surcharge_amount = surcharge
        self.total_amount = quantize_money(subtotal + surcharge)

    def save(self, *args, **kwargs):
        if not self.code:
            while True:
                candidate = generate_reference_code("PAY")
                if not Payment.objects.filter(code=candidate).exists():
                    self.code = candidate
                    break
        self.recalculate_totals()
        super().save(*args, **kwargs)


class Invoice(DateTimeModel, SoftDeleteModel):
    invoice_number = models.CharField(
        max_length=24,
        unique=True,
        editable=False,
        blank=True,
        verbose_name="Số hóa đơn",
    )
    table_session = models.OneToOneField(
        TableSession,
        on_delete=models.CASCADE,
        related_name="invoice",
        verbose_name="Phiên phục vụ",
    )
    payment = models.OneToOneField(
        Payment,
        on_delete=models.SET_NULL,
        related_name="invoice",
        blank=True,
        null=True,
        verbose_name="Thanh toán",
    )
    issued_at = models.DateTimeField(default=timezone.now, verbose_name="Giờ xuất bill")
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="issued_invoices",
        blank=True,
        null=True,
        verbose_name="Người xuất bill",
    )
    customer_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Tên khách",
    )
    subtotal_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Tiền món",
    )
    surcharge_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Phụ phí",
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Tổng cộng",
    )
    note = models.TextField(blank=True, null=True, verbose_name="Ghi chú")

    class Meta:
        db_table = "restaurant_invoices"
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"
        ordering = ["-issued_at", "-id"]

    def __str__(self):
        return self.invoice_number or f"INV-{self.pk}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            while True:
                candidate = generate_reference_code("INV")
                if not Invoice.objects.filter(invoice_number=candidate).exists():
                    self.invoice_number = candidate
                    break

        if self.payment_id:
            self.subtotal_amount = self.payment.subtotal_amount
            self.surcharge_amount = self.payment.surcharge_amount
            self.total_amount = self.payment.total_amount

        super().save(*args, **kwargs)
