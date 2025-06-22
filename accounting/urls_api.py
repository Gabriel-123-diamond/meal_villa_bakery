from django.urls import path
from . import api_views

urlpatterns = [
    path('suppliers/', api_views.SupplierListCreateAPIView.as_view(), name='supplier-list-create'),
    path('purchase-orders/', api_views.PurchaseOrderListCreateAPIView.as_view(), name='po-list-create'),
    path('purchase-orders/<str:po_id>/receive/', api_views.ReceivePurchaseOrderAPIView.as_view(), name='po-receive'),
]

