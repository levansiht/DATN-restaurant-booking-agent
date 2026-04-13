from datetime import time
from decimal import Decimal

from django.db import migrations


DEMO_PROFILE = {
    "name": "PSCD Japanese Dining",
    "description": (
        "Nhà hàng Nhật hiện đại với thực đơn cân bằng giữa món dễ ăn, món nhóm và "
        "các lựa chọn nhẹ bụng cho khách cần tư vấn nhanh."
    ),
    "phone_number": "02873001234",
    "email": "hello@pscd-dining.local",
    "address": "12 Nguyen Hue, Ben Nghe Ward, District 1, Ho Chi Minh City",
    "opening_time": time(10, 30),
    "closing_time": time(22, 0),
    "website": "http://localhost:5173",
    "ai_greeting": (
        "Xin chào, mình là trợ lý gọi món của PSCD Japanese Dining. "
        "Bạn chỉ cần cho biết đi mấy người, mức ngân sách và khẩu vị, "
        "mình sẽ gợi ý món hợp lý và hỗ trợ đặt bàn."
    ),
    "price_range_min": Decimal("45000.00"),
    "price_range_max": Decimal("399000.00"),
    "is_active": True,
}

DEMO_CATEGORIES = [
    {
        "name": "Khai vị",
        "description": "Nhóm món nhỏ giúp bắt đầu bữa ăn nhẹ nhàng và dễ chia sẻ.",
        "display_order": 10,
    },
    {
        "name": "Sushi & Sashimi",
        "description": "Các lựa chọn tươi, dễ gọi cho cặp đôi hoặc nhóm nhỏ.",
        "display_order": 20,
    },
    {
        "name": "Món chính",
        "description": "Những món no bụng, phù hợp bữa trưa hoặc bữa tối nhanh gọn.",
        "display_order": 30,
    },
    {
        "name": "Lẩu & Nướng",
        "description": "Các món đậm vị dành cho nhóm thích ăn no và có trải nghiệm.",
        "display_order": 40,
    },
    {
        "name": "Đồ uống",
        "description": "Đồ uống cân bằng vị, dễ ghép với món chính và món nướng.",
        "display_order": 50,
    },
    {
        "name": "Tráng miệng",
        "description": "Món kết bữa nhẹ, phù hợp upsell sau khi chốt món chính.",
        "display_order": 60,
    },
]

