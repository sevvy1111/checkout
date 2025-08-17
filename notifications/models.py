# sevvy1111/checkout/checkout-baa1ef489cd0a3ed08221be9d8b13c13223c8fd8/notifications/models.py
from django.db import models
from django.conf import settings


class Notification(models.Model):
    """
    A model to store notifications for users.
    """
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    message = models.CharField(max_length=255)
    notification_type = models.CharField(max_length=50)
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    link = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.message

    class Meta:
        ordering = ['-timestamp']