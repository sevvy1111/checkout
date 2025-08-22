# listings/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.db.models import Avg, Sum, F
from cloudinary.models import CloudinaryField

User = get_user_model()


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='children',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['parent__name', 'name']

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} -> {self.name}"
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
    CONDITION_CHOICES = (
        ("NEW", "New"),
        ("USED", "Used"),
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
    condition = models.CharField(max_length=4, choices=CONDITION_CHOICES, default="USED")
    objects = ListingQuerySet.as_manager()

    class Meta:
        ordering = ["-featured", "-created"]

    def __str__(self):
        return f"{self.title} — {self.price}"

    def get_absolute_url(self):
        return reverse("listings:listing_detail", args=[self.pk])

    def has_sufficient_stock(self, quantity):
        """Checks if the listing has enough stock for a given quantity."""
        return self.stock >= quantity


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
    order_item = models.OneToOneField('OrderItem', on_delete=models.CASCADE, related_name='review', null=True)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

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
        """Checks if any item in the cart exceeds the available stock."""
        return self.items.filter(quantity__gt=F('listing__stock')).exists()


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
    credit_used = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"

    def calculate_total_price(self):
        """Calculates the total price from items, shipping fee, and applied credit."""
        subtotal = self.items.aggregate(
            total=Sum(F('quantity') * F('price'))
        )['total'] or 0

        # Ensure total doesn't go below zero after applying credit
        total_before_credit = subtotal + self.shipping_fee
        final_total = total_before_credit - self.credit_used
        self.total_price = max(final_total, 0)

    def is_seller(self, user):
        """Check if a user is a seller for any item in this order."""
        return self.items.filter(listing__seller=user).exists()


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    listing = models.ForeignKey(Listing, on_delete=models.SET_NULL, null=True, related_name='order_items')
    product_title = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)

    @property
    def total_price(self):
        return self.quantity * self.price

    def __str__(self):
        return f"{self.quantity} x {self.product_title or '[Deleted Listing]'}"