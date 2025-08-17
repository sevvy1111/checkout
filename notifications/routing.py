# sevvy1111/checkout/checkout-6284e1df24802e516d66595b54136462676a4c2c/notifications/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
]