DEMO_MENU_ITEMS = [
    {
        "category": "Khai vị",
        "name": "Edamame Muối Biển",
        "description": "Đậu nành Nhật hấp nóng, nêm muối biển nhẹ, dễ mở vị và hợp nhiều khẩu vị.",
        "price": Decimal("45000.00"),
        "status": "ACTIVE",
        "is_recommended": True,
        "is_vegetarian": True,
        "is_best_seller": False,
        "is_kid_friendly": True,
        "spicy_level": "NONE",
        "tags": ["khai vị", "nhẹ bụng", "dễ chia sẻ"],
        "dietary_labels": ["vegetarian"],
        "preparation_time_minutes": 5,
    },
    {
        "category": "Khai vị",
        "name": "Gyoza Tôm Thịt",
        "description": "Bánh xếp áp chảo nhân tôm thịt, lớp vỏ giòn nhẹ, hợp gọi mở màn cho bàn 2-4 người.",
        "price": Decimal("79000.00"),
        "status": "ACTIVE",
        "is_recommended": True,
        "is_vegetarian": False,
        "is_best_seller": True,
        "is_kid_friendly": True,
        "spicy_level": "NONE",
        "tags": ["khai vị", "bán chạy", "dễ ăn"],
        "dietary_labels": ["seafood"],
        "preparation_time_minutes": 10,
    },
    {
        "category": "Khai vị",
        "name": "Takoyaki Osaka",
        "description": "Bánh bạch tuộc sốt Nhật và cá bào, hương vị đậm vừa phải, phù hợp khách lần đầu thử.",
        "price": Decimal("85000.00"),
        "status": "ACTIVE",
        "is_recommended": False,
        "is_vegetarian": False,
        "is_best_seller": True,
        "is_kid_friendly": False,
        "spicy_level": "NONE",
        "tags": ["khai vị", "ăn chơi", "đậm vị"],
        "dietary_labels": ["seafood"],
        "preparation_time_minutes": 12,
    },
    {
        "category": "Khai vị",
        "name": "Salad Rong Biển Mè Rang",
        "description": "Salad mát vị với rong biển và mè rang, thích hợp gọi kèm món nướng để cân bằng vị.",
        "price": Decimal("69000.00"),
        "status": "ACTIVE",
        "is_recommended": True,
        "is_vegetarian": True,
        "is_best_seller": False,
        "is_kid_friendly": False,
        "spicy_level": "NONE",
        "tags": ["khai vị", "thanh nhẹ", "ít dầu mỡ"],
        "dietary_labels": ["vegetarian", "light"],
        "preparation_time_minutes": 7,
    },
    {
        "category": "Sushi & Sashimi",
        "name": "Salmon Nigiri 2 pcs",
        "description": "Hai miếng nigiri cá hồi tươi, vị béo nhẹ và dễ ăn cho khách mới thử sushi.",
        "price": Decimal("89000.00"),
        "status": "ACTIVE",
        "is_recommended": True,
        "is_vegetarian": False,
        "is_best_seller": False,
        "is_kid_friendly": False,
        "spicy_level": "NONE",
        "tags": ["sushi", "dễ ăn", "ăn thử"],
        "dietary_labels": ["seafood", "raw"],
        "preparation_time_minutes": 8,
    },
    {
        "category": "Sushi & Sashimi",
        "name": "California Roll",
        "description": "Cuộn thanh cua, bơ và dưa leo với vị cân bằng, phù hợp cả người lớn lẫn trẻ em.",
        "price": Decimal("119000.00"),
        "status": "ACTIVE",
        "is_recommended": True,
        "is_vegetarian": False,
        "is_best_seller": True,
        "is_kid_friendly": True,
        "spicy_level": "NONE",
        "tags": ["sushi", "trẻ em", "dễ ăn"],
        "dietary_labels": ["seafood"],
        "preparation_time_minutes": 10,
    },
    {
        "category": "Sushi & Sashimi",
        "name": "Combo Sashimi 3 Loại",
        "description": "Set sashimi tổng hợp dành cho 2 người, phù hợp khách muốn thử nhiều vị trong một lần gọi.",
        "price": Decimal("259000.00"),
        "status": "ACTIVE",
        "is_recommended": True,
        "is_vegetarian": False,
        "is_best_seller": True,
        "is_kid_friendly": False,
        "spicy_level": "NONE",
        "tags": ["nhóm 2 người", "premium", "chia sẻ"],
        "dietary_labels": ["seafood", "raw"],
        "preparation_time_minutes": 15,
    },
    {
        "category": "Món chính",
        "name": "Cơm Gà Teriyaki",
        "description": "Gà nướng sốt teriyaki cùng cơm Nhật, vị đậm vừa, là lựa chọn an toàn cho bữa trưa.",
        "price": Decimal("149000.00"),
        "status": "ACTIVE",
        "is_recommended": True,
        "is_vegetarian": False,
        "is_best_seller": True,
        "is_kid_friendly": True,
        "spicy_level": "NONE",
        "tags": ["món chính", "ăn no", "bữa trưa"],
        "dietary_labels": ["grill"],
        "preparation_time_minutes": 14,
        "serving_start_time": time(10, 30),
        "serving_end_time": time(14, 30),
    },
    {
        "category": "Món chính",
        "name": "Udon Hải Sản",
        "description": "Mì udon nước dùng thanh, topping hải sản vừa đủ no mà không gây ngấy.",
        "price": Decimal("159000.00"),
        "status": "ACTIVE",
        "is_recommended": True,
        "is_vegetarian": False,
        "is_best_seller": False,
        "is_kid_friendly": False,
        "spicy_level": "MILD",
        "tags": ["món nước", "thanh vị", "ăn tối"],
        "dietary_labels": ["seafood"],
        "preparation_time_minutes": 16,
    },
    {
        "category": "Món chính",
        "name": "Cà Ri Rau Củ Nhật",
        "description": "Cà ri Nhật vị dịu với rau củ hầm mềm, hợp khách ăn chay hoặc muốn món ấm bụng.",
        "price": Decimal("135000.00"),
        "status": "ACTIVE",
        "is_recommended": True,
        "is_vegetarian": True,
        "is_best_seller": False,
        "is_kid_friendly": True,
        "spicy_level": "MILD",
        "tags": ["món chính", "chay", "ấm bụng"],
        "dietary_labels": ["vegetarian"],
        "preparation_time_minutes": 15,
        "serving_start_time": time(10, 30),
        "serving_end_time": time(14, 30),
    },
    {
        "category": "Món chính",
        "name": "Cơm Lươn Unagi Don",
        "description": "Cơm lươn nướng sốt ngọt mặn, đậm vị nhưng vẫn gọn gàng cho khách đi 1-2 người.",
        "price": Decimal("229000.00"),
        "status": "ACTIVE",
        "is_recommended": True,
        "is_vegetarian": False,
        "is_best_seller": False,
        "is_kid_friendly": False,
        "spicy_level": "NONE",
        "tags": ["món chính", "đậm vị", "cao cấp"],
        "dietary_labels": ["grill"],
        "preparation_time_minutes": 18,
        "serving_start_time": time(10, 30),
        "serving_end_time": time(14, 30),
    },
    {
        "category": "Lẩu & Nướng",
        "name": "Bò Nướng Sốt Miso",
        "description": "Thịt bò nướng mềm cùng sốt miso đậm đà, phù hợp nhóm thích món mặn và dễ gọi thêm đồ uống.",
        "price": Decimal("289000.00"),
        "status": "ACTIVE",
        "is_recommended": True,
        "is_vegetarian": False,
        "is_best_seller": True,
        "is_kid_friendly": False,
        "spicy_level": "MILD",
        "tags": ["món nướng", "đậm vị", "nhóm 2-3 người"],
        "dietary_labels": ["grill"],
        "preparation_time_minutes": 20,
        "serving_start_time": time(17, 0),
        "serving_end_time": time(22, 0),
    },
    {
        "category": "Lẩu & Nướng",
        "name": "Cá Hồi Nướng Muối Koji",
        "description": "Cá hồi nướng giữ vị béo tự nhiên, hợp khách muốn món chính cân bằng và không quá nặng vị.",
        "price": Decimal("249000.00"),
        "status": "ACTIVE",
        "is_recommended": True,
        "is_vegetarian": False,
        "is_best_seller": False,
        "is_kid_friendly": False,
        "spicy_level": "NONE",
        "tags": ["món nướng", "thanh vị", "cá hồi"],
        "dietary_labels": ["seafood", "grill"],
        "preparation_time_minutes": 18,
        "serving_start_time": time(17, 0),
        "serving_end_time": time(22, 0),
    },
    {
        "category": "Lẩu & Nướng",
        "name": "Lẩu Sukiyaki 2 Người",
        "description": "Set lẩu ngọt thanh cho 2 người, có thịt, rau và mì, rất hợp khách muốn ăn no và ngồi lâu.",
        "price": Decimal("399000.00"),
        "status": "ACTIVE",
        "is_recommended": True,
        "is_vegetarian": False,
        "is_best_seller": True,
        "is_kid_friendly": False,
        "spicy_level": "NONE",
        "tags": ["lẩu", "nhóm 2 người", "ăn no"],
        "dietary_labels": ["hotpot"],
        "preparation_time_minutes": 22,
        "serving_start_time": time(17, 0),
        "serving_end_time": time(22, 0),
    },
    {
        "category": "Đồ uống",
        "name": "Yuzu Soda",
        "description": "Nước yuzu có ga mát và thơm, dễ ghép với món nướng hoặc món chiên để cân vị.",
        "price": Decimal("49000.00"),
        "status": "ACTIVE",
        "is_recommended": True,
        "is_vegetarian": True,
        "is_best_seller": True,
        "is_kid_friendly": True,
        "spicy_level": "NONE",
        "tags": ["đồ uống", "giải ngấy", "dễ ghép món"],
        "dietary_labels": ["drink", "vegetarian"],
        "preparation_time_minutes": 4,
    },
    {
        "category": "Đồ uống",
        "name": "Trà Oolong Đào",
        "description": "Trà lạnh vị đào nhẹ, phù hợp khách thích đồ uống thanh và không quá ngọt.",
        "price": Decimal("45000.00"),
        "status": "ACTIVE",
        "is_recommended": True,
        "is_vegetarian": True,
        "is_best_seller": False,
        "is_kid_friendly": True,
        "spicy_level": "NONE",
        "tags": ["đồ uống", "thanh nhẹ", "ít ngọt"],
        "dietary_labels": ["drink", "vegetarian"],
        "preparation_time_minutes": 4,
    },
    {
        "category": "Đồ uống",
        "name": "Matcha Latte",
        "description": "Matcha latte dịu, hợp khách thích vị trà sữa kiểu Nhật và muốn thêm một món tráng miệng nhẹ.",
        "price": Decimal("59000.00"),
        "status": "ACTIVE",
        "is_recommended": False,
        "is_vegetarian": True,
        "is_best_seller": False,
        "is_kid_friendly": True,
        "spicy_level": "NONE",
        "tags": ["đồ uống", "trẻ em", "ngọt nhẹ"],
        "dietary_labels": ["drink", "vegetarian"],
        "preparation_time_minutes": 6,
    },
    {
        "category": "Tráng miệng",
        "name": "Mochi Kem 3 Vị",
        "description": "Set mochi kem nhỏ gọn, dễ upsell sau bữa ăn và phù hợp nhóm đi gia đình.",
        "price": Decimal("69000.00"),
        "status": "ACTIVE",
        "is_recommended": True,
        "is_vegetarian": True,
        "is_best_seller": True,
        "is_kid_friendly": True,
        "spicy_level": "NONE",
        "tags": ["tráng miệng", "trẻ em", "dễ upsell"],
        "dietary_labels": ["dessert", "vegetarian"],
        "preparation_time_minutes": 5,
    },
    {
        "category": "Tráng miệng",
        "name": "Pudding Matcha",
        "description": "Pudding matcha mềm mịn, vị ngọt vừa, hợp khách muốn kết bữa gọn và không quá no.",
        "price": Decimal("55000.00"),
        "status": "ACTIVE",
        "is_recommended": True,
        "is_vegetarian": True,
        "is_best_seller": False,
        "is_kid_friendly": True,
        "spicy_level": "NONE",
        "tags": ["tráng miệng", "ngọt nhẹ", "kết bữa"],
        "dietary_labels": ["dessert", "vegetarian"],
        "preparation_time_minutes": 5,
    },
]

