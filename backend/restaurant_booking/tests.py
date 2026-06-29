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

    def test_create_booking_without_deposit_skips_payment_and_confirms(self):
        booking, payment = create_booking_with_payment(
            flow=BookingPayment.BookingFlow.CHATBOT,
            table_id=self.table.id,
            guest_name="Pham Thi D",
            guest_phone="0901234570",
            guest_email="guest4@example.com",
            booking_date="2099-10-13",
            booking_time="18:00",
            party_size=2,
            duration_hours=Decimal("2.0"),
            notes="",
            source=Booking.BookingSource.WEBSITE,
            with_deposit=False,
        )

        self.assertIsNone(payment)
        self.assertEqual(booking.status, Booking.BookingStatus.CONFIRMED)

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


class SlotExtractorTests(SimpleTestCase):
    def setUp(self):
        from restaurant_booking.services.slot_extractor import BookingSlotExtractor

        self.extractor = BookingSlotExtractor()
        self.extractor.enable_llm = False

    def test_email_is_not_misread_as_a_date(self):
        values = self.extractor.extract_from_text("levansia1ct@gmail.com")
        self.assertEqual(values.get("guest_email"), "levansia1ct@gmail.com")
        self.assertNotIn("booking_date", values)

    def test_tomorrow_and_evening_time(self):
        values = self.extractor.extract_from_text("Ngày mai và 7h tối")
        self.assertIn("booking_date", values)
        self.assertEqual(values.get("booking_time"), "19:00")

    def test_defer_choice_and_affirmation(self):
        self.assertTrue(self.extractor.is_defer_choice("Chọn cho tôi 1 chỗ hợp lí nhé"))
        self.assertTrue(self.extractor.is_affirmative("Ok chốt đi"))
        self.assertFalse(self.extractor.is_affirmative("Không phải"))

    def test_table_choice_by_id_and_by_position(self):
        options = [{"table_id": 28, "floor": 2}, {"table_id": 29, "floor": 2}]
        self.assertEqual(self.extractor.parse_table_choice("Chọn bàn 28 nhé", options), 28)
        self.assertEqual(self.extractor.parse_table_choice("Phương án 2", options), 29)

    def test_bare_contact_name_with_phone(self):
        self.assertEqual(self.extractor.extract_contact_name("Sỷ, 0334407762"), "Sỷ")
        self.assertEqual(self.extractor.extract_contact_name("Tên Lê Văn Sỹ"), "Lê Văn Sỹ")

    def test_placeholder_values_never_fill_slots(self):
        from restaurant_booking.services.slot_extractor import is_placeholder

        self.assertTrue(is_placeholder("null"))
        self.assertTrue(is_placeholder("None"))
        self.assertTrue(is_placeholder(""))
        self.assertFalse(is_placeholder("Sỷ"))

        merged = self.extractor.merge(
            existing_slots={"guest_name": "null", "guest_email": "null"},
            user_input="0334407762",
            use_llm=False,
        )
        self.assertNotIn("guest_name", merged)
        self.assertNotIn("guest_email", merged)
        self.assertEqual(merged.get("guest_phone"), "0334407762")


