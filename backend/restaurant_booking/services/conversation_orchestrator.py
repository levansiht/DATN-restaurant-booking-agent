"""Single entry point that owns conversation routing and state.

Replaces the old per-turn keyword router. It loads a persistent
:class:`ChatSession`, keeps the conversation mode *sticky* (once in booking we
stay in booking until the guest finishes or explicitly bails), and delegates to
either the sales/menu responder or the booking state machine.
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from restaurant_booking.models import ChatSession, MenuItem
from restaurant_booking.services.booking_state_machine import BookingStateMachine
from restaurant_booking.services.sales_chat import RestaurantStructuredChatService
from restaurant_booking.services.slot_extractor import BookingSlotExtractor, normalize_text

logger = logging.getLogger(__name__)

Stage = ChatSession.Stage
Mode = ChatSession.Mode

# Explicit "I want to reserve a table" signals.
BOOKING_INTENT_TERMS = (
    "dat ban",
    "dat mot ban",
    "giu ban",
    "giu cho",
    "dat cho",
    "con ban",
    "ban trong",
    "booking",
    "reserve",
    "reservation",
    "muon dat",
)


class ConversationOrchestrator:
    def __init__(self):
        self.sales = RestaurantStructuredChatService()
        self.extractor = BookingSlotExtractor()
        self.fsm = BookingStateMachine(extractor=self.extractor)

    def build_response(
        self,
        *,
        session_id: Optional[str],
        user_input: str,
        chat_history: Optional[list[dict]] = None,
        selected_item_ids: Optional[list[int]] = None,
    ) -> dict:
        chat_history = chat_history or []
        selected_item_ids = [int(item_id) for item_id in (selected_item_ids or []) if item_id]

        session = self._load_or_create_session(session_id)
        if selected_item_ids:
            session.selected_item_ids = selected_item_ids

        normalized = normalize_text(user_input)
        payload = self._route(
            session=session,
            user_input=user_input,
            normalized=normalized,
            chat_history=chat_history,
            selected_item_ids=selected_item_ids,
        )

        session.save()
        return self._finalize(payload, session)

    # ------------------------------------------------------------------ #
    # Routing
    # ------------------------------------------------------------------ #
    def _route(
        self,
        *,
        session: ChatSession,
        user_input: str,
        normalized: str,
        chat_history: list[dict],
        selected_item_ids: list[int],
    ) -> dict:
        if session.mode == Mode.BOOKING:
            return self._route_in_booking(
                session=session,
                user_input=user_input,
                normalized=normalized,
                chat_history=chat_history,
                selected_item_ids=selected_item_ids,
            )
        # SALES mode
        if self._wants_booking(normalized):
            self._enter_booking(session, chat_history, fresh=False)
            return self.fsm.process(session=session, user_input=user_input, chat_history=chat_history)
        return self._sales(session, user_input, normalized, chat_history, selected_item_ids)

    def _route_in_booking(
        self,
        *,
        session: ChatSession,
        user_input: str,
        normalized: str,
        chat_history: list[dict],
        selected_item_ids: list[int],
    ) -> dict:
        # Booking already finished in a previous turn.
        if session.stage == Stage.DONE:
            if self._wants_booking(normalized):
                self._enter_booking(session, chat_history, fresh=True)
                return self.fsm.process(session=session, user_input=user_input, chat_history=chat_history)
            session.mode = Mode.SALES
            return self._sales(session, user_input, chat_history, selected_item_ids)

        # Guest explicitly abandons the reservation.
        if self.extractor.is_cancel(user_input):
            session.mode = Mode.SALES
            session.stage = Stage.NONE
            return self._sales(session, user_input, chat_history, selected_item_ids)

        # Guest wants to go back to browsing the menu mid-booking. Keep the
        # collected slots so they can resume later, just switch mode.
        if self.extractor.wants_menu(normalized) and not self._wants_booking(normalized):
            session.mode = Mode.SALES
            return self._sales(session, user_input, normalized, chat_history, selected_item_ids)

        return self.fsm.process(session=session, user_input=user_input, chat_history=chat_history)

    # ------------------------------------------------------------------ #
    # Mode helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _wants_booking(normalized: str) -> bool:
        return any(term in normalized for term in BOOKING_INTENT_TERMS)

    def _enter_booking(self, session: ChatSession, chat_history: list[dict], *, fresh: bool) -> None:
        if fresh:
            session.reset_booking_state()
        session.mode = Mode.BOOKING
        # Leave the stage as NONE on the entry turn so the triggering message
        # ("tôi muốn đặt bàn") is not mistaken for the guest's name. The state
        # machine's resolver will advance to COLLECT_NAME and ask for it next.
        if session.stage == Stage.DONE:
            session.stage = Stage.NONE
        # Recover any booking details already mentioned during the sales phase.
        session.slots = self.extractor.backfill_from_history(
            existing_slots=session.slots or {},
            chat_history=chat_history,
        )
        # Carry over the name already learned during the menu phase so the
        # booking flow never re-asks for it.
        if session.customer_name and not session.slots.get("guest_name"):
            session.slots["guest_name"] = session.customer_name

    def _sales(
        self,
        session: ChatSession,
        user_input: str,
        normalized: str,
        chat_history: list[dict],
        selected_item_ids: list[int],
    ) -> dict:
        # Persist dishes the guest commits to during chat so "chốt món" is real
        # and the selection carries into the booking flow.
        detected = self.sales.detect_mentioned_item_ids(user_input)
        if detected:
            existing = list(session.selected_item_ids or [])
            for item_id in detected:
                if item_id not in existing:
                    existing.append(item_id)
            session.selected_item_ids = existing

        # Once the guest has chosen dishes and signals a decision ("chốt",
        # "đồng ý", "ok"), close the order deterministically instead of letting
        # the LLM keep re-asking "em chốt nhé?" every turn.
        wants_more_menu = self.sales._wants_menu_listing(normalized)
        if (
            session.selected_item_ids
            and self.sales._is_decision_or_ack(normalized)
            and not wants_more_menu
        ):
            session.order_closed = True
            return self._closed_order_payload(session)

        payload = self.sales.build_sales_payload(
            user_input=user_input,
            chat_history=chat_history,
            selected_item_ids=selected_item_ids or session.selected_item_ids or [],
            known_name=session.customer_name or None,
        )
        if payload.get("customer_name") and not session.customer_name:
            session.customer_name = payload["customer_name"]
        return payload

    def _closed_order_payload(self, session: ChatSession) -> dict:
        names = self._preordered_item_names(session)
        addressed = session.customer_name or "mình"
        if names:
            message = (
                f"Dạ {addressed} ơi, em đã chốt món: {', '.join(names)}. "
                "Mình đặt bàn luôn để em giữ chỗ nhé?"
            )
        else:
            message = f"Dạ {addressed} ơi, em ghi nhận rồi ạ. Mình đặt bàn luôn nhé?"
        return {
            "intent": "recommend_menu",
            "assistant_message": message,
            "conversation_goal": "close_order",
            "sale_stage": "decision",
            "recommended_items": [],
            "upsell_items": [],
            "next_action": "none",
            "booking_fields_needed": [],
            "next_question": None,
            "soft_close": None,
            "question_to_user": None,
            "quick_replies": ["Đặt bàn", "Xem thêm món"],
        }

    @staticmethod
    def _preordered_item_names(session: ChatSession) -> list[str]:
        item_ids = session.selected_item_ids or []
        if not item_ids:
            return []
        name_map = {item.id: item.name for item in MenuItem.objects.filter(id__in=item_ids)}
        return [name_map[item_id] for item_id in item_ids if item_id in name_map]

    # ------------------------------------------------------------------ #
    # Session persistence
    # ------------------------------------------------------------------ #
    def _load_or_create_session(self, session_id: Optional[str]) -> ChatSession:
        normalized_id = (session_id or "").strip()
        if normalized_id:
            session = ChatSession.objects.filter(session_id=normalized_id).first()
            if session:
                return session
            return ChatSession(session_id=normalized_id)
        return ChatSession(session_id=str(uuid.uuid4()))

    @staticmethod
    def _finalize(payload: dict, session: ChatSession) -> dict:
        payload = dict(payload or {})
        payload.setdefault("available_tables", [])
        payload.setdefault("booking_summary", None)
        payload["booking_code"] = session.booking_code
        payload["session_id"] = session.session_id
        # Internal-only field never sent to the client.
        payload.pop("customer_name", None)
        return payload
