from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import datetime
from bson import ObjectId

from bakery_management.db import get_mongo_db
from .serializers import CustomerSerializer
from users.api_views import IsAdminOrManager

class CustomerListCreateAPIView(APIView):
    permission_classes = [IsAdminOrManager]

    def get(self, request, format=None):
        db = get_mongo_db()
        customers = list(db.customers.find({}))
        for customer in customers:
            customer['_id'] = str(customer['_id'])
        serializer = CustomerSerializer(customers, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = CustomerSerializer(data=request.data)
        if serializer.is_valid():
            db = get_mongo_db()
            customer_data = serializer.validated_data
            
            if customer_data.get('email'):
                if db.customers.find_one({'email': customer_data['email']}):
                    return Response({'error': 'A customer with this email already exists.'}, status=status.HTTP_400_BAD_REQUEST)
            
            customer_data['joined_at'] = datetime.datetime.utcnow()
            customer_data['order_history'] = []
            customer_data['loyalty_points'] = 0
            
            result = db.customers.insert_one(customer_data)
            customer_data['_id'] = str(result.inserted_id)
            return Response(customer_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomerDetailAPIView(APIView):
    permission_classes = [IsAdminOrManager]

    def get_object(self, pk):
        db = get_mongo_db()
        try:
            return db.customers.find_one({"_id": ObjectId(pk)})
        except Exception:
            return None

    def get(self, request, pk, format=None):
        customer = self.get_object(pk)
        if not customer:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        db = get_mongo_db()
        order_ids_str = customer.get('order_history', [])
        order_ids = [ObjectId(oid) for oid in order_ids_str]
        orders = list(db.orders.find({"_id": {"$in": order_ids}}).sort("created_at", -1))
        
        for order in orders:
            order['_id'] = str(order['_id'])
            
        customer['order_history'] = orders
        customer['_id'] = str(customer['_id'])
        
        serializer = CustomerSerializer(customer)
        return Response(serializer.data)
        
    def put(self, request, pk, format=None):
        customer = self.get_object(pk)
        if not customer:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        serializer = CustomerSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            db = get_mongo_db()
            db.customers.update_one({"_id": ObjectId(pk)}, {"$set": serializer.validated_data})
            updated_customer = self.get_object(pk)
            updated_customer['_id'] = str(updated_customer['_id'])
            return Response(CustomerSerializer(updated_customer).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        customer = self.get_object(pk)
        if not customer:
            return Response(status=status.HTTP_404_NOT_FOUND)
            
        db = get_mongo_db()
        db.customers.delete_one({"_id": ObjectId(pk)})
        return Response(status=status.HTTP_204_NO_CONTENT)

class AdjustCustomerPointsAPIView(APIView):
    permission_classes = [IsAdminOrManager]

    def post(self, request, pk, format=None):
        try:
            points_to_adjust = int(request.data.get('points', 0))
            reason = request.data.get('reason', 'Manual adjustment by manager.')
        except (ValueError, TypeError):
            return Response({"error": "Invalid 'points' value provided."}, status=status.HTTP_400_BAD_REQUEST)

        db = get_mongo_db()
        try:
            customer_oid = ObjectId(pk)
        except Exception:
            return Response({"error": "Invalid customer ID."}, status=status.HTTP_400_BAD_REQUEST)
        
        result = db.customers.update_one(
            {"_id": customer_oid},
            {"$inc": {"loyalty_points": points_to_adjust}}
        )

        if result.matched_count == 0:
            return Response({"error": "Customer not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response({"success": f"{abs(points_to_adjust)} points {'added' if points_to_adjust > 0 else 'deducted'} successfully."})

