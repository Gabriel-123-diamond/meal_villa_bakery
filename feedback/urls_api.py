from django.urls import path
from . import api_views

urlpatterns = [
    path('feedback/submit/', api_views.FeedbackSubmitAPIView.as_view(), name='feedback-submit'),
    path('feedback/', api_views.FeedbackListAPIView.as_view(), name='feedback-list'),
    path('feedback/<str:pk>/', api_views.FeedbackDetailAPIView.as_view(), name='feedback-detail'),
]