DEMO_PAIRINGS = {
    "Edamame Muối Biển": ["Yuzu Soda", "Trà Oolong Đào"],
    "Gyoza Tôm Thịt": ["Yuzu Soda", "Pudding Matcha"],
    "Takoyaki Osaka": ["Yuzu Soda"],
    "Salad Rong Biển Mè Rang": ["Cá Hồi Nướng Muối Koji", "Combo Sashimi 3 Loại"],
    "Salmon Nigiri 2 pcs": ["Trà Oolong Đào"],
    "California Roll": ["Matcha Latte", "Mochi Kem 3 Vị"],
    "Combo Sashimi 3 Loại": ["Trà Oolong Đào", "Yuzu Soda"],
    "Cơm Gà Teriyaki": ["Trà Oolong Đào", "Pudding Matcha"],
    "Udon Hải Sản": ["Yuzu Soda"],
    "Cà Ri Rau Củ Nhật": ["Salad Rong Biển Mè Rang", "Yuzu Soda"],
    "Cơm Lươn Unagi Don": ["Trà Oolong Đào", "Mochi Kem 3 Vị"],
    "Bò Nướng Sốt Miso": ["Yuzu Soda", "Mochi Kem 3 Vị"],
    "Cá Hồi Nướng Muối Koji": ["Salad Rong Biển Mè Rang", "Trà Oolong Đào"],
    "Lẩu Sukiyaki 2 Người": ["Trà Oolong Đào", "Pudding Matcha"],
}


