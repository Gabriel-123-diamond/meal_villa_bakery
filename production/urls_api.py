from django.urls import path
from . import api_views

urlpatterns = [
    path('recipes/', api_views.RecipeListCreateAPIView.as_view(), name='recipe-list-create'),
    path('recipes/<str:recipe_id>/cost/', api_views.RecipeCostDetailAPIView.as_view(), name='recipe-cost-detail'),
    path('produce/', api_views.ProductionRunAPIView.as_view(), name='production-run'),
]

