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
    path("users/", admin_user_list_create, name="admin_user_list_create"),
    path("users/<int:user_id>/", admin_user_detail, name="admin_user_detail"),
]
