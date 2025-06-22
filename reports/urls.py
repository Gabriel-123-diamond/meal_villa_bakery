from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reporting_dashboard_view, name='dashboard'),
    path('forecast/', views.demand_forecast_view, name='forecast'),
    path('profit-loss/', views.profit_loss_view, name='profit_loss'),
]

