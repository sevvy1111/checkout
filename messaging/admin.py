# sevvy1111/checkout/checkout-6284e1df24802e516d66595b54136462676a4c2c/messaging/admin.py
from django.contrib import admin
from .models import Conversation, Message

class MessageInline(admin.TabularInline):
    model = Message
    extra = 1
    readonly_fields = ('sender', 'receiver', 'text', 'image', 'timestamp', 'is_read')

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'last_message_time') # Corrected: Replaced old fields with last_message_time
    search_fields = ('id', 'participants__username')
    filter_horizontal = ('participants',)
    inlines = [MessageInline]

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'receiver', 'conversation', 'timestamp', 'is_read')
    list_filter = ('is_read', 'timestamp')
    search_fields = ('text', 'sender__username', 'receiver__username')
    readonly_fields = ('timestamp',)