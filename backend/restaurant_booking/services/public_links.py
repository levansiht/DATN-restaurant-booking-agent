from django.conf import settings


BOOKING_SEARCH_PATH = "/restaurant-booking/search"


def build_booking_search_url(booking_code):
    website_url = (settings.WEBSITE_URL or "http://localhost:5173").rstrip("/")
    return f"{website_url}{BOOKING_SEARCH_PATH}?code={booking_code}"