def _get_first_by_name(model, name):
    return model.objects.filter(is_deleted=False, name=name).order_by("id").first()


def seed_demo_restaurant_menu(apps, schema_editor):
    RestaurantProfile = apps.get_model("restaurant_booking", "RestaurantProfile")
    MenuCategory = apps.get_model("restaurant_booking", "MenuCategory")
    MenuItem = apps.get_model("restaurant_booking", "MenuItem")

    active_profile = (
        RestaurantProfile.objects.filter(is_deleted=False, is_active=True).order_by("id").first()
    )
    if active_profile is None:
        active_profile = RestaurantProfile.objects.create(**DEMO_PROFILE)

    should_seed_items = not MenuItem.objects.filter(is_deleted=False).exists()
    categories_by_name = {}

    if should_seed_items:
        for category_data in DEMO_CATEGORIES:
            category = _get_first_by_name(MenuCategory, category_data["name"])
            if category is None:
                category = MenuCategory.objects.create(
                    name=category_data["name"],
                    description=category_data["description"],
                    display_order=category_data["display_order"],
                    is_active=True,
                )
            elif not category.is_active:
                category.is_active = True
                category.save(update_fields=["is_active", "updated_at"])
            categories_by_name[category.name] = category

        items_by_name = {}
        for item_data in DEMO_MENU_ITEMS:
            item = _get_first_by_name(MenuItem, item_data["name"])
            if item is None:
                item = MenuItem.objects.create(
                    category=categories_by_name.get(item_data["category"]),
                    name=item_data["name"],
                    description=item_data["description"],
                    price=item_data["price"],
                    status=item_data["status"],
                    is_recommended=item_data["is_recommended"],
                    is_vegetarian=item_data["is_vegetarian"],
                    is_best_seller=item_data["is_best_seller"],
                    is_kid_friendly=item_data["is_kid_friendly"],
                    spicy_level=item_data["spicy_level"],
                    tags=item_data["tags"],
                    dietary_labels=item_data["dietary_labels"],
                    preparation_time_minutes=item_data["preparation_time_minutes"],
                    serving_start_time=item_data.get("serving_start_time"),
                    serving_end_time=item_data.get("serving_end_time"),
                )
            items_by_name[item.name] = item

        for source_name, target_names in DEMO_PAIRINGS.items():
            source_item = items_by_name.get(source_name)
            if source_item is None:
                continue
            for target_name in target_names:
                target_item = items_by_name.get(target_name)
                if target_item is not None and target_item.id != source_item.id:
                    source_item.suggested_pairings.add(target_item)

    if active_profile.price_range_min is None:
        active_profile.price_range_min = DEMO_PROFILE["price_range_min"]
    if active_profile.price_range_max is None:
        active_profile.price_range_max = DEMO_PROFILE["price_range_max"]
    active_profile.save(update_fields=["price_range_min", "price_range_max", "updated_at"])


class Migration(migrations.Migration):

    dependencies = [
        ("restaurant_booking", "0008_menucategory_default_image_alt_text_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_demo_restaurant_menu, migrations.RunPython.noop),
    ]
