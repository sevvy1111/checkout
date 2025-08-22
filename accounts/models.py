# accounts/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.templatetags.static import static
from django.core.validators import RegexValidator
from django.db.models import Avg
from cloudinary.models import CloudinaryField
from django.urls import reverse
from listings.models import Review

User = get_user_model()


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = CloudinaryField('avatar', blank=True, null=True)
    bio = models.TextField(blank=True)
    credit_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    phone_validator = RegexValidator(
        regex=r'^\d{10}$',
        message="Phone number must be 10 digits, e.g., 9171234567."
    )
    phone = models.CharField(
        validators=[phone_validator],
        max_length=10,
        blank=True,
        help_text='Enter your 10-digit PH mobile number (e.g., 9171234567).'
    )

    def __str__(self):
        return f'{self.user.username} Profile'

    def get_absolute_url(self):
        return reverse('accounts:public_profile', kwargs={'username': self.user.username})

    @property
    def display_avatar_url(self):
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        return static('images/default_avatar.svg')

    @property
    def full_phone_number(self):
        if self.phone:
            return f'+63{self.phone}'
        return ""

    def get_seller_average_rating(self):
        """Calculates the average rating for all listings sold by the user."""
        return Review.objects.filter(
            listing__seller=self.user
        ).aggregate(Avg('rating'))['rating__avg']