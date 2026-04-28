from decimal import Decimal
from unittest.mock import MagicMock

from django.test import SimpleTestCase, TestCase, override_settings

from restaurant_booking.models import Booking, BookingPayment, RestaurantProfile, Table
from restaurant_booking.services.llm_router import LLMRouterService
from restaurant_booking.services.sales_chat import RestaurantStructuredChatService, SalesChatPlan
from restaurant_booking.services.booking_payments import (
    create_booking_with_payment,
    process_sepay_ipn,
)
from restaurant_booking.services.availability import booking_has_conflict


def build_candidate(item_id: int, name: str) -> dict:
    return {
        "id": item_id,
        "name": name,
        "category_name": "Món chính",
        "price": 120000,
        "tags": [],
        "badges": [],
        "dietary_labels": [],
        "is_recommended": True,
        "is_best_seller": False,
        "is_vegetarian": False,
        "is_kid_friendly": False,
        "spicy_level": "NONE",
        "description": "",
    }


class RestaurantStructuredChatServiceTests(SimpleTestCase):
    def setUp(self):
        self.service = RestaurantStructuredChatService.__new__(RestaurantStructuredChatService)
        self.service.router = MagicMock()

    def test_route_request_keeps_menu_query_in_sales_even_if_router_returns_booking(self):
        self.service.router.route.return_value = ("booking", 0.92)

        route = self.service._route_request(
            user_input="Gợi ý món cho 2 người",
            chat_history=[],
            selected_item_ids=[],
        )

        self.assertEqual(route, "sales")

    def test_route_request_sends_booking_followup_to_booking(self):
        self.service.router.route.return_value = ("sales", 0.91)
        chat_history = [
            {
                "role": "assistant",
                "content": "Dạ em hỗ trợ đặt bàn cho anh/chị ạ. Anh/chị muốn đặt ngày nào và khoảng mấy giờ ạ?",
            }
        ]

        route = self.service._route_request(
            user_input="7h tối nay",
            chat_history=chat_history,
            selected_item_ids=[],
        )

        self.assertEqual(route, "booking")

    def test_should_start_booking_after_menu_requires_explicit_request(self):
        selected_items = [build_candidate(1, "Sushi cá hồi")]

        self.assertFalse(
            self.service._should_start_booking_after_menu(
                normalized_input="toi nay di 2 nguoi",
                chat_history=[],
                selected_items=selected_items,
            )
        )
        self.assertTrue(
            self.service._should_start_booking_after_menu(
                normalized_input="giu ban giup minh toi nay",
                chat_history=[],
                selected_items=selected_items,
            )
        )

    def test_build_sales_payload_greeting_with_selected_items_forces_clarify_need(self):
        selected_item = build_candidate(99, "Sushi cá hồi")
        recommended_item = {"id": 1, "name": "Set nướng"}
        upsell_item = {"id": 2, "name": "Trà lạnh"}

        self.service._get_restaurant_profile_payload = MagicMock(return_value={"name": "PSCD"})
        self.service._resolve_selected_items = MagicMock(return_value=[selected_item])
        self.service._derive_menu_filters = MagicMock(return_value={})
        self.service._select_candidate_items = MagicMock(return_value=[build_candidate(1, "Set nướng")])
        self.service._build_upsell_candidates = MagicMock(return_value=[build_candidate(2, "Trà lạnh")])
        self.service._invoke_structured_plan = MagicMock(
            return_value=SalesChatPlan(
                intent="upsell",
                assistant_message="Em thấy món này ổn, em giữ bàn luôn cho mình nhé?",
                conversation_goal="close_order",
                sale_stage="decision",
                next_action="upsell",
                next_question=None,
                soft_close="Em giữ bàn luôn cho mình nhé?",
                quick_replies=["Giữ bàn tối nay"],
            )
        )
        self.service._hydrate_item_picks = MagicMock(
            side_effect=[[recommended_item], [upsell_item]]
        )

        payload = self.service._build_sales_payload(
            user_input="Xin chào",
            chat_history=[],
            selected_item_ids=[99],
        )

        self.assertEqual(payload["conversation_goal"], "clarify_need")
        self.assertEqual(payload["sale_stage"], "discovery")
        self.assertEqual(payload["next_action"], "ask_preference")
        self.assertEqual(payload["recommended_items"], [])
        self.assertEqual(payload["upsell_items"], [])
        self.assertIn("Dạ em chào", payload["assistant_message"])
        self.assertNotIn("giu ban", self.service._normalize_text(payload["assistant_message"]))


