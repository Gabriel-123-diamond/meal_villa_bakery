from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, time, timedelta

from bakery_management.db import get_mongo_db
from .serializers import DailySalesSummarySerializer, DemandForecastSerializer
from users.api_views import IsAdminOrManager

class SalesSummaryAPIView(APIView):
    """
    API endpoint for viewing an aggregated summary of sales data.
    """
    permission_classes = [IsAdminOrManager]
    def get(self, request, format=None):
        db = get_mongo_db()
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        if not start_date_str or not end_date_str: return Response({"error": "Please provide 'start_date' and 'end_date' query parameters."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            start_date = datetime.combine(datetime.strptime(start_date_str, "%Y-%m-%d").date(), time.min)
            end_date = datetime.combine(datetime.strptime(end_date_str, "%Y-%m-%d").date(), time.max)
        except ValueError:
            return Response({"error": "Invalid date format. Please use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        pipeline = [ {'$match': {'created_at': {'$gte': start_date, '$lte': end_date}}}, {'$group': {'_id': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$created_at'}}, 'total_sales': {'$sum': '$total_price'}, 'order_count': {'$sum': 1}}}, {'$project': {'_id': 0, 'date': '$_id', 'total_sales': '$total_sales', 'order_count': '$order_count'}}, {'$sort': {'date': 1}}]
        results = list(db.orders.aggregate(pipeline))
        serializer = DailySalesSummarySerializer(results, many=True)
        return Response(serializer.data)

class ProfitLossAPIView(APIView):
    """
    Calculates revenue, cost of goods sold, and gross profit for a date range.
    """
    permission_classes = [IsAdminOrManager]

    def get(self, request, format=None):
        db = get_mongo_db()
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        if not start_date_str or not end_date_str: return Response({"error": "Please provide 'start_date' and 'end_date' query parameters."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            start_date = datetime.combine(datetime.strptime(start_date_str, "%Y-%m-%d").date(), time.min)
            end_date = datetime.combine(datetime.strptime(end_date_str, "%Y-%m-%d").date(), time.max)
        except ValueError:
            return Response({"error": "Invalid date format. Please use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        
        pipeline = [
            {'$match': {'created_at': {'$gte': start_date, '$lte': end_date}, 'status': 'completed'}},
            {'$group': {
                '_id': None,
                'total_revenue': {'$sum': '$total_price'},
                'total_cogs': {'$sum': '$cost_of_goods_sold'}
            }}
        ]
        
        result = list(db.orders.aggregate(pipeline))
        
        if not result:
            data = {"start_date": start_date_str, "end_date": end_date_str, "total_revenue": 0, "total_cogs": 0, "gross_profit": 0}
        else:
            revenue = result[0].get('total_revenue', 0)
            cogs = result[0].get('total_cogs', 0)
            data = {
                "start_date": start_date_str,
                "end_date": end_date_str,
                "total_revenue": revenue,
                "total_cogs": cogs,
                "gross_profit": revenue - cogs
            }
        
        serializer = ProfitLossSerializer(data)
        return Response(serializer.data)

class DemandForecastAPIView(APIView):
    """
    Analyzes historical sales to forecast future demand for a product.
    Requires 'product_id' and 'days_to_predict' query parameters.
    """
    permission_classes = [IsAdminOrManager]
    
    def get(self, request, format=None):
        product_id = request.query_params.get('product_id')
        days_to_predict = request.query_params.get('days_to_predict', '7') # Default to 7 days

        if not product_id:
            return Response({"error": "product_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            days_to_predict = int(days_to_predict)
        except ValueError:
            return Response({"error": "days_to_predict must be an integer."}, status=status.HTTP_400_BAD_REQUEST)

        db = get_mongo_db()
        product = db.products.find_one({"_id": ObjectId(product_id)})
        if not product:
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
            
        # Analyze sales from the last 28 days
        start_date = datetime.now() - timedelta(days=28)
        pipeline = [
            {'$match': {"items.product_id": product_id, "created_at": {"$gte": start_date}}},
            {'$unwind': "$items"},
            {'$match': {"items.product_id": product_id}},
            {'$group': {'_id': None, 'total_sold': {'$sum': "$items.quantity"}}}
        ]
        result = list(db.orders.aggregate(pipeline))
        total_sold_last_28_days = result[0]['total_sold'] if result else 0
        avg_daily_sales = total_sold_last_28_days / 28.0
        
        predicted_sales_units = round(avg_daily_sales * days_to_predict)
        current_stock = product.get('current_stock', 0)
        needed_production_units = max(0, predicted_sales_units - current_stock)
        
        # Check ingredient shortages if production is needed
        ingredient_shortages = []
        if needed_production_units > 0:
            # Find the recipe associated with this product (simple name match)
            recipe = db.recipes.find_one({"name": {"$regex": product['name'], "$options": "i"}})
            if recipe:
                for ingredient in recipe.get('ingredients', []):
                    required_qty = ingredient['quantity'] * needed_production_units
                    supply = db.baker_production_supplies.find_one({"name_lower": ingredient['ingredient_name'].lower()})
                    current_supply_qty = supply.get('quantity', 0) if supply else 0
                    shortage = max(0, required_qty - current_supply_qty)
                    if shortage > 0:
                        ingredient_shortages.append({
                            "ingredient_name": ingredient['ingredient_name'],
                            "required_quantity": round(required_qty, 2),
                            "current_quantity": round(current_supply_qty, 2),
                            "shortage": round(shortage, 2),
                            "unit": ingredient['unit']
                        })

        response_data = {
            "product_name": product['name'],
            "forecast_period_days": days_to_predict,
            "predicted_sales_units": predicted_sales_units,
            "current_stock": current_stock,
            "needed_production_units": needed_production_units,
            "ingredient_shortages": ingredient_shortages
        }
        
        serializer = DemandForecastSerializer(response_data)
        return Response(serializer.data)

