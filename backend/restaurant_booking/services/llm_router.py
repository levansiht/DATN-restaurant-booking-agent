"""
LLM-based router for intelligent conversation intent classification.

Instead of keyword-based routing, uses LLM to understand user intent
and route to appropriate handler (sales/menu or booking/table).
"""

import re
from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage

from common.services.llm_service import LLMProvider, get_llm_service


class RouteDecision(BaseModel):
    """
    LLM's routing decision with reasoning.
    
    Attributes:
        route: Target route (sales, booking, unknown)
        confidence: Confidence score 0-1
        reason: Explanation for the routing decision
        key_signals: List of keywords/signals detected
    """
    route: Literal["sales", "booking", "unknown"] = Field(
        ..., 
        description="Routing destination"
    )
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Confidence score 0.0-1.0"
    )
    reason: str = Field(
        ...,
        max_length=200,
        description="Brief explanation of routing decision"
    )
    key_signals: list[str] = Field(
        default_factory=list,
        description="Detected keywords/signals"
    )


class LLMRouterService:
    """
    Intelligent routing using LLM to classify user intent.
    
    Advantages over keyword-based routing:
    - Understands context and natural language variations
    - Less prone to misclassification for edge cases
    - Can handle multi-intent queries
    - Provides confidence scores
    - Explains routing decisions (for debugging)
    
    Fallback:
    - If LLM call fails, falls back to keyword-based routing
    """
    
    # Keyword fallback (used if LLM fails)
    BOOKING_KEYWORDS = {
        "dat ban", "giu ban", "con ban", "ban trong", "giu cho", "dat cho",
        "table", "booking", "reserve", "reservation", "dat ban",
    }
    
    MENU_KEYWORDS = {
        "menu", "an gi", "goi y", "mon", "combo", "best seller", "noi bat",
        "gia", "chay", "do uong", "kem", "recommendation", "suggest",
    }

    GREETING_TERMS = {
        "xin chao", "chao", "hello", "hi", "alo",
    }

    ACKNOWLEDGEMENT_TERMS = {
        "ok", "oke", "okay", "okie", "da", "duoc", "vang", "cam on", "thanks", "thank you",
    }

    BOOKING_CONFIRMATION_TERMS = {
        "ok", "oke", "okay", "okie", "da", "duoc", "vang", "dong y", "dung roi", "chinh xac",
    }

    BOOKING_QUESTION_TERMS = {
        "dat ban",
        "giu ban",
        "thong tin dat ban",
        "kiem tra ban",
        "ngay nao",
        "khoang may gio",
        "luc may gio",
        "di may nguoi",
        "so nguoi",
        "khu vuc nao",
        "tang nao",
        "chon ban nao",
        "ban so",
        "so dien thoai",
        "email",
        "xac nhan",
    }

    TABLE_PREFERENCE_TERMS = {
        "trong nha",
        "ngoai troi",
        "phong rieng",
        "quay bar",
        "ghe ngoi",
        "gan cua so",
        "cua so",
        "tang 1",
        "tang 2",
    }

    SYSTEM_PROMPT = """
You are a precise intent classifier for a restaurant chatbot.

Your task: Analyze user input and classify their intent into exactly ONE category.

**Categories:**
1. **SALES**: User wants menu recommendations, food suggestions, pricing, nutritional info, 
   food categories (vegetarian, low spice, beverages, desserts), general restaurant info,
   or is just greeting / opening the conversation and should be handed to a front-of-house style reply.
   Examples: "Gợi ý 5 món chay", "Menu có gì?", "Giá thế nào?", "Đồ uống gì?"

2. **BOOKING**: User wants to reserve a table, check availability, modify booking,
   or is directly answering a booking question already in progress.
   Examples: "Đặt bàn hôm nay", "Còn bàn cho 4 người lúc 7h?", "Thay đổi booking", "7h tối nay" after staff asked booking time

3. **UNKNOWN**: User's intent is unclear, off-topic, or requires additional context.
   Examples: "OK", "Cảm ơn", "Tôi không biết", "Xin chào"

**Output:** Return valid JSON only with these fields:
- route: "sales" | "booking" | "unknown"
- confidence: 0.0-1.0 (how sure you are)
- reason: brief explanation
- key_signals: list of 1-3 detected keywords/indicators

**Rules:**
1. BOOKING only when user clearly wants to reserve/check table, or current turn is a direct follow-up to a booking question.
2. Time/date/party-size alone do NOT mean BOOKING unless booking context is already active.
3. If user mentions food/menu/recommendation/price → SALES
4. Greeting / "ok" / "cảm ơn" alone are not BOOKING.
5. If context unclear → UNKNOWN (don't guess)
6. Be strict about UNKNOWN - only use when truly unclear
7. For mixed queries, pick the PRIMARY intent
8. Consider chat history context when making decisions

**Examples:**
User: "Gợi ý 5 món chay cho 2 người" → SALES (primary: recommendations, secondary: party size)
User: "Còn bàn cho 3 người hôm nay 7h?" → BOOKING
User: "Menu nào rồi?" → SALES
User: "Đặt bàn sau, gợi ý món trước?" → SALES (sequential: user asks menu first then booking)
User: "Xin chào" → UNKNOWN
User: "7h tối nay" after assistant asked booking date/time → BOOKING
User: "Ok" → UNKNOWN
"""
    
    def __init__(self, llm_provider: LLMProvider = LLMProvider.OPENAI):
        """Initialize router with LLM."""
        model_name = "gpt-4o-mini"
        if llm_provider != LLMProvider.OPENAI:
            model_name = "claude-3-sonnet-20240229"
        
        self.llm = get_llm_service().create_agent_llm(
            provider=llm_provider,
            model=model_name,
            temperature=0.0,  # Deterministic for routing
            max_tokens=300,
            streaming=False,
        )
        
        # Structured output for reliable routing
        self.structured_router = self.llm.with_structured_output(
            RouteDecision,
            method="json_schema",
            strict=True,
        )
    
    def route(
        self,
        user_input: str,
        chat_history: list[dict] = None,
        confidence_threshold: float = 0.6,
    ) -> tuple[Literal["sales", "booking"], float]:
        """
        Route user input to appropriate handler.
        
        Args:
            user_input: User's message
            chat_history: Previous messages for context
            confidence_threshold: Min confidence to trust LLM decision (else fallback)
        
        Returns:
            Tuple of (route, confidence)
            - route: "sales" or "booking"
            - confidence: 0.0-1.0
        """
        try:
            decision = self._llm_route(user_input, chat_history)
            
            # If confidence too low or route is unknown, use fallback
            if decision.confidence < confidence_threshold or decision.route == "unknown":
                fallback_route = self._fallback_route(user_input, chat_history)
                # Use lower confidence for fallback
                return fallback_route, max(0.3, decision.confidence * 0.8)
            
            return decision.route, decision.confidence
            
        except Exception as e:
            # If LLM fails, use keyword-based fallback
            print(f"[LLM Router] LLM failed: {e}. Using keyword fallback.")
            route = self._fallback_route(user_input, chat_history)
            return route, 0.5  # Medium confidence for fallback
    
    def _llm_route(
        self,
        user_input: str,
        chat_history: list[dict] = None,
    ) -> RouteDecision:
        """Call LLM to make routing decision."""
        # Build context from recent history
        context_text = ""
        if chat_history:
            recent = chat_history[-3:]  # Last 3 messages
            context_text = "\n".join([
                f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                for msg in recent
            ])
        
        # Build user message with context
        user_message_content = f"""User input: {user_input}"""
        if context_text:
            user_message_content += f"\n\nRecent conversation:\n{context_text}"
        
        # Call LLM
        response = self.structured_router.invoke([
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(content=user_message_content),
        ])
        
        return response
    
    def _fallback_route(
        self,
        user_input: str,
        chat_history: list[dict] = None,
    ) -> Literal["sales", "booking"]:
        """
        Keyword-based fallback routing when LLM is unavailable.
        
        Simple heuristics:
        1. Check current input for keywords
        2. Check recent history for context
        3. Default to sales if unsure
        """
        normalized = self._normalize(user_input)

        # Check current input
        if self._contains_booking_keyword(normalized):
            return "booking"
        if self._is_booking_followup_response(normalized, chat_history):
            return "booking"
        if self._contains_menu_keyword(normalized):
            return "sales"
        if self._is_social_turn(normalized):
            return "sales"

        # Check recent history context
        if chat_history:
            recent = " ".join([
                self._normalize(msg.get("content", ""))
                for msg in chat_history[-4:]
            ])
            if self._contains_booking_keyword(recent) and self._contains_booking_detail(normalized):
                return "booking"

        # Default to sales
        return "sales"

    @classmethod
    def _contains_booking_keyword(cls, normalized_text: str) -> bool:
        return any(keyword in normalized_text for keyword in cls.BOOKING_KEYWORDS)

    @classmethod
    def _contains_menu_keyword(cls, normalized_text: str) -> bool:
        return any(keyword in normalized_text for keyword in cls.MENU_KEYWORDS)

    @classmethod
    def _is_social_turn(cls, normalized_text: str) -> bool:
        if not normalized_text:
            return True
        if cls._contains_booking_keyword(normalized_text) or cls._contains_menu_keyword(normalized_text):
            return False

        tokens = normalized_text.split()
        compact = " ".join(token for token in tokens if token not in {"a", "nhe", "voi", "giup", "minh", "em"})
        return (
            compact in cls.GREETING_TERMS
            or compact in cls.ACKNOWLEDGEMENT_TERMS
            or compact.startswith("tu van")
            or compact.startswith("ho tro")
        )

    @classmethod
    def _contains_booking_detail(cls, normalized_text: str) -> bool:
        return bool(
            re.search(r"\b\d+\s*(nguoi|khach)\b", normalized_text)
            or re.search(r"\b([01]?\d|2[0-3])[:hg][0-5]?\d?\b", normalized_text)
            or re.search(r"\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b", normalized_text)
            or any(term in normalized_text for term in ["hom nay", "ngay mai", "toi nay", "ngay kia"])
            or any(term in normalized_text for term in cls.TABLE_PREFERENCE_TERMS)
            or re.search(r"\b(?:ban|table)\s*\d+\b", normalized_text)
            or bool(re.search(r"(?:\+?84|0)\d{8,10}", re.sub(r"[^\d+]", "", normalized_text)))
            or bool(re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", normalized_text))
        )

    @classmethod
    def _assistant_asked_booking_question(cls, chat_history: list[dict] = None) -> bool:
        if not chat_history:
            return False

        last_assistant_message = next(
            (
                cls._normalize(message.get("content", ""))
                for message in reversed(chat_history)
                if message.get("role") == "assistant"
            ),
            "",
        )
        if not last_assistant_message:
            return False
        return any(term in last_assistant_message for term in cls.BOOKING_QUESTION_TERMS)

    @classmethod
    def _is_booking_confirmation(cls, normalized_text: str) -> bool:
        return normalized_text in cls.BOOKING_CONFIRMATION_TERMS or any(
            term in normalized_text
            for term in [
                "dong y",
                "dung roi",
                "chinh xac",
                "giu ban giup",
                "dat ban giup",
                "giu ban do",
                "lay ban do",
            ]
        )

    @classmethod
    def _is_booking_followup_response(
        cls,
        normalized_text: str,
        chat_history: list[dict] = None,
    ) -> bool:
        if not cls._assistant_asked_booking_question(chat_history):
            return False
        return cls._is_booking_confirmation(normalized_text) or cls._contains_booking_detail(normalized_text)

    @staticmethod
    def _normalize(text: str) -> str:
        """Normalize Vietnamese text for keyword matching."""
        import unicodedata
        # Remove accents
        nfd = unicodedata.normalize("NFD", text.lower())
        normalized = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
        return normalized.replace("\u0111", "d")


# Singleton instance
_router_instance = None

def get_llm_router(llm_provider: LLMProvider = LLMProvider.OPENAI) -> LLMRouterService:
    """Get or create LLM router singleton."""
    global _router_instance
    if _router_instance is None:
        _router_instance = LLMRouterService(llm_provider)
    return _router_instance