class LLMRouterServiceFallbackTests(SimpleTestCase):
    def setUp(self):
        self.router = LLMRouterService.__new__(LLMRouterService)

    def test_fallback_route_detects_booking_followup(self):
        chat_history = [
            {
                "role": "assistant",
                "content": "Dạ anh/chị muốn đặt ngày nào và khoảng mấy giờ ạ?",
            }
        ]

        route = self.router._fallback_route("7h tối nay", chat_history)

        self.assertEqual(route, "booking")

    def test_fallback_route_treats_greeting_as_sales_side(self):
        route = self.router._fallback_route("xin chào", [])

        self.assertEqual(route, "sales")


@override_settings(
    SEPAY_MERCHANT_ID="SP-TEST-LOCAL",
    SEPAY_SECRET_KEY="secret-local",
    SEPAY_ENVIRONMENT="sandbox",
)
class BookingPaymentIntegrationTests(TestCase):
    def setUp(self):
        self.table = Table.objects.create(
            table_type=Table.TableType.INDOOR,
            capacity=4,
            floor=1,
            status=Table.TableStatus.AVAILABLE,
        )
        RestaurantProfile.objects.create(
            name="PSCD",
            public_booking_fee_amount=Decimal("100000"),
            chatbot_booking_fee_amount=Decimal("120000"),
            is_active=True,
        )

    def test_create_booking_with_payment_uses_public_fee_for_website_flow(self):
        booking, payment = create_booking_with_payment(
            flow=BookingPayment.BookingFlow.WEBSITE,
            table_id=self.table.id,
            guest_name="Nguyen Van A",
            guest_phone="0901234567",
            guest_email="guest@example.com",
            booking_date="2099-10-10",
            booking_time="19:00",
            party_size=2,
            duration_hours=Decimal("2.0"),
            notes="",
            source=Booking.BookingSource.WEBSITE,
        )

        self.assertEqual(booking.status, Booking.BookingStatus.PENDING)
        self.assertIsNotNone(payment)
        self.assertEqual(payment.amount, Decimal("100000"))
        self.assertEqual(payment.status, BookingPayment.PaymentStatus.PENDING)
        self.assertEqual(payment.flow, BookingPayment.BookingFlow.WEBSITE)

    def test_create_booking_with_payment_uses_chatbot_fee_for_chatbot_flow(self):
        _booking, payment = create_booking_with_payment(
            flow=BookingPayment.BookingFlow.CHATBOT,
            table_id=self.table.id,
            guest_name="Tran Thi B",
            guest_phone="0901234568",
            guest_email="guest2@example.com",
            booking_date="2099-10-11",
            booking_time="20:00",
            party_size=2,
            duration_hours=Decimal("2.0"),
            notes="",
            source=Booking.BookingSource.WEBSITE,
        )

        self.assertEqual(payment.amount, Decimal("120000"))
        self.assertEqual(payment.flow, BookingPayment.BookingFlow.CHATBOT)

    def test_process_sepay_ipn_marks_payment_paid_and_confirms_booking(self):
        booking, payment = create_booking_with_payment(
            flow=BookingPayment.BookingFlow.WEBSITE,
            table_id=self.table.id,
            guest_name="Le Van C",
            guest_phone="0901234569",
            guest_email="guest3@example.com",
            booking_date="2099-10-12",
            booking_time="18:30",
            party_size=2,
            duration_hours=Decimal("2.0"),
            notes="",
            source=Booking.BookingSource.WEBSITE,
        )

        result = process_sepay_ipn(
            {
                "notification_type": "ORDER_PAID",
                "order": {
                    "order_id": "ORDER-123",
                    "order_amount": "100000",
                    "order_currency": "VND",
                    "order_invoice_number": payment.order_invoice_number,
                },
                "transaction": {
                    "transaction_id": "TX-123",
                    "transaction_status": "SUCCESS",
                    "transaction_amount": "100000",
                    "transaction_currency": "VND",
                    "transaction_date": "2099-10-01 10:00:00",
                    "payment_method": "BANK_TRANSFER",
                },
            },
            "secret-local",
        )

        booking.refresh_from_db()
        payment.refresh_from_db()

        self.assertEqual(result["payment_status"], BookingPayment.PaymentStatus.PAID)
        self.assertEqual(payment.status, BookingPayment.PaymentStatus.PAID)
        self.assertEqual(booking.status, Booking.BookingStatus.CONFIRMED)
        self.assertEqual(payment.sepay_transaction_id, "TX-123")

    def test_unpaid_booking_does_not_block_same_table_slot(self):
        booking, _payment = create_booking_with_payment(
            flow=BookingPayment.BookingFlow.WEBSITE,
            table_id=self.table.id,
            guest_name="Guest Pending",
            guest_phone="0901000001",
            guest_email="pending@example.com",
            booking_date="2099-10-14",
            booking_time="19:00",
            party_size=2,
            duration_hours=Decimal("2.0"),
            notes="",
            source=Booking.BookingSource.WEBSITE,
        )

        self.assertEqual(booking.status, Booking.BookingStatus.PENDING)
        self.assertFalse(
            booking_has_conflict(
                table=self.table,
                booking_date="2099-10-14",
                booking_time="19:00",
                duration_hours=Decimal("2.0"),
            )
        )

    def test_paid_booking_is_cancelled_if_slot_was_confirmed_by_other_booking(self):
        first_booking, first_payment = create_booking_with_payment(
            flow=BookingPayment.BookingFlow.WEBSITE,
            table_id=self.table.id,
            guest_name="First Guest",
            guest_phone="0901000002",
            guest_email="first@example.com",
            booking_date="2099-10-15",
            booking_time="19:00",
            party_size=2,
            duration_hours=Decimal("2.0"),
            notes="",
            source=Booking.BookingSource.WEBSITE,
        )
        second_booking, second_payment = create_booking_with_payment(
            flow=BookingPayment.BookingFlow.WEBSITE,
            table_id=self.table.id,
            guest_name="Second Guest",
            guest_phone="0901000003",
            guest_email="second@example.com",
            booking_date="2099-10-15",
            booking_time="19:00",
            party_size=2,
            duration_hours=Decimal("2.0"),
            notes="",
            source=Booking.BookingSource.WEBSITE,
        )

        second_payment.status = BookingPayment.PaymentStatus.PAID
        second_payment.save(update_fields=["status", "updated_at"])
        second_booking.mark_confirmed()

        result = process_sepay_ipn(
            {
                "notification_type": "ORDER_PAID",
                "order": {
                    "order_id": "ORDER-CONFLICT",
                    "order_amount": "100000",
                    "order_currency": "VND",
                    "order_invoice_number": first_payment.order_invoice_number,
                },
                "transaction": {
                    "transaction_id": "TX-CONFLICT",
                    "transaction_status": "SUCCESS",
                    "transaction_amount": "100000",
                    "transaction_currency": "VND",
                    "transaction_date": "2099-10-01 10:00:00",
                    "payment_method": "BANK_TRANSFER",
                },
            },
            "secret-local",
        )

        first_booking.refresh_from_db()
        first_payment.refresh_from_db()

        self.assertEqual(first_payment.status, BookingPayment.PaymentStatus.PAID)
        self.assertEqual(first_booking.status, Booking.BookingStatus.CANCELLED)
        self.assertEqual(result["booking_status"], Booking.BookingStatus.CANCELLED)
