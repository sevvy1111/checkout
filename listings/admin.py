# listings/admin.py
from django.contrib import admin
from .models import Listing, ListingImage, SavedItem, Cart, CartItem, Checkout

class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 1

@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ("title", "seller", "price", "status", "category", "city", "created", "stock")
    list_filter = ("status", "category", "city", "featured")
    search_fields = ("title", "description", "seller__username", "city")
    inlines = [ListingImageInline]

# The Category model and its admin have been removed, so we only register these.
admin.site.register(ListingImage)
admin.site.register(SavedItem)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Checkout)