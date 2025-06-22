from django.urls import path
from . import views

app_name = 'feedback'

urlpatterns = [
    path('submit/', views.feedback_form_view, name='submit'),
    path('manage/', views.feedback_management_view, name='management'),
]

