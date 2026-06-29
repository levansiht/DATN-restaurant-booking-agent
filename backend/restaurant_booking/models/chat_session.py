import uuid

from django.db import models

from common.models.base import DateTimeModel


class ChatSession(DateTimeModel):
    """Server-side state for a single chatbot conversation.

    The chatbot is otherwise stateless (the frontend replays ``chat_history``
    each turn). This model persists the few things that cannot be reliably
    re-derived from the transcript: the *sticky* conversation mode, the booking
    slots collected so far, the booking finite-state-machine stage, the last
    table options shown to the guest, and the resulting booking code.
    """

    class Mode(models.TextChoices):
        SALES = "SALES", "Tư vấn / menu"
        BOOKING = "BOOKING", "Đặt bàn"

    class Stage(models.TextChoices):
        NONE = "NONE", "Chưa vào booking"
        COLLECT_NAME = "COLLECT_NAME", "Hỏi tên"
        COLLECT_DATETIME = "COLLECT_DATETIME", "Hỏi ngày giờ"
        COLLECT_PARTY_SIZE = "COLLECT_PARTY_SIZE", "Hỏi số người"
        COLLECT_SEATING = "COLLECT_SEATING", "Hỏi khu vực / tầng"
        SELECT_TABLE = "SELECT_TABLE", "Chọn bàn"
        DEPOSIT_NOTICE = "DEPOSIT_NOTICE", "Thông báo đặt cọc"
        COLLECT_CONTACT = "COLLECT_CONTACT", "Hỏi thông tin liên hệ"
        CONFIRM = "CONFIRM", "Chờ xác nhận"
        DONE = "DONE", "Đã hoàn tất"

    session_id = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        default=uuid.uuid4,
        verbose_name="Mã phiên chat",
    )
    mode = models.CharField(
        max_length=16,
        choices=Mode.choices,
        default=Mode.SALES,
        verbose_name="Chế độ hội thoại",
    )
    stage = models.CharField(
        max_length=32,
        choices=Stage.choices,
        default=Stage.NONE,
        verbose_name="Bước trong luồng đặt bàn",
    )
    slots = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Thông tin đặt bàn đã thu thập",
    )
    customer_name = models.CharField(
        max_length=120,
        blank=True,
        null=True,
        verbose_name="Tên khách",
    )
    selected_item_ids = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Món khách đã chọn trước",
    )
    last_table_options = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Danh sách bàn trống đã gợi ý gần nhất",
    )
    booking_code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Mã đặt bàn đã tạo",
    )

    class Meta:
        db_table = "restaurant_chat_sessions"
        verbose_name = "Chat session"
        verbose_name_plural = "Chat sessions"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.session_id} ({self.mode}/{self.stage})"

    @property
    def has_preordered_items(self) -> bool:
        return bool(self.selected_item_ids)

    def reset_booking_state(self):
        """Clear booking progress so a fresh reservation can start cleanly."""
        self.mode = self.Mode.BOOKING
        # NONE on purpose: the resolver will move to COLLECT_NAME, but the
        # triggering message must not be parsed as the name.
        self.stage = self.Stage.NONE
        # Keep guest contact info (name/phone/email) so we don't re-ask a
        # returning guest, but drop reservation-specific choices.
        preserved_keys = {"guest_name", "guest_phone", "guest_email"}
        self.slots = {
            key: value for key, value in (self.slots or {}).items() if key in preserved_keys
        }
        self.last_table_options = []
        self.booking_code = None
