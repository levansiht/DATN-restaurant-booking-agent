from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from restaurant_booking.models import Booking, Table
from restaurant_booking.services.availability import (
    BookingValidationError,
    TABLE_CONFLICT_MESSAGE,
    booking_has_conflict,
    create_pending_booking,
)


class RestaurantBookingChatRequestSerializer(serializers.Serializer):
    user_input = serializers.CharField(required=True)
    chat_history = serializers.JSONField(required=True)
    selected_item_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        default=list,
    )


class TableSerializer(serializers.ModelSerializer):
    table_type_label = serializers.CharField(source="get_table_type_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    is_available_for_booking = serializers.BooleanField(read_only=True)

    class Meta:
        model = Table
        fields = [
            "id",
            "table_type",
            "table_type_label",
            "capacity",
            "floor",
            "status",
            "status_label",
            "width",
            "length",
            "notes",
            "is_available_for_booking",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class BookingSerializer(serializers.ModelSerializer):
    table_id = serializers.IntegerField(source="table.id", read_only=True)
    table_type = serializers.CharField(source="table.table_type", read_only=True)
    table_type_label = serializers.CharField(source="table.get_table_type_display", read_only=True)
    table_floor = serializers.IntegerField(source="table.floor", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    source_label = serializers.CharField(source="get_source_display", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "code",
            "guest_name",
            "guest_email",
            "guest_phone",
            "booking_date",
            "booking_time",
            "duration_hours",
            "party_size",
            "status",
            "status_label",
            "source",
            "source_label",
            "notes",
            "cancellation_reason",
            "table_id",
            "table_type",
            "table_type_label",
            "table_floor",
            "confirmed_at",
            "cancelled_at",
            "created_at",
            "updated_at",
        ]


class PublicBookingCreateSerializer(serializers.Serializer):
    table_id = serializers.IntegerField()
    guest_name = serializers.CharField(max_length=255)
    guest_phone = serializers.CharField(max_length=20)
    guest_email = serializers.EmailField()
    booking_date = serializers.DateField(input_formats=["%Y-%m-%d"])
    booking_time = serializers.TimeField(input_formats=["%H:%M"])
    party_size = serializers.IntegerField(min_value=1, max_value=20)
    duration_hours = serializers.DecimalField(
        max_digits=3,
        decimal_places=1,
        min_value=Decimal("0.5"),
        max_value=Decimal("8.0"),
        required=False,
        default=Decimal("2.0"),
    )
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, attrs):
        table = Table.objects.filter(id=attrs["table_id"], is_deleted=False).first()
        if not table:
            raise serializers.ValidationError({"table_id": "Bàn không tồn tại."})

        if attrs["party_size"] > table.capacity:
            raise serializers.ValidationError(
                {"party_size": "Số lượng khách vượt quá sức chứa của bàn đã chọn."}
            )

        if table.status != Table.TableStatus.AVAILABLE:
            raise serializers.ValidationError(
                {"table_id": f"Bàn này hiện không khả dụng ({table.get_status_display()})."}
            )

        booking_date = attrs["booking_date"]
        booking_time = attrs["booking_time"]

        if booking_date < timezone.localdate():
            raise serializers.ValidationError(
                {"booking_date": "Không thể đặt bàn cho ngày trong quá khứ."}
            )

        if booking_has_conflict(
            table=table,
            booking_date=booking_date,
            booking_time=booking_time,
            duration_hours=attrs["duration_hours"],
        ):
            raise serializers.ValidationError(
                {"table_id": TABLE_CONFLICT_MESSAGE}
            )

        attrs["table"] = table
        return attrs

    def create(self, validated_data):
        validated_data.pop("table", None)
        table_id = validated_data.pop("table_id")

        try:
            return create_pending_booking(
                table_id=table_id,
                guest_name=validated_data["guest_name"],
                guest_phone=validated_data["guest_phone"],
                guest_email=validated_data["guest_email"],
                booking_date=validated_data["booking_date"],
                booking_time=validated_data["booking_time"],
                party_size=validated_data["party_size"],
                duration_hours=validated_data["duration_hours"],
                notes=validated_data.get("notes") or "",
                source=Booking.BookingSource.WEBSITE,
            )
        except BookingValidationError as exc:
            raise serializers.ValidationError(exc.detail) from exc


class AdminBookingStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Booking.BookingStatus.choices)
    cancellation_reason = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )


class AdminTableWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = [
            "table_type",
            "capacity",
            "floor",
            "status",
            "width",
            "length",
            "notes",
        ]
