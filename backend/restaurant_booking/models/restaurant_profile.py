from datetime import time

from django.db import models
from django.core.validators import MinValueValidator

from common.models.base import DateTimeModel, SoftDeleteModel


class RestaurantProfile(DateTimeModel, SoftDeleteModel):
    name = models.CharField(max_length=255, verbose_name="Tên nhà hàng")
    description = models.TextField(blank=True, null=True, verbose_name="Mô tả")
    phone_number = models.CharField(
        max_length=32,
        blank=True,
        null=True,
        verbose_name="Số điện thoại",
    )
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    address = models.CharField(
        max_length=512,
        blank=True,
        null=True,
        verbose_name="Địa chỉ",
    )
    opening_time = models.TimeField(default=time(9, 0), verbose_name="Giờ mở cửa")
    closing_time = models.TimeField(default=time(22, 0), verbose_name="Giờ đóng cửa")
    website = models.URLField(blank=True, null=True, verbose_name="Website")
    ai_greeting = models.TextField(
        blank=True,
        null=True,
        verbose_name="Thông điệp AI mặc định",
    )
    price_range_min = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Giá thấp nhất",
    )
    price_range_max = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Giá cao nhất",
    )
    public_booking_fee_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=100000,
        validators=[MinValueValidator(0)],
        verbose_name="Phí giữ chỗ đặt bàn trực tiếp",
    )
    chatbot_booking_fee_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=100000,
        validators=[MinValueValidator(0)],
        verbose_name="Phí giữ chỗ đặt bàn qua chatbot",
    )
    is_active = models.BooleanField(default=True, verbose_name="Đang áp dụng")

    class Meta:
        db_table = "restaurant_profiles"
        verbose_name = "Restaurant profile"
        verbose_name_plural = "Restaurant profiles"
        ordering = ["-is_active", "-updated_at", "id"]

    def __str__(self):
        return self.name

    @classmethod
    def get_active_profile(cls):
        return cls.objects.filter(is_active=True).order_by("-updated_at", "id").first()
