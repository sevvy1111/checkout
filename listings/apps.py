# listings/apps.py
from django.apps import AppConfig


class ListingsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "listings"

    def ready(self):
        import listings.signals
        import listings.templatetags.listings_tags
        import listings.signals