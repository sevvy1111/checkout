# listings/templatetags/listings_tags.py
from django import template
from listings.models import Category
register = template.Library()

@register.filter
def multiply(value, arg):
    return value * arg

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def philippine_currency(value):
    """
    Formats a number as Philippine currency with thousands separators.
    Example: 1234567.89 -> 1,234,567.89
    """
    try:
        if value is None:
            return ""
        # Format the number with a comma as a thousand separator and two decimal places
        return f"{float(value):,.2f}"
    except (ValueError, TypeError):
        return value

@register.filter
def cart_total(items):
    """Calculates the total price of all items in a cart."""
    total = sum(item.listing.price * item.quantity for item in items)
    return total
@register.simple_tag
def get_categories():
    return Category.objects.all()