from django.urls import path
from . import api_views

urlpatterns = [
    path('products/', api_views.ProductListCreateAPIView.as_view(), name='product-list-create'),
    path('products/<str:pk>/', api_views.ProductDetailAPIView.as_view(), name='product-detail'),
    path('orders/create/', api_views.OrderCreateAPIView.as_view(), name='order-create'),
    path('orders/', api_views.OrderListAPIView.as_view(), name='order-list'),
    path('orders/<str:pk>/', api_views.OrderDetailAPIView.as_view(), name='order-detail'),
    path('promotions/', api_views.PromotionListCreateAPIView.as_view(), name='promotion-list-create'),
    path('promotions/<str:pk>/', api_views.PromotionDetailAPIView.as_view(), name='promotion-detail'),
]

