from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from common.models.base import DateTimeModel, SoftDeleteModel


class MenuCategory(DateTimeModel, SoftDeleteModel):
    name = models.CharField(max_length=255, verbose_name="Tên danh mục")
    description = models.TextField(blank=True, null=True, verbose_name="Mô tả")
    display_order = models.PositiveIntegerField(default=0, verbose_name="Thứ tự hiển thị")
    is_active = models.BooleanField(default=True, verbose_name="Đang bán")
    default_image_url = models.URLField(blank=True, null=True, verbose_name="Ảnh mặc định")
    default_image_alt_text = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Mô tả ảnh mặc định",
    )

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

    class SpicyLevel(models.TextChoices):
        NONE = "NONE", "Không cay"
        MILD = "MILD", "Ít cay"
        MEDIUM = "MEDIUM", "Cay vừa"
        HOT = "HOT", "Cay nhiều"

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
    is_best_seller = models.BooleanField(default=False, verbose_name="Bán chạy")
    is_kid_friendly = models.BooleanField(default=False, verbose_name="Phù hợp trẻ em")
    image_url = models.URLField(blank=True, null=True, verbose_name="Ảnh món")
    image_alt_text = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Mô tả ảnh",
    )
    is_illustration = models.BooleanField(default=False, verbose_name="Ảnh minh họa")
    spicy_level = models.CharField(
        max_length=16,
        choices=SpicyLevel.choices,
        default=SpicyLevel.NONE,
        verbose_name="Mức độ cay",
    )
    tags = models.JSONField(default=list, blank=True, verbose_name="Tag món ăn")
    dietary_labels = models.JSONField(default=list, blank=True, verbose_name="Nhãn ăn kiêng")
    preparation_time_minutes = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Thời gian chuẩn bị (phút)",
    )
    serving_start_time = models.TimeField(blank=True, null=True, verbose_name="Giờ bán từ")
    serving_end_time = models.TimeField(blank=True, null=True, verbose_name="Giờ bán đến")
    suggested_pairings = models.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        related_name="paired_from",
        verbose_name="Món gợi ý ăn kèm",
    )

    class Meta:
        db_table = "restaurant_menu_items"
        verbose_name = "Menu item"
        verbose_name_plural = "Menu items"
        ordering = ["name", "id"]

    def __str__(self):
        return self.name

    @property
    def is_currently_served(self):
        if not self.serving_start_time and not self.serving_end_time:
            return True

        now = timezone.localtime().time()
        if self.serving_start_time and now < self.serving_start_time:
            return False
        if self.serving_end_time and now > self.serving_end_time:
            return False
        return True
