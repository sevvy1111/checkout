# sevvy1111/checkout/checkout-baa1ef489cd0a3ed08221be9d8b13c13223c8fd8/notifications/apps.py
from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'

    def ready(self):

        pass