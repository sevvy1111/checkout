# accounts/admin.py

from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    # Corrected the field name from 'is_verified' to 'is_phone_verified'
    list_display = ('user', 'phone', 'is_phone_verified')
    search_fields = ('user__username', 'phone')