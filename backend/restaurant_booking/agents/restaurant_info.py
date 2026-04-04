from typing import Any, List, Optional

from langchain_core.tools import StructuredTool
from django.db.models import Q

from restaurant_booking.agents.io_models.input import (
    BudgetSuggestionInput,
    MenuSearchInput,
    RestaurantInfoInput,
)
from restaurant_booking.models import MenuItem, RestaurantProfile


class RestaurantKnowledgeService:
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
        items = MenuItem.objects.filter(
            is_deleted=False,
            status=MenuItem.AvailabilityStatus.ACTIVE,
        ).select_related("category")

        if query:
            items = items.filter(name__icontains=query)
        if max_price is not None:
            items = items.filter(price__lte=max_price)
        if is_vegetarian is not None:
            items = items.filter(is_vegetarian=is_vegetarian)
        if recommended_only:
            items = items.filter(is_recommended=True)

        results = [
            {
                "id": item.id,
                "name": item.name,
                "category": item.category.name if item.category else None,
                "price": item.price,
                "description": item.description,
                "is_recommended": item.is_recommended,
                "is_vegetarian": item.is_vegetarian,
                "preparation_time_minutes": item.preparation_time_minutes,
            }
            for item in items.order_by("price", "name", "id")[:10]
        ]

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

        items = MenuItem.objects.filter(
            is_deleted=False,
            status=MenuItem.AvailabilityStatus.ACTIVE,
        ).select_related("category")

        if preference:
            items = items.filter(
                Q(name__icontains=preference) | Q(description__icontains=preference)
            )

        estimated_budget_per_item = budget / max(int(party_size or 1), 1)
        shortlisted = items.filter(price__lte=estimated_budget_per_item).order_by(
            "-is_recommended",
            "price",
            "name",
        )[:5]

        suggestions = [
            {
                "id": item.id,
                "name": item.name,
                "price": item.price,
                "category": item.category.name if item.category else None,
                "reason": (
                    f"Phù hợp mức {estimated_budget_per_item:.0f} mỗi người"
                    + (" và bám khẩu vị đã nêu." if preference else ".")
                ),
            }
            for item in shortlisted
        ]

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
