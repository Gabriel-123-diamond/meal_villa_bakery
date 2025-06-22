from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import InventoryItemSerializer
from bakery_management.db import get_mongo_db

class CleanerSupplyListAPIView(APIView):
    """
    API endpoint to list all cleaner supplies from MongoDB.
    """
    def get(self, request, format=None):
        db = get_mongo_db()
        items = list(db.cleaner_inventory_items.find({}))
        for item in items:
            item['_id'] = str(item['_id'])
        serializer = InventoryItemSerializer(items, many=True)
        return Response(serializer.data)

class BakerSupplyListAPIView(APIView):
    """
    API endpoint to list all baker supplies from MongoDB.
    """
    def get(self, request, format=None):
        db = get_mongo_db()
        items = list(db.baker_production_supplies.find({}))
        for item in items:
            item['_id'] = str(item['_id'])
        serializer = InventoryItemSerializer(items, many=True)
        return Response(serializer.data)

class StorekeeperSupplyListAPIView(APIView):
    """
    API endpoint to list all storekeeper supplies from MongoDB.
    """
    def get(self, request, format=None):
        db = get_mongo_db()
        items = list(db.storekeeper_supplies_items.find({}))
        for item in items:
            item['_id'] = str(item['_id'])
        serializer = InventoryItemSerializer(items, many=True)
        return Response(serializer.data)

