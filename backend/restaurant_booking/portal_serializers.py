from decimal import Decimal

from rest_framework import serializers

from restaurant_booking.models import (
    Invoice,
    MenuCategory,
    MenuItem,
    Order,
    OrderItem,
    Payment,
    RestaurantProfile,
    SessionTable,
    Table,
    TableSession,
)


class RestaurantProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestaurantProfile
        fields = [
            "id",
            "name",
            "description",
            "phone_number",
            "email",
            "address",
            "opening_time",
            "closing_time",
            "website",
            "ai_greeting",
            "price_range_min",
            "price_range_max",
            "public_booking_fee_amount",
            "chatbot_booking_fee_amount",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class MenuCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuCategory
        fields = [
            "id",
            "name",
            "description",
            "display_order",
            "is_active",
            "default_image_url",
            "default_image_alt_text",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class MenuItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    suggested_pairings = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=MenuItem.objects.filter(is_deleted=False),
        required=False,
    )
    suggested_pairing_items = serializers.SerializerMethodField()

    class Meta:
        model = MenuItem
        fields = [
            "id",
            "category",
            "category_name",
            "name",
            "description",
            "price",
            "status",
            "is_recommended",
            "is_vegetarian",
            "is_best_seller",
            "is_kid_friendly",
            "image_url",
            "image_alt_text",
            "is_illustration",
            "spicy_level",
            "tags",
            "dietary_labels",
            "preparation_time_minutes",
            "serving_start_time",
            "serving_end_time",
            "suggested_pairings",
            "suggested_pairing_items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_suggested_pairing_items(self, obj):
        queryset = obj.suggested_pairings.filter(is_deleted=False).order_by("name", "id")
        return [
            {
                "id": item.id,
                "name": item.name,
                "price": item.price,
            }
            for item in queryset
        ]

    def validate_tags(self, value):
        if value is None:
            return []
        return [str(tag).strip() for tag in value if str(tag).strip()]

    def validate_dietary_labels(self, value):
        if value is None:
            return []
        return [str(label).strip() for label in value if str(label).strip()]

    def validate_suggested_pairings(self, value):
        instance_id = getattr(self.instance, "id", None)
        return [item for item in value if item.id != instance_id]


class SessionTableSerializer(serializers.ModelSerializer):
    table_type = serializers.CharField(source="table.table_type", read_only=True)
    table_type_label = serializers.CharField(source="table.get_table_type_display", read_only=True)
    table_floor = serializers.IntegerField(source="table.floor", read_only=True)
    table_capacity = serializers.IntegerField(source="table.capacity", read_only=True)

    class Meta:
        model = SessionTable
        fields = [
            "id",
            "table",
            "table_type",
            "table_type_label",
            "table_floor",
            "table_capacity",
            "role",
            "is_active",
            "assigned_at",
            "released_at",
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    line_total = serializers.SerializerMethodField()
    menu_item_name = serializers.CharField(source="menu_item.name", read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "menu_item",
            "menu_item_name",
            "item_name",
            "quantity",
            "unit_price",
            "line_total",
            "kitchen_status",
            "note",
            "created_at",
            "updated_at",
        ]

    def get_line_total(self, obj):
        return obj.line_total


class OrderSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()
    subtotal_amount = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "table_session",
            "code",
            "status",
            "notes",
            "created_by",
            "created_by_name",
            "subtotal_amount",
            "sent_to_kitchen_at",
            "closed_at",
            "created_at",
            "updated_at",
            "items",
        ]

    def get_items(self, obj):
        items = getattr(obj, "items", None)
        if items is None:
            return []
        queryset = items.filter(is_deleted=False).order_by("created_at", "id")
        return OrderItemSerializer(queryset, many=True).data

    def get_subtotal_amount(self, obj):
        return obj.subtotal_amount


class PaymentSerializer(serializers.ModelSerializer):
    paid_by_name = serializers.CharField(source="paid_by.full_name", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "table_session",
            "code",
            "status",
            "method",
            "subtotal_amount",
            "surcharge_amount",
            "total_amount",
            "card_surcharge_rate",
            "note",
            "paid_at",
            "paid_by",
            "paid_by_name",
            "created_at",
            "updated_at",
        ]


class InvoiceSerializer(serializers.ModelSerializer):
    issued_by_name = serializers.CharField(source="issued_by.full_name", read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id",
            "invoice_number",
            "table_session",
            "payment",
            "issued_at",
            "issued_by",
            "issued_by_name",
            "customer_name",
            "subtotal_amount",
            "surcharge_amount",
            "total_amount",
            "note",
            "created_at",
            "updated_at",
        ]


class TableSessionSerializer(serializers.ModelSerializer):
    session_tables = serializers.SerializerMethodField()
    orders = serializers.SerializerMethodField()
    payments = serializers.SerializerMethodField()
    invoice = serializers.SerializerMethodField()
    booking_code = serializers.CharField(source="booking.code", read_only=True)
    opened_by_name = serializers.CharField(source="opened_by.full_name", read_only=True)
    closed_by_name = serializers.CharField(source="closed_by.full_name", read_only=True)
    subtotal_amount = serializers.SerializerMethodField()

    class Meta:
        model = TableSession
        fields = [
            "id",
            "booking",
            "booking_code",
            "code",
            "guest_name",
            "guest_phone",
            "guest_count",
            "opened_at",
            "closed_at",
            "opened_by",
            "opened_by_name",
            "closed_by",
            "closed_by_name",
            "status",
            "notes",
            "created_at",
            "updated_at",
            "subtotal_amount",
            "session_tables",
            "orders",
            "payments",
            "invoice",
        ]

    def get_session_tables(self, obj):
        queryset = obj.session_tables.filter(is_deleted=False).select_related("table").order_by(
            "-is_active",
            "assigned_at",
            "id",
        )
        return SessionTableSerializer(queryset, many=True).data

    def get_orders(self, obj):
        queryset = obj.orders.filter(is_deleted=False).prefetch_related("items").order_by(
            "-created_at",
            "-id",
        )
        return OrderSerializer(queryset, many=True).data

    def get_payments(self, obj):
        queryset = obj.payments.filter(is_deleted=False).order_by("-created_at", "-id")
        return PaymentSerializer(queryset, many=True).data

    def get_invoice(self, obj):
        try:
            invoice = obj.invoice
        except Invoice.DoesNotExist:
            return None

        if not invoice or invoice.is_deleted:
            return None
        return InvoiceSerializer(invoice).data

    def get_subtotal_amount(self, obj):
        total = sum(
            (
                item.line_total
                for order in obj.orders.filter(is_deleted=False)
                for item in order.items.filter(is_deleted=False)
                if item.kitchen_status != OrderItem.KitchenStatus.CANCELLED
            ),
            Decimal("0.00"),
        )
        return total


class TableSessionCreateSerializer(serializers.Serializer):
    table_ids = serializers.ListField(child=serializers.IntegerField(min_value=1), min_length=1)
    guest_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    guest_phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    guest_count = serializers.IntegerField(min_value=1, required=False, default=1)
    booking_id = serializers.IntegerField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class TableSessionUpdateSerializer(serializers.Serializer):
    guest_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    guest_phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    guest_count = serializers.IntegerField(min_value=1, required=False)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class SessionMergeTableSerializer(serializers.Serializer):
    table_id = serializers.IntegerField(min_value=1)


class SessionMoveTableSerializer(serializers.Serializer):
    from_table_id = serializers.IntegerField(min_value=1)
    to_table_id = serializers.IntegerField(min_value=1)


class OrderCreateSerializer(serializers.Serializer):
    table_session_id = serializers.IntegerField(min_value=1)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class OrderUpdateSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    status = serializers.ChoiceField(choices=Order.OrderStatus.choices, required=False)


class OrderItemCreateSerializer(serializers.Serializer):
    menu_item_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class OrderItemUpdateSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1, required=False)
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class OrderSplitItemSerializer(serializers.Serializer):
    order_item_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)
    target_order_id = serializers.IntegerField(required=False, allow_null=True)


class OrderMergeSerializer(serializers.Serializer):
    source_order_id = serializers.IntegerField(min_value=1)
    target_order_id = serializers.IntegerField(min_value=1)


class CheckoutSerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=Payment.PaymentMethod.choices)
    issue_invoice = serializers.BooleanField(required=False, default=True)
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class PublicRestaurantProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestaurantProfile
        fields = [
            "name",
            "description",
            "phone_number",
            "email",
            "address",
            "opening_time",
            "closing_time",
            "website",
            "ai_greeting",
            "price_range_min",
            "price_range_max",
            "public_booking_fee_amount",
            "chatbot_booking_fee_amount",
        ]


class PublicMenuItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    tags = serializers.ListField(read_only=True)
    dietary_labels = serializers.ListField(read_only=True)

    class Meta:
        model = MenuItem
        fields = [
            "id",
            "category",
            "category_name",
            "name",
            "description",
            "price",
            "status",
            "is_recommended",
            "is_vegetarian",
            "is_best_seller",
            "is_kid_friendly",
            "image_url",
            "image_alt_text",
            "is_illustration",
            "spicy_level",
            "tags",
            "dietary_labels",
            "preparation_time_minutes",
            "serving_start_time",
            "serving_end_time",
        ]
