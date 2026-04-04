from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from restaurant_booking.models import (
    Booking,
    Invoice,
    MenuItem,
    Order,
    OrderItem,
    Payment,
    SessionTable,
    Table,
    TableSession,
)
from restaurant_booking.realtime import publish_realtime_event
from restaurant_booking.services.availability import BookingValidationError


ACTIVE_SESSION_STATUSES = [
    TableSession.SessionStatus.OPEN,
    TableSession.SessionStatus.PAYMENT_PENDING,
]
MUTABLE_ORDER_STATUSES = [
    Order.OrderStatus.OPEN,
    Order.OrderStatus.SENT_TO_KITCHEN,
    Order.OrderStatus.PARTIALLY_SERVED,
]


def _publish_operations_event(event_type, payload=None):
    publish_realtime_event(
        {
            "domain": "restaurant_booking",
            "type": event_type,
            "payload": payload or {},
            "emitted_at": timezone.now().isoformat(),
        }
    )


def _get_session_queryset():
    return TableSession.objects.select_related(
        "booking",
        "opened_by",
        "closed_by",
    ).prefetch_related(
        "session_tables__table",
        "orders__items",
        "payments",
    )


def _get_order_queryset():
    return Order.objects.select_related(
        "table_session",
        "created_by",
    ).prefetch_related("items")


def _ensure_session_mutable(session):
    if session.status not in ACTIVE_SESSION_STATUSES:
        raise BookingValidationError(
            {"table_session_id": "Phiên phục vụ này không còn ở trạng thái thao tác."}
        )


def _ensure_order_mutable(order):
    if order.status not in MUTABLE_ORDER_STATUSES:
        raise BookingValidationError({"order_id": "Order này không còn cho phép chỉnh sửa."})


def _find_active_assignment_for_table(table_id, *, for_update=False):
    assignments = SessionTable.objects.filter(
        table_id=table_id,
        is_deleted=False,
        is_active=True,
        table_session__is_deleted=False,
        table_session__status__in=ACTIVE_SESSION_STATUSES,
    )
    if for_update:
        assignments = assignments.select_for_update()
    return assignments.first()


def _lock_table_for_assignment(table_id, *, allow_reserved=False):
    table = (
        Table.objects.select_for_update()
        .filter(id=table_id, is_deleted=False)
        .first()
    )

    if not table:
        raise BookingValidationError({"table_id": f"Bàn {table_id} không tồn tại."})

    allowed_statuses = [Table.TableStatus.AVAILABLE]
    if allow_reserved:
        allowed_statuses.append(Table.TableStatus.RESERVED)

    if table.status not in allowed_statuses:
        raise BookingValidationError(
            {
                "table_id": (
                    f"Bàn {table_id} hiện không thể gán cho phiên phục vụ "
                    f"({table.get_status_display()})."
                )
            }
        )

    active_assignment = _find_active_assignment_for_table(table_id, for_update=True)
    if active_assignment:
        raise BookingValidationError(
            {"table_id": f"Bàn {table_id} đang thuộc một phiên phục vụ khác."}
        )

    return table


def _set_table_available_if_released(table):
    still_in_use = SessionTable.objects.filter(
        table=table,
        is_deleted=False,
        is_active=True,
        table_session__status__in=ACTIVE_SESSION_STATUSES,
    ).exists()
    if not still_in_use and table.status != Table.TableStatus.AVAILABLE:
        table.status = Table.TableStatus.AVAILABLE
        table.save(update_fields=["status", "updated_at"])


def list_table_sessions(status=None):
    sessions = _get_session_queryset().filter(is_deleted=False).order_by("-opened_at", "-id")
    if status:
        sessions = sessions.filter(status=status)
    return sessions


def list_orders(status=None):
    orders = _get_order_queryset().filter(is_deleted=False).order_by("-created_at", "-id")
    if status:
        orders = orders.filter(status=status)
    return orders


def list_payments(status=None):
    payments = Payment.objects.select_related("table_session", "paid_by").filter(
        is_deleted=False
    ).order_by("-created_at", "-id")
    if status:
        payments = payments.filter(status=status)
    return payments


