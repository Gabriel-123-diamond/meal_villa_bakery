from django.urls import path
from . import views

app_name = 'events' # This line was missing

urlpatterns = [
    path('', views.event_list_view, name='list'),
    path('manage/', views.event_management_view, name='management'),
]

