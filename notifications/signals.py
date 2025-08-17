# sevvy1111/checkout/checkout-6284e1df24802e516d66595b54136462676a4c2c/notifications/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Notification


@receiver(post_save, sender=Notification)
def send_notification_on_save(sender, instance, created, **kwargs):
    """
    Sends a real-time notification to the recipient when a new
    Notification object is created.
    """
    if created:
        channel_layer = get_channel_layer()
        group_name = f'user_{instance.recipient.id}_notifications'

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "send_notification",
                "message": instance.message,
                "link": instance.link,
            }
        )