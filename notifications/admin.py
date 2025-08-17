# notifications/admin.py
from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'message', 'notification_type', 'is_read', 'timestamp')
    list_filter = ('is_read', 'notification_type', 'timestamp')
    search_fields = ('recipient__username', 'message')