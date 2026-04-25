from __future__ import annotations

import re
import unicodedata
import json
from decimal import Decimal
from typing import Literal, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from common.services.llm_service import LLMProvider, get_llm_service
from restaurant_booking.agents.restaurant_booking_agent import RestaurantBookingAgent
from restaurant_booking.models import MenuItem, RestaurantProfile
from restaurant_booking.services.menu_catalog import MenuCatalogService
from restaurant_booking.services.llm_router import get_llm_router


BOOKING_TRIGGER_TERMS = (
    "dat ban",
    "giu ban",
    "con ban",
    "ban trong",
    "giu cho",
    "dat cho",
    "table",
    "booking",
)
BOOKING_CONTEXT_TERMS = (
    "may nguoi",
    "luc",
    "toi nay",
    "ngay mai",
    "hom nay",
    "den quan",
    "qua quan",
    "an tai quan",
    "ghe quan",
)
GREETING_TERMS = (
    "xin chao",
    "chao",
    "hello",
    "hi",
    "alo",
)
ACKNOWLEDGEMENT_TERMS = (
    "ok",
    "oke",
    "okay",
    "okie",
    "cam on",
    "thanks",
    "thank you",
    "vang",
    "da",
    "duoc",
)
VAGUE_HELP_TERMS = (
    "tu van",
    "tu van giup",
    "ho tro",
    "ho tro giup",
)
DINE_IN_TERMS = (
    "an tai quan",
    "tai quan",
    "den quan",
    "qua quan",
    "ngoi lai",
    "dung bua tai quan",
)
MENU_TERMS = (
    "menu",
    "an gi",
    "goi y mon",
    "mon nao",
    "combo",
    "best seller",
    "noi bat",
    "gia",
    "chay",
    "it cay",
    "trang mieng",
    "do uong",
    "an kem",
)
PURCHASE_SIGNAL_TERMS = (
    "mon nay",
    "nghe on",
    "on do",
    "thich mon nay",
    "nghieng ve",
    "chon mon",
    "chot mon",
    "chot luon",
    "lay mon nay",
    "dat mon",
)
BOOKING_CONFIRMATION_TERMS = (
    "ok",
    "oke",
    "okay",
    "okie",
    "da",
    "duoc",
    "vang",
    "dong y",
    "dung roi",
    "chinh xac",
    "giu ban giup",
    "dat ban giup",
    "giu ban do",
    "lay ban do",
)
BOOKING_PROMPT_TERMS = (
    "dat ban",
    "giu ban",
    "thong tin dat ban",
    "kiem tra ban",
    "ngay nao",
    "khoang may gio",
    "luc may gio",
    "di may nguoi",
    "so nguoi",
    "khu vuc nao",
    "tang nao",
    "chon ban nao",
    "ban so",
    "so dien thoai",
    "email",
    "xac nhan",
)
TABLE_PREFERENCE_TERMS = (
    "trong nha",
    "ngoai troi",
    "phong rieng",
    "quay bar",
    "ghe ngoi",
    "gan cua so",
    "cua so",
    "tang 1",
    "tang 2",
)
BOOKING_FIELD_ORDER = ("date", "time", "party_size", "name", "phone", "email")
BOOKING_FIELD_LABELS = {
    "date": "Ngày",
    "time": "Giờ",
    "party_size": "Số người",
    "name": "Tên",
    "phone": "Số điện thoại",
    "email": "Email",
}
BookingFieldName = Literal["date", "time", "party_size", "name", "phone", "email"]


class SuggestedItemPick(BaseModel):
    item_id: int = Field(..., description="ID món được chọn từ candidate list")
    short_reason: str = Field(
        ...,
        description="Lý do rất ngắn, tối đa 18 từ, giống cách nhân viên tư vấn",
        max_length=120,
    )


class SalesChatPlan(BaseModel):
    intent: Literal[
        "discover_menu",
        "recommend_menu",
        "restaurant_info",
        "upsell",
        "mixed",
        "booking",
    ] = "discover_menu"
    assistant_message: str = Field(..., max_length=900)
    conversation_goal: Literal[
        "clarify_need",
        "recommend",
        "upsell",
        "close_order",
        "collect_booking_info",
        "confirm_booking",
    ] = Field(
        default="recommend",
        description="Mục tiêu bán hàng chính của lượt trả lời hiện tại",
    )
    sale_stage: Literal["discovery", "consideration", "decision", "booking"] = Field(
        default="discovery",
        description="Giai đoạn hội thoại hiện tại để điều hướng cách tư vấn và chốt",
    )
    recommended_items: list[SuggestedItemPick] = Field(default_factory=list)
    upsell_items: list[SuggestedItemPick] = Field(default_factory=list)
    next_action: Literal[
        "none",
        "ask_preference",
        "ask_budget",
        "ask_booking_info",
        "show_menu",
        "confirm_booking",
        "upsell",
    ] = "none"
    booking_fields_needed: list[BookingFieldName] = Field(
        default_factory=list,
        max_length=6,
        description="Các trường còn thiếu nếu cần chuyển sang giữ bàn hoặc hoàn tất booking",
    )
    next_question: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Câu hỏi tiếp theo, chỉ dùng khi thật sự cần hỏi thêm đúng một ý ngắn",
    )
    soft_close: Optional[str] = Field(
        default=None,
        max_length=220,
        description="Câu chốt mềm lịch sự khi khách đã có tín hiệu ra quyết định",
    )
    quick_replies: list[str] = Field(default_factory=list, max_length=4)


