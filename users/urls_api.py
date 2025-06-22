from django.urls import path
from . import api_views

urlpatterns = [
    path('users/', api_views.UserListCreateAPIView.as_view(), name='user-list-create'),
    path('users/<int:pk>/', api_views.UserDetailAPIView.as_view(), name='user-detail'),
]

