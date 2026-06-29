"""Deterministic booking finite-state-machine.

Code (not the LLM) decides which question to ask next and when to search /
confirm / book. The LLM is only used indirectly, for slot extraction. This is
what keeps the conversation from looping: the stage is derived from the slots
already stored in the session, so the bot always advances and never re-asks.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from restaurant_booking.models import ChatSession, MenuItem, Table
from restaurant_booking.services.availability import (
    BookingValidationError,
    TABLE_CONFLICT_MESSAGE,
    get_available_tables,
)
from restaurant_booking.services.booking_payments import (
    BookingPaymentConfigurationError,
    create_booking_with_payment,
    get_booking_fee_amount,
)
from restaurant_booking.services.booking_notes import build_preorder_note, merge_notes
from restaurant_booking.models import Booking, BookingPayment
from restaurant_booking.services.public_links import build_booking_search_url
from restaurant_booking.services.slot_extractor import (
    BookingSlotExtractor,
    is_placeholder,
    normalize_text,
)


Stage = ChatSession.Stage

DURATION_HOURS = Decimal("2.0")


class BookingStateMachine:
    def __init__(self, extractor: Optional[BookingSlotExtractor] = None):
        self.extractor = extractor or BookingSlotExtractor()

    # ------------------------------------------------------------------ #
    # Entry point
    # ------------------------------------------------------------------ #
    def process(self, *, session: ChatSession, user_input: str, chat_history: list[dict]) -> dict:
        slots = self.extractor.merge(
            existing_slots=session.slots or {},
            user_input=user_input,
            chat_history=chat_history,
        )

        current_stage = session.stage or Stage.COLLECT_NAME

        # When we've explicitly asked for the name (start of booking or contact
        # step), accept a bare name reply ("Sỷ", "Sỷ, 0334407762") without a
        # "tên là" prefix.
        if (
            current_stage in (Stage.COLLECT_NAME, Stage.COLLECT_CONTACT, Stage.DEPOSIT_NOTICE)
            and not slots.get("guest_name")
        ):
            bare_name = self.extractor.extract_contact_name(user_input)
            if bare_name:
                slots["guest_name"] = bare_name

        if slots.get("guest_name"):
            session.customer_name = slots["guest_name"]

        # Guest defers the seating choice ("để em chọn giúp", "sao cũng được").
        if (
            current_stage == Stage.COLLECT_SEATING
            and self.extractor.is_defer_choice(user_input)
            and not slots.get("table_type")
            and not slots.get("floor")
        ):
            slots["seating_any"] = True

        # When stuck at table selection (often because no table fits), let the
        # guest reset a single criterion and re-ask instead of looping.
        if current_stage == Stage.SELECT_TABLE:
            if self.extractor.wants_change_area(user_input):
                for key in ("table_type", "floor", "seating_any", "table_id"):
                    slots.pop(key, None)
                session.last_table_options = []
            elif self.extractor.wants_change_time(user_input):
                slots.pop("booking_time", None)
                slots.pop("table_id", None)
                session.last_table_options = []
            elif self.extractor.wants_change_date(user_input):
                slots.pop("booking_date", None)
                slots.pop("table_id", None)
                session.last_table_options = []

        # Guest picks a table from the list we last showed.
        if current_stage == Stage.SELECT_TABLE and session.last_table_options and not slots.get("table_id"):
            chosen_id = self.extractor.parse_table_choice(user_input, session.last_table_options)
            if chosen_id:
                slots["table_id"] = chosen_id
                for option in session.last_table_options:
                    if int(option["table_id"]) == chosen_id:
                        if option.get("table_type_code"):
                            slots["table_type"] = option["table_type_code"]
                        if option.get("floor"):
                            slots["floor"] = option["floor"]
                        break

        # Guest confirms the summary -> create the booking.
        if current_stage == Stage.CONFIRM and self._has_all_for_booking(slots):
            if self.extractor.is_affirmative(user_input):
                session.slots = slots
                return self._create_booking(session)
            # If they explicitly object, fall through to recompute and re-ask.

        session.slots = slots
        stage = self._resolve_stage(session, slots)
        session.stage = stage
        return self._respond(session, stage)

    # ------------------------------------------------------------------ #
    # Stage resolution
    # ------------------------------------------------------------------ #
    def _resolve_stage(self, session: ChatSession, slots: dict) -> str:
        if session.booking_code:
            return Stage.DONE
        # Greet by name first: collect the guest's name up-front so the rest of
        # the conversation can address them properly.
        if not slots.get("guest_name"):
            return Stage.COLLECT_NAME
        if not slots.get("booking_date") or not slots.get("booking_time"):
            return Stage.COLLECT_DATETIME
        if not slots.get("party_size"):
            return Stage.COLLECT_PARTY_SIZE
        if not self._seating_resolved(slots):
            return Stage.COLLECT_SEATING
        if not slots.get("table_id"):
            return Stage.SELECT_TABLE
        # Every chatbot booking requires a hold deposit, so always inform the
        # guest once before collecting contact details.
        if not slots.get("deposit_notified"):
            return Stage.DEPOSIT_NOTICE
        if not self._contact_complete(slots):
            return Stage.COLLECT_CONTACT
        return Stage.CONFIRM

    @staticmethod
    def _seating_resolved(slots: dict) -> bool:
        return bool(slots.get("table_type") or slots.get("floor") or slots.get("seating_any"))

    @staticmethod
    def _contact_complete(slots: dict) -> bool:
        return bool(slots.get("guest_name") and slots.get("guest_phone") and slots.get("guest_email"))

    @staticmethod
    def _has_all_for_booking(slots: dict) -> bool:
        return all(
            slots.get(key)
            for key in ("booking_date", "booking_time", "party_size", "table_id", "guest_name", "guest_phone", "guest_email")
        )

    # ------------------------------------------------------------------ #
    # Stage responders
    # ------------------------------------------------------------------ #
    def _respond(self, session: ChatSession, stage: str) -> dict:
        slots = session.slots or {}
        handlers = {
            Stage.COLLECT_NAME: self._respond_name,
            Stage.COLLECT_DATETIME: self._respond_datetime,
            Stage.COLLECT_PARTY_SIZE: self._respond_party_size,
            Stage.COLLECT_SEATING: self._respond_seating,
            Stage.SELECT_TABLE: self._respond_select_table,
            Stage.DEPOSIT_NOTICE: self._respond_contact,  # deposit text prepended inside
            Stage.COLLECT_CONTACT: self._respond_contact,
            Stage.CONFIRM: self._respond_confirm,
            Stage.DONE: self._respond_done,
        }
        handler = handlers.get(stage, self._respond_datetime)
        return handler(session, slots)

    def _respond_name(self, session: ChatSession, slots: dict) -> dict:
        return self._payload(
            session=session,
            message="Dạ em hỗ trợ đặt bàn cho mình ngay ạ. Mình cho em xin tên để tiện xưng hô nhé?",
            quick_replies=[],
        )

    def _respond_datetime(self, session: ChatSession, slots: dict) -> dict:
        name = self._address(session)
        has_date = bool(slots.get("booking_date"))
        has_time = bool(slots.get("booking_time"))
        if not has_date and not has_time:
            message = f"Dạ {name} muốn đặt vào ngày nào và khoảng mấy giờ ạ?"
        elif has_date and not has_time:
            message = f"Dạ {name} muốn đặt khoảng mấy giờ ạ?"
        else:
            message = f"Dạ {name} muốn đặt vào ngày nào ạ?"
        return self._payload(
            session=session,
            message=message,
            quick_replies=["Tối nay 19:00", "Ngày mai 19:00", "Cuối tuần"],
        )

    def _respond_party_size(self, session: ChatSession, slots: dict) -> dict:
        name = self._address(session)
        return self._payload(
            session=session,
            message=f"Dạ {name} đi mấy người để em kiểm tra bàn phù hợp ạ?",
            quick_replies=["2 người", "4 người", "6 người"],
        )

    def _respond_seating(self, session: ChatSession, slots: dict) -> dict:
        name = self._address(session)
        message = (
            f"Dạ {name} muốn ngồi khu vực nào ạ: trong nhà, ngoài trời, phòng riêng, "
            "quầy bar, ghế booth hay cạnh cửa sổ? Nếu được, em chọn chỗ hợp lý giúp cũng được ạ."
        )
        return self._payload(
            session=session,
            message=message,
            quick_replies=["Trong nhà", "Cạnh cửa sổ", "Để em chọn giúp"],
        )

    def _respond_select_table(self, session: ChatSession, slots: dict) -> dict:
        name = self._address(session)
        options = self._search_tables(slots)
        session.last_table_options = options

        if not options:
            return self._payload(
                session=session,
                message=(
                    f"Dạ rất tiếc {name}, khung giờ {slots.get('booking_time')} ngày {slots.get('booking_date')} "
                    "hiện chưa còn bàn phù hợp. Mình muốn đổi giờ khác, đổi khu vực hay để em kiểm tra ngày khác ạ?"
                ),
                quick_replies=["Đổi giờ", "Đổi khu vực", "Đổi ngày"],
            )

        lines = [
            f"- Bàn {option['table_id']} · {option['table_type']} · tầng {option['floor']} · {option['capacity']} chỗ"
            for option in options
        ]
        first_id = options[0]["table_id"]
        message = (
            f"Dạ hiện còn các bàn phù hợp cho {slots.get('party_size')} người vào "
            f"{slots.get('booking_date')} lúc {slots.get('booking_time')}:\n"
            + "\n".join(lines)
            + f"\n{name} chọn bàn nào giúp em nhé (ví dụ: bàn {first_id})."
        )
        return self._payload(
            session=session,
            message=message,
            available_tables=options,
            quick_replies=[f"Bàn {option['table_id']}" for option in options[:3]],
        )

    def _respond_contact(self, session: ChatSession, slots: dict) -> dict:
        name = self._address(session)
        prefix = ""
        if session.stage == Stage.DEPOSIT_NOTICE or not slots.get("deposit_notified"):
            slots["deposit_notified"] = True
            session.slots = slots
            session.stage = Stage.COLLECT_CONTACT
            prefix = (
                f"Đơn đặt bàn qua trợ lý cần đặt cọc giữ chỗ {self._deposit_amount_text()}đ "
                "để xác nhận ạ. "
            )

        has_name = bool(slots.get("guest_name"))
        has_phone = bool(slots.get("guest_phone"))

        if not has_name and not has_phone:
            question = "Mình cho em xin tên và số điện thoại để em hoàn tất đặt bàn ạ?"
        elif not has_phone:
            question = "Mình cho em xin số điện thoại để em hoàn tất đặt bàn ạ?"
        elif not has_name:
            question = "Mình cho em xin tên để em ghi vào đơn đặt bàn ạ?"
        else:
            question = "Mình cho em xin email để em gửi xác nhận đặt bàn ạ?"

        return self._payload(
            session=session,
            message=f"{prefix}Dạ {question}" if prefix else f"Dạ {question}",
            quick_replies=[],
        )

    def _respond_confirm(self, session: ChatSession, slots: dict) -> dict:
        name = self._address(session)
        summary = self._build_summary(slots)
        preordered_names = self._preordered_item_names(session)
        summary["preordered_items"] = preordered_names
        summary_lines = [
            f"- Bàn: {summary['table_id']} ({summary['table_type']}, tầng {summary['floor']})",
            f"- Ngày giờ: {summary['booking_date']} lúc {summary['booking_time']}",
            f"- Số khách: {summary['party_size']}",
            f"- Tên: {summary['guest_name']}",
            f"- Điện thoại: {summary['guest_phone']}",
            f"- Email: {summary['guest_email']}",
        ]
        if preordered_names:
            summary_lines.append(f"- Món đặt trước: {', '.join(preordered_names)}")
        deposit_note = (
            f" Sau khi mình xác nhận, em sẽ tạo phiếu cọc giữ chỗ {self._deposit_amount_text()}đ qua SePay ạ."
        )
        message = (
            f"Dạ em xác nhận lại thông tin đặt bàn của {name}:\n"
            + "\n".join(summary_lines)
            + f"\nThông tin trên đã đúng chưa ạ? Mình nhắn \"xác nhận\" để em chốt nhé.{deposit_note}"
        )
        return self._payload(
            session=session,
            message=message,
            booking_summary=summary,
            quick_replies=["Xác nhận", "Sửa thông tin"],
            next_action="confirm_booking",
            conversation_goal="confirm_booking",
        )

    def _respond_done(self, session: ChatSession, slots: dict) -> dict:
        name = self._address(session)
        return self._payload(
            session=session,
            message=(
                f"Dạ đơn đặt bàn của {name} đã hoàn tất với mã {session.booking_code} ạ. "
                "Em có thể hỗ trợ thêm gì cho mình không ạ?"
            ),
            next_action="none",
            conversation_goal="confirm_booking",
        )

    # ------------------------------------------------------------------ #
    # Booking creation
    # ------------------------------------------------------------------ #
    def _create_booking(self, session: ChatSession) -> dict:
        slots = session.slots or {}
        name = self._address(session)
        try:
            booking, payment = create_booking_with_payment(
                flow=BookingPayment.BookingFlow.CHATBOT,
                table_id=int(slots["table_id"]),
                guest_name=slots["guest_name"],
                guest_phone=slots["guest_phone"],
                guest_email=slots["guest_email"],
                booking_date=slots["booking_date"],
                booking_time=slots["booking_time"],
                party_size=int(slots["party_size"]),
                duration_hours=DURATION_HOURS,
                notes=self._build_booking_notes(session, slots),
                source=Booking.BookingSource.WEBSITE,
                with_deposit=True,
            )
        except BookingValidationError as exc:
            detail = exc.detail if isinstance(exc.detail, dict) else {}
            error_message = (
                detail.get("table_id")
                or detail.get("booking_time")
                or detail.get("booking_date")
                or detail.get("party_size")
                or str(exc.detail)
            )
            # Table got taken in the meantime: let the guest re-pick.
            slots.pop("table_id", None)
            session.slots = slots
            session.last_table_options = []
            session.stage = Stage.SELECT_TABLE
            if error_message == TABLE_CONFLICT_MESSAGE:
                error_message = (
                    f"Bàn {slots.get('table_id', '')} vừa có khách khác giữ ở khung giờ này. "
                    "Mình chọn giúp em bàn khác nhé."
                )
            return self._payload(
                session=session,
                message=f"Dạ {error_message}",
                quick_replies=["Xem bàn khác"],
            )
        except BookingPaymentConfigurationError as exc:
            return self._payload(
                session=session,
                message=f"Dạ hệ thống thanh toán đang tạm gián đoạn ({exc}). Mình thử lại giúp em sau ít phút nhé.",
                next_action="none",
            )

        session.booking_code = booking.code
        session.stage = Stage.DONE
        lookup_url = build_booking_search_url(booking.code)

        if payment:
            amount = self._format_vnd(payment.amount)
            message = (
                f"Dạ {name}, em đã tạo phiếu giữ chỗ kèm đặt cọc. Mã đặt bàn: {booking.code}. "
                f"Phí giữ chỗ qua SePay là {amount} VND. "
                f"Mình mở trang này để thanh toán giúp em nhé: {lookup_url}. "
                "Sau khi SePay báo thanh toán thành công, đơn đặt bàn sẽ được xác nhận ngay ạ."
            )
        else:
            message = (
                f"Dạ {name}, em đã xác nhận đặt bàn thành công (không cần đặt cọc). "
                f"Mã đặt bàn: {booking.code}. Thông tin xác nhận đã được gửi tới email của mình. "
                f"Mình có thể tra cứu đơn tại đây: {lookup_url}"
            )

        return self._payload(
            session=session,
            message=message,
            booking_summary=self._build_summary(slots),
            next_action="none",
            conversation_goal="confirm_booking",
        )

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _search_tables(self, slots: dict) -> list[dict]:
        try:
            tables = get_available_tables(
                booking_date=slots["booking_date"],
                booking_time=slots["booking_time"],
                party_size=int(slots["party_size"]),
                table_type=slots.get("table_type"),
                floor=slots.get("floor"),
                duration_hours=DURATION_HOURS,
            )
        except Exception:  # noqa: BLE001
            return []
        return [
            {
                "table_id": table.id,
                "table_type": table.get_table_type_display(),
                "table_type_code": table.table_type,
                "capacity": table.capacity,
                "floor": table.floor,
            }
            for table in tables[:8]
        ]

    def _build_booking_notes(self, session: ChatSession, slots: dict) -> str:
        """Combine any free-text note with the dishes chosen during chat."""
        preorder_note = build_preorder_note(self._preordered_item_names(session))
        return merge_notes(slots.get("note"), preorder_note)

    @staticmethod
    def _preordered_item_names(session: ChatSession) -> list[str]:
        item_ids = session.selected_item_ids or []
        if not item_ids:
            return []
        item_map = {item.id: item.name for item in MenuItem.objects.filter(id__in=item_ids)}
        return [item_map[item_id] for item_id in item_ids if item_id in item_map]

    def _build_summary(self, slots: dict) -> dict:
        table_type_label = slots.get("table_type") or ""
        if slots.get("table_id"):
            table = Table.objects.filter(id=slots["table_id"]).first()
            if table:
                table_type_label = table.get_table_type_display()
        return {
            "table_id": slots.get("table_id"),
            "table_type": table_type_label,
            "floor": slots.get("floor"),
            "booking_date": slots.get("booking_date"),
            "booking_time": slots.get("booking_time"),
            "party_size": slots.get("party_size"),
            "guest_name": slots.get("guest_name"),
            "guest_phone": slots.get("guest_phone"),
            "guest_email": slots.get("guest_email"),
        }

    @staticmethod
    def _address(session: ChatSession) -> str:
        name = (session.customer_name or "").strip()
        if not name or is_placeholder(name):
            return "mình"
        return name

    @staticmethod
    def _format_vnd(amount) -> str:
        normalized = Decimal(str(amount or 0))
        return f"{int(normalized):,}".replace(",", ".")

    def _deposit_amount_text(self) -> str:
        try:
            amount = get_booking_fee_amount(BookingPayment.BookingFlow.CHATBOT)
        except Exception:  # noqa: BLE001
            amount = Decimal("100000")
        return self._format_vnd(amount)

    def _payload(
        self,
        *,
        session: ChatSession,
        message: str,
        available_tables: Optional[list[dict]] = None,
        booking_summary: Optional[dict] = None,
        quick_replies: Optional[list[str]] = None,
        next_action: str = "ask_booking_info",
        conversation_goal: str = "collect_booking_info",
    ) -> dict:
        return {
            "intent": "booking",
            "assistant_message": message,
            "conversation_goal": conversation_goal,
            "sale_stage": "booking",
            "recommended_items": [],
            "upsell_items": [],
            "next_action": next_action,
            "booking_fields_needed": [],
            "next_question": None,
            "soft_close": None,
            "question_to_user": None,
            "quick_replies": quick_replies or [],
            "available_tables": available_tables or [],
            "booking_summary": booking_summary,
            "booking_code": session.booking_code,
        }
