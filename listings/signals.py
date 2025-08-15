# messaging/signals.py
import json
import platform
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from accounts.models import Notification
from messaging.models import Message
from listings.models import Review


@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    if created:
        # Send WebSocket notification to both users
        timestamp_format = '%b. %d, %Y, %#I:%M %p' if platform.system() == 'Windows' else '%b. %d, %Y, %-I:%M %p'
        message_data = {
            "type": "chat_message",
            "message": instance.text,
            "sender": instance.sender.username,
            "timestamp": instance.timestamp.strftime(timestamp_format),
            "image_url": instance.image.url if instance.image else None,
        }

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{instance.conversation.pk}",
            message_data
        )

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