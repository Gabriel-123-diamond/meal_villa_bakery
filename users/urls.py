from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('staff/', views.staff_management_view, name='staff_management'),
    path('settings/', views.settings_view, name='settings'), # New
]

