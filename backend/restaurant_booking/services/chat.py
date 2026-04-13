import json

from restaurant_booking.services.sales_chat import RestaurantStructuredChatService


class RestaurantBookingChatService:
    def __init__(self):
        self.chat_service = RestaurantStructuredChatService()

    def chat(self, request, data):
        user_input = data.get("user_input", "")
        chat_history = data.get("chat_history", [])
        selected_item_ids = data.get("selected_item_ids", [])

        yield f"data: {json.dumps({'type': 'start'})}\n\n"
        try:
            payload = self.chat_service.build_response(
                user_input=user_input,
                chat_history=chat_history,
                selected_item_ids=selected_item_ids,
            )
            yield f"data: {json.dumps({'type': 'payload', 'content': payload}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'end'})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'content': str(exc)}, ensure_ascii=False)}\n\n"
