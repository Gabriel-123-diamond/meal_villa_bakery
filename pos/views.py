from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from users.views import is_staff_member
from cart.cart import Cart

def product_catalog_view(request):
    return render(request, 'pos/catalog.html')

def checkout_view(request):
    cart = Cart(request)
    return render(request, 'pos/checkout.html', {'cart': cart})

@login_required
def pos_terminal_view(request):
    return render(request, 'pos/terminal.html')

@login_required
@user_passes_test(is_staff_member)
def order_tracking_view(request):
    return render(request, 'pos/order_tracking.html')

@login_required
@user_passes_test(is_staff_member)
def product_management_view(request):
    return render(request, 'pos/product_management.html')

@login_required
@user_passes_test(is_staff_member)
def promotions_management_view(request):
    return render(request, 'pos/promotions_management.html')

@login_required
def custom_order_view(request):
    return render(request, 'pos/custom_order.html')

@login_required
@user_passes_test(is_staff_member)
def delivery_dashboard_view(request):
    """
    Renders the delivery and order status dashboard for managers.
    """
    return render(request, 'pos/delivery_dashboard.html')

