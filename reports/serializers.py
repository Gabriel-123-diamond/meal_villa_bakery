from rest_framework import serializers

class DailySalesSummarySerializer(serializers.Serializer):
    date = serializers.DateField()
    total_sales = serializers.FloatField()
    order_count = serializers.IntegerField()

class IngredientShortageSerializer(serializers.Serializer):
    ingredient_name = serializers.CharField()
    required_quantity = serializers.FloatField()
    current_quantity = serializers.FloatField()
    shortage = serializers.FloatField()
    unit = serializers.CharField()

class DemandForecastSerializer(serializers.Serializer):
    product_name = serializers.CharField()
    forecast_period_days = serializers.IntegerField()
    predicted_sales_units = serializers.IntegerField()
    current_stock = serializers.IntegerField()
    needed_production_units = serializers.IntegerField()
    ingredient_shortages = IngredientShortageSerializer(many=True)

class ProfitLossSerializer(serializers.Serializer):
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    total_revenue = serializers.FloatField()
    total_cogs = serializers.FloatField()
    gross_profit = serializers.FloatField()