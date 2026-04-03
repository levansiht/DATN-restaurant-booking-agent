from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from common.models.base import DateTimeModel, SoftDeleteModel


class MenuCategory(DateTimeModel, SoftDeleteModel):
    name = models.CharField(max_length=255, verbose_name="Tên danh mục")
    description = models.TextField(blank=True, null=True, verbose_name="Mô tả")
    display_order = models.PositiveIntegerField(default=0, verbose_name="Thứ tự hiển thị")
    is_active = models.BooleanField(default=True, verbose_name="Đang bán")

    class Meta:
        db_table = "restaurant_menu_categories"
        verbose_name = "Menu category"
        verbose_name_plural = "Menu categories"
        ordering = ["display_order", "name", "id"]

    def __str__(self):
        return self.name


class MenuItem(DateTimeModel, SoftDeleteModel):
    class AvailabilityStatus(models.TextChoices):
        ACTIVE = "ACTIVE", "Đang bán"
        INACTIVE = "INACTIVE", "Tạm ẩn"
        OUT_OF_STOCK = "OUT_OF_STOCK", "Hết món"

    category = models.ForeignKey(
        MenuCategory,
        on_delete=models.SET_NULL,
        related_name="items",
        blank=True,
        null=True,
        verbose_name="Danh mục",
    )
    name = models.CharField(max_length=255, verbose_name="Tên món")
    description = models.TextField(blank=True, null=True, verbose_name="Mô tả")
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Giá bán",
    )
    status = models.CharField(
        max_length=20,
        choices=AvailabilityStatus.choices,
        default=AvailabilityStatus.ACTIVE,
        verbose_name="Trạng thái",
    )
    is_recommended = models.BooleanField(default=False, verbose_name="Món gợi ý")
    is_vegetarian = models.BooleanField(default=False, verbose_name="Món chay")
    preparation_time_minutes = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Thời gian chuẩn bị (phút)",
    )

    class Meta:
        db_table = "restaurant_menu_items"
        verbose_name = "Menu item"
        verbose_name_plural = "Menu items"
        ordering = ["name", "id"]

    def __str__(self):
        return self.name
