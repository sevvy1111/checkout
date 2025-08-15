# accounts/models.py
from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(default="avatar.svg", upload_to="avatars/")
    phone = models.CharField(
        max_length=13,
        null=True,
        blank=True,
        help_text="Enter phone number in the format +639xxxxxxxxx"
    )
    bio = models.TextField(null=True, blank=True)

    # Renamed for clarity and added verification code field
    is_phone_verified = models.BooleanField(default=False)
    phone_verification_code = models.CharField(max_length=6, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} Profile"


# The Notification model remains the same
class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    message = models.CharField(max_length=255)
    link = models.URLField()
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return self.message