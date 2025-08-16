# marketplace/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace.settings')

# The `get_asgi_application()` call is essential for loading Django's app registry
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            # This import needs to be inside the URLRouter to be executed after the app registry is ready.
            # Make sure you remove the import from the top of the file.
            (lambda: messaging.routing.websocket_urlpatterns)()
        )
    ),
})
