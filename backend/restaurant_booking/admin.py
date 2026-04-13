from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Booking,
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


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'table_type', 'capacity', 'floor', 
        'status', 'is_available_for_booking', 'created_at', 'updated_at'
    ]
    list_filter = [
        'table_type', 'status', 'floor', 
    ]
    search_fields = ['notes']
    list_editable = ['status']
    ordering = ['floor', 'id']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('table_type', 'capacity', 'floor', )
        }),
        ('Status & Availability', {
            'fields': ('status',)
        }),
        ('Dimensions (Optional)', {
            'fields': ('width', 'length'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def is_available_for_booking(self, obj):
        if obj.status == Table.TableStatus.AVAILABLE:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Available</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ Not Available</span>'
            )
    is_available_for_booking.short_description = 'Available for Booking'


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'guest_name', 'table_display', 'booking_date',
        'booking_time', 'party_size', 'status', 'source', 'created_at', 'updated_at'
    ]
    list_filter = [
        'status', 'source', 'booking_date', 'table__table_type', 'table__floor'
    ]
    search_fields = [
        'guest_name', 'guest_email', 'guest_phone'
    ]
    list_editable = ['status']
    ordering = ['-created_at']

    fieldsets = (
        ('Booking Information', {
            'fields': (
                'table', 'booking_date', 'booking_time', 'duration_hours',
                'party_size', 'status', 'source'
            )
        }),
        ('Guest Information', {
            'fields': (
                'guest_name', 'guest_email', 'guest_phone'
            )
        }),
        ('Internal Notes', {
            'fields': (
                'notes', 
            ),
            'classes': ('collapse',)
        }),
        ('Status & Confirmation', {
            'fields': (
                'cancellation_reason',
            ),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = [
        'created_at', 'updated_at',
    ]

    def table_display(self, obj):
        return f"Table {obj.table.id} ({obj.table.get_table_type_display()})"
    table_display.short_description = 'Table'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('table')

    actions = ['mark_confirmed', 'mark_cancelled', 'mark_completed', 'mark_no_show']

    def mark_confirmed(self, request, queryset):
        updated = queryset.filter(status=Booking.BookingStatus.PENDING).update(
            status=Booking.BookingStatus.CONFIRMED
        )
        self.message_user(request, f'{updated} bookings marked as confirmed.')
    mark_confirmed.short_description = 'Mark selected bookings as confirmed'

    def mark_cancelled(self, request, queryset):
        updated = queryset.exclude(status=Booking.BookingStatus.CANCELLED).update(
            status=Booking.BookingStatus.CANCELLED
        )
        self.message_user(request, f'{updated} bookings marked as cancelled.')
    mark_cancelled.short_description = 'Mark selected bookings as cancelled'

    def mark_completed(self, request, queryset):
        updated = queryset.filter(status=Booking.BookingStatus.CONFIRMED).update(
            status=Booking.BookingStatus.COMPLETED
        )
        self.message_user(request, f'{updated} bookings marked as completed.')
    mark_completed.short_description = 'Mark selected bookings as completed'

    def mark_no_show(self, request, queryset):
        updated = queryset.filter(status=Booking.BookingStatus.CONFIRMED).update(
            status=Booking.BookingStatus.NO_SHOW
        )
        self.message_user(request, f'{updated} bookings marked as no show.')
    mark_no_show.short_description = 'Mark selected bookings as no show'


@admin.register(RestaurantProfile)
class RestaurantProfileAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "phone_number",
        "opening_time",
        "closing_time",
        "is_active",
        "updated_at",
    ]
    list_filter = ["is_active"]
    search_fields = ["name", "phone_number", "email", "address"]
    ordering = ["-is_active", "-updated_at"]


@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "display_order",
        "is_active",
        "default_image_url",
        "updated_at",
    ]
    list_filter = ["is_active"]
    search_fields = ["name"]
    ordering = ["display_order", "name"]


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "category",
        "price",
        "status",
        "is_recommended",
        "is_best_seller",
        "updated_at",
    ]
    list_filter = [
        "status",
        "is_recommended",
        "is_best_seller",
        "is_vegetarian",
        "is_kid_friendly",
        "spicy_level",
        "category",
    ]
    search_fields = ["name", "description"]
    ordering = ["name"]
    filter_horizontal = ["suggested_pairings"]


@admin.register(TableSession)
class TableSessionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "code",
        "guest_name",
        "guest_count",
        "status",
        "opened_at",
        "closed_at",
    ]
    list_filter = ["status", "opened_at"]
    search_fields = ["code", "guest_name", "guest_phone"]
    autocomplete_fields = ["booking", "opened_by", "closed_by"]
    ordering = ["-opened_at"]


@admin.register(SessionTable)
class SessionTableAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "table_session",
        "table",
        "role",
        "is_active",
        "assigned_at",
        "released_at",
    ]
    list_filter = ["role", "is_active"]
    autocomplete_fields = ["table_session", "table"]
    ordering = ["-assigned_at"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "code",
        "table_session",
        "status",
        "created_by",
        "sent_to_kitchen_at",
        "closed_at",
    ]
    list_filter = ["status"]
    search_fields = ["code", "table_session__code"]
    autocomplete_fields = ["table_session", "created_by"]
    ordering = ["-created_at"]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "order",
        "item_name",
        "quantity",
        "unit_price",
        "kitchen_status",
        "created_by",
    ]
    list_filter = ["kitchen_status"]
    search_fields = ["item_name", "order__code"]
    autocomplete_fields = ["order", "menu_item", "created_by"]
    ordering = ["created_at", "id"]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "code",
        "table_session",
        "method",
        "status",
        "subtotal_amount",
        "surcharge_amount",
        "total_amount",
        "paid_at",
    ]
    list_filter = ["method", "status"]
    search_fields = ["code", "table_session__code"]
    autocomplete_fields = ["table_session", "paid_by"]
    ordering = ["-created_at"]


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "invoice_number",
        "table_session",
        "payment",
        "customer_name",
        "total_amount",
        "issued_at",
    ]
    search_fields = ["invoice_number", "customer_name", "table_session__code"]
    autocomplete_fields = ["table_session", "payment", "issued_by"]
    ordering = ["-issued_at"]


# Customize admin site
admin.site.site_header = "Restaurant Support System"
admin.site.site_title = "Restaurant Admin"
admin.site.index_title = "Restaurant Operations"
