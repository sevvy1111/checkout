# sevvy1111/checkout/checkout-6284e1df24802e516d66595b54136462676a4c2c/marketplace/asgi.py
import os
from django.core.asgi import get_asgi_application

# Set the settings module environment variable first.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace.settings')

# Initialize the Django application. This MUST happen before you import
# anything that might touch Django's models or settings.
django_asgi_app = get_asgi_application()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import messaging.routing
import notifications.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            messaging.routing.websocket_urlpatterns +
            notifications.routing.websocket_urlpatterns
        )
    ),
})