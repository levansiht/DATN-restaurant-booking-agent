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


BOOKING_TERMS = (
    "dat ban",
    "giu ban",
    "con ban",
    "ban trong",
    "table",
    "booking",
    "may nguoi",
    "luc",
    "toi nay",
    "ngay mai",
    "hom nay",
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
    assistant_message: str = Field(..., max_length=700)
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
    question_to_user: Optional[str] = Field(default=None, max_length=200)
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
        route = self._route_request(user_input=user_input, chat_history=chat_history)
        if route == "booking":
            return self._build_booking_payload(user_input=user_input, chat_history=chat_history)
        return self._build_sales_payload(
            user_input=user_input,
            chat_history=chat_history,
            selected_item_ids=selected_item_ids,
        )

    def _route_request(self, *, user_input: str, chat_history: list[dict]) -> str:
        normalized_input = self._normalize_text(user_input)
        if any(term in normalized_input for term in MENU_TERMS):
            return "sales"
        if any(term in normalized_input for term in BOOKING_TERMS):
            return "booking"

        recent_text = " ".join(
            self._normalize_text(message.get("content", ""))
            for message in chat_history[-4:]
        )
        if any(term in recent_text for term in BOOKING_TERMS):
            return "booking"
        return "sales"

    def _build_booking_payload(self, *, user_input: str, chat_history: list[dict]) -> dict:
        booking_agent = RestaurantBookingAgent(callbacks=None, queue=None)
        self._load_chat_history_into_agent_memory(booking_agent.agent, chat_history)
        result = booking_agent.run(user_input)
        assistant_message = result.get("output") if isinstance(result, dict) else str(result)
        next_action = "ask_booking_info"
        if "ma dat ban" in self._normalize_text(assistant_message):
            next_action = "confirm_booking"
        return {
            "intent": "booking",
            "assistant_message": assistant_message,
            "recommended_items": [],
            "upsell_items": [],
            "next_action": next_action,
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
                selected_item_ids=selected_item_ids,
            )
        except Exception:
            plan = SalesChatPlan(
                intent="upsell" if selected_item_ids else "recommend_menu",
                assistant_message=self._fallback_message(candidate_items, selected_item_ids),
                next_action="upsell" if selected_item_ids else "ask_preference",
                quick_replies=self._fallback_quick_replies(
                    "upsell" if selected_item_ids else "ask_preference"
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

        quick_replies = [reply.strip() for reply in getattr(plan, "quick_replies", []) if reply.strip()][:4]
        if not quick_replies:
            quick_replies = self._fallback_quick_replies(plan.next_action if plan else "ask_preference")

        question_to_user = getattr(plan, "question_to_user", None)
        if not question_to_user and plan.next_action in {"ask_preference", "ask_budget"}:
            question_to_user = "Anh/chị nghiêng về vị đậm, thanh nhẹ hay muốn chốt theo ngân sách ạ?"

        return {
            "intent": getattr(plan, "intent", "recommend_menu"),
            "assistant_message": assistant_message,
            "recommended_items": recommended_items,
            "upsell_items": upsell_items,
            "next_action": getattr(plan, "next_action", "ask_preference"),
            "question_to_user": question_to_user,
            "quick_replies": quick_replies,
        }

    def _invoke_structured_plan(
        self,
        *,
        user_input: str,
        chat_history: list[dict],
        restaurant_info: dict,
        candidate_items: list[dict],
        upsell_candidates: list[dict],
        selected_item_ids: list[int],
    ) -> SalesChatPlan:
        history_lines = []
        for message in chat_history[-6:]:
            role = "Khách" if message.get("role") == "user" else "Trợ lý"
            history_lines.append(f"{role}: {message.get('content', '')}")

        system_prompt = """
        Bạn là trợ lý tư vấn món ăn kiêm sale cho nhà hàng PSCD.
        Mục tiêu:
        - Tư vấn như nhân viên thật, chủ động hỏi lại rất ngắn gọn.
        - Chỉ được đề xuất món có trong candidate list.
        - Tuyệt đối không tự bịa giá, ảnh, tình trạng món.
        - Gợi ý tối đa 5 món chính và tối đa 3 món upsell.
        - Nếu chưa đủ thông tin, đặt 1 câu hỏi tiếp theo thật ngắn.
        - Nếu khách đã có món nghiêng về, ưu tiên upsell nhẹ bằng món ăn kèm/đồ uống/tráng miệng.
        - Văn phong thân thiện, lịch sự, ngắn gọn, theo kiểu anh/chị - em.
        """
        human_prompt = {
            "restaurant_info": restaurant_info,
            "recent_history": history_lines,
            "selected_item_ids": selected_item_ids,
            "user_input": user_input,
            "candidate_items": candidate_items,
            "upsell_candidates": upsell_candidates,
            "response_rules": {
                "recommendation_limit": 5,
                "upsell_limit": 3,
                "prefer_short_reasons": True,
            },
        }
        return self.structured_llm.invoke(
            [
                SystemMessage(content=system_prompt.strip()),
                HumanMessage(content=json.dumps(human_prompt, ensure_ascii=False)),
            ]
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
            return "Em đã nhìn thấy mình đang nghiêng về vài món rồi, để em gợi ý thêm đồ ăn kèm để bàn ăn cân bằng hơn."
        if candidate_items:
            return "Em chọn sẵn vài món để mình dễ nhìn và dễ ra quyết định hơn, ưu tiên món dễ ăn và hợp bối cảnh hiện tại."
        return "Hiện em chưa thấy món thật sát nhu cầu. Anh/chị muốn em lọc theo vị, mức giá hay nhu cầu cho nhóm nhỏ ạ?"

    def _fallback_quick_replies(self, next_action: str) -> list[str]:
        if next_action == "ask_budget":
            return ["Dưới 200k", "Khoảng 300k", "Tư vấn món dễ ăn"]
        if next_action == "upsell":
            return ["Thêm món ăn kèm", "Gọi thêm đồ uống", "Chốt bàn giúp mình"]
        return ["Món ít cay", "Món cho 2 người", "Gợi ý theo ngân sách"]

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
