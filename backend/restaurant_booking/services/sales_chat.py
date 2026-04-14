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
        normalized_input = self._normalize_text(user_input)
        has_menu_signal = any(term in normalized_input for term in MENU_TERMS)
        has_booking_trigger = any(term in normalized_input for term in BOOKING_TRIGGER_TERMS)
        has_booking_context = any(term in normalized_input for term in BOOKING_CONTEXT_TERMS)
        has_purchase_signal = self._has_purchase_signal(
            normalized_input=normalized_input,
            selected_item_ids=selected_item_ids,
        )

        if has_menu_signal and not has_booking_trigger:
            return "sales"
        if has_booking_trigger:
            return "booking"

        recent_text = " ".join(
            self._normalize_text(message.get("content", ""))
            for message in chat_history[-4:]
        )
        if any(term in recent_text for term in BOOKING_TRIGGER_TERMS):
            return "booking"
        if has_booking_context and has_purchase_signal:
            return "booking"
        return "sales"

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
            plan = SalesChatPlan(
                intent="upsell" if selected_item_ids else "recommend_menu",
                assistant_message=self._fallback_message(candidate_items, selected_item_ids),
                conversation_goal="close_order" if selected_item_ids else "clarify_need",
                sale_stage="decision" if selected_item_ids else "discovery",
                next_action="upsell" if selected_item_ids else "ask_preference",
                next_question=(
                    None
                    if selected_item_ids
                    else "Anh/chị muốn em chốt theo vị dễ ăn, đậm vị hay theo ngân sách ạ?"
                ),
                soft_close=(
                    "Nếu mình thấy ổn, em chốt theo hướng món chính + món kèm nhẹ cho mình nhé?"
                    if selected_item_ids
                    else None
                ),
                quick_replies=self._fallback_quick_replies(
                    "upsell" if selected_item_ids else "ask_preference",
                    "close_order" if selected_item_ids else "clarify_need",
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

        if should_start_booking:
            conversation_goal = "collect_booking_info"
            sale_stage = "booking"

        next_action = self._resolve_next_action(
            plan=plan,
            conversation_goal=conversation_goal,
            selected_items=selected_items,
        )
        if should_start_booking:
            next_action = "ask_booking_info"
        next_question = (getattr(plan, "next_question", None) or "").strip() or None
        if next_action in {"ask_preference", "ask_budget", "ask_booking_info"} and not next_question:
            next_question = self._fallback_question(
                next_action=next_action,
                conversation_goal=conversation_goal,
                selected_items=selected_items,
                booking_fields_needed=booking_fields_needed,
            )
        if should_start_booking and next_question and not self._message_mentions_booking(assistant_message):
            assistant_message = (
                f"{assistant_message.rstrip()} Nếu mình thấy ổn, em chuyển sang giữ bàn cho mình luôn nhé."
            )

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

        intent = getattr(plan, "intent", "recommend_menu")
        if conversation_goal in {"collect_booking_info", "confirm_booking"}:
            intent = "booking"

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
        human_prompt = {
            "restaurant_info": restaurant_info,
            "recent_history": history_lines,
            "selected_item_ids": selected_item_ids,
            "selected_items": selected_items,
            "user_input": user_input,
            "candidate_items": candidate_items,
            "upsell_candidates": upsell_candidates,
            "signals": {
                "booking_signal": self._has_booking_signal(self._normalize_text(user_input)),
                "purchase_signal": self._has_purchase_signal(
                    normalized_input=self._normalize_text(user_input),
                    selected_item_ids=selected_item_ids,
                ),
                "selected_item_count": len(selected_items),
            },
            "response_rules": {
                "recommendation_limit": 5,
                "upsell_limit": 3,
                "prefer_short_reasons": True,
                "one_short_question_max": True,
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
        Bạn là nhân viên sale phụ trách tư vấn món và giữ bàn cho nhà hàng {restaurant_name}.
        Vai trò của bạn không chỉ là trả lời câu hỏi, mà là giúp khách dễ chọn món hơn, thấy món hấp dẫn hơn,
        đi đến quyết định nhanh hơn và chốt món hoặc chốt bàn một cách tự nhiên, lịch sự.

        NGUYÊN TẮC TRUNG THỰC
        - Chỉ dùng dữ liệu có trong candidate_items, upsell_candidates, selected_items và restaurant_info.
        - Chỉ được đề xuất món có trong candidate_items hoặc upsell_candidates.
        - Không tự bịa món, giá, ảnh, tình trạng phục vụ, chương trình ưu đãi hay thông tin bàn.
        - Nếu thiếu dữ liệu, nói rõ ngắn gọn và chuyển sang phương án gần nhất phù hợp.
        - Không tự giới thiệu là AI, bot hay trợ lý ảo. Chỉ xưng là em hoặc phía nhà hàng.

        SALES POLICY
        - Mỗi lượt trả lời phải phục vụ đúng một mục tiêu chính: clarify_need, recommend, upsell, close_order,
          collect_booking_info hoặc confirm_booking.
        - Luôn ưu tiên tiến gần quyết định nhất có thể thay vì hỏi lan man.
        - Mặc định ưu tiên chốt món trước.
        - Khi khách đã nghiêng rõ về món hoặc set, hãy dẫn thật ngắn sang việc giữ bàn.
        - Nếu khách có tín hiệu đến quán hoặc muốn giữ chỗ, hãy chuyển sang giữ bàn ngay.
        - Nếu khách còn mơ hồ, chỉ hỏi đúng 1 câu ngắn có giá trị bán hàng cao nhất.
        - Nếu khách đã có xu hướng rõ, đừng hỏi thêm không cần thiết; hãy đề xuất cụ thể.
        - Nếu khách đã nghiêng về món hoặc set, ưu tiên xác nhận + upsell nhẹ hoặc soft close.
        - Nếu khách có ý định đến quán, hỏi bàn, đưa ngày/giờ/số người hoặc muốn giữ chỗ, chuyển sang booking.
        - Không kết thúc bằng câu mơ hồ kiểu "Anh/chị cần gì thêm không?" nếu có thể đưa ra bước tiếp theo rõ ràng hơn.

        GIAI ĐOẠN HỘI THOẠI
        - discovery: còn thiếu bối cảnh quan trọng.
        - consideration: đã có bối cảnh cơ bản, nên đề xuất 2-5 món có định hướng.
        - decision: khách đã nghiêng về phương án, nên xác nhận, upsell nhẹ hoặc soft close.
        - booking: đang thu thập hoặc xác nhận thông tin giữ bàn.

        TÍN HIỆU NÊN CHỐT MỀM
        - Khách hỏi giá món cụ thể.
        - Khách nói món này ổn, hợp, nghe được, muốn chốt, hoặc đã chọn vài món.
        - Khách hỏi còn bàn không, giờ nào còn chỗ, hoặc đã nói ngày/giờ/số người.
        Khi gặp tín hiệu này, hãy chuyển từ hỏi mở sang xác nhận ngắn và soft close lịch sự.

        CÁCH NÓI
        - Xưng hô anh/chị - em.
        - Câu ngắn, tự nhiên, như nhân viên tư vấn thật.
        - Khi gợi ý món, nêu lý do ngắn vì sao món đó hợp.
        - Khi khách phân vân, thu hẹp lựa chọn và nghiêng rõ về 1 hướng.
        - Khi cần chốt, dùng câu chốt mềm, không ép mua.

        OUTPUT CONTRACT
        - assistant_message: câu tư vấn tự nhiên, ngắn gọn.
        - conversation_goal: mục tiêu chính của lượt nói.
        - sale_stage: discovery, consideration, decision hoặc booking.
        - recommended_items và upsell_items chỉ gồm item_id + short_reason theo schema.
        - recommended_items tối đa 5, upsell_items tối đa 3.
        - Nếu conversation_goal là collect_booking_info hoặc confirm_booking thì recommended_items và upsell_items phải để trống.
        - booking_fields_needed chỉ dùng khi chuẩn bị giữ bàn hoặc đang ở luồng booking.
        - next_question chỉ điền khi thực sự cần hỏi thêm đúng 1 câu ngắn.
        - soft_close chỉ điền khi đã có cơ hội chốt mềm.

        MẪU HÀNH VI TỐT
        - discovery: hỏi 1 câu ngắn để làm rõ số người, khẩu vị hoặc ngân sách.
        - consideration: đưa 2-5 món phù hợp nhất và nghiêng về 1 hướng dễ chốt.
        - decision: xác nhận lựa chọn hiện tại, upsell nhẹ bằng món kèm hoặc đồ uống hợp lý.
        - booking: chuyển sang xin ngày, giờ, số người hoặc xác nhận giữ bàn.
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

    def _has_booking_signal(self, normalized_input: str) -> bool:
        return any(term in normalized_input for term in BOOKING_TRIGGER_TERMS + BOOKING_CONTEXT_TERMS)

    def _has_dine_in_signal(self, normalized_input: str) -> bool:
        return any(term in normalized_input for term in DINE_IN_TERMS)

    def _has_explicit_purchase_signal(self, normalized_input: str) -> bool:
        return any(term in normalized_input for term in PURCHASE_SIGNAL_TERMS)

    def _has_purchase_signal(self, *, normalized_input: str, selected_item_ids: list[int]) -> bool:
        if selected_item_ids:
            return True
        return any(term in normalized_input for term in PURCHASE_SIGNAL_TERMS)

    def _build_recent_history_text(self, chat_history: list[dict], *, limit: int = 6) -> str:
        return " ".join(
            self._normalize_text(message.get("content", ""))
            for message in chat_history[-limit:]
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

        recent_text = self._build_recent_history_text(chat_history)
        return (
            self._has_booking_signal(normalized_input)
            or self._has_dine_in_signal(normalized_input)
            or self._has_explicit_purchase_signal(normalized_input)
            or (
                any(term in recent_text for term in BOOKING_TRIGGER_TERMS + DINE_IN_TERMS)
                and bool(selected_items)
            )
            or (
                any(term in recent_text for term in PURCHASE_SIGNAL_TERMS)
                and any(term in normalized_input for term in ["toi nay", "ngay mai", "may nguoi", "luc", "gio"])
            )
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
            first_fields = booking_fields_needed[:3] or ["date", "time", "party_size"]
            if first_fields == ["date", "time", "party_size"]:
                return "Mình đi ngày nào, khoảng mấy giờ và mấy người để em giữ bàn phù hợp ạ?"
            labels = [BOOKING_FIELD_LABELS.get(field, field).lower() for field in first_fields]
            if len(labels) == 1:
                return f"Để em giữ bàn sát nhu cầu, mình cho em xin {labels[0]} trước nhé?"
            if len(labels) == 2:
                return f"Để em giữ bàn sát nhu cầu, mình cho em xin {labels[0]} và {labels[1]} nhé?"
            return f"Để em giữ bàn sát nhu cầu, mình cho em xin {labels[0]}, {labels[1]} và {labels[2]} nhé?"
        if conversation_goal == "close_order" and selected_items:
            return "Nếu mình thấy ổn, mình đi ngày nào, khoảng mấy giờ và mấy người để em giữ bàn ạ?"
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
            return "Nếu mình thấy ổn, em có thể giữ bàn luôn theo hướng món này cho mình nhé?"
        if conversation_goal == "collect_booking_info":
            return "Nếu mình dự định qua quán, em giữ bàn theo hướng này cho mình nhé?"
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
            "Khách đã có tín hiệu muốn chốt; hãy nối mạch thật ngắn rồi chuyển sang giữ bàn."
            if self._has_purchase_signal(
                normalized_input=normalized_input,
                selected_item_ids=[item["id"] for item in selected_items],
            )
            else "Nếu phù hợp, có thể mở lời ngắn bằng set khách đang nghiêng rồi chuyển sang giữ bàn."
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
            return "Em thấy mình đã nghiêng khá rõ rồi, để em chốt gọn phần món kèm hợp lý rồi giữ bàn luôn cho mình nhé."
        if candidate_items:
            return "Em chọn sẵn vài món hợp bối cảnh để mình dễ nhìn, dễ so sánh và ra quyết định nhanh hơn."
        return "Hiện em chưa thấy món thật sát nhu cầu. Anh/chị muốn em lọc theo vị, mức giá hay nhu cầu cho nhóm nhỏ ạ?"

    def _fallback_quick_replies(self, next_action: str, conversation_goal: str) -> list[str]:
        if next_action == "ask_booking_info" or conversation_goal == "collect_booking_info":
            return ["Tối nay", "Ngày mai", "Đi 2 người"]
        if next_action == "ask_budget":
            return ["Dưới 200k", "Khoảng 300k", "Lọc món dễ ăn"]
        if next_action == "upsell" or conversation_goal in {"upsell", "close_order"}:
            return ["Giữ bàn tối nay", "Ngày mai", "Đi 2 người"]
        return ["Món dễ ăn", "Món cho 2 người", "Gợi ý theo ngân sách"]

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