def open_table_session(
    *,
    table_ids,
    guest_name="",
    guest_phone="",
    guest_count=1,
    booking_id=None,
    notes="",
    actor=None,
):
    table_ids = [int(table_id) for table_id in table_ids or [] if table_id]
    if not table_ids:
        raise BookingValidationError({"table_ids": "Cần chọn ít nhất một bàn."})

    with transaction.atomic():
        booking = None
        if booking_id:
            booking = (
                Booking.objects.select_for_update()
                .filter(id=booking_id, is_deleted=False)
                .first()
            )
            if not booking:
                raise BookingValidationError({"booking_id": "Booking không tồn tại."})

        session = TableSession.objects.create(
            booking=booking,
            guest_name=guest_name or getattr(booking, "guest_name", None),
            guest_phone=guest_phone or getattr(booking, "guest_phone", None),
            guest_count=guest_count or getattr(booking, "party_size", 1),
            notes=notes or getattr(booking, "notes", ""),
            opened_by=actor,
            status=TableSession.SessionStatus.OPEN,
        )

        for index, table_id in enumerate(table_ids):
            table = _lock_table_for_assignment(
                table_id,
                allow_reserved=booking is not None,
            )
            table.status = Table.TableStatus.OCCUPIED
            table.save(update_fields=["status", "updated_at"])

            SessionTable.objects.create(
                table_session=session,
                table=table,
                role=(
                    SessionTable.AssignmentRole.PRIMARY
                    if index == 0
                    else SessionTable.AssignmentRole.MERGED
                ),
                is_active=True,
            )

        if booking and booking.status in [
            Booking.BookingStatus.PENDING,
            Booking.BookingStatus.CONFIRMED,
        ]:
            booking.status = Booking.BookingStatus.CONFIRMED
            booking.save(update_fields=["status", "updated_at"])

    _publish_operations_event(
        "session.changed",
        {"table_session_id": session.id, "action": "opened"},
    )
    return _get_session_queryset().get(id=session.id)


def update_table_session(session_id, *, guest_name=None, guest_phone=None, guest_count=None, notes=None):
    with transaction.atomic():
        session = _get_session_queryset().select_for_update().filter(
            id=session_id,
            is_deleted=False,
        ).first()
        if not session:
            raise BookingValidationError({"table_session_id": "Phiên phục vụ không tồn tại."})

        _ensure_session_mutable(session)

        update_fields = ["updated_at"]
        if guest_name is not None:
            session.guest_name = guest_name
            update_fields.append("guest_name")
        if guest_phone is not None:
            session.guest_phone = guest_phone
            update_fields.append("guest_phone")
        if guest_count is not None:
            session.guest_count = guest_count
            update_fields.append("guest_count")
        if notes is not None:
            session.notes = notes
            update_fields.append("notes")

        session.save(update_fields=update_fields)

    _publish_operations_event(
        "session.changed",
        {"table_session_id": session.id, "action": "updated"},
    )
    return _get_session_queryset().get(id=session.id)


def merge_table_into_session(session_id, *, table_id):
    with transaction.atomic():
        session = _get_session_queryset().select_for_update().filter(
            id=session_id,
            is_deleted=False,
        ).first()
        if not session:
            raise BookingValidationError({"table_session_id": "Phiên phục vụ không tồn tại."})

        _ensure_session_mutable(session)
        if SessionTable.objects.filter(
            table_session=session,
            table_id=table_id,
            is_deleted=False,
            is_active=True,
        ).exists():
            raise BookingValidationError({"table_id": "Bàn này đã nằm trong phiên phục vụ."})

        table = _lock_table_for_assignment(table_id)
        table.status = Table.TableStatus.OCCUPIED
        table.save(update_fields=["status", "updated_at"])

        SessionTable.objects.create(
            table_session=session,
            table=table,
            role=SessionTable.AssignmentRole.MERGED,
            is_active=True,
        )

    _publish_operations_event(
        "session.changed",
        {"table_session_id": session.id, "action": "table_merged"},
    )
    return _get_session_queryset().get(id=session.id)


