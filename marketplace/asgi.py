# marketplace/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
# The import statement has been moved inside ProtocolTypeRouter to ensure Django's apps are loaded.

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            # This import will be called after Django's app registry is ready.
            messaging.routing.websocket_urlpatterns
        )
    ),
})