class RestaurantStructuredChatService:
    def __init__(
        self,
        llm_provider: LLMProvider = LLMProvider.OPENAI,
    ):
        self.catalog_service = MenuCatalogService()
        self.router = get_llm_router(llm_provider)  # LLM-based router
        model_name = "gpt-4o-mini"
        if llm_provider != LLMProvider.OPENAI:
            model_name = "claude-3-sonnet-20240229"
        self.llm = get_llm_service().create_agent_llm(
            provider=llm_provider,
            model=model_name,
            temperature=0.2,
            max_tokens=900,
            streaming=False,
        )
        self.structured_llm = self.llm.with_structured_output(
            SalesChatPlan,
            method="json_schema",
            strict=True,
        )

    def build_response(self, *, user_input: str, chat_history=None, selected_item_ids=None) -> dict:
        chat_history = chat_history or []
        selected_item_ids = [int(item_id) for item_id in selected_item_ids or [] if item_id]
        route = self._route_request(
            user_input=user_input,
            chat_history=chat_history,
            selected_item_ids=selected_item_ids,
        )
        if route == "booking":
            return self._build_booking_payload(
                user_input=user_input,
                chat_history=chat_history,
                selected_item_ids=selected_item_ids,
            )
        return self._build_sales_payload(
            user_input=user_input,
            chat_history=chat_history,
            selected_item_ids=selected_item_ids,
        )

    def _route_request(
        self,
        *,
        user_input: str,
        chat_history: list[dict],
        selected_item_ids: list[int],
    ) -> str:
        """
        Use LLM to intelligently route user input to sales or booking.
        
        Flow:
        1. Call LLM router with user input + context
        2. LLM returns: route (sales/booking) + confidence
        3. If confidence too low, fallback to keyword-based
        4. Return routing decision
        
        Returns:
            "sales" or "booking"
        """
        normalized_input = self._normalize_text(user_input)
        if self._can_route_to_booking(normalized_input=normalized_input, chat_history=chat_history):
            return "booking"

        # Use LLM router instead of keyword matching
        route, confidence = self.router.route(
            user_input=user_input,
            chat_history=chat_history,
            confidence_threshold=0.65,  # Require 65%+ confidence to trust LLM
        )

        if route == "booking" and not self._can_route_to_booking(
            normalized_input=normalized_input,
            chat_history=chat_history,
        ):
            return "sales"

        return route

    def _build_booking_payload(
        self,
        *,
        user_input: str,
        chat_history: list[dict],
        selected_item_ids: list[int],
    ) -> dict:
        selected_items = self._resolve_selected_items(selected_item_ids)
        booking_agent = RestaurantBookingAgent(
            callbacks=None,
            queue=None,
            sales_handoff=self._build_booking_handoff_context(
                selected_items=selected_items,
                user_input=user_input,
                chat_history=chat_history,
            ),
        )
        self._load_chat_history_into_agent_memory(booking_agent.agent, chat_history)
        result = booking_agent.run(user_input)
        assistant_message = result.get("output") if isinstance(result, dict) else str(result)
        next_action = "ask_booking_info"
        if "ma dat ban" in self._normalize_text(assistant_message):
            next_action = "confirm_booking"
        booking_fields_needed = []
        if next_action == "ask_booking_info":
            booking_fields_needed = self._infer_booking_fields_needed(
                user_input=user_input,
                chat_history=chat_history,
            )[:5]
        return {
            "intent": "booking",
            "assistant_message": assistant_message,
            "conversation_goal": "confirm_booking" if next_action == "confirm_booking" else "collect_booking_info",
            "sale_stage": "booking",
            "recommended_items": [],
            "upsell_items": [],
            "next_action": next_action,
            "booking_fields_needed": [],
            "next_question": None,
            "soft_close": None,
            "question_to_user": None,
            "quick_replies": [],
        }

    def _build_sales_payload(
        self,
        *,
        user_input: str,
        chat_history: list[dict],
        selected_item_ids: list[int],
    ) -> dict:
        restaurant_info = self._get_restaurant_profile_payload()
        selected_items = self._resolve_selected_items(selected_item_ids)
        normalized_input = self._normalize_text(user_input)
        has_menu_signal = self._has_menu_signal(normalized_input)
        force_clarify_need = self._should_force_clarify_need(normalized_input)
        has_explicit_purchase_signal = self._has_explicit_purchase_signal(normalized_input)
        should_start_booking = self._should_start_booking_after_menu(
            normalized_input=normalized_input,
            chat_history=chat_history,
            selected_items=selected_items,
        )
        menu_filters = self._derive_menu_filters(user_input)
        candidate_items = self._select_candidate_items(user_input=user_input, filters=menu_filters)
        candidate_map = {item["id"]: item for item in candidate_items}

        upsell_candidates = self._build_upsell_candidates(selected_item_ids)
        upsell_map = {item["id"]: item for item in upsell_candidates}

        try:
            plan = self._invoke_structured_plan(
                user_input=user_input,
                chat_history=chat_history,
                restaurant_info=restaurant_info,
                candidate_items=candidate_items,
                upsell_candidates=upsell_candidates,
                selected_items=selected_items,
                selected_item_ids=selected_item_ids,
            )
        except Exception:
            if force_clarify_need:
                fallback_message = self._fallback_clarify_need_message(selected_items=selected_items)
                fallback_goal = "clarify_need"
                fallback_stage = "discovery"
                fallback_action = "ask_preference"
                fallback_question = None
                fallback_soft_close = None
            elif has_explicit_purchase_signal and selected_items:
                fallback_message = self._fallback_message(candidate_items, selected_item_ids)
                fallback_goal = "close_order"
                fallback_stage = "decision"
                fallback_action = "upsell"
                fallback_question = None
                fallback_soft_close = self._fallback_soft_close(
                    conversation_goal="close_order",
                    selected_items=selected_items,
                    recommended_items=[],
                    upsell_items=[],
                )
            else:
                fallback_message = self._fallback_message(candidate_items, selected_item_ids)
                fallback_goal = "recommend" if has_menu_signal else "clarify_need"
                fallback_stage = "consideration" if has_menu_signal else "discovery"
                fallback_action = "show_menu" if has_menu_signal else "ask_preference"
                fallback_question = (
                    None
                    if has_menu_signal
                    else "Dạ anh/chị muốn em gợi ý theo vị dễ ăn, mức giá hay nhóm đi mấy người ạ?"
                )
                fallback_soft_close = None

            plan = SalesChatPlan(
                intent="upsell" if has_explicit_purchase_signal and selected_items else "recommend_menu",
                assistant_message=fallback_message,
                conversation_goal=fallback_goal,
                sale_stage=fallback_stage,
                next_action=fallback_action,
                next_question=fallback_question,
                soft_close=fallback_soft_close,
                quick_replies=self._fallback_quick_replies(
                    fallback_action,
                    fallback_goal,
                ),
            )

        recommended_items = self._hydrate_item_picks(
            getattr(plan, "recommended_items", []),
            candidate_map,
            fallback_candidates=candidate_items[:3],
            limit=5,
        )
        upsell_items = self._hydrate_item_picks(
            getattr(plan, "upsell_items", []),
            upsell_map,
            fallback_candidates=upsell_candidates[:2],
            limit=3,
            exclude_ids={item["id"] for item in recommended_items},
        )

        assistant_message = getattr(plan, "assistant_message", "").strip()
        if not assistant_message:
            assistant_message = self._fallback_message(candidate_items, selected_item_ids)

        conversation_goal = getattr(plan, "conversation_goal", "recommend")
        sale_stage = getattr(plan, "sale_stage", "consideration")
        booking_fields_needed = self._sanitize_booking_fields(
            getattr(plan, "booking_fields_needed", [])
        )

        if force_clarify_need:
            conversation_goal = "clarify_need"
            sale_stage = "discovery"
        elif should_start_booking:
            conversation_goal = "collect_booking_info"
            sale_stage = "booking"
        elif conversation_goal in {"collect_booking_info", "confirm_booking"}:
            conversation_goal = "recommend" if has_menu_signal else "clarify_need"
            sale_stage = "consideration" if has_menu_signal else "discovery"
            booking_fields_needed = []
            if self._message_mentions_booking(assistant_message):
                assistant_message = (
                    self._fallback_message(candidate_items, selected_item_ids)
                    if has_menu_signal
                    else self._fallback_clarify_need_message(selected_items=selected_items)
                )

        next_action = self._resolve_next_action(
            plan=plan,
            conversation_goal=conversation_goal,
            selected_items=selected_items,
        )
        if force_clarify_need:
            next_action = "ask_preference"
        elif should_start_booking:
            next_action = "ask_booking_info"
        elif conversation_goal == "recommend" and next_action in {"ask_booking_info", "confirm_booking"}:
            next_action = "show_menu"
        elif conversation_goal == "clarify_need" and next_action in {"ask_booking_info", "confirm_booking"}:
            next_action = "ask_preference"
        next_question = (getattr(plan, "next_question", None) or "").strip() or None
        if force_clarify_need:
            assistant_message = self._fallback_clarify_need_message(selected_items=selected_items)
            next_question = None
        if not force_clarify_need and next_action in {"ask_preference", "ask_budget", "ask_booking_info"} and not next_question:
            next_question = self._fallback_question(
                next_action=next_action,
                conversation_goal=conversation_goal,
                selected_items=selected_items,
                booking_fields_needed=booking_fields_needed,
            )
        if should_start_booking and not self._message_mentions_booking(assistant_message):
            assistant_message = "Dạ em hỗ trợ đặt bàn cho anh/chị ạ."

        if conversation_goal in {"collect_booking_info", "confirm_booking"} and not booking_fields_needed:
            booking_fields_needed = self._infer_booking_fields_needed(
                user_input=user_input,
                chat_history=chat_history,
            )
        if conversation_goal == "confirm_booking":
            booking_fields_needed = []

        if conversation_goal in {"collect_booking_info", "confirm_booking"} or next_action == "ask_booking_info":
            recommended_items = []
            upsell_items = []
        if conversation_goal == "clarify_need":
            recommended_items = []
            upsell_items = []

        soft_close = (getattr(plan, "soft_close", None) or "").strip() or None
        if conversation_goal == "clarify_need":
            soft_close = None
        elif not soft_close:
            soft_close = self._fallback_soft_close(
                conversation_goal=conversation_goal,
                selected_items=selected_items,
                recommended_items=recommended_items,
                upsell_items=upsell_items,
            )

        quick_replies = [reply.strip() for reply in getattr(plan, "quick_replies", []) if reply.strip()][:4]
        if not quick_replies:
            quick_replies = (
                []
                if next_action == "confirm_booking"
                else self._fallback_quick_replies(next_action, conversation_goal)
            )
        elif conversation_goal in {"collect_booking_info", "confirm_booking"}:
            quick_replies = self._fallback_quick_replies(next_action, conversation_goal)
        if conversation_goal == "clarify_need":
            quick_replies = self._fallback_quick_replies(next_action, conversation_goal)

        intent = getattr(plan, "intent", "recommend_menu")
        if conversation_goal in {"collect_booking_info", "confirm_booking"}:
            intent = "booking"
        elif conversation_goal == "clarify_need":
            intent = "discover_menu"

        assistant_message = self._compose_visible_message(
            assistant_message=assistant_message,
            soft_close=soft_close,
            next_question=next_question,
        )

        return {
            "intent": intent,
            "assistant_message": assistant_message,
            "conversation_goal": conversation_goal,
            "sale_stage": sale_stage,
            "recommended_items": recommended_items,
            "upsell_items": upsell_items,
            "next_action": next_action,
            "booking_fields_needed": [],
            "next_question": None,
            "soft_close": None,
            "question_to_user": None,
            "quick_replies": [],
        }

    def _invoke_structured_plan(
        self,
        *,
        user_input: str,
        chat_history: list[dict],
        restaurant_info: dict,
        candidate_items: list[dict],
        upsell_candidates: list[dict],
        selected_items: list[dict],
        selected_item_ids: list[int],
    ) -> SalesChatPlan:
        history_lines = []
        for message in chat_history[-6:]:
            role = "Khách" if message.get("role") == "user" else "Nhân viên"
            history_lines.append(f"{role}: {message.get('content', '')}")

        system_prompt = self._build_sales_system_prompt(restaurant_info)
        normalized_input = self._normalize_text(user_input)
        human_prompt = {
            "restaurant_info": restaurant_info,
            "recent_history": history_lines,
            "selected_item_ids": selected_item_ids,
            "selected_items": selected_items,
            "user_input": user_input,
            "candidate_items": candidate_items,
            "upsell_candidates": upsell_candidates,
            "signals": {
                "booking_signal": self._has_explicit_booking_intent(normalized_input),
                "booking_followup_response": self._is_booking_followup_response(
                    normalized_input=normalized_input,
                    chat_history=chat_history,
                ),
                "booking_context_only": (
                    self._has_booking_context(normalized_input)
                    and not self._has_explicit_booking_intent(normalized_input)
                ),
                "purchase_signal": self._has_explicit_purchase_signal(normalized_input),
                "greeting_or_vague_turn": self._should_force_clarify_need(normalized_input),
                "selected_item_count": len(selected_items),
            },
            "response_rules": {
                "recommendation_limit": 5,
                "upsell_limit": 3,
                "prefer_short_reasons": True,
                "one_short_question_max": True,
                "no_cards_when_clarify_need": True,
            },
        }
        return self.structured_llm.invoke(
            [
                SystemMessage(content=system_prompt.strip()),
                HumanMessage(content=json.dumps(human_prompt, ensure_ascii=False)),
            ]
        )

    def _build_sales_system_prompt(self, restaurant_info: dict) -> str:
        restaurant_name = restaurant_info.get("name") or "PSCD Japanese Dining"
        return f"""
You are a professional restaurant staff member for {restaurant_name}.

Your job: advise dishes naturally like a real waiter or hostess. Do not rush. Do not push booking unless the customer clearly asks for it.

ABSOLUTE RULES
1. ONLY recommend items from candidate_items and upsell_candidates.
2. NEVER invent dishes, prices, promotions, availability, or table details.
3. Speak like a real staff member. Never mention AI or bot identity.
4. selected_items / selected_item_ids mean the guest is interested in those dishes. They do NOT automatically mean the guest wants to book a table.
5. Time, date, party size, or dine-in context alone do NOT mean booking. They are just context unless the guest explicitly wants to reserve, keep, check, or confirm a table.
6. NEVER say phrases like "em giữ bàn luôn", "mình chọn bàn nào", "em chuyển sang booking nhé" unless booking_signal or booking_followup_response is true.

CONVERSATION STATES
- clarify_need: just greet naturally and ask what the guest needs.
- recommend: recommend dishes only after the guest clearly asks about menu / dishes / price / filters.
- upsell: suggest 1-3 matching add-ons only when the guest is already leaning toward a dish.
- close_order: help the guest narrow down or confirm a dish direction without forcing booking.
- collect_booking_info / confirm_booking: only when booking_signal or booking_followup_response is true.

STATE RULES
1. If greeting_or_vague_turn is true:
   - Must use clarify_need.
   - assistant_message must only greet and ask the main need.
   - recommended_items = []
   - upsell_items = []
   - soft_close = null
   - Do not mention booking.

2. If the guest asks menu or dish questions:
   - Use recommend or clarify_need.
   - Recommend 2-5 dishes max when enough information is available.
   - If still vague, ask ONE short question only.

3. If the guest is leaning toward a selected dish:
   - Use upsell or close_order.
   - You may confirm the direction and suggest a matching side/drink.
   - Do not move to booking unless booking_signal or booking_followup_response is true.

4. If booking_signal or booking_followup_response is true:
   - Move to collect_booking_info or confirm_booking.
   - recommended_items = []
   - upsell_items = []
   - Focus only on booking information still missing.

STYLE
- Use anh/chị - em.
- Warm, short, natural, professional.
- Ask at most ONE short question in sales states.
- Avoid sounding like a form.

OUTPUT RULES
- assistant_message: short natural staff reply, max 900 chars.
- conversation_goal: clarify_need | recommend | upsell | close_order | collect_booking_info | confirm_booking
- sale_stage: discovery | consideration | decision | booking
- recommended_items: max 5
- upsell_items: max 3
- booking_fields_needed: only for booking states
- next_question: only if needed, one short question
- soft_close: only for recommend / upsell / close_order, never for clarify_need

FEW-SHOT EXAMPLES
Example 1
User: "Xin chào"
Signals: greeting_or_vague_turn=true
→ conversation_goal: clarify_need
→ sale_stage: discovery
→ recommended_items: []
→ assistant_message: "Dạ em chào anh/chị. Anh/chị muốn em hỗ trợ xem menu, gợi ý món hay giải đáp thông tin nhà hàng ạ?"

Example 2
User: "Tư vấn giúp mình"
Signals: greeting_or_vague_turn=true
→ conversation_goal: clarify_need
→ assistant_message: "Dạ em chào anh/chị. Anh/chị muốn em gợi ý món theo gu ăn, mức giá hay số người ạ?"

Example 3
User: "Gợi ý món cho 2 người"
Signals: booking_context_only=true, booking_signal=false
→ conversation_goal: recommend
→ sale_stage: consideration
→ recommended_items: [2-4 relevant dishes]
→ assistant_message: mention dishes only, do not mention booking

Example 4
User: "Được, mình nghiêng về món này"
Context: selected_item_count > 0
Signals: purchase_signal=true, booking_signal=false
→ conversation_goal: close_order
→ sale_stage: decision
→ upsell_items: matching side/drink
→ assistant_message: confirm dish direction, no booking mention

Example 5
User: "Ok giữ bàn giúp mình tối nay"
Signals: booking_signal=true
→ conversation_goal: collect_booking_info
→ sale_stage: booking
→ recommended_items: []
→ assistant_message: "Dạ em hỗ trợ đặt bàn cho anh/chị ạ."
→ next_question: ask the next missing booking information
"""


    def _resolve_selected_items(self, selected_item_ids: list[int]) -> list[dict]:
        if not selected_item_ids:
            return []
        queryset = self.catalog_service.active_queryset().filter(id__in=selected_item_ids)
        item_map = {item.id: item for item in queryset}
        selected_items: list[dict] = []
        for item_id in selected_item_ids:
            item = item_map.get(item_id)
            if item:
                selected_items.append(self._serialize_candidate_item(item))
        return selected_items[:5]

    def _has_explicit_booking_intent(self, normalized_input: str) -> bool:
        return any(term in normalized_input for term in BOOKING_TRIGGER_TERMS)

    def _has_booking_signal(self, normalized_input: str) -> bool:
        return self._has_explicit_booking_intent(normalized_input)

    def _has_booking_context(self, normalized_input: str) -> bool:
        return any(term in normalized_input for term in BOOKING_CONTEXT_TERMS)

    def _has_menu_signal(self, normalized_input: str) -> bool:
        return any(term in normalized_input for term in MENU_TERMS)

    def _has_dine_in_signal(self, normalized_input: str) -> bool:
        return any(term in normalized_input for term in DINE_IN_TERMS)

    def _has_explicit_purchase_signal(self, normalized_input: str) -> bool:
        return any(term in normalized_input for term in PURCHASE_SIGNAL_TERMS)

    def _has_purchase_signal(self, *, normalized_input: str, selected_item_ids: list[int]) -> bool:
        return any(term in normalized_input for term in PURCHASE_SIGNAL_TERMS)

    def _is_social_turn(self, normalized_input: str) -> bool:
        if not normalized_input:
            return True
        if self._has_explicit_booking_intent(normalized_input) or self._has_menu_signal(normalized_input):
            return False
        tokens = normalized_input.split()
        compact = " ".join(
            token
            for token in tokens
            if token not in {"a", "nhe", "voi", "giup", "minh", "em", "anh", "chi"}
        )
        return (
            compact in GREETING_TERMS
            or compact in ACKNOWLEDGEMENT_TERMS
            or any(compact.startswith(term) for term in VAGUE_HELP_TERMS)
        )

    def _should_force_clarify_need(self, normalized_input: str) -> bool:
        return self._is_social_turn(normalized_input)

    def _build_recent_history_text(self, chat_history: list[dict], *, limit: int = 6) -> str:
        return " ".join(
            self._normalize_text(message.get("content", ""))
            for message in chat_history[-limit:]
        )

    def _last_assistant_message(self, chat_history: list[dict]) -> str:
        return next(
            (
                self._normalize_text(message.get("content", ""))
                for message in reversed(chat_history)
                if message.get("role") == "assistant"
            ),
            "",
        )

    def _assistant_is_booking_prompt(self, chat_history: list[dict]) -> bool:
        last_assistant_message = self._last_assistant_message(chat_history)
        if not last_assistant_message:
            return False
        return any(term in last_assistant_message for term in BOOKING_PROMPT_TERMS)

    def _contains_booking_followup_data(self, normalized_input: str) -> bool:
        compact = re.sub(r"[^\d+]", "", normalized_input)
        return bool(
            self._has_date_reference(normalized_input)
            or self._has_time_reference(normalized_input)
            or self._has_party_size_reference(normalized_input)
            or self._has_name_reference(normalized_input)
            or self._has_phone_reference(compact)
            or self._has_email_reference(normalized_input)
            or re.search(r"\b(?:ban|table)\s*\d+\b", normalized_input)
            or any(term in normalized_input for term in TABLE_PREFERENCE_TERMS)
        )

    def _is_booking_confirmation(self, normalized_input: str) -> bool:
        return normalized_input in BOOKING_CONFIRMATION_TERMS or any(
            term in normalized_input for term in BOOKING_CONFIRMATION_TERMS
        )

    def _is_booking_followup_response(
        self,
        *,
        normalized_input: str,
        chat_history: list[dict],
    ) -> bool:
        if not self._assistant_is_booking_prompt(chat_history):
            return False
        return self._is_booking_confirmation(normalized_input) or self._contains_booking_followup_data(
            normalized_input
        )

    def _can_route_to_booking(self, *, normalized_input: str, chat_history: list[dict]) -> bool:
        return self._has_explicit_booking_intent(normalized_input) or self._is_booking_followup_response(
            normalized_input=normalized_input,
            chat_history=chat_history,
        )

    def _should_start_booking_after_menu(
        self,
        *,
        normalized_input: str,
        chat_history: list[dict],
        selected_items: list[dict],
    ) -> bool:
        if not selected_items:
            return False

        return self._has_explicit_booking_intent(normalized_input) or self._is_booking_followup_response(
            normalized_input=normalized_input,
            chat_history=chat_history,
        )

    def _resolve_next_action(
        self,
        *,
        plan: SalesChatPlan,
        conversation_goal: str,
        selected_items: list[dict],
    ) -> str:
        plan_next_action = getattr(plan, "next_action", "none")
        if plan_next_action != "none":
            return plan_next_action

        if conversation_goal == "clarify_need":
            return "ask_preference"
        if conversation_goal == "recommend":
            return "show_menu"
        if conversation_goal in {"upsell", "close_order"}:
            return "upsell" if selected_items else "show_menu"
        if conversation_goal == "collect_booking_info":
            return "ask_booking_info"
        if conversation_goal == "confirm_booking":
            return "confirm_booking"
        return "ask_preference"

    def _fallback_question(
        self,
        *,
        next_action: str,
        conversation_goal: str,
        selected_items: list[dict],
        booking_fields_needed: list[str],
    ) -> Optional[str]:
        if next_action == "ask_budget":
            return "Mình muốn giữ mức khoảng bao nhiêu để em lọc cho gọn ạ?"
        if next_action == "ask_booking_info":
            first_fields = booking_fields_needed[:2] or ["date", "time"]
            if first_fields == ["date", "time"]:
                return "Dạ anh/chị muốn đặt ngày nào và khoảng mấy giờ ạ?"
            if first_fields == ["party_size"]:
                return "Dạ anh/chị đi mấy người để em kiểm tra bàn phù hợp ạ?"
            if first_fields == ["name", "phone"]:
                return "Dạ anh/chị cho em xin tên và số điện thoại để em ghi nhận thông tin đặt bàn ạ?"
            if first_fields == ["email"]:
                return "Dạ anh/chị cho em xin email để em gửi xác nhận đặt bàn ạ?"
            labels = [BOOKING_FIELD_LABELS.get(field, field).lower() for field in first_fields]
            if len(labels) == 1:
                return f"Dạ anh/chị cho em xin {labels[0]} trước ạ?"
            return f"Dạ anh/chị cho em xin {labels[0]} và {labels[1]} ạ?"
        if conversation_goal == "close_order" and selected_items:
            return "Anh/chị muốn em gợi ý thêm món kèm hợp vị hay xem món tương tự ạ?"
        return "Anh/chị nghiêng về vị dễ ăn, đậm vị hay muốn em lọc theo ngân sách ạ?"

    def _fallback_soft_close(
        self,
        *,
        conversation_goal: str,
        selected_items: list[dict],
        recommended_items: list[dict],
        upsell_items: list[dict],
    ) -> Optional[str]:
        lead_item = (selected_items or recommended_items or upsell_items or [{}])[0]
        lead_name = lead_item.get("name")

        if conversation_goal == "recommend" and recommended_items:
            if lead_name:
                return f"Nếu mình muốn chốt nhanh, em nghiêng về hướng lấy {lead_name} trước rồi bổ sung nhẹ cho cân bằng hơn."
            return "Nếu mình muốn chốt nhanh, em nghiêng về nhóm món này vì dễ chọn và khá cân bằng vị."
        if conversation_goal in {"upsell", "close_order"} and (upsell_items or selected_items):
            return "Nếu anh/chị thấy hợp, em gợi ý thêm 1 món kèm nhẹ để set ăn tròn vị hơn nhé?"
        if conversation_goal == "collect_booking_info":
            return "Em xin thêm vài thông tin để kiểm tra bàn phù hợp cho anh/chị ạ."
        return None

    def _sanitize_booking_fields(self, fields: list[str]) -> list[str]:
        sanitized: list[str] = []
        for field in fields or []:
            if field in BOOKING_FIELD_ORDER and field not in sanitized:
                sanitized.append(field)
        return sanitized

    def _infer_booking_fields_needed(self, *, user_input: str, chat_history: list[dict]) -> list[str]:
        recent_text = " ".join(message.get("content", "") for message in chat_history[-6:])
        combined_raw = f"{recent_text} {user_input}".strip()
        normalized = self._normalize_text(combined_raw)
        missing_fields: list[str] = []

        if not self._has_date_reference(normalized):
            missing_fields.append("date")
        if not self._has_time_reference(normalized):
            missing_fields.append("time")
        if not self._has_party_size_reference(normalized):
            missing_fields.append("party_size")
        if not self._has_name_reference(normalized):
            missing_fields.append("name")
        if not self._has_phone_reference(normalized):
            missing_fields.append("phone")
        if not self._has_email_reference(combined_raw.lower()):
            missing_fields.append("email")
        return missing_fields

    def _has_date_reference(self, normalized_text: str) -> bool:
        return bool(
            re.search(r"\b\d{4}-\d{2}-\d{2}\b", normalized_text)
            or re.search(r"\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b", normalized_text)
            or any(term in normalized_text for term in ["hom nay", "ngay mai", "toi nay", "ngay kia"])
        )

    def _has_time_reference(self, normalized_text: str) -> bool:
        return bool(
            re.search(r"\b([01]?\d|2[0-3])[:hg][0-5]?\d?\b", normalized_text)
            or any(term in normalized_text for term in ["buoi sang", "buoi trua", "buoi chieu", "buoi toi"])
        )

    def _has_party_size_reference(self, normalized_text: str) -> bool:
        return bool(
            re.search(r"\b\d+\s*(nguoi|khach|ban)\b", normalized_text)
            or re.search(r"\bdi\s+\d+\b", normalized_text)
        )

    def _has_name_reference(self, normalized_text: str) -> bool:
        return any(
            term in normalized_text
            for term in ["ten la", "toi la", "minh la", "em la", "anh la", "chi la", "quy danh"]
        )

    def _has_phone_reference(self, normalized_text: str) -> bool:
        compact = re.sub(r"[^\d+]", "", normalized_text)
        return bool(re.search(r"(?:\+?84|0)\d{8,10}", compact))

    def _has_email_reference(self, raw_text: str) -> bool:
        return bool(re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", raw_text))

    def _message_mentions_booking(self, message: str) -> bool:
        normalized_message = self._normalize_text(message)
        return any(
            term in normalized_message
            for term in [
                "giu ban",
                "dat ban",
                "giu cho",
                "dat cho",
                "kiem tra ban",
                "mấy giờ",
                "may gio",
                "may nguoi",
            ]
        )

    def _compose_visible_message(
        self,
        *,
        assistant_message: str,
        soft_close: Optional[str],
        next_question: Optional[str],
    ) -> str:
        message = (assistant_message or "").strip()
        message = self._append_message_line(message, soft_close)
        message = self._append_message_line(message, next_question)
        return message

    def _append_message_line(self, base_message: str, extra_message: Optional[str]) -> str:
        extra_message = (extra_message or "").strip()
        if not extra_message:
            return (base_message or "").strip()

        base_message = (base_message or "").strip()
        if not base_message:
            return extra_message

        normalized_base = self._normalize_text(base_message)
        normalized_extra = self._normalize_text(extra_message)
        if normalized_extra and normalized_extra in normalized_base:
            return base_message

        separator = " " if base_message.endswith((".", "!", "?", ":")) else ". "
        return f"{base_message}{separator}{extra_message}"

    def _build_booking_handoff_context(
        self,
        *,
        selected_items: list[dict],
        user_input: str,
        chat_history: list[dict],
    ) -> Optional[str]:
        if not selected_items:
            return None

        recent_user_messages = [
            message.get("content", "").strip()
            for message in chat_history[-3:]
            if message.get("role") == "user" and message.get("content")
        ]
        highlighted_items = ", ".join(item["name"] for item in selected_items[:3])
        normalized_input = self._normalize_text(user_input)
        transition_hint = (
            "Khách vừa xác nhận nhu cầu đặt bàn; hãy nối mạch thật ngắn từ món đang quan tâm rồi tiếp tục booking."
            if self._has_purchase_signal(
                normalized_input=normalized_input,
                selected_item_ids=[item["id"] for item in selected_items],
            )
            else "Nếu phù hợp, có thể nhắc rất ngắn các món khách đang quan tâm rồi tiếp tục booking."
        )
        recent_context = f"Ngữ cảnh gần đây: {' | '.join(recent_user_messages)}." if recent_user_messages else ""
        return "\n".join(
            line
            for line in [
                f"- Khách đang quan tâm các món: {highlighted_items}.",
                f"- {transition_hint}",
                f"- {recent_context}" if recent_context else "",
            ]
            if line
        )

    def _select_candidate_items(self, *, user_input: str, filters: dict) -> list[dict]:
        items = self.catalog_service.filter_items(
            vegetarian=filters.get("vegetarian"),
            recommended=filters.get("recommended"),
            best_seller=filters.get("best_seller"),
            kid_friendly=filters.get("kid_friendly"),
            spicy_level=filters.get("spicy_level"),
            max_price=filters.get("max_price"),
            served_now=True if filters.get("served_now") else None,
        )
        if not items:
            items = self.catalog_service.filter_items(served_now=True)

        ranked_items = sorted(
            items,
            key=lambda item: self._score_item_for_query(item, user_input, filters),
            reverse=True,
        )
        return [self._serialize_candidate_item(item) for item in ranked_items[:10]]

    def _build_upsell_candidates(self, selected_item_ids: list[int]) -> list[dict]:
        if not selected_item_ids:
            return []

        items = self.catalog_service.filter_items(limit=50)
        item_map = {item.id: item for item in items}
        pairings: list[MenuItem] = []
        seen_ids: set[int] = set()
        for item_id in selected_item_ids:
            selected_item = item_map.get(item_id)
            if not selected_item:
                continue
            for pairing in selected_item.suggested_pairings.filter(
                is_deleted=False,
                status=MenuItem.AvailabilityStatus.ACTIVE,
            ):
                if pairing.id in seen_ids or pairing.id in selected_item_ids:
                    continue
                pairings.append(pairing)
                seen_ids.add(pairing.id)
        return [self._serialize_candidate_item(item) for item in pairings[:6]]

    def _serialize_candidate_item(self, item: MenuItem) -> dict:
        payload = self.catalog_service.serialize_menu_item(item)
        return {
            "id": payload["id"],
            "name": payload["name"],
            "category_name": payload["category_name"],
            "price": float(payload["price"]),
            "badges": payload["badges"],
            "tags": payload["tags"],
            "dietary_labels": payload["dietary_labels"],
            "is_recommended": payload["is_recommended"],
            "is_best_seller": payload["is_best_seller"],
            "is_vegetarian": payload["is_vegetarian"],
            "is_kid_friendly": payload["is_kid_friendly"],
            "spicy_level": payload["spicy_level"],
            "description": payload["description"] or "",
        }

    def _hydrate_item_picks(
        self,
        picks: list[SuggestedItemPick],
        item_map: dict[int, dict],
        *,
        fallback_candidates: list[dict],
        limit: int,
        exclude_ids: Optional[set[int]] = None,
    ) -> list[dict]:
        exclude_ids = exclude_ids or set()
        hydrated_items: list[dict] = []
        seen_ids = set(exclude_ids)

        for pick in picks[:limit]:
            candidate = item_map.get(pick.item_id)
            if not candidate or candidate["id"] in seen_ids:
                continue
            hydrated_items.append(self._build_card_payload(candidate, pick.short_reason))
            seen_ids.add(candidate["id"])

        for candidate in fallback_candidates:
            if len(hydrated_items) >= limit or candidate["id"] in seen_ids:
                continue
            hydrated_items.append(
                self._build_card_payload(candidate, "Dễ chọn, đúng với nhu cầu hiện tại.")
            )
            seen_ids.add(candidate["id"])
        return hydrated_items

    def _build_card_payload(self, candidate: dict, short_reason: str) -> dict:
        menu_item = self.catalog_service.active_queryset().filter(id=candidate["id"]).first()
        if not menu_item:
            return {
                "id": candidate["id"],
                "name": candidate["name"],
                "price": candidate["price"],
                "category_name": candidate.get("category_name"),
                "short_reason": short_reason,
                "tags": candidate.get("tags", []),
                "image_url": "",
                "image_alt_text": candidate["name"],
                "image_badge": None,
            }
        payload = self.catalog_service.serialize_menu_item(menu_item)
        return {
            "id": payload["id"],
            "name": payload["name"],
            "price": float(payload["price"]),
            "category_name": payload["category_name"],
            "short_reason": short_reason,
            "tags": payload["badges"],
            "image_url": payload["image_url"],
            "image_alt_text": payload["image_alt_text"],
            "image_badge": payload["image_badge"],
            "is_best_seller": payload["is_best_seller"],
            "is_vegetarian": payload["is_vegetarian"],
        }

    def _score_item_for_query(self, item: MenuItem, user_input: str, filters: dict) -> int:
        normalized_input = self._normalize_text(user_input)
        haystack = self._normalize_text(f"{item.name} {item.description or ''} {' '.join(item.tags or [])}")
        score = 0
        tokens = [token for token in normalized_input.split() if len(token) > 2]
        score += sum(4 for token in tokens if token in haystack)
        if item.is_best_seller:
            score += 3 if filters.get("best_seller") else 1
        if item.is_recommended:
            score += 3 if filters.get("recommended") else 1
        if filters.get("vegetarian") and item.is_vegetarian:
            score += 5
        if filters.get("kid_friendly") and item.is_kid_friendly:
            score += 5
        if filters.get("spicy_level") and item.spicy_level == filters["spicy_level"]:
            score += 4
        if filters.get("max_price") is not None and item.price <= filters["max_price"]:
            score += 2
        if "an kem" in normalized_input and item.suggested_pairings.exists():
            score += 2
        return score

    def _derive_menu_filters(self, user_input: str) -> dict:
        normalized_input = self._normalize_text(user_input)
        max_price = self._extract_budget(normalized_input)
        return {
            "vegetarian": "chay" in normalized_input,
            "recommended": any(term in normalized_input for term in ["goi y", "noi bat", "signature"]),
            "best_seller": any(term in normalized_input for term in ["best seller", "ban chay", "noi tieng"]),
            "kid_friendly": any(term in normalized_input for term in ["tre em", "be", "kid"]),
            "served_now": any(term in normalized_input for term in ["toi nay", "bay gio", "hom nay"]),
            "spicy_level": self._detect_spicy_level(normalized_input),
            "max_price": max_price,
        }

    def _detect_spicy_level(self, normalized_input: str) -> Optional[str]:
        if "khong cay" in normalized_input:
            return MenuItem.SpicyLevel.NONE
        if "it cay" in normalized_input or "cay nhe" in normalized_input:
            return MenuItem.SpicyLevel.MILD
        if "cay vua" in normalized_input:
            return MenuItem.SpicyLevel.MEDIUM
        if "rat cay" in normalized_input or "cay nhieu" in normalized_input:
            return MenuItem.SpicyLevel.HOT
        return None

    def _extract_budget(self, normalized_input: str) -> Optional[Decimal]:
        match = re.search(r"(\d+(?:[\.,]\d+)?)\s*(k|nghin|ngan|trieu)?", normalized_input)
        if not match:
            return None
        number_token = match.group(1)
        unit = match.group(2) or ""
        if unit:
            raw_amount = Decimal(number_token.replace(",", "."))
        else:
            raw_amount = Decimal(number_token.replace(".", "").replace(",", ""))
        multiplier = Decimal("1")
        if unit in {"k", "nghin", "ngan"}:
            multiplier = Decimal("1000")
        elif unit == "trieu":
            multiplier = Decimal("1000000")
        if raw_amount < 50 and multiplier == Decimal("1"):
            return None
        return raw_amount * multiplier

    def _get_restaurant_profile_payload(self) -> dict:
        profile = RestaurantProfile.get_active_profile()
        if not profile:
            return {
                "name": "PSCD Japanese Dining",
                "description": "Nhà hàng phong cách hiện đại, phục vụ khách đặt bàn online.",
                "price_range_min": None,
                "price_range_max": None,
                "opening_time": "10:00",
                "closing_time": "22:00",
            }
        return {
            "name": profile.name,
            "description": profile.description,
            "price_range_min": float(profile.price_range_min) if profile.price_range_min else None,
            "price_range_max": float(profile.price_range_max) if profile.price_range_max else None,
            "opening_time": profile.opening_time.strftime("%H:%M") if profile.opening_time else None,
            "closing_time": profile.closing_time.strftime("%H:%M") if profile.closing_time else None,
        }

    def _fallback_message(self, candidate_items: list[dict], selected_item_ids: list[int]) -> str:
        if selected_item_ids:
            return "Em thấy mình đang nghiêng về vài món rồi. Nếu anh/chị muốn, em gợi ý thêm món kèm hoặc món tương tự để mình dễ chốt hơn ạ."
        if candidate_items:
            return "Dạ em có thể gợi ý món theo vị, mức giá hoặc số người để anh/chị dễ chọn hơn ạ."
        return "Dạ anh/chị muốn em gợi ý theo vị, mức giá hay nhu cầu dùng bữa để em hỗ trợ sát hơn ạ?"

    def _fallback_clarify_need_message(self, *, selected_items: list[dict]) -> str:
        if selected_items:
            return "Dạ em chào anh/chị. Anh/chị muốn em tư vấn thêm về món mình đang xem hay lọc món theo gu ăn ạ?"
        return "Dạ em chào anh/chị. Anh/chị muốn em hỗ trợ xem menu, gợi ý món hay giải đáp thông tin nhà hàng ạ?"

    def _fallback_quick_replies(self, next_action: str, conversation_goal: str) -> list[str]:
        if next_action == "ask_booking_info" or conversation_goal == "collect_booking_info":
            return ["Tối nay", "Ngày mai", "Đi 2 người"]
        if next_action == "ask_budget":
            return ["Dưới 200k", "Khoảng 300k", "Lọc món dễ ăn"]
        if next_action == "upsell" or conversation_goal in {"upsell", "close_order"}:
            return ["Gợi ý món kèm", "Món tương tự", "Xem món khác"]
        return ["Gợi ý món dễ ăn", "Món cho 2 người", "Theo ngân sách"]

    def _load_chat_history_into_agent_memory(self, agent, messages):
        if not messages:
            return
        if hasattr(agent, "memory") and agent.memory:
            agent.memory.clear()
        for message in messages:
            if message.get("role") == "user":
                agent.memory.chat_memory.add_user_message(message.get("content", ""))
            elif message.get("role") == "assistant":
                agent.memory.chat_memory.add_ai_message(message.get("content", ""))

    def _normalize_text(self, value: str) -> str:
        normalized = unicodedata.normalize("NFD", (value or "").strip().lower())
        normalized = normalized.replace("\u0111", "d")
        normalized = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
        return " ".join(normalized.split())
