# sevvy1111/checkout/checkout-6284e1df24802e516d66595b54136462676a4c2c/notifications/apps.py
from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'

    def ready(self):

        import notifications.signals