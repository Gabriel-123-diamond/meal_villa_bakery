from django.urls import path
from . import views

app_name = 'performance'

urlpatterns = [
    path('<int:user_id>/', views.performance_review_view, name='review'),
]

