# listings/context_processors.py
from .models import CartItem

def cart_item_count(request):
    if request.user.is_authenticated:
        try:
            cart = request.user.cart
            count = CartItem.objects.filter(cart=cart).count()
            return {'cart_item_count': count}
        except:
            return {'cart_item_count': 0}
    return {'cart_item_count': 0}