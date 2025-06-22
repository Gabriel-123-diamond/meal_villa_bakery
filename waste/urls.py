from django.urls import path
from . import views

app_name = 'waste'

urlpatterns = [
    path('', views.log_waste_view, name='log'),
    path('report/', views.waste_report_view, name='report'),
]

