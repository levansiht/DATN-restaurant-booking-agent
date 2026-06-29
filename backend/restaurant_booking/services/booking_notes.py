"""Helpers for the booking ``notes`` field shared by the chatbot, email and
n8n/Telegram notifications.

The chatbot stores pre-ordered dishes inside ``Booking.notes`` using a fixed
prefix so every channel (email, calendar, Telegram) can render them, and the
kitchen knows what to prepare. When the guest only books a table (no dishes),
no pre-order line is added.
"""

from __future__ import annotations

PREORDER_NOTE_PREFIX = "Món đặt trước:"


def build_preorder_note(item_names) -> str:
    names = [str(name).strip() for name in (item_names or []) if str(name).strip()]
    if not names:
        return ""
    return f"{PREORDER_NOTE_PREFIX} " + ", ".join(names)


def merge_notes(base_note: str | None, preorder_note: str | None) -> str:
    base = (base_note or "").strip()
    preorder = (preorder_note or "").strip()
    if base and preorder:
        return f"{base} | {preorder}"
    return base or preorder


def extract_preorder_items(notes: str | None) -> list[str]:
    """Parse the dish names back out of a booking note. Empty when none."""
    if not notes or PREORDER_NOTE_PREFIX not in notes:
        return []
    segment = notes.split(PREORDER_NOTE_PREFIX, 1)[1]
    # The pre-order line is always appended last, but guard against a trailing
    # separator just in case.
    segment = segment.split("|", 1)[0]
    return [part.strip() for part in segment.split(",") if part.strip()]
