from django.urls import path
from . import api_views

urlpatterns = [
    path('cart/', api_views.CartAPIView.as_view(), name='cart-api'),
]

