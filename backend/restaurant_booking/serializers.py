from datetime import datetime
from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from restaurant_booking.models import Booking, Table


def booking_has_conflict(table, booking_date, booking_time, duration_hours=2.0, exclude_booking_id=None):
    requested_start = datetime.combine(booking_date, booking_time)
    requested_end = requested_start + timezone.timedelta(hours=float(duration_hours))

    conflicting_bookings = Booking.objects.filter(
        table=table,
        booking_date=booking_date,
        status__in=[Booking.BookingStatus.PENDING, Booking.BookingStatus.CONFIRMED],
    )

    if exclude_booking_id:
        conflicting_bookings = conflicting_bookings.exclude(id=exclude_booking_id)

    for booking in conflicting_bookings:
        booking_start = datetime.combine(booking_date, booking.booking_time)
        booking_end = booking_start + timezone.timedelta(hours=float(booking.duration_hours))
        if requested_start < booking_end and requested_end > booking_start:
            return True

    return False


class RestaurantBookingChatRequestSerializer(serializers.Serializer):
    user_input = serializers.CharField(required=True)
    chat_history = serializers.JSONField(required=True)


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
                {"table_id": "Bàn đã có lịch đặt trùng khung giờ này."}
            )

        attrs["table"] = table
        return attrs

    def create(self, validated_data):
        table = validated_data.pop("table")
        validated_data.pop("table_id", None)
        return Booking.objects.create(
            table=table,
            source=Booking.BookingSource.WEBSITE,
            status=Booking.BookingStatus.PENDING,
            **validated_data,
        )


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
