# listings/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.db.models import Avg
from cloudinary.models import CloudinaryField

User = get_user_model()


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class ListingQuerySet(models.QuerySet):
    def with_avg_rating(self):
        return self.annotate(average_rating=Avg('reviews__rating'))


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
    category = models.ForeignKey(Category, related_name='listings', on_delete=models.PROTECT, null=True)
    city = models.CharField(max_length=120)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    created = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="available")
    featured = models.BooleanField(default=False)
    stock = models.PositiveIntegerField(default=1)

    objects = ListingQuerySet.as_manager()

    class Meta:
        ordering = ["-featured", "-created"]

    def __str__(self):
        return f"{self.title} — {self.price}"

    def get_absolute_url(self):
        return reverse("listings:listing_detail", args=[self.pk])


class ListingImage(models.Model):
    listing = models.ForeignKey(Listing, related_name="images", on_delete=models.CASCADE)
    image = CloudinaryField('listing_image')
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


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user.username}"

    @property
    def has_out_of_stock_items(self):

        return any(item.quantity > item.listing.stock for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def total_price(self):
        return self.quantity * self.listing.price

    def __str__(self):
        return f"{self.quantity} x {self.listing.title}"


class Order(models.Model):
    PAYMENT_CHOICES = [
        ('COD', 'Cash on Delivery'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    full_name = models.CharField(max_length=150)
    shipping_address = models.CharField(max_length=255)
    shipping_city = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=20)
    gift_note = models.TextField(blank=True, null=True)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_CHOICES, default='COD')
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    # Storing listing details at the time of purchase is crucial for historical accuracy,
    # especially if the original listing is deleted or its price changes.
    # For a production system, consider denormalizing further by also storing title and image.
    listing = models.ForeignKey(Listing, on_delete=models.SET_NULL, null=True, related_name='order_items')
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2) # Price per item at time of order

    @property
    def total_price(self):
        return self.quantity * self.price

    def get_total_price(self):
        return self.listing.price * self.quantity if self.listing else 0

    def __str__(self):
        if self.listing:
            return f"{self.quantity} x {self.listing.title}"
        return f"{self.quantity} x [Deleted Listing]"