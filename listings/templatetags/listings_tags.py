# listings/templatetags/listings_tags.py
from django import template
import locale

register = template.Library()

@register.filter(name='philippine_currency')
def philippine_currency(value):
    """
    Formats a number as a string with commas for thousands separators
    and two decimal places, suitable for Philippine currency display.
    """
    try:
        return f"{value:,.2f}"
    except (ValueError, TypeError):
        return value

@register.filter(name='listing_status_badge')
def listing_status_badge(status):
    """
    Returns a Bootstrap badge color class based on the listing status.
    """
    if status == 'available':
        return 'success'
    elif status == 'sold':
        return 'danger'
    elif status == 'hidden':
        return 'secondary'
    return 'light'

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Allows accessing a dictionary item by a key in the template.
    Usage: {{ my_dict|get_item:my_key }}
    """
    return dictionary.get(key)