# support/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from .models import SupportTicket, SupportMessage
from .bot import get_bot_response


class SupportConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return

        self.ticket = await self.get_or_create_ticket()
        self.room_group_name = f'support_{self.ticket.id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # FIX: Added "Learn how to sell" back to the welcome message
        welcome_message = (
            "Hi! Is there anything I can help you with?<br>"
            "<ul>"
            "<li><a href='#' class='chat-suggestion' data-message='Track my order'>Track your order</a></li>"
            "<li><a href='#' class='chat-suggestion' data-message='Search for products'>Search for products</a></li>"
            "<li><a href='#' class='chat-suggestion' data-message='View my wishlist'>View your wishlist</a></li>"
            "<li><a href='#' class='chat-suggestion' data-message='How to sell'>Learn how to sell</a></li>"
            "<li><a href='#' class='chat-suggestion' data-message='Report a user'>Report a user</a></li>"
            "</ul>"
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'chat_message', 'sender': 'bot', 'message': welcome_message}
        )

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']

        await self.save_message('user', message)
        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'chat_message', 'sender': 'user', 'message': message}
        )

        message_history = await self.get_message_history()
        bot_response = await self.get_bot_response_async(message, message_history)

        await self.save_message('bot', bot_response)
        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'chat_message', 'sender': 'bot', 'message': bot_response}
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'sender': event['sender'],
            'message': event['message'],
        }))

    @database_sync_to_async
    def get_or_create_ticket(self):
        ticket, created = SupportTicket.objects.get_or_create(user=self.user, status__in=['open', 'escalated'])
        if not created and ticket.status == 'closed':
            ticket = SupportTicket.objects.create(user=self.user, status='open')
        return ticket

    @database_sync_to_async
    def save_message(self, sender, message):
        if "chat-suggestion" in message:
            return
        return SupportMessage.objects.create(ticket=self.ticket, sender=sender, message=message)

    @database_sync_to_async
    def get_message_history(self):
        return list(self.ticket.messages.all().order_by('timestamp'))

    @database_sync_to_async
    def get_bot_response_async(self, message, message_history):
        return get_bot_response(self.user, message, message_history)