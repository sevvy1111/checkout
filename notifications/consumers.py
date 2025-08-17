# sevvy1111/checkout/checkout-6284e1df24802e516d66595b54136462676a4c2c/notifications/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    A consumer to handle WebSocket connections for real-time notifications.
    """
    async def connect(self):
        """
        Accepts the WebSocket connection if the user is authenticated and
        adds them to a user-specific group.
        """
        if self.scope["user"].is_authenticated:
            self.user = self.scope["user"]
            self.group_name = f'user_{self.user.id}_notifications'

            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        """
        Removes the user from their notification group upon disconnection.
        """
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def send_notification(self, event):
        """
        Handler for the 'send_notification' event. Pushes the notification
        data down to the client.
        """
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'link': event.get('link', '#'),
        }))