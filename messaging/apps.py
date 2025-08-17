# sevvy1111/checkout/checkout-6284e1df24802e516d66595b54136462676a4c2c/messaging/apps.py
from django.apps import AppConfig


class MessagingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'messaging'

    def ready(self):
        # This line should be removed
        pass