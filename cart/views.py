from django.shortcuts import render
from .cart import Cart

def cart_detail_view(request):
    """
    Renders the page showing the contents of the user's shopping cart.
    """
    cart = Cart(request)
    return render(request, 'cart/detail.html', {'cart': cart})

