# sevvy1111/checkout/checkout-6284e1df24802e516d66595b54136462676a4c2c/marketplace/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

# Import routing from BOTH of your apps
import messaging.routing
import notifications.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            # Add the URL patterns from both apps to a single list
            messaging.routing.websocket_urlpatterns +
            notifications.routing.websocket_urlpatterns
        )
    ),
})