from django.urls import path
from . import api_views

urlpatterns = [
    path('compliance/tasks/', api_views.ComplianceTaskListCreateAPIView.as_view(), name='compliance-task-list'),
    path('compliance/logs/', api_views.ComplianceLogListAPIView.as_view(), name='compliance-log-list'),
    path('compliance/log/', api_views.ComplianceLogCreateAPIView.as_view(), name='compliance-log-create'),
]

