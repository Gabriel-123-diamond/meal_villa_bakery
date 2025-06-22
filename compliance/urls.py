from django.urls import path
from . import views

app_name = 'compliance' # This line was missing

urlpatterns = [
    path('checklist/', views.daily_checklist_view, name='checklist'),
    path('manage/', views.compliance_management_view, name='management'),
]

