from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from bson import ObjectId
import datetime

from bakery_management.db import get_mongo_db
from .serializers import WasteLogSerializer
from users.api_views import IsAdminOrManager

class WasteLogCreateAPIView(APIView):
    """
    Log a new waste entry. This will deduct stock from the product.
    Accessible by any authenticated user.
    """
    def post(self, request, format=None):
        serializer = WasteLogSerializer(data=request.data)
        if serializer.is_valid():
            db = get_mongo_db()
            data = serializer.validated_data
            product_id = data['product_id']
            quantity_wasted = data['quantity']
            
            try:
                product_oid = ObjectId(product_id)
                product = db.products.find_one({"_id": product_oid})
                if not product:
                    return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
            except Exception:
                return Response({"error": "Invalid product_id."}, status=status.HTTP_400_BAD_REQUEST)

            # Deduct stock
            db.products.update_one(
                {"_id": product_oid},
                {"$inc": {"current_stock": -quantity_wasted}}
            )

            # Create log entry
            log_entry = {
                "product_id": product_id,
                "product_name": product.get('name', 'Unknown Product'),
                "quantity": quantity_wasted,
                "reason": data['reason'],
                "logged_by_name": request.user.get_full_name() or request.user.username,
                "logged_at": datetime.datetime.utcnow()
            }
            db.waste_logs.insert_one(log_entry)
            
            return Response({"success": "Waste logged successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class WasteLogListAPIView(APIView):
    """
    List all waste logs, for managers.
    """
    permission_classes = [IsAdminOrManager]

    def get(self, request, format=None):
        db = get_mongo_db()
        logs = list(db.waste_logs.find({}).sort("logged_at", -1))
        for log in logs:
            log['_id'] = str(log['_id'])
        serializer = WasteLogSerializer(logs, many=True)
        return Response(serializer.data)

