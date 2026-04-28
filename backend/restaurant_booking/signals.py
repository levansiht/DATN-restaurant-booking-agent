from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from restaurant_booking.models import Booking, BookingPayment, Table
from restaurant_booking.realtime import publish_realtime_event
from restaurant_booking.services.n8n_notifications import notify_admin_booking_event


def _get_previous_field_value(model, instance, field_name):
    if not instance.pk:
        return None

    return (
        model.objects.filter(pk=instance.pk)
        .values_list(field_name, flat=True)
        .first()
    )


@receiver(pre_save, sender=Booking, dispatch_uid="restaurant_booking_booking_previous_status")
def remember_booking_previous_status(sender, instance, **kwargs):
    instance._previous_status = _get_previous_field_value(Booking, instance, "status")


@receiver(pre_save, sender=BookingPayment, dispatch_uid="restaurant_booking_payment_previous_status")
def remember_booking_payment_previous_status(sender, instance, **kwargs):
    instance._previous_status = _get_previous_field_value(BookingPayment, instance, "status")


@receiver(post_save, sender=Booking, dispatch_uid="restaurant_booking_booking_realtime_event")
def publish_booking_realtime_event(sender, instance, created, **kwargs):
    publish_realtime_event(
        {
            "domain": "restaurant_booking",
            "type": "booking.changed",
            "action": "created" if created else "updated",
            "booking_id": instance.id,
            "table_id": instance.table_id,
            "booking_date": instance.booking_date.isoformat() if instance.booking_date else None,
            "booking_time": instance.booking_time.strftime("%H:%M") if instance.booking_time else None,
            "duration_hours": float(instance.duration_hours) if instance.duration_hours is not None else None,
            "status": instance.status,
            "updated_at": instance.updated_at.isoformat() if instance.updated_at else None,
        }
    )

    previous_status = getattr(instance, "_previous_status", None)
    event = None
    action = None
    if created:
        event = "booking.created"
        action = "created"
    elif previous_status and previous_status != instance.status:
        event = f"booking.{instance.status.lower()}"
        action = "status_changed"

    if event:
        transaction.on_commit(
            lambda: notify_admin_booking_event(
                event=event,
                booking=instance,
                action=action,
                previous_status=previous_status,
            )
        )


@receiver(post_save, sender=BookingPayment, dispatch_uid="restaurant_booking_payment_n8n_event")
def publish_booking_payment_n8n_event(sender, instance, created, **kwargs):
    previous_status = getattr(instance, "_previous_status", None)
    event = None
    action = None
    if not created and previous_status and previous_status != instance.status:
        event = f"booking_payment.{instance.status.lower()}"
        action = "status_changed"

    if event:
        transaction.on_commit(
            lambda: notify_admin_booking_event(
                event=event,
                booking=instance.booking,
                payment=instance,
                action=action,
                previous_status=previous_status,
            )
        )


@receiver(post_save, sender=Table, dispatch_uid="restaurant_booking_table_realtime_event")
def publish_table_realtime_event(sender, instance, created, **kwargs):
    publish_realtime_event(
        {
            "domain": "restaurant_booking",
            "type": "table.changed",
            "action": "created" if created else "updated",
            "table_id": instance.id,
            "status": instance.status,
            "floor": instance.floor,
            "updated_at": instance.updated_at.isoformat() if instance.updated_at else None,
        }
    )
