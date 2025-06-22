from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from bson import ObjectId

from bakery_management.db import get_mongo_db
from .serializers import RecipeSerializer, ProductionRunSerializer, RecipeCostSerializer

class RecipeListCreateAPIView(APIView):
    # This view remains unchanged
    def get(self, request, format=None):
        db = get_mongo_db()
        recipes = list(db.recipes.find({}))
        for recipe in recipes:
            recipe['_id'] = str(recipe['_id'])
        serializer = RecipeSerializer(recipes, many=True)
        return Response(serializer.data)
    def post(self, request, format=None):
        serializer = RecipeSerializer(data=request.data)
        if serializer.is_valid():
            db = get_mongo_db()
            db.recipes.insert_one(serializer.validated_data)
            return Response(serializer.validated_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProductionRunAPIView(APIView):
    # This view remains unchanged
    def post(self, request, format=None):
        serializer = ProductionRunSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        db = get_mongo_db()
        try:
            recipe_oid = ObjectId(data['recipe_id'])
            product_oid = ObjectId(data['product_id'])
        except Exception:
            return Response({"error": "Invalid recipe_id or product_id format."}, status=status.HTTP_400_BAD_REQUEST)
        recipe = db.recipes.find_one({"_id": recipe_oid})
        product = db.products.find_one({"_id": product_oid})
        if not recipe: return Response({"error": "Recipe not found."}, status=status.HTTP_404_NOT_FOUND)
        if not product: return Response({"error": "Finished product not found."}, status=status.HTTP_404_NOT_FOUND)
        for ingredient in recipe.get('ingredients', []):
            ingredient_name = ingredient['ingredient_name']
            required_quantity = ingredient['quantity'] * data['quantity_produced']
            baker_supply = db.baker_production_supplies.find_one({"name_lower": ingredient_name.lower()})
            if not baker_supply or baker_supply.get('quantity', 0) < required_quantity:
                return Response({"error": "Insufficient ingredients.", "details": f"Not enough {ingredient_name}. Required: {required_quantity}, Available: {baker_supply.get('quantity', 0) if baker_supply else 0}"}, status=status.HTTP_400_BAD_REQUEST)
        for ingredient in recipe.get('ingredients', []):
            ingredient_name = ingredient['ingredient_name']
            required_quantity = ingredient['quantity'] * data['quantity_produced']
            db.baker_production_supplies.update_one({"name_lower": ingredient_name.lower()}, {"$inc": {"quantity": -required_quantity}})
        db.products.update_one({"_id": product_oid}, {"$inc": {"current_stock": data['quantity_produced']}})
        return Response({"success": f"Successfully produced {data['quantity_produced']} units of {product['name']}.", "product_id": str(product_oid), "new_stock": product['current_stock'] + data['quantity_produced']}, status=status.HTTP_200_OK)

class RecipeCostDetailAPIView(APIView):
    """
    API endpoint to calculate the total material cost for a single recipe.
    """
    def get(self, request, recipe_id, format=None):
        db = get_mongo_db()
        try:
            recipe_oid = ObjectId(recipe_id)
        except Exception:
            return Response({"error": "Invalid recipe ID format."}, status=status.HTTP_400_BAD_REQUEST)

        recipe = db.recipes.find_one({"_id": recipe_oid})
        if not recipe:
            return Response({"error": "Recipe not found."}, status=status.HTTP_404_NOT_FOUND)

        total_recipe_cost = 0.0
        cost_breakdown = []

        for ingredient in recipe.get('ingredients', []):
            ingredient_name = ingredient['ingredient_name']
            required_quantity = float(ingredient.get('quantity', 0))
            
            supply_item = db.baker_production_supplies.find_one({"name_lower": ingredient_name.lower()})
            
            cost_per_unit = float(supply_item.get('cost_per_unit', 0)) if supply_item else 0
            ingredient_total_cost = required_quantity * cost_per_unit
            total_recipe_cost += ingredient_total_cost

            cost_breakdown.append({
                "ingredient_name": ingredient_name,
                "required_quantity": required_quantity,
                "unit": ingredient.get('unit'),
                "cost_per_unit": cost_per_unit,
                "ingredient_total_cost": ingredient_total_cost
            })
        
        response_data = {
            "recipe_id": str(recipe_oid),
            "recipe_name": recipe.get('name'),
            "total_recipe_cost": total_recipe_cost,
            "cost_breakdown": cost_breakdown
        }

        serializer = RecipeCostSerializer(response_data)
        return Response(serializer.data)

