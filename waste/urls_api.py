from django.urls import path
from . import api_views

urlpatterns = [
    path('waste/log/', api_views.WasteLogCreateAPIView.as_view(), name='waste-log-create'),
    path('waste/logs/', api_views.WasteLogListAPIView.as_view(), name='waste-log-list'),
]

