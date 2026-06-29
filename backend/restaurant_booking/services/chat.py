import json
import logging

from restaurant_booking.services.conversation_orchestrator import ConversationOrchestrator

logger = logging.getLogger(__name__)


class RestaurantBookingChatService:
    def __init__(self):
        self.orchestrator = ConversationOrchestrator()

    def chat(self, request, data):
        user_input = data.get("user_input", "")
        chat_history = data.get("chat_history", [])
        selected_item_ids = data.get("selected_item_ids", [])
        session_id = data.get("session_id")

        yield f"data: {json.dumps({'type': 'start'})}\n\n"
        try:
            payload = self.orchestrator.build_response(
                session_id=session_id,
                user_input=user_input,
                chat_history=chat_history,
                selected_item_ids=selected_item_ids,
            )
            yield f"data: {json.dumps({'type': 'payload', 'content': payload}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'end'})}\n\n"
        except Exception:
            logger.exception("Restaurant booking chat failed.")
            message = "Xin lỗi, PSCD đang gặp sự cố khi phản hồi. Mình vui lòng thử lại sau ít phút ạ."
            yield f"data: {json.dumps({'type': 'error', 'content': message}, ensure_ascii=False)}\n\n"
