"""Deterministic + LLM-assisted booking slot extraction.

This module is the single source of truth for turning free-form Vietnamese
chat into the structured booking slots the state machine needs. It deliberately
favours deterministic regex/keyword parsing (cheap, predictable, testable) and
only falls back to a structured LLM extraction to recover values that natural
phrasing hides (e.g. a bare name reply, an unusual date phrasing).

Merge rule: a slot already present in the session is NEVER overwritten by an
empty value, so the bot never "forgets" and re-asks something the guest gave.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel, Field

from common.services.llm_service import (
    LLMProvider,
    OPENAI_ROUTER_MODEL,
    get_llm_service,
)
from restaurant_booking.models import Table


# Values an LLM (or a careless user) may emit for an "unknown" field. They are
# truthy strings, so without filtering they would wrongly satisfy "slot filled"
# checks and skip required questions.
PLACEHOLDER_VALUES = {
    "",
    "null",
    "none",
    "nil",
    "n/a",
    "na",
    "unknown",
    "khong",
    "khong ro",
    "khong co",
    "chua co",
    "chua biet",
    "string",
}

# Tokens to drop when pulling a bare name out of a contact reply.
NAME_STOPWORDS = {
    "ten",
    "la",
    "toi",
    "minh",
    "em",
    "anh",
    "chi",
    "so",
    "dien",
    "thoai",
    "sdt",
    "dt",
    "email",
    "mail",
    "va",
    "cua",
    "nhe",
    "a",
    "goi",
    "cho",
    "day",
    "nha",
}


BOOKING_SLOT_KEYS = (
    "booking_date",
    "booking_time",
    "party_size",
    "table_type",
    "floor",
    "table_id",
    "guest_name",
    "guest_phone",
    "guest_email",
    "note",
)

TABLE_TYPE_KEYWORDS = (
    ("trong nha", Table.TableType.INDOOR),
    ("indoor", Table.TableType.INDOOR),
    ("ngoai troi", Table.TableType.OUTDOOR),
    ("outdoor", Table.TableType.OUTDOOR),
    ("san vuon", Table.TableType.OUTDOOR),
    ("phong rieng", Table.TableType.PRIVATE),
    ("private", Table.TableType.PRIVATE),
    ("vip", Table.TableType.PRIVATE),
    ("quay bar", Table.TableType.BAR),
    ("bar", Table.TableType.BAR),
    ("ghe ngoi", Table.TableType.BOOTH),
    ("booth", Table.TableType.BOOTH),
    ("gan cua so", Table.TableType.WINDOW),
    ("cua so", Table.TableType.WINDOW),
    ("window", Table.TableType.WINDOW),
)

AFFIRMATIVE_TERMS = (
    "dung roi",
    "dung",
    "chinh xac",
    "chuan",
    "ok",
    "oke",
    "okay",
    "okie",
    "dong y",
    "xac nhan",
    "chot",
    "chot don",
    "chot di",
    "dat di",
    "dat luon",
    "vang",
    "duoc",
    "yes",
    "uh",
    "u",
)

NEGATIVE_TERMS = (
    "khong dung",
    "sai",
    "chua dung",
    "khong phai",
    "doi lai",
    "sua lai",
    "thay doi",
)

DEFER_CHOICE_TERMS = (
    "tuy",
    "tuy ban",
    "tuy em",
    "sao cung duoc",
    "the nao cung duoc",
    "gi cung duoc",
    "cho nao cung duoc",
    "ban nao cung duoc",
    "chon giup",
    "chon ho",
    "chon gium",
    "ban chon",
    "em chon",
    "hop li",
    "hop ly",
    "phu hop",
    "goi y giup",
)

CANCEL_TERMS = (
    "huy dat ban",
    "huy booking",
    "khong dat ban nua",
    "khong dat nua",
    "thoi khong dat",
    "dung dat ban",
    "huy dat",
)

BACK_TO_MENU_TERMS = (
    "xem menu",
    "xem thuc don",
    "goi y mon",
    "doi mon",
    "tu van mon",
    "xem mon",
    "chon mon khac",
)


class ExtractedSlots(BaseModel):
    """Structured shape for LLM slot extraction (all optional)."""

    booking_date: Optional[str] = Field(default=None, description="YYYY-MM-DD")
    booking_time: Optional[str] = Field(default=None, description="HH:MM 24h")
    party_size: Optional[int] = Field(default=None)
    table_type: Optional[str] = Field(
        default=None,
        description="INDOOR|OUTDOOR|PRIVATE|BAR|BOOTH|WINDOW",
    )
    floor: Optional[int] = Field(default=None)
    guest_name: Optional[str] = Field(default=None)
    guest_phone: Optional[str] = Field(default=None)
    guest_email: Optional[str] = Field(default=None)
    note: Optional[str] = Field(default=None)


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFD", (value or "").strip().lower())
    normalized = normalized.replace("\u0111", "d")
    normalized = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    return " ".join(normalized.split())


def is_placeholder(value) -> bool:
    """True for empty / "null"-like values that must not fill a slot."""
    if value is None:
        return True
    if isinstance(value, str):
        return normalize_text(value) in PLACEHOLDER_VALUES
    return False


class BookingSlotExtractor:
    """Extract and merge booking slots from the conversation."""

    def __init__(self, llm_provider: LLMProvider = LLMProvider.OPENAI):
        self._llm_provider = llm_provider
        self._structured_llm = None  # lazy
        # Allows tests (or a degraded/offline mode) to rely purely on the
        # deterministic parsers without hitting the LLM.
        self.enable_llm = True

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def merge(
        self,
        *,
        existing_slots: dict,
        user_input: str,
        chat_history: Optional[list[dict]] = None,
        use_llm: bool = True,
    ) -> dict:
        """Return updated slots after parsing ``user_input``.

        Deterministic parsing runs first; the LLM only fills slots still
        missing afterwards. Existing non-empty slots are preserved.
        """
        slots = self._sanitize_slots(existing_slots)
        deterministic = self.extract_from_text(user_input)
        self._apply(slots, deterministic)

        if use_llm and self.enable_llm and self._has_missing_core(slots):
            llm_values = self._safe_llm_extract(chat_history or [], user_input)
            self._apply(slots, llm_values)

        return slots

    def backfill_from_history(self, *, existing_slots: dict, chat_history: list[dict]) -> dict:
        """Seed slots from earlier user messages when entering the booking flow.

        Runs deterministic parsing over every prior user turn (oldest first so a
        later correction wins) so context like party size given during the menu
        phase is not lost on hand-off.
        """
        slots = dict(existing_slots or {})
        for message in chat_history or []:
            if message.get("role") != "user":
                continue
            self._apply(slots, self.extract_from_text(message.get("content", "")))
        return slots

    def extract_from_text(self, text: str) -> dict:
        """Deterministic extraction from a single message."""
        normalized = normalize_text(text)
        values: dict = {}

        booking_date = self._extract_date(normalized)
        if booking_date:
            values["booking_date"] = booking_date

        booking_time = self._extract_time(normalized)
        if booking_time:
            values["booking_time"] = booking_time

        party_size = self._extract_party_size(normalized)
        if party_size:
            values["party_size"] = party_size

        table_type = self._extract_table_type(normalized)
        if table_type:
            values["table_type"] = table_type

        floor = self._extract_floor(normalized)
        if floor:
            values["floor"] = floor

        phone = self._extract_phone(text)
        if phone:
            values["guest_phone"] = phone

        email = self._extract_email(text)
        if email:
            values["guest_email"] = email

        name = self._extract_name(text)
        if name:
            values["guest_name"] = name

        return values

    # ------------------------------------------------------------------ #
    # Intent helpers (used by the state machine / orchestrator)
    # ------------------------------------------------------------------ #
    @staticmethod
    def is_affirmative(text: str) -> bool:
        normalized = normalize_text(text)
        if not normalized:
            return False
        if any(term in normalized for term in NEGATIVE_TERMS):
            return False
        tokens = normalized.split()
        if normalized in AFFIRMATIVE_TERMS:
            return True
        return any(term in normalized for term in AFFIRMATIVE_TERMS) or (
            len(tokens) <= 4 and any(token in AFFIRMATIVE_TERMS for token in tokens)
        )

    @staticmethod
    def is_negative(text: str) -> bool:
        normalized = normalize_text(text)
        return any(term in normalized for term in NEGATIVE_TERMS)

    @staticmethod
    def is_defer_choice(text: str) -> bool:
        normalized = normalize_text(text)
        return any(term in normalized for term in DEFER_CHOICE_TERMS)

    @staticmethod
    def is_cancel(text: str) -> bool:
        normalized = normalize_text(text)
        return any(term in normalized for term in CANCEL_TERMS)

    @staticmethod
    def wants_menu(text: str) -> bool:
        normalized = normalize_text(text)
        return any(term in normalized for term in BACK_TO_MENU_TERMS)

    def extract_contact_name(self, text: str) -> Optional[str]:
        """Pull a bare name out of a contact reply such as "Sỷ, 0334407762".

        Only meant to be used when the bot has explicitly asked for the name,
        because it is permissive (no "tên là" prefix required).
        """
        if not text:
            return None
        cleaned = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", " ", text)
        cleaned = re.sub(r"(?:\+?84|0)\d{8,10}", " ", cleaned)
        cleaned = re.sub(r"\d+", " ", cleaned)
        tokens = [
            token.strip()
            for token in re.split(r"[\s,;:./]+", cleaned)
            if token.strip() and normalize_text(token) not in NAME_STOPWORDS
        ]
        candidate = " ".join(tokens)
        name = self._clean_name(candidate)
        if name and not is_placeholder(name):
            return name
        return None

    @staticmethod
    def is_no_note(text: str) -> bool:
        normalized = normalize_text(text)
        return any(
            term in normalized
            for term in ("khong", "khong co", "khong can", "khong ghi chu", "bo qua", "thoi")
        )

    @staticmethod
    def parse_table_choice(text: str, options: list[dict]) -> Optional[int]:
        """Map a free-form table pick to a concrete table_id.

        Handles: "bàn 28", "table 28", "phương án 1", "số 2", bare "28".
        A number that matches an option ``table_id`` wins; otherwise it is
        treated as a 1-based position in the listed options.
        """
        if not options:
            return None
        normalized = normalize_text(text)
        option_ids = {int(option["table_id"]) for option in options}

        explicit = re.search(r"\b(?:ban|table|ban so|so ban)\s*(\d{1,3})\b", normalized)
        if explicit:
            candidate = int(explicit.group(1))
            if candidate in option_ids:
                return candidate

        position = re.search(r"\b(?:phuong an|lua chon|so|option)\s*(\d{1,2})\b", normalized)
        if position:
            index = int(position.group(1))
            if 1 <= index <= len(options):
                return int(options[index - 1]["table_id"])

        numbers = [int(token) for token in re.findall(r"\b(\d{1,3})\b", normalized)]
        for number in numbers:
            if number in option_ids:
                return number
        for number in numbers:
            if 1 <= number <= len(options):
                return int(options[number - 1]["table_id"])
        return None

    # ------------------------------------------------------------------ #
    # Deterministic field parsers
    # ------------------------------------------------------------------ #
    def _extract_date(self, normalized: str) -> Optional[str]:
        today = datetime.now()

        def has_word(word: str) -> bool:
            # Word-boundary match so "mai" doesn't fire inside "gmail" etc.
            return re.search(rf"\b{re.escape(word)}\b", normalized) is not None

        if has_word("ngay kia"):
            return (today + timedelta(days=2)).strftime("%Y-%m-%d")
        # Require the "ngày mai" phrase (not the bare word "mai") so a guest
        # named "Mai"/"Nay" is not misread as a date.
        if any(has_word(term) for term in ("ngay mai", "toi mai")):
            return (today + timedelta(days=1)).strftime("%Y-%m-%d")
        if any(has_word(term) for term in ("hom nay", "toi nay", "trua nay", "chieu nay", "sang nay", "bay gio")):
            return today.strftime("%Y-%m-%d")

        weekdays = {
            "thu 2": 0, "thu hai": 0, "thu 3": 1, "thu ba": 1,
            "thu 4": 2, "thu tu": 2, "thu 5": 3, "thu nam": 3,
            "thu 6": 4, "thu sau": 4, "thu 7": 5, "thu bay": 5,
            "chu nhat": 6,
        }
        for label, weekday in weekdays.items():
            if label in normalized:
                days_ahead = weekday - today.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

        iso = re.search(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", normalized)
        if iso:
            year, month, day = (int(part) for part in iso.groups())
            parsed = self._safe_date(year, month, day)
            if parsed:
                return parsed

        dmy = re.search(r"\b(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?\b", normalized)
        if dmy:
            day = int(dmy.group(1))
            month = int(dmy.group(2))
            year = int(dmy.group(3)) if dmy.group(3) else today.year
            if year < 100:
                year += 2000
            parsed = self._safe_date(year, month, day)
            if parsed:
                return parsed
        return None

    @staticmethod
    def _safe_date(year: int, month: int, day: int) -> Optional[str]:
        try:
            return datetime(year, month, day).strftime("%Y-%m-%d")
        except ValueError:
            return None

    def _extract_time(self, normalized: str) -> Optional[str]:
        is_evening = any(term in normalized for term in ("toi", "buoi toi"))
        is_afternoon = any(term in normalized for term in ("chieu", "buoi chieu"))
        is_noon = "trua" in normalized
        is_morning = any(term in normalized for term in ("sang", "buoi sang"))

        match = re.search(r"\b([01]?\d|2[0-3])\s*[:hg]\s*([0-5]\d)\b", normalized)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            hour = self._apply_period(hour, is_evening, is_afternoon, is_noon, is_morning)
            return f"{hour:02d}:{minute:02d}"

        match = re.search(r"\b([01]?\d|2[0-3])\s*(?:h|g|gio)\b", normalized)
        if match:
            hour = int(match.group(1))
            hour = self._apply_period(hour, is_evening, is_afternoon, is_noon, is_morning)
            return f"{hour:02d}:00"

        return None

    @staticmethod
    def _apply_period(hour, is_evening, is_afternoon, is_noon, is_morning) -> int:
        if hour < 12 and (is_evening or is_afternoon):
            return hour + 12
        if is_noon and hour < 12:
            return 12 if hour == 12 else hour
        # morning / explicit 24h hours stay as-is
        return hour

    def _extract_party_size(self, normalized: str) -> Optional[int]:
        match = re.search(
            r"\b(?:di|den|nhom|cho|chung\s*(?:toi|minh|em|anh|chi))\s*(\d+)\b"
            r"|\b(\d+)\s*(?:nguoi|khach|ban)\b"
            r"|\bdi\s+(\d+)\b",
            normalized,
        )
        if not match:
            return None
        raw = match.group(1) or match.group(2) or match.group(3)
        if not raw:
            return None
        size = int(raw)
        return size if 1 <= size <= 20 else None

    def _extract_table_type(self, normalized: str) -> Optional[str]:
        for keyword, table_type in TABLE_TYPE_KEYWORDS:
            if keyword in normalized:
                return str(table_type)
        return None

    def _extract_floor(self, normalized: str) -> Optional[int]:
        match = re.search(r"\b(?:tang|lau|floor)\s*([12])\b", normalized)
        if match:
            return int(match.group(1))
        return None

    def _extract_phone(self, raw_text: str) -> Optional[str]:
        compact = re.sub(r"[^\d+]", "", raw_text or "")
        match = re.search(r"(?:\+?84|0)\d{8,10}", compact)
        return match.group(0) if match else None

    def _extract_email(self, raw_text: str) -> Optional[str]:
        match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", raw_text or "")
        return match.group(0) if match else None

    def _extract_name(self, raw_text: str) -> Optional[str]:
        patterns = [
            r"(?:mình|minh|tôi|toi|em|anh|chị|chi)\s+(?:tên là|ten la|tên|ten|là|la)\s+([^\n,.!?;:]{2,50})",
            r"(?:tên mình|ten minh|tên tôi|ten toi)\s+(?:là|la)?\s*([^\n,.!?;:]{2,50})",
            r"(?:gọi mình là|goi minh la|cứ gọi mình là|cu goi minh la)\s+([^\n,.!?;:]{2,50})",
        ]
        for pattern in patterns:
            match = re.search(pattern, raw_text or "", flags=re.IGNORECASE)
            if not match:
                continue
            name = self._clean_name(match.group(1))
            if name:
                return name
        return None

    @staticmethod
    def _clean_name(value: str) -> Optional[str]:
        name = re.split(
            r"\s+(?:và|va|rồi|roi|nhé|nhe|ạ|a|đặt|dat|gợi|goi|muốn|muon|cho|giúp|giup)\b",
            (value or "").strip(),
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]
        name = re.sub(r"\s+", " ", name).strip(" -_.,!?;:()[]{}\"'")
        if not name or len(name) > 40 or len(name.split()) > 4:
            return None
        normalized = normalize_text(name)
        if normalized in {"anh", "chi", "em", "toi", "minh", "khach", "admin", "bot"}:
            return None
        if not re.search(r"[A-Za-zÀ-ỹ]", name):
            return None
        return " ".join(part[:1].upper() + part[1:] for part in name.split())

    # ------------------------------------------------------------------ #
    # LLM fallback
    # ------------------------------------------------------------------ #
    @staticmethod
    def _has_missing_core(slots: dict) -> bool:
        core = ("booking_date", "booking_time", "party_size", "guest_name")
        return any(not slots.get(key) for key in core)

    def _safe_llm_extract(self, chat_history: list[dict], user_input: str) -> dict:
        try:
            extracted = self._llm_extract(chat_history, user_input)
        except Exception:  # noqa: BLE001 - extraction must never break the chat
            return {}
        values = extracted.model_dump()
        return {key: value for key, value in values.items() if value not in (None, "")}

    def _llm_extract(self, chat_history: list[dict], user_input: str) -> ExtractedSlots:
        structured_llm = self._get_structured_llm()
        today = datetime.now()
        system_prompt = (
            "Bạn trích xuất thông tin đặt bàn nhà hàng từ hội thoại tiếng Việt.\n"
            "Chỉ trả về giá trị khách đã NÓI RÕ; nếu không chắc để null.\n"
            "Không bịa, không suy đoán. Đại từ (anh/chị/mình/tôi/em) KHÔNG phải tên.\n"
            f"Hôm nay: {today.strftime('%Y-%m-%d')}. Ngày mai: {(today + timedelta(days=1)).strftime('%Y-%m-%d')}.\n"
            "table_type chỉ thuộc: INDOOR, OUTDOOR, PRIVATE, BAR, BOOTH, WINDOW.\n"
            "booking_date dạng YYYY-MM-DD, booking_time dạng HH:MM (24h)."
        )
        history_lines = [
            f"{'Khách' if message.get('role') == 'user' else 'Nhân viên'}: {message.get('content', '')}"
            for message in (chat_history or [])[-10:]
        ]
        human_prompt = (
            "Hội thoại gần đây:\n"
            + "\n".join(history_lines)
            + f"\n\nTin nhắn mới nhất của khách: {user_input}"
        )
        from langchain_core.messages import HumanMessage, SystemMessage

        return structured_llm.invoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)]
        )

    def _get_structured_llm(self):
        if self._structured_llm is None:
            model_name = OPENAI_ROUTER_MODEL
            if self._llm_provider != LLMProvider.OPENAI:
                model_name = "claude-3-sonnet-20240229"
            llm = get_llm_service().create_agent_llm(
                provider=self._llm_provider,
                model=model_name,
                reasoning_effort="minimal",
                max_tokens=500,
                streaming=False,
            )
            self._structured_llm = llm.with_structured_output(
                ExtractedSlots,
                method="json_schema",
                strict=True,
            )
        return self._structured_llm

    @staticmethod
    def _sanitize_slots(existing_slots: Optional[dict]) -> dict:
        """Drop any placeholder ("null"-like) values already stored, so a
        previously corrupted session self-heals instead of skipping questions.
        """
        cleaned: dict = {}
        for key, value in (existing_slots or {}).items():
            if key in BOOKING_SLOT_KEYS and is_placeholder(value):
                continue
            cleaned[key] = value
        return cleaned

    @staticmethod
    def _apply(slots: dict, new_values: dict) -> None:
        for key, value in (new_values or {}).items():
            if key not in BOOKING_SLOT_KEYS:
                continue
            if value in (None, "", []) or is_placeholder(value):
                continue
            slots[key] = value
