# accounts/models.py

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
        # Corrected logic to handle the fallback gracefully
        if self.avatar and hasattr(self.avatar, 'url') and self.avatar.url:
            return self.avatar.url
        return settings.STATIC_URL + 'images/default_avatar.svg'

    # New property to get the seller's average rating directly from the profile
    @property
    def seller_average_rating(self):
        return self.user.listings.aggregate(avg_rating=models.Avg('reviews__rating'))['avg_rating']


