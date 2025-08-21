# sevvy1111/checkout/checkout-6284e1df24802e516d66595b54136462676a4c2c/messaging/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from cloudinary.models import CloudinaryField
from django.db.models import Count

class ConversationManager(models.Manager):
    def get_or_create_conversation(self, user1, user2):

        if user1 == user2:
            return None

        conversation = self.get_queryset().filter(
            participants=user1
        ).filter(
            participants=user2
        ).annotate(
            p_count=Count('participants')
        ).filter(
            p_count=2
        ).first()

        if conversation is None:
            conversation = self.create()
            conversation.participants.add(user1, user2)

        return conversation

class Conversation(models.Model):
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    last_message_time = models.DateTimeField(null=True, blank=True)
    objects = ConversationManager()

    def __str__(self):
        return f"Conversation ({self.id})"

    def get_other_user(self, current_user):
        return self.participants.exclude(id=current_user.id).first()


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    text = models.TextField(blank=True)
    image = CloudinaryField('message_image', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            self.conversation.last_message_time = self.timestamp
            self.conversation.save(update_fields=['last_message_time'])

    class Meta:
        ordering = ['timestamp']