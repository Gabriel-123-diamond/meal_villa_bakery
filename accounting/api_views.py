from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from bson import ObjectId
from decimal import Decimal
import datetime

from bakery_management.db import get_mongo_db
from .serializers import SupplierSerializer, PurchaseOrderSerializer

class SupplierListCreateAPIView(APIView):
    """
    API endpoint to list all suppliers or create a new one.
    """
    def get(self, request, format=None):
        db = get_mongo_db()
        suppliers = list(db.suppliers.find({}))
        for supplier in suppliers:
            supplier['_id'] = str(supplier['_id'])
        serializer = SupplierSerializer(suppliers, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = SupplierSerializer(data=request.data)
        if serializer.is_valid():
            db = get_mongo_db()
            db.suppliers.insert_one(serializer.validated_data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PurchaseOrderListCreateAPIView(APIView):
    """
    API endpoint to list all purchase orders or create a new one.
    """
    def get(self, request, format=None):
        db = get_mongo_db()
        purchase_orders = list(db.purchase_orders.find({}).sort("order_date", -1))
        for po in purchase_orders:
            po['_id'] = str(po['_id'])
        serializer = PurchaseOrderSerializer(purchase_orders, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = PurchaseOrderSerializer(data=request.data)
        if serializer.is_valid():
            db = get_mongo_db()
            po_data = serializer.validated_data

            try:
                supplier_oid = ObjectId(po_data['supplier_id'])
                supplier = db.suppliers.find_one({"_id": supplier_oid})
                if not supplier:
                    return Response({"error": "Supplier not found."}, status=status.HTTP_404_NOT_FOUND)
            except Exception:
                return Response({"error": "Invalid supplier_id."}, status=status.HTTP_400_BAD_REQUEST)

            total_cost = sum(Decimal(str(item['cost_per_unit'])) * Decimal(str(item['quantity'])) for item in po_data['items'])
            
            po_data['items'] = [dict(item) for item in po_data['items']]

            db_object = {
                "supplier_id": str(supplier_oid),
                "supplier_name": supplier.get('name'),
                "items": po_data['items'],
                "total_cost": float(total_cost),
                "order_date": datetime.datetime.utcnow(),
                "status": "placed"
            }
            result = db.purchase_orders.insert_one(db_object)
            db_object['_id'] = str(result.inserted_id)
            
            return Response(PurchaseOrderSerializer(db_object).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ReceivePurchaseOrderAPIView(APIView):
    """
    API endpoint to mark a purchase order as 'received' and update inventory stock and costs.
    """
    def post(self, request, po_id, format=None):
        db = get_mongo_db()
        try:
            po_oid = ObjectId(po_id)
        except Exception:
            return Response({"error": "Invalid purchase order ID format."}, status=status.HTTP_400_BAD_REQUEST)

        purchase_order = db.purchase_orders.find_one({"_id": po_oid})
        if not purchase_order:
            return Response({"error": "Purchase order not found."}, status=status.HTTP_404_NOT_FOUND)
        if purchase_order.get('status') == 'received':
            return Response({"error": "This order has already been received."}, status=status.HTTP_400_BAD_REQUEST)

        for item in purchase_order.get('items', []):
            item_name_lower = item['item_name'].lower()
            quantity_received = float(item['quantity'])
            cost_per_unit_received = float(item['cost_per_unit'])
            
            collection_to_update = None
            if any(keyword in item_name_lower for keyword in ['soap', 'cleaner', 'freshener']):
                collection_to_update = db.cleaner_inventory_items
            elif any(keyword in item_name_lower for keyword in ['flour', 'sugar', 'yeast', 'salt']):
                collection_to_update = db.baker_production_supplies
            else:
                collection_to_update = db.storekeeper_supplies_items

            # Calculate weighted average cost
            current_item = collection_to_update.find_one({"name_lower": item_name_lower})
            if current_item:
                current_qty = float(current_item.get('quantity', 0))
                current_cost = float(current_item.get('cost_per_unit', 0))
                new_total_qty = current_qty + quantity_received
                new_avg_cost = ((current_qty * current_cost) + (quantity_received * cost_per_unit_received)) / new_total_qty if new_total_qty > 0 else 0
            else:
                new_avg_cost = cost_per_unit_received

            collection_to_update.update_one(
                {"name_lower": item_name_lower},
                {
                    "$inc": {"quantity": quantity_received},
                    "$set": {
                        "name": item['item_name'],
                        "unit": item['unit'],
                        "cost_per_unit": new_avg_cost
                    },
                    "$setOnInsert": {"name_lower": item_name_lower}
                },
                upsert=True
            )

        db.purchase_orders.update_one({"_id": po_oid}, {"$set": {"status": "received"}})

        return Response({"success": f"Order {po_id} marked as received and inventory has been updated."})

