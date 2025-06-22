from django.urls import path
from . import api_views

urlpatterns = [
    path('inventory/cleaner/', api_views.CleanerSupplyListAPIView.as_view(), name='cleaner-supply-list'),
    path('inventory/baker/', api_views.BakerSupplyListAPIView.as_view(), name='baker-supply-list'),
    path('inventory/storekeeper/', api_views.StorekeeperSupplyListAPIView.as_view(), name='storekeeper-supply-list'),
]

