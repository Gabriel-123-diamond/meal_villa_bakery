from django.urls import path
from . import api_views

urlpatterns = [
    path('events/', api_views.EventListCreateAPIView.as_view(), name='event-list-create'),
    path('events/<str:pk>/', api_views.EventDetailAPIView.as_view(), name='event-detail'),
    path('events/<str:pk>/register/', api_views.EventRegistrationAPIView.as_view(), name='event-register'),
]

