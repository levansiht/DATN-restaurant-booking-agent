from django.urls import path

from accounts.views.admin_portal import (
    admin_session,
    admin_user_detail,
    admin_user_list_create,
)
from restaurant_booking.admin_views import (
    admin_booking_detail,
    admin_booking_list,
    admin_booking_status_update,
    admin_dashboard_summary,
    admin_table_detail,
    admin_table_list_create,
    admin_table_release,
)
from restaurant_booking.portal_views import (
    admin_invoice_list,
    admin_menu_category_detail,
    admin_menu_category_list_create,
    admin_menu_item_detail,
    admin_menu_item_list_create,
    admin_order_detail,
    admin_order_item_create,
    admin_order_item_detail,
    admin_order_list_create,
    admin_order_merge,
    admin_order_send_to_kitchen,
    admin_order_split_item,
    admin_payment_list,
    admin_restaurant_profile_detail,
    admin_table_session_checkout,
    admin_table_session_detail,
    admin_table_session_list_create,
    admin_table_session_merge_table,
    admin_table_session_move_table,
)


urlpatterns = [
    path("session/", admin_session, name="admin_session"),
    path("dashboard/summary/", admin_dashboard_summary, name="admin_dashboard_summary"),
    path("bookings/", admin_booking_list, name="admin_booking_list"),
    path("bookings/<int:booking_id>/", admin_booking_detail, name="admin_booking_detail"),
    path(
        "bookings/<int:booking_id>/status/",
        admin_booking_status_update,
        name="admin_booking_status_update",
    ),
    path("tables/", admin_table_list_create, name="admin_table_list_create"),
    path("tables/<int:table_id>/", admin_table_detail, name="admin_table_detail"),
    path("tables/<int:table_id>/release/", admin_table_release, name="admin_table_release"),
    path("restaurant-profile/", admin_restaurant_profile_detail, name="admin_restaurant_profile_detail"),
    path("menu/categories/", admin_menu_category_list_create, name="admin_menu_category_list_create"),
    path("menu/categories/<int:category_id>/", admin_menu_category_detail, name="admin_menu_category_detail"),
    path("menu/items/", admin_menu_item_list_create, name="admin_menu_item_list_create"),
    path("menu/items/<int:item_id>/", admin_menu_item_detail, name="admin_menu_item_detail"),
    path("sessions/", admin_table_session_list_create, name="admin_table_session_list_create"),
    path("sessions/<int:session_id>/", admin_table_session_detail, name="admin_table_session_detail"),
    path(
        "sessions/<int:session_id>/merge-table/",
        admin_table_session_merge_table,
        name="admin_table_session_merge_table",
    ),
    path(
        "sessions/<int:session_id>/move-table/",
        admin_table_session_move_table,
        name="admin_table_session_move_table",
    ),
    path(
        "sessions/<int:session_id>/checkout/",
        admin_table_session_checkout,
        name="admin_table_session_checkout",
    ),
    path("orders/", admin_order_list_create, name="admin_order_list_create"),
    path("orders/<int:order_id>/", admin_order_detail, name="admin_order_detail"),
    path(
        "orders/<int:order_id>/send-to-kitchen/",
        admin_order_send_to_kitchen,
        name="admin_order_send_to_kitchen",
    ),
    path("orders/<int:order_id>/items/", admin_order_item_create, name="admin_order_item_create"),
    path("order-items/<int:order_item_id>/", admin_order_item_detail, name="admin_order_item_detail"),
    path(
        "orders/<int:order_id>/split-item/",
        admin_order_split_item,
        name="admin_order_split_item",
    ),
    path("orders/merge/", admin_order_merge, name="admin_order_merge"),
    path("payments/", admin_payment_list, name="admin_payment_list"),
    path("invoices/", admin_invoice_list, name="admin_invoice_list"),
    path("users/", admin_user_list_create, name="admin_user_list_create"),
    path("users/<int:user_id>/", admin_user_detail, name="admin_user_detail"),
]