@override_settings(
    SEPAY_MERCHANT_ID="SP-TEST-LOCAL",
    SEPAY_SECRET_KEY="secret-local",
    SEPAY_ENVIRONMENT="sandbox",
)
class ConversationOrchestratorFlowTests(TestCase):
    def setUp(self):
        from restaurant_booking.services.conversation_orchestrator import ConversationOrchestrator

        self.orchestrator = ConversationOrchestrator()
        # Keep the flow deterministic: rely only on regex/keyword parsing.
        self.orchestrator.extractor.enable_llm = False

        RestaurantProfile.objects.create(
            name="PSCD",
            public_booking_fee_amount=Decimal("100000"),
            chatbot_booking_fee_amount=Decimal("120000"),
            is_active=True,
        )
        self.tables = [
            Table.objects.create(
                table_type=Table.TableType.INDOOR,
                capacity=capacity,
                floor=2,
                status=Table.TableStatus.AVAILABLE,
            )
            for capacity in (2, 4, 6)
        ]

        self.session_id = "test-session-1"
        self.history = []

    def _say(self, text):
        payload = self.orchestrator.build_response(
            session_id=self.session_id,
            user_input=text,
            chat_history=self.history,
            selected_item_ids=[],
        )
        self.history.append({"role": "user", "content": text})
        self.history.append({"role": "assistant", "content": payload["assistant_message"]})
        return payload

    def _normalize(self, text):
        from restaurant_booking.services.slot_extractor import normalize_text

        return normalize_text(text)

    def test_booking_flow_closes_without_relooping(self):
        # 1. Enter booking.
        payload = self._say("Tôi muốn đặt bàn")
        self.assertEqual(payload["intent"], "booking")
        self.assertIn("ngay nao", self._normalize(payload["assistant_message"]))

        # 2. Date + time together.
        payload = self._say("Ngày mai 19:00")
        normalized = self._normalize(payload["assistant_message"])
        self.assertIn("may nguoi", normalized)

        # 3. Party size -> seating question, no menu greeting loop.
        payload = self._say("2 người")
        self.assertNotIn("xem menu", self._normalize(payload["assistant_message"]))

        # 4. Defer the seating choice -> the bot lists concrete tables.
        payload = self._say("Chọn cho tôi 1 chỗ hợp lý")
        self.assertTrue(payload["available_tables"], "Expected available tables to be offered")
        chosen_table_id = payload["available_tables"][0]["table_id"]

        # 5. Pick a table -> asks for contact (name + phone).
        payload = self._say(f"Chọn bàn {chosen_table_id}")
        self.assertIn("so dien thoai", self._normalize(payload["assistant_message"]))

        # 6. Provide name + phone -> asks for email (never re-asks the name).
        payload = self._say("Tôi tên Sỹ, số điện thoại 0334407762")
        self.assertIn("email", self._normalize(payload["assistant_message"]))

        # 7. Provide email -> confirmation summary.
        payload = self._say("levansia1ct@gmail.com")
        self.assertIsNotNone(payload["booking_summary"])
        self.assertEqual(payload["booking_summary"]["guest_name"], "Sỹ")
        self.assertEqual(payload["booking_summary"]["table_id"], chosen_table_id)

        # 8. Confirm -> booking is created with a hold deposit (SePay).
        payload = self._say("Xác nhận")
        self.assertTrue(payload["booking_code"], "Expected a booking code after confirmation")
        booking = Booking.objects.get(code=payload["booking_code"])
        # Every chatbot booking now requires a deposit, so it stays PENDING
        # until SePay confirms payment.
        self.assertEqual(booking.status, Booking.BookingStatus.PENDING)
        self.assertTrue(hasattr(booking, "payment"))
        self.assertIn("sepay", self._normalize(payload["assistant_message"]))
        self.assertEqual(booking.guest_name, "Sỹ")
        self.assertEqual(booking.guest_phone, "0334407762")

    def test_bare_name_reply_is_captured_and_asks_email(self):
        self._say("Tôi muốn đặt bàn")
        self._say("Tối nay 19:00")
        self._say("2 người")
        listing = self._say("Trong nhà")
        table_id = listing["available_tables"][0]["table_id"]
        self._say(f"Bàn {table_id}")

        # Bare name + phone in one message (no "tên là" prefix).
        payload = self._say("Sỷ, 0334407762")
        # Must ask for the email next, not jump to a confirmation with nulls.
        self.assertIn("email", self._normalize(payload["assistant_message"]))
        self.assertIsNone(payload["booking_summary"])

        payload = self._say("levansia1ct@gmail.com")
        self.assertIsNotNone(payload["booking_summary"])
        self.assertEqual(payload["booking_summary"]["guest_name"], "Sỷ")
        self.assertNotIn("null", self._normalize(payload["assistant_message"]))

    def test_name_is_remembered_and_not_reasked(self):
        self._say("Tôi tên Sỹ, tôi muốn đặt bàn")
        session = self.orchestrator._load_or_create_session(self.session_id)
        self.assertEqual(session.customer_name, "Sỹ")

        # A later bare answer must not drop back to the sales greeting loop.
        payload = self._say("Ngày mai 19:00")
        self.assertEqual(payload["intent"], "booking")
        self.assertNotIn(
            "xem menu, goi y mon hay giai dap",
            self._normalize(payload["assistant_message"]),
        )

    def test_preordered_items_trigger_deposit_link(self):
        payload = self.orchestrator.build_response(
            session_id="deposit-session",
            user_input="Tôi muốn đặt bàn",
            chat_history=[],
            selected_item_ids=[123],
        )
        history = [
            {"role": "user", "content": "Tôi muốn đặt bàn"},
            {"role": "assistant", "content": payload["assistant_message"]},
        ]

        def say(text, items=None):
            nonlocal history
            result = self.orchestrator.build_response(
                session_id="deposit-session",
                user_input=text,
                chat_history=history,
                selected_item_ids=items or [],
            )
            history.append({"role": "user", "content": text})
            history.append({"role": "assistant", "content": result["assistant_message"]})
            return result

        say("Ngày mai 19:00")
        say("2 người")
        listing = say("Trong nhà tầng 2")
        self.assertTrue(listing["available_tables"])
        table_id = listing["available_tables"][0]["table_id"]
        contact = say(f"Chọn bàn {table_id}")
        # Deposit explanation must appear once a table is chosen for preorders.
        self.assertIn("dat coc", self._normalize(contact["assistant_message"]))
        say("Tôi tên Sỹ, số điện thoại 0334407762")
        say("levansia1ct@gmail.com")
        done = say("Xác nhận")
        self.assertTrue(done["booking_code"])
        booking = Booking.objects.get(code=done["booking_code"])
        # Deposit flow leaves the booking pending until SePay confirms payment.
        self.assertEqual(booking.status, Booking.BookingStatus.PENDING)
        self.assertTrue(hasattr(booking, "payment"))
        self.assertIn("sepay", self._normalize(done["assistant_message"]))


