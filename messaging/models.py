import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from cloudinary.models import CloudinaryField


class ConversationManager(models.Manager):
    def get_or_create_conversation(self, user1, user2):
        """
        Gets or creates a unique conversation between two users.
        """
        if user1 == user2:
            return None

        # Sort usernames to create a consistent, unique key
        usernames = sorted([user1.username, user2.username])
        key = "_".join(usernames)

        # Use get_or_create on the unique key
        conversation, created = self.get_or_create(conversation_key=key)

        # If the conversation is new, add the participants
        if created:
            conversation.participants.add(user1, user2)

        return conversation


class Conversation(models.Model):
    """
    Represents a private conversation between two users.
    """
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='conversations'
    )
    # Unique key to enforce one-on-one conversation uniqueness
    conversation_key = models.CharField(
        max_length=255, unique=True, null=True, blank=True
    )
    last_message_time = models.DateTimeField(null=True, blank=True)
    objects = ConversationManager()

    def __str__(self):
        """
        Returns a human-readable string representation of the conversation.
        """
        users = self.participants.all()
        if users.count() > 1:
            return f"Conversation between {users[0].username} and {users[1].username}"
        return f"Conversation ({self.id})"

    def get_other_user(self, current_user):
        """
        Retrieves the other participant in the conversation.
        """
        return self.participants.exclude(id=current_user.id).first()


class Message(models.Model):
    """
    Represents a single message within a conversation.
    """
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_messages'
    )
    text = models.TextField(blank=True)
    image = CloudinaryField('message_image', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        """
        Updates the conversation's last_message_time on new message save.
        """
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            self.conversation.last_message_time = self.timestamp
            self.conversation.save(update_fields=['last_message_time'])

    class Meta:
        ordering = ['timestamp']