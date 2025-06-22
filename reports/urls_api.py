from django.urls import path
from . import api_views

urlpatterns = [
    path('reports/sales-summary/', api_views.SalesSummaryAPIView.as_view(), name='sales-summary'),
    path('reports/demand-forecast/', api_views.DemandForecastAPIView.as_view(), name='demand-forecast'),
    path('reports/profit-loss/', api_views.ProfitLossAPIView.as_view(), name='profit-loss'),
]

