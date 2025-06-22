from rest_framework import serializers

class RecipeIngredientSerializer(serializers.Serializer):
    ingredient_name = serializers.CharField(max_length=100)
    quantity = serializers.FloatField()
    unit = serializers.CharField(max_length=50)

class RecipeSerializer(serializers.Serializer):
    _id = serializers.CharField(read_only=True)
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False)
    instructions = serializers.CharField()
    ingredients = RecipeIngredientSerializer(many=True)

class ProductionRunSerializer(serializers.Serializer):
    recipe_id = serializers.CharField(max_length=24)
    product_id = serializers.CharField(max_length=24)
    quantity_produced = serializers.IntegerField(min_value=1)

class IngredientCostSerializer(serializers.Serializer):
    ingredient_name = serializers.CharField()
    required_quantity = serializers.FloatField()
    unit = serializers.CharField()
    cost_per_unit = serializers.FloatField()
    ingredient_total_cost = serializers.FloatField()

class RecipeCostSerializer(serializers.Serializer):
    recipe_id = serializers.CharField()
    recipe_name = serializers.CharField()
    total_recipe_cost = serializers.FloatField()
    cost_breakdown = IngredientCostSerializer(many=True)