def move_table_in_session(session_id, *, from_table_id, to_table_id):
    with transaction.atomic():
        session = _get_session_queryset().select_for_update().filter(
            id=session_id,
            is_deleted=False,
        ).first()
        if not session:
            raise BookingValidationError({"table_session_id": "Phiên phục vụ không tồn tại."})

        _ensure_session_mutable(session)

        source_assignment = (
            SessionTable.objects.select_for_update()
            .filter(
                table_session=session,
                table_id=from_table_id,
                is_deleted=False,
                is_active=True,
            )
            .select_related("table")
            .first()
        )
        if not source_assignment:
            raise BookingValidationError({"from_table_id": "Bàn nguồn không nằm trong phiên."})

        target_table = _lock_table_for_assignment(to_table_id)
        target_table.status = Table.TableStatus.OCCUPIED
        target_table.save(update_fields=["status", "updated_at"])

        source_assignment.is_active = False
        source_assignment.released_at = timezone.now()
        source_assignment.save(update_fields=["is_active", "released_at", "updated_at"])

        SessionTable.objects.create(
            table_session=session,
            table=target_table,
            role=source_assignment.role,
            is_active=True,
        )

        _set_table_available_if_released(source_assignment.table)

    _publish_operations_event(
        "session.changed",
        {"table_session_id": session.id, "action": "table_moved"},
    )
    return _get_session_queryset().get(id=session.id)


def create_order(session_id, *, actor=None, notes=""):
    with transaction.atomic():
        session = TableSession.objects.select_for_update().filter(
            id=session_id,
            is_deleted=False,
        ).first()
        if not session:
            raise BookingValidationError({"table_session_id": "Phiên phục vụ không tồn tại."})

        _ensure_session_mutable(session)

        order = Order.objects.create(
            table_session=session,
            created_by=actor,
            status=Order.OrderStatus.OPEN,
            notes=notes,
        )

    _publish_operations_event("order.changed", {"order_id": order.id, "action": "created"})
    return _get_order_queryset().get(id=order.id)


def update_order(order_id, *, notes=None, status=None):
    with transaction.atomic():
        order = Order.objects.select_for_update().filter(id=order_id, is_deleted=False).first()
        if not order:
            raise BookingValidationError({"order_id": "Order không tồn tại."})

        _ensure_order_mutable(order)

        update_fields = ["updated_at"]
        if notes is not None:
            order.notes = notes
            update_fields.append("notes")
        if status is not None:
            order.status = status
            update_fields.append("status")

        order.save(update_fields=update_fields)

    _publish_operations_event("order.changed", {"order_id": order.id, "action": "updated"})
    return _get_order_queryset().get(id=order.id)


def add_order_item(order_id, *, menu_item_id, quantity, note="", actor=None):
    quantity = int(quantity)
    if quantity <= 0:
        raise BookingValidationError({"quantity": "Số lượng phải lớn hơn 0."})

    with transaction.atomic():
        order = Order.objects.select_for_update().filter(id=order_id, is_deleted=False).first()
        if not order:
            raise BookingValidationError({"order_id": "Order không tồn tại."})

        _ensure_order_mutable(order)

        menu_item = MenuItem.objects.filter(id=menu_item_id, is_deleted=False).first()
        if not menu_item:
            raise BookingValidationError({"menu_item_id": "Món ăn không tồn tại."})
        if menu_item.status != MenuItem.AvailabilityStatus.ACTIVE:
            raise BookingValidationError(
                {"menu_item_id": f"Món {menu_item.name} hiện chưa sẵn sàng để order."}
            )

        existing_item = OrderItem.objects.select_for_update().filter(
            order=order,
            menu_item=menu_item,
            note=note or None,
            kitchen_status=OrderItem.KitchenStatus.PENDING,
            is_deleted=False,
        ).first()

        if existing_item:
            existing_item.quantity += quantity
            existing_item.save(update_fields=["quantity", "updated_at"])
            item = existing_item
        else:
            item = OrderItem.objects.create(
                order=order,
                menu_item=menu_item,
                item_name=menu_item.name,
                quantity=quantity,
                unit_price=menu_item.price,
                note=note or None,
                created_by=actor,
            )

        if order.status == Order.OrderStatus.CANCELLED:
            order.status = Order.OrderStatus.OPEN
            order.save(update_fields=["status", "updated_at"])

    _publish_operations_event("order.changed", {"order_id": order.id, "action": "item_added"})
    return _get_order_queryset().get(id=order.id), item


def update_order_item(order_item_id, *, quantity=None, note=None):
    with transaction.atomic():
        item = OrderItem.objects.select_related("order").select_for_update().filter(
            id=order_item_id,
            is_deleted=False,
        ).first()
        if not item:
            raise BookingValidationError({"order_item_id": "Món trong order không tồn tại."})

        _ensure_order_mutable(item.order)

        update_fields = ["updated_at"]
        if quantity is not None:
            quantity = int(quantity)
            if quantity <= 0:
                raise BookingValidationError({"quantity": "Số lượng phải lớn hơn 0."})
            item.quantity = quantity
            update_fields.append("quantity")
        if note is not None:
            item.note = note or None
            update_fields.append("note")

        item.save(update_fields=update_fields)

    _publish_operations_event(
        "order.changed",
        {"order_id": item.order_id, "action": "item_updated"},
    )
    return item