class AdminRevenueReportTests(TestCase):
    def setUp(self):
        from datetime import time

        from django.utils import timezone

        from accounts.models.user import User
        from restaurant_booking.models import Payment, TableSession
        from rest_framework.test import APIClient

        self.client = APIClient()
        self.user = User.objects.create_user(
            email="reporter@example.com",
            password="pw",
            role=User.UserRole.SUPER_ADMIN,
            status=User.UserStatus.ACTIVE,
        )
        self.client.force_authenticate(self.user)

        self.table = Table.objects.create(
            table_type=Table.TableType.INDOOR,
            capacity=4,
            floor=1,
            status=Table.TableStatus.AVAILABLE,
        )
        now = timezone.now()

        # Dine-in revenue: a paid table-session payment (200,000 VND).
        session = TableSession.objects.create(guest_name="Khach 1", guest_count=2)
        Payment.objects.create(
            table_session=session,
            status=Payment.PaymentStatus.PAID,
            method=Payment.PaymentMethod.CASH,
            subtotal_amount=Decimal("200000"),
            paid_at=now,
        )

        # Deposit revenue: a paid chatbot booking deposit (120,000 VND).
        booking = Booking.objects.create(
            table=self.table,
            guest_name="Khach 2",
            guest_phone="0900000000",
            guest_email="khach2@example.com",
            booking_date=timezone.localdate(),
            booking_time=time(19, 0),
            party_size=2,
        )
        BookingPayment.objects.create(
            booking=booking,
            provider=BookingPayment.Provider.SEPAY,
            flow=BookingPayment.BookingFlow.CHATBOT,
            status=BookingPayment.PaymentStatus.PAID,
            amount=Decimal("120000"),
            currency="VND",
            order_invoice_number="BK-REVENUE-TEST",
            paid_at=now,
        )

    def test_revenue_report_aggregates_dine_in_and_deposits(self):
        response = self.client.get("/api/admin/reports/revenue/")

        self.assertEqual(response.status_code, 200)
        summary = response.data["summary"]
        self.assertEqual(summary["dine_in_revenue"], 200000.0)
        self.assertEqual(summary["deposit_revenue"], 120000.0)
        self.assertEqual(summary["total_revenue"], 320000.0)
        self.assertEqual(summary["dine_in_count"], 1)
        self.assertEqual(summary["deposit_count"], 1)

        chatbot_flow = next(
            row for row in response.data["deposit_by_flow"] if row["flow"] == "CHATBOT"
        )
        self.assertEqual(chatbot_flow["amount"], 120000.0)
        self.assertEqual(len(response.data["timeseries"]), response.data["range"]["days"])

    def test_revenue_report_requires_reporting_permission(self):
        from accounts.models.user import User
        from rest_framework.test import APIClient

        waiter = User.objects.create_user(
            email="waiter@example.com",
            password="pw",
            role=User.UserRole.WAITER,
            status=User.UserStatus.ACTIVE,
        )
        client = APIClient()
        client.force_authenticate(waiter)

        response = client.get("/api/admin/reports/revenue/")
        self.assertEqual(response.status_code, 403)
