from django.urls import path
from . import api_views

urlpatterns = [
    path('performance/logs/', api_views.PerformanceLogListCreateAPIView.as_view(), name='performance-log-list-create'),
]

