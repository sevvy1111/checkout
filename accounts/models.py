# accounts/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.templatetags.static import static
from cloudinary.models import CloudinaryField

User = get_user_model()


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = CloudinaryField('avatar', blank=True, null=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return f'{self.user.username} Profile'

    @property
    def display_avatar_url(self):
        """
        Returns the avatar URL if it exists, otherwise returns the URL for a default avatar.
        """
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        return static('images/default_avatar.svg')