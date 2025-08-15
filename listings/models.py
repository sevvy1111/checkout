# listings/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.db.models import Avg

User = get_user_model()


# The Category model is no longer needed and can be removed.

class Listing(models.Model):
    STATUS_CHOICES = (
        ("available", "Available"),
        ("sold", "Sold"),
        ("hidden", "Hidden"),
    )

    seller = models.ForeignKey(User, related_name="listings", on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)

    # Category is now a CharField to handle a large, predefined list
    category = models.CharField(max_length=100)

    city = models.CharField(max_length=120)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    created = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="available")
    featured = models.BooleanField(default=False)
    stock = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["-featured", "-created"]

    def __str__(self):
        return f"{self.title} — {self.price}"

    def get_absolute_url(self):
        return reverse("listings:listing_detail", args=[self.pk])


# ... (The rest of your models: ListingImage, SavedItem, Review, and the User property remain the same) ...
class ListingImage(models.Model):
    listing = models.ForeignKey(Listing, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="listings/%Y/%m/%d")
    caption = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"Image for {self.listing.title}"


class SavedItem(models.Model):
    user = models.ForeignKey(User, related_name="saved_items", on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, related_name="saved_by", on_delete=models.CASCADE)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "listing")

    def __str__(self):
        return f"{self.user} saved {self.listing}"


class Review(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='reviews')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('listing', 'author')

    def __str__(self):
        return f"Review by {self.author.username} for {self.listing.title}"


# --- New models for shopping cart ---
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user.username}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.listing.title}"


class Checkout(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='checkouts')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # New fields for shipping information
    full_name = models.CharField(max_length=150)
    shipping_address = models.CharField(max_length=255)
    shipping_city = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=20)

    # New fields for payment integration
    payment_id = models.CharField(max_length=150, blank=True, null=True)
    paid = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Checkout of {self.quantity} x {self.listing.title} by {self.user.username}"


@property
def average_rating(self):
    return Review.objects.filter(listing__seller=self).aggregate(Avg('rating'))['rating__avg']


User.add_to_class("average_rating", average_rating)