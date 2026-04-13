from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Iterable, Optional
from urllib.parse import quote

from django.db.models import Prefetch, QuerySet

from restaurant_booking.models import MenuCategory, MenuItem


GENERIC_MENU_IMAGE = "generic"


def parse_bool_param(value):
    if value is None or value == "":
        return None
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return None


def normalize_text_list(values: Optional[Iterable[str]]) -> list[str]:
    normalized: list[str] = []
    for raw_value in values or []:
        value = str(raw_value or "").strip()
        if value and value not in normalized:
            normalized.append(value)
    return normalized


def parse_text_list_param(value: Optional[str]) -> list[str]:
    if not value:
        return []
    return normalize_text_list(part for part in str(value).split(","))


def parse_decimal_param(value: Optional[str]) -> Optional[Decimal]:
    if value in {None, ""}:
        return None
    sanitized = (
        str(value)
        .replace("VND", "")
        .replace("vnd", "")
        .replace("đ", "")
        .replace(",", "")
        .strip()
    )
    try:
        return Decimal(sanitized)
    except (InvalidOperation, TypeError):
        return None


def _pick_placeholder_tone(category_name: Optional[str]) -> tuple[str, str]:
    label = (category_name or "").lower()
    if any(keyword in label for keyword in ["khai", "starter", "appet"]):
        return "#f5d0a8", "#a04725"
    if any(keyword in label for keyword in ["trang", "dessert", "sweet"]):
        return "#f3d4dd", "#9a4f67"
    if any(keyword in label for keyword in ["uong", "drink", "beverage"]):
        return "#c9e6ef", "#2f6b82"
    if any(keyword in label for keyword in ["nuong", "grill", "main", "chinh"]):
        return "#f0c39a", "#7f2d1f"
    if any(keyword in label for keyword in ["lau", "hotpot", "soup"]):
        return "#d3d6f5", "#4b548f"
    return "#eadcc6", "#6f4b33"


def build_menu_placeholder_data_uri(title: str, category_name: Optional[str] = None) -> str:
    accent_start, accent_end = _pick_placeholder_tone(category_name)
    safe_title = (title or "PSCD").strip()[:28]
    safe_category = (category_name or "PSCD Dining").strip()[:26]
    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 480" role="img" aria-label="{safe_title}">
      <defs>
        <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="{accent_start}" />
          <stop offset="100%" stop-color="{accent_end}" />
        </linearGradient>
      </defs>
      <rect width="640" height="480" rx="32" fill="url(#bg)" />
      <circle cx="502" cy="116" r="88" fill="rgba(255,255,255,0.18)" />
      <circle cx="152" cy="390" r="112" fill="rgba(255,255,255,0.12)" />
      <rect x="104" y="112" width="432" height="256" rx="40" fill="rgba(255,255,255,0.16)" />
      <text x="320" y="220" text-anchor="middle" font-size="46" font-family="Georgia, serif" fill="#fffaf2">
        {safe_title}
      </text>
      <text x="320" y="282" text-anchor="middle" font-size="22" font-family="Arial, sans-serif" fill="rgba(255,250,242,0.88)">
        {safe_category}
      </text>
      <text x="320" y="338" text-anchor="middle" font-size="18" font-family="Arial, sans-serif" fill="rgba(255,250,242,0.78)">
        Hinh minh hoa menu
      </text>
    </svg>
    """
    return f"data:image/svg+xml;charset=UTF-8,{quote(svg.strip())}"


def resolve_menu_image_payload(item: MenuItem) -> dict:
    category = getattr(item, "category", None)
    if item.image_url:
        return {
            "image_url": item.image_url,
            "image_alt_text": item.image_alt_text or f"Mon {item.name}",
            "image_source": "item",
            "image_badge": "Hinh minh hoa" if item.is_illustration else None,
            "has_real_image": not item.is_illustration,
        }

    if category and category.default_image_url:
        return {
            "image_url": category.default_image_url,
            "image_alt_text": (
                item.image_alt_text
                or category.default_image_alt_text
                or f"Hinh minh hoa cho mon {item.name}"
            ),
            "image_source": "category_default",
            "image_badge": "Hinh minh hoa",
            "has_real_image": False,
        }

    return {
        "image_url": build_menu_placeholder_data_uri(item.name, category.name if category else None),
        "image_alt_text": item.image_alt_text or f"Hinh minh hoa cho mon {item.name}",
        "image_source": GENERIC_MENU_IMAGE,
        "image_badge": "Hinh minh hoa",
        "has_real_image": False,
    }


def build_menu_badges(item: MenuItem) -> list[str]:
    badges: list[str] = []
    if item.is_best_seller:
        badges.append("Best seller")
    if item.is_recommended:
        badges.append("Goi y")
    if item.is_vegetarian:
        badges.append("Chay")
    if item.is_kid_friendly:
        badges.append("Tre em")
    spicy_labels = {
        MenuItem.SpicyLevel.MILD: "It cay",
        MenuItem.SpicyLevel.MEDIUM: "Cay vua",
        MenuItem.SpicyLevel.HOT: "Cay",
    }
    spicy_badge = spicy_labels.get(item.spicy_level)
    if spicy_badge:
        badges.append(spicy_badge)
    badges.extend(normalize_text_list(item.tags))
    return badges


class MenuCatalogService:
    def base_queryset(self) -> QuerySet[MenuItem]:
        return (
            MenuItem.objects.filter(is_deleted=False)
            .select_related("category")
            .prefetch_related(
                Prefetch(
                    "suggested_pairings",
                    queryset=MenuItem.objects.filter(is_deleted=False).select_related("category"),
                )
            )
            .order_by("category__display_order", "name", "id")
        )

    def active_queryset(self) -> QuerySet[MenuItem]:
        return self.base_queryset().filter(status=MenuItem.AvailabilityStatus.ACTIVE)

    def category_queryset(self) -> QuerySet[MenuCategory]:
        return MenuCategory.objects.filter(is_deleted=False, is_active=True).order_by(
            "display_order",
            "name",
            "id",
        )

    def filter_items(
        self,
        *,
        query: Optional[str] = None,
        category_id: Optional[str] = None,
        vegetarian: Optional[bool] = None,
        recommended: Optional[bool] = None,
        best_seller: Optional[bool] = None,
        kid_friendly: Optional[bool] = None,
        spicy_level: Optional[str] = None,
        max_price: Optional[Decimal] = None,
        tags: Optional[Iterable[str]] = None,
        served_now: Optional[bool] = None,
        include_inactive: bool = False,
        limit: Optional[int] = None,
    ) -> list[MenuItem]:
        queryset = self.base_queryset() if include_inactive else self.active_queryset()

        if query:
            queryset = queryset.filter(name__icontains=query.strip())
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if vegetarian is True:
            queryset = queryset.filter(is_vegetarian=True)
        if recommended is True:
            queryset = queryset.filter(is_recommended=True)
        if best_seller is True:
            queryset = queryset.filter(is_best_seller=True)
        if kid_friendly is True:
            queryset = queryset.filter(is_kid_friendly=True)
        if spicy_level:
            queryset = queryset.filter(spicy_level=spicy_level)
        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)

        items = list(queryset)
        normalized_tags = {tag.lower() for tag in normalize_text_list(tags)}
        if normalized_tags:
            items = [
                item
                for item in items
                if normalized_tags.issubset({tag.lower() for tag in normalize_text_list(item.tags)})
            ]
        if served_now is True:
            items = [item for item in items if item.is_currently_served]
        if limit is not None:
            items = items[:limit]
        return items

    def serialize_category(self, category: MenuCategory) -> dict:
        fallback_image = (
            category.default_image_url
            or build_menu_placeholder_data_uri(category.name, category.name)
        )
        return {
            "id": category.id,
            "name": category.name,
            "description": category.description,
            "display_order": category.display_order,
            "default_image_url": fallback_image,
            "default_image_alt_text": (
                category.default_image_alt_text
                or f"Hinh minh hoa danh muc {category.name}"
            ),
            "is_active": category.is_active,
        }

    def serialize_menu_item(self, item: MenuItem) -> dict:
        image_payload = resolve_menu_image_payload(item)
        suggested_pairings = [
            {
                "id": pairing.id,
                "name": pairing.name,
                "price": pairing.price,
            }
            for pairing in getattr(item, "suggested_pairings").all()
            if not pairing.is_deleted and pairing.status == MenuItem.AvailabilityStatus.ACTIVE
        ]
        return {
            "id": item.id,
            "category": item.category_id,
            "category_name": item.category.name if item.category else None,
            "name": item.name,
            "description": item.description,
            "short_description": (item.description or "").strip()[:140],
            "price": item.price,
            "status": item.status,
            "is_recommended": item.is_recommended,
            "is_vegetarian": item.is_vegetarian,
            "is_best_seller": item.is_best_seller,
            "is_kid_friendly": item.is_kid_friendly,
            "spicy_level": item.spicy_level,
            "tags": normalize_text_list(item.tags),
            "dietary_labels": normalize_text_list(item.dietary_labels),
            "badges": build_menu_badges(item),
            "preparation_time_minutes": item.preparation_time_minutes,
            "serving_start_time": item.serving_start_time.strftime("%H:%M")
            if item.serving_start_time
            else None,
            "serving_end_time": item.serving_end_time.strftime("%H:%M")
            if item.serving_end_time
            else None,
            "is_currently_served": item.is_currently_served,
            "suggested_pairings": suggested_pairings,
            **image_payload,
        }

    def serialize_catalog(
        self,
        *,
        query: Optional[str] = None,
        category_id: Optional[str] = None,
        vegetarian: Optional[bool] = None,
        recommended: Optional[bool] = None,
        best_seller: Optional[bool] = None,
        kid_friendly: Optional[bool] = None,
        spicy_level: Optional[str] = None,
        max_price: Optional[Decimal] = None,
        tags: Optional[Iterable[str]] = None,
        served_now: Optional[bool] = None,
    ) -> dict:
        items = self.filter_items(
            query=query,
            category_id=category_id,
            vegetarian=vegetarian,
            recommended=recommended,
            best_seller=best_seller,
            kid_friendly=kid_friendly,
            spicy_level=spicy_level,
            max_price=max_price,
            tags=tags,
            served_now=served_now,
        )
        categories = [self.serialize_category(category) for category in self.category_queryset()]
        return {
            "categories": categories,
            "items": [self.serialize_menu_item(item) for item in items],
            "meta": {
                "count": len(items),
                "selected_filters": {
                    "query": query or "",
                    "category": category_id or "",
                    "vegetarian": vegetarian,
                    "recommended": recommended,
                    "best_seller": best_seller,
                    "kid_friendly": kid_friendly,
                    "spicy_level": spicy_level or "",
                    "max_price": str(max_price) if max_price is not None else "",
                    "tags": list(normalize_text_list(tags)),
                    "served_now": served_now,
                },
            },
        }
