# messaging/models.py
# chore: Add missing imports
from django.db import models
from django.conf import settings
from django.urls import reverse
from cloudinary.models import CloudinaryField

class Conversation(models.Model):
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='conversations'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return reverse('messaging:conversation_detail', kwargs={'pk': self.pk})

    def __str__(self):
        # A simple representation of the conversation participants
        usernames = ', '.join(user.username for user in self.participants.all())
        return f"Conversation with {usernames}"

class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages'
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages'
    )
    text = models.TextField(blank=True, null=True)
    image = CloudinaryField('message_image', blank=True, null=True)
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"From {self.sender.username} to {self.receiver.username} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        ordering = ['timestamp']