from typing import Any, List, Optional

from langchain_core.tools import StructuredTool

from restaurant_booking.agents.io_models.input import (
    BudgetSuggestionInput,
    MenuSearchInput,
    RestaurantInfoInput,
)
from restaurant_booking.models import RestaurantProfile
from restaurant_booking.services.menu_catalog import MenuCatalogService


class RestaurantKnowledgeService:
    def __init__(self):
        self.catalog_service = MenuCatalogService()

    def _fallback_profile(self):
        return {
            "name": "PSCD Restaurant",
            "address": "Lô A4-13, Nguyễn Sinh Sắc, Hòa Khánh, Đà Nẵng",
            "phone_number": "0906.906.906",
            "email": "pscds@gmail.com",
            "opening_time": "10:00",
            "closing_time": "22:00",
            "website": "pscd.com",
            "description": (
                "Phong cách hiện đại, ẩm thực Á-Âu, có khu VIP, ngoài trời và dịch vụ tiệc."
            ),
            "price_range_min": None,
            "price_range_max": None,
        }

    def _serialize_profile(self, profile):
        if not profile:
            return self._fallback_profile()

        return {
            "name": profile.name,
            "address": profile.address,
            "phone_number": profile.phone_number,
            "email": profile.email,
            "opening_time": profile.opening_time.strftime("%H:%M")
            if profile.opening_time
            else None,
            "closing_time": profile.closing_time.strftime("%H:%M")
            if profile.closing_time
            else None,
            "website": profile.website,
            "description": profile.description,
            "ai_greeting": profile.ai_greeting,
            "price_range_min": profile.price_range_min,
            "price_range_max": profile.price_range_max,
        }

    def _get_restaurant_info(self, topic: Optional[str] = None):
        profile = RestaurantProfile.get_active_profile()
        info = self._serialize_profile(profile)

        if not topic:
            return info

        topic_lower = topic.lower()
        if "giờ" in topic_lower or "open" in topic_lower or "close" in topic_lower:
            return {
                "opening_time": info.get("opening_time"),
                "closing_time": info.get("closing_time"),
            }
        if "địa chỉ" in topic_lower or "address" in topic_lower or "ở đâu" in topic_lower:
            return {
                "name": info.get("name"),
                "address": info.get("address"),
            }
        if "liên hệ" in topic_lower or "phone" in topic_lower or "email" in topic_lower:
            return {
                "phone_number": info.get("phone_number"),
                "email": info.get("email"),
                "website": info.get("website"),
            }
        if "giá" in topic_lower or "khoảng giá" in topic_lower or "price" in topic_lower:
            return {
                "price_range_min": info.get("price_range_min"),
                "price_range_max": info.get("price_range_max"),
            }
        return info

    def _search_menu_items(
        self,
        query: Optional[str] = None,
        max_price: Optional[float] = None,
        is_vegetarian: Optional[bool] = None,
        recommended_only: Optional[bool] = False,
    ):
        items = self.catalog_service.filter_items(
            query=query,
            max_price=max_price,
            vegetarian=is_vegetarian,
            recommended=recommended_only,
            limit=10,
        )
        results = [self.catalog_service.serialize_menu_item(item) for item in items]

        if not results:
            return "Chưa tìm thấy món phù hợp trong menu hiện tại."
        return results

    def _suggest_menu_by_budget(
        self,
        budget: float,
        party_size: Optional[int] = 1,
        preference: Optional[str] = None,
    ):
        if budget <= 0:
            return "Ngân sách phải lớn hơn 0."

        estimated_budget_per_item = budget / max(int(party_size or 1), 1)
        items = self.catalog_service.filter_items(
            query=preference,
            max_price=estimated_budget_per_item,
            limit=5,
        )
        suggestions = []
        for item in items:
            payload = self.catalog_service.serialize_menu_item(item)
            payload["reason"] = (
                f"Phù hợp mức {estimated_budget_per_item:.0f} mỗi người"
                + (" và bám khẩu vị đã nêu." if preference else ".")
            )
            suggestions.append(payload)

        if not suggestions:
            return "Hiện chưa có món phù hợp đúng mức ngân sách này. Có thể tăng ngân sách hoặc nới tiêu chí."
        return suggestions

    def create_tools(self) -> List[Any]:
        return [
            StructuredTool.from_function(
                func=self._get_restaurant_info,
                name="get_restaurant_info",
                description=(
                    "Tra cứu thông tin nhà hàng như địa chỉ, giờ mở cửa, liên hệ, mô tả, khoảng giá."
                ),
                args_schema=RestaurantInfoInput,
            ),
            StructuredTool.from_function(
                func=self._search_menu_items,
                name="search_menu_items",
                description=(
                    "Tìm món trong menu theo tên, giá tối đa, món chay hoặc món gợi ý."
                ),
                args_schema=MenuSearchInput,
            ),
            StructuredTool.from_function(
                func=self._suggest_menu_by_budget,
                name="suggest_menu_by_budget",
                description=(
                    "Gợi ý món theo ngân sách, số người và khẩu vị nếu người dùng hỏi tư vấn món."
                ),
                args_schema=BudgetSuggestionInput,
            ),
        ]
