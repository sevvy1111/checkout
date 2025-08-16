# messaging/signals.py
import json
import platform
from django.dispatch import Signal, receiver
from django.db.models.signals import post_save
from django.urls import reverse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from accounts.models import Notification
from messaging.models import Message
from listings.models import Review

# The chat message broadcast is now handled directly in the view to pass temp_id
# so we remove the signal receiver here to avoid duplicate broadcasts.
# We keep the signal for future use if needed, but the receiver is gone.
# chat_message_signal = Signal() # This is already defined in the original file

@receiver(post_save, sender=Review)
def create_review_notification(sender, instance, created, **kwargs):
    if created:
        seller = instance.listing.seller
        notification = Notification.objects.create(
            recipient=seller,
            sender=instance.author,
            message=f"{instance.author.username} left a {instance.rating}-star review on your listing '{instance.listing.title}'.",
            link=instance.listing.get_absolute_url()
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"notifications_{seller.username}",
            {
                "type": "send_notification",
                "message": notification.message,
                "link": notification.link,
            },
        )