# listings/context_processors.py
from .models import Cart
from .filters import ListingFilter # Import the filter

def cart_item_count(request):
    if request.user.is_authenticated:
        try:
            cart = request.user.cart
            return {'cart_item_count': cart.items.count()}
        except Cart.DoesNotExist:
            return {'cart_item_count': 0}
    return {'cart_item_count': 0}

def search_filter_context(request):
    """
    Makes the ListingFilter available on all pages for the navbar search.
    """
    return {'search_filter_form': ListingFilter(request.GET, queryset=None)}