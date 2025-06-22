from django.urls import path
from . import views

app_name = 'production'

urlpatterns = [
    path('recipes/', views.recipe_management_view, name='recipe_management'),
]

