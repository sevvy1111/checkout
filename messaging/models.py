# sevvy1111/checkout/checkout-6284e1df24802e516d66595b54136462676a4c2c/messaging/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from cloudinary.models import CloudinaryField


class Conversation(models.Model):
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    last_message_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Conversation ({self.id})"

    def get_other_user(self, current_user):
        """
        Given the current user, returns the other participant in the conversation.
        """
        return self.participants.exclude(id=current_user.id).first()


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    # This line is the fix: ensure blank=True is present
    text = models.TextField(blank=True)
    image = CloudinaryField('message_image', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            # Update the conversation's last message time only on new messages
            self.conversation.last_message_time = self.timestamp
            self.conversation.save(update_fields=['last_message_time'])

    class Meta:
        ordering = ['timestamp']