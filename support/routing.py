# support/routing.py
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/support/', consumers.SupportConsumer.as_asgi()),
]