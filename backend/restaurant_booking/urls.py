from django.urls import path
from restaurant_booking.views import (
    booking_payment_checkout,
    restaurant_chat_stream,
    sepay_payment_ipn,
    table_list,
    table_search,
    table_detail,
    booking_create,
    booking_search_by_code,
)
from restaurant_booking.portal_views import menu_public_list, restaurant_profile_public
app_name = 'restaurant_booking'

urlpatterns = [
    # Restaurant booking chat endpoints
    path('chat/stream/', restaurant_chat_stream, name='restaurant_chat_stream'),

    # Public restaurant information
    path('restaurant-profile/', restaurant_profile_public, name='restaurant_profile_public'),
    path('menu/', menu_public_list, name='menu_public_list'),
    
    # Table management endpoints
    path('tables/', table_list, name='table_list'),
    path('tables/search/', table_search, name='table_search'),
    path('tables/<int:table_id>/', table_detail, name='table_detail'),
    
    # Booking management endpoints
    path('bookings/create/', booking_create, name='booking_create'),
    path('bookings/search/', booking_search_by_code, name='booking_search_by_code'),
    path('bookings/<str:booking_code>/payment/checkout/', booking_payment_checkout, name='booking_payment_checkout'),
    path('payments/sepay/ipn/', sepay_payment_ipn, name='sepay_payment_ipn'),
]
