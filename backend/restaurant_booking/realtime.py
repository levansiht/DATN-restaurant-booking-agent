from __future__ import annotations

import asyncio
import json
import logging
import select
import threading
from contextlib import suppress

import psycopg2
from django.conf import settings
from django.db import transaction
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


logger = logging.getLogger(__name__)

REALTIME_CHANNEL = "restaurant_booking_updates"
WEBSOCKET_PATH = "/ws/restaurant-booking/updates/"


def _get_database_dsn():
    database = settings.DATABASES["default"]
    return {
        "dbname": database["NAME"],
        "user": database["USER"],
        "password": database["PASSWORD"],
        "host": database["HOST"],
        "port": database["PORT"],
    }


class BookingRealtimeHub:
    def __init__(self):
        self._queues = set()
        self._lock = threading.Lock()
        self._listener_started = False
        self._loop = None

    def ensure_listener(self, loop):
        with self._lock:
            if self._loop is None:
                self._loop = loop

            if self._listener_started:
                return

            listener_thread = threading.Thread(
                target=self._listen_for_events,
                name="restaurant-booking-realtime-listener",
                daemon=True,
            )
            listener_thread.start()
            self._listener_started = True

    def register(self, queue):
        self._queues.add(queue)

    def unregister(self, queue):
        self._queues.discard(queue)

    def _dispatch_in_loop(self, event):
        stale_queues = []
        for queue in list(self._queues):
            try:
                queue.put_nowait(event)
            except Exception:
                stale_queues.append(queue)

        for queue in stale_queues:
            self._queues.discard(queue)

    def _schedule_dispatch(self, event):
        if not self._loop or not self._loop.is_running():
            return
        self._loop.call_soon_threadsafe(self._dispatch_in_loop, event)

    def _listen_for_events(self):
        while True:
            connection = None
            cursor = None
            try:
                connection = psycopg2.connect(**_get_database_dsn())
                connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                cursor = connection.cursor()
                cursor.execute(f"LISTEN {REALTIME_CHANNEL};")

                while True:
                    if select.select([connection], [], [], 1) == ([], [], []):
                        continue

                    connection.poll()
                    while connection.notifies:
                        notification = connection.notifies.pop(0)
                        event = json.loads(notification.payload)
                        self._schedule_dispatch(event)
            except Exception:
                logger.exception("Realtime listener crashed. Retrying in 1 second.")
                with suppress(Exception):
                    if cursor:
                        cursor.close()
                with suppress(Exception):
                    if connection:
                        connection.close()
                threading.Event().wait(1)


booking_realtime_hub = BookingRealtimeHub()


def publish_realtime_event(event):
    payload = json.dumps(event, default=str)

    def _notify():
        connection = None
        cursor = None
        try:
            connection = psycopg2.connect(**_get_database_dsn())
            connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = connection.cursor()
            cursor.execute("SELECT pg_notify(%s, %s)", [REALTIME_CHANNEL, payload])
        except Exception:
            logger.exception("Failed to publish realtime event.")
        finally:
            with suppress(Exception):
                if cursor:
                    cursor.close()
            with suppress(Exception):
                if connection:
                    connection.close()

    transaction.on_commit(_notify)


async def restaurant_booking_updates_websocket(scope, receive, send):
    loop = asyncio.get_running_loop()
    booking_realtime_hub.ensure_listener(loop)

    queue = asyncio.Queue()
    booking_realtime_hub.register(queue)

    await send({"type": "websocket.accept"})
    await send(
        {
            "type": "websocket.send",
            "text": json.dumps(
                {"domain": "restaurant_booking", "type": "connection.ready"}
            ),
        }
    )

    try:
        while True:
            receive_task = asyncio.create_task(receive())
            queue_task = asyncio.create_task(queue.get())

            done, pending = await asyncio.wait(
                {receive_task, queue_task},
                return_when=asyncio.FIRST_COMPLETED,
            )

            for pending_task in pending:
                pending_task.cancel()
                with suppress(asyncio.CancelledError):
                    await pending_task

            if receive_task in done:
                message = receive_task.result()
                message_type = message.get("type")

                if message_type == "websocket.disconnect":
                    break

                if message_type == "websocket.receive" and message.get("text") == "ping":
                    await send({"type": "websocket.send", "text": '{"type":"pong"}'})
                    continue

            if queue_task in done:
                event = queue_task.result()
                await send(
                    {
                        "type": "websocket.send",
                        "text": json.dumps(event, default=str),
                    }
                )
    finally:
        booking_realtime_hub.unregister(queue)
