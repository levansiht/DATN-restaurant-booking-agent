from django.urls import path
from restaurant_booking.views import (
    restaurant_chat_stream,
    table_list,
    table_search,
    table_detail,
    booking_create,
    booking_search_by_code,
)
app_name = 'restaurant_booking'

urlpatterns = [
    # Restaurant booking chat endpoints
    path('chat/stream/', restaurant_chat_stream, name='restaurant_chat_stream'),
    
    # Table management endpoints
    path('tables/', table_list, name='table_list'),
    path('tables/search/', table_search, name='table_search'),
    path('tables/<int:table_id>/', table_detail, name='table_detail'),
    
    # Booking management endpoints
    path('bookings/create/', booking_create, name='booking_create'),
    path('bookings/search/', booking_search_by_code, name='booking_search_by_code'),
]
