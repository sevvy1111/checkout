# listings/admin.py
from django.contrib import admin
from .models import Listing, ListingImage, SavedItem, Cart, CartItem, Order, OrderItem, Review, Category

@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'seller', 'price', 'status', 'stock', 'created')
    list_filter = ('status', 'featured', 'created')
    search_fields = ('title', 'description', 'seller__username')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_price', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'full_name')

# Register other models for better admin visibility
admin.site.register(ListingImage)
admin.site.register(SavedItem)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(OrderItem)
admin.site.register(Review)
admin.site.register(Category)