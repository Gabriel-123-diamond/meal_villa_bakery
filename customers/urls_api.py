from django.urls import path
from . import api_views

urlpatterns = [
    path('customers/', api_views.CustomerListCreateAPIView.as_view(), name='customer-list-create'),
    path('customers/<str:pk>/', api_views.CustomerDetailAPIView.as_view(), name='customer-detail'),
    path('customers/<str:pk>/adjust-points/', api_views.AdjustCustomerPointsAPIView.as_view(), name='customer-adjust-points'),
]

