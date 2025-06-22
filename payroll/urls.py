from django.urls import path
from . import views

app_name = 'payroll'

urlpatterns = [
    path('', views.payroll_management_view, name='management'),
    path('log/', views.payroll_log_view, name='log'), # New
]

