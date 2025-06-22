from django.urls import path
from . import api_views

urlpatterns = [
    path('schedule/shifts/', api_views.ShiftListCreateAPIView.as_view(), name='shift-list-create'),
    path('schedule/shifts/<str:pk>/', api_views.ShiftDetailAPIView.as_view(), name='shift-detail'),
]

