from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    path('', views.customer_management_view, name='management'),
]

