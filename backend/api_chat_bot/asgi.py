"""
ASGI config for seikai project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from restaurant_booking.realtime import (
    WEBSOCKET_PATH,
    restaurant_booking_updates_websocket,
)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api_chat_bot.settings")

django_asgi_app = get_asgi_application()


async def application(scope, receive, send):
    if (
        scope["type"] == "websocket"
        and scope.get("path") in {WEBSOCKET_PATH, WEBSOCKET_PATH.rstrip("/")}
    ):
        await restaurant_booking_updates_websocket(scope, receive, send)
        return

    await django_asgi_app(scope, receive, send)
