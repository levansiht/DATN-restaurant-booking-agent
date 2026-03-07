from django.db.models.signals import post_save
from django.dispatch import receiver

from restaurant_booking.models import Booking, Table
from restaurant_booking.realtime import publish_realtime_event


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
