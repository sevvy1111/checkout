# accounts/models.py
# refactor: Improve model property to be a method on the Profile model for better encapsulation
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from cloudinary.models import CloudinaryField

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = CloudinaryField('avatar', blank=True, null=True)
    phone = models.CharField(
        max_length=13,
        null=True,
        blank=True,
        help_text="Enter phone number in the format +639xxxxxxxxx"
    )
    bio = models.TextField(null=True, blank=True)

    is_phone_verified = models.BooleanField(default=False)
    phone_verification_code = models.CharField(max_length=6, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} Profile"

    @property
    def display_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return settings.STATIC_URL + 'images/default_avatar.svg'

    # New property to get the seller's average rating directly from the profile
    @property
    def seller_average_rating(self):
        return self.user.listings.aggregate(avg_rating=models.Avg('reviews__rating'))['avg_rating']


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