def remove_order_item(order_item_id):
    with transaction.atomic():
        item = OrderItem.objects.select_related("order").select_for_update().filter(
            id=order_item_id,
            is_deleted=False,
        ).first()
        if not item:
            raise BookingValidationError({"order_item_id": "Món trong order không tồn tại."})

        _ensure_order_mutable(item.order)
        item.delete()

    _publish_operations_event(
        "order.changed",
        {"order_id": item.order_id, "action": "item_removed"},
    )
    return item.order_id


def send_order_to_kitchen(order_id):
    with transaction.atomic():
        order = Order.objects.select_for_update().filter(id=order_id, is_deleted=False).first()
        if not order:
            raise BookingValidationError({"order_id": "Order không tồn tại."})

        _ensure_order_mutable(order)

        pending_items = OrderItem.objects.filter(
            order=order,
            is_deleted=False,
            kitchen_status=OrderItem.KitchenStatus.PENDING,
        )
        if not pending_items.exists():
            raise BookingValidationError({"order_id": "Order không có món mới để gửi bếp."})

        pending_items.update(
            kitchen_status=OrderItem.KitchenStatus.SENT_TO_KITCHEN,
            updated_at=timezone.now(),
        )
        order.status = Order.OrderStatus.SENT_TO_KITCHEN
        order.sent_to_kitchen_at = timezone.now()
        order.save(update_fields=["status", "sent_to_kitchen_at", "updated_at"])

    _publish_operations_event(
        "order.changed",
        {"order_id": order.id, "action": "sent_to_kitchen"},
    )
    return _get_order_queryset().get(id=order.id)


def split_order_item(order_id, *, order_item_id, quantity, target_order_id=None, actor=None):
    quantity = int(quantity)
    if quantity <= 0:
        raise BookingValidationError({"quantity": "Số lượng tách phải lớn hơn 0."})

    with transaction.atomic():
        order = Order.objects.select_related("table_session").select_for_update().filter(
            id=order_id,
            is_deleted=False,
        ).first()
        if not order:
            raise BookingValidationError({"order_id": "Order nguồn không tồn tại."})

        _ensure_order_mutable(order)

        item = OrderItem.objects.select_for_update().filter(
            id=order_item_id,
            order=order,
            is_deleted=False,
        ).first()
        if not item:
            raise BookingValidationError({"order_item_id": "Món cần tách không tồn tại."})
        if quantity > item.quantity:
            raise BookingValidationError({"quantity": "Số lượng tách vượt quá số lượng hiện có."})

        if target_order_id:
            target_order = Order.objects.select_for_update().filter(
                id=target_order_id,
                table_session=order.table_session,
                is_deleted=False,
            ).first()
            if not target_order:
                raise BookingValidationError({"target_order_id": "Order đích không hợp lệ."})
            _ensure_order_mutable(target_order)
        else:
            target_order = Order.objects.create(
                table_session=order.table_session,
                created_by=actor,
                status=Order.OrderStatus.OPEN,
                notes="Order được tách từ order khác",
            )

        if quantity == item.quantity:
            item.order = target_order
            item.save(update_fields=["order", "updated_at"])
        else:
            item.quantity -= quantity
            item.save(update_fields=["quantity", "updated_at"])
            OrderItem.objects.create(
                order=target_order,
                menu_item=item.menu_item,
                item_name=item.item_name,
                quantity=quantity,
                unit_price=item.unit_price,
                kitchen_status=item.kitchen_status,
                note=item.note,
                created_by=actor,
            )

    _publish_operations_event(
        "order.changed",
        {"order_id": order.id, "target_order_id": target_order.id, "action": "split"},
    )
    return _get_order_queryset().get(id=order.id), _get_order_queryset().get(id=target_order.id)


def merge_orders(*, source_order_id, target_order_id):
    if source_order_id == target_order_id:
        raise BookingValidationError({"target_order_id": "Order nguồn và order đích phải khác nhau."})

    with transaction.atomic():
        source_order = Order.objects.select_related("table_session").select_for_update().filter(
            id=source_order_id,
            is_deleted=False,
        ).first()
        target_order = Order.objects.select_related("table_session").select_for_update().filter(
            id=target_order_id,
            is_deleted=False,
        ).first()

        if not source_order or not target_order:
            raise BookingValidationError({"order_id": "Không tìm thấy order nguồn hoặc order đích."})
        if source_order.table_session_id != target_order.table_session_id:
            raise BookingValidationError({"target_order_id": "Chỉ được ghép các order cùng một phiên."})

        _ensure_order_mutable(source_order)
        _ensure_order_mutable(target_order)

        for item in OrderItem.objects.select_for_update().filter(
            order=source_order,
            is_deleted=False,
        ):
            matched_item = OrderItem.objects.select_for_update().filter(
                order=target_order,
                menu_item=item.menu_item,
                unit_price=item.unit_price,
                note=item.note,
                kitchen_status=item.kitchen_status,
                is_deleted=False,
            ).first()

            if matched_item:
                matched_item.quantity += item.quantity
                matched_item.save(update_fields=["quantity", "updated_at"])
                item.delete()
            else:
                item.order = target_order
                item.save(update_fields=["order", "updated_at"])

        source_order.status = Order.OrderStatus.COMPLETED
        source_order.closed_at = timezone.now()
        source_order.save(update_fields=["status", "closed_at", "updated_at"])

    _publish_operations_event(
        "order.changed",
        {"source_order_id": source_order_id, "target_order_id": target_order_id, "action": "merged"},
    )
    return _get_order_queryset().get(id=target_order_id)


def checkout_table_session(session_id, *, method, actor=None, issue_invoice=True, note=""):
    with transaction.atomic():
        session = _get_session_queryset().select_for_update().filter(
            id=session_id,
            is_deleted=False,
        ).first()
        if not session:
            raise BookingValidationError({"table_session_id": "Phiên phục vụ không tồn tại."})

        _ensure_session_mutable(session)

        active_items = OrderItem.objects.filter(
            order__table_session=session,
            order__is_deleted=False,
            is_deleted=False,
        ).exclude(kitchen_status=OrderItem.KitchenStatus.CANCELLED)

        if not active_items.exists():
            raise BookingValidationError({"table_session_id": "Phiên phục vụ chưa có món để thanh toán."})

        subtotal_amount = sum((item.line_total for item in active_items), Decimal("0.00"))

        payment = Payment.objects.create(
            table_session=session,
            method=method,
            status=Payment.PaymentStatus.PAID,
            subtotal_amount=subtotal_amount,
            note=note,
            paid_at=timezone.now(),
            paid_by=actor,
        )

        invoice = None
        if issue_invoice:
            invoice = Invoice.objects.create(
                table_session=session,
                payment=payment,
                issued_by=actor,
                customer_name=session.guest_name,
                note=note,
            )

        Order.objects.filter(
            table_session=session,
            is_deleted=False,
            status__in=MUTABLE_ORDER_STATUSES,
        ).update(
            status=Order.OrderStatus.COMPLETED,
            closed_at=timezone.now(),
            updated_at=timezone.now(),
        )

        session.status = TableSession.SessionStatus.CLOSED
        session.closed_at = timezone.now()
        session.closed_by = actor
        session.save(update_fields=["status", "closed_at", "closed_by", "updated_at"])

        for assignment in SessionTable.objects.select_for_update().filter(
            table_session=session,
            is_deleted=False,
            is_active=True,
        ).select_related("table"):
            assignment.is_active = False
            assignment.released_at = timezone.now()
            assignment.save(update_fields=["is_active", "released_at", "updated_at"])
            _set_table_available_if_released(assignment.table)

        if session.booking and session.booking.status in [
            Booking.BookingStatus.PENDING,
            Booking.BookingStatus.CONFIRMED,
        ]:
            session.booking.status = Booking.BookingStatus.COMPLETED
            session.booking.save(update_fields=["status", "updated_at"])

    _publish_operations_event(
        "payment.changed",
        {"table_session_id": session_id, "payment_id": payment.id, "action": "checked_out"},
    )
    return (
        _get_session_queryset().get(id=session.id),
        Payment.objects.select_related("table_session", "paid_by").get(id=payment.id),
        Invoice.objects.select_related("table_session", "payment", "issued_by")
        .filter(id=getattr(invoice, "id", None))
        .first(),
    )
