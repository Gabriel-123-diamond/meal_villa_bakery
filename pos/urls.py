from django.urls import path
from . import views

app_name = 'pos'

urlpatterns = [
    path('terminal/', views.pos_terminal_view, name='terminal'),
    path('orders/', views.order_tracking_view, name='order_tracking'),
    path('products/', views.product_management_view, name='product_management'),
    path('promotions/', views.promotions_management_view, name='promotions_management'),
    path('menu/', views.product_catalog_view, name='catalog'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('custom-order/', views.custom_order_view, name='custom_order'),
    path('delivery-dashboard/', views.delivery_dashboard_view, name='delivery_dashboard'), # New
]

