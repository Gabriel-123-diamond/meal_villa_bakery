from rest_framework import serializers

class SupplierSerializer(serializers.Serializer):
    _id = serializers.CharField(read_only=True)
    name = serializers.CharField(max_length=255)
    contact_person = serializers.CharField(max_length=100, required=False)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(max_length=20)
    address = serializers.CharField(required=False)
    
class PurchaseOrderItemSerializer(serializers.Serializer):
    # This refers to the name of the item we are buying, not its ID in our system
    item_name = serializers.CharField(max_length=255)
    quantity = serializers.FloatField()
    unit = serializers.CharField(max_length=50)
    cost_per_unit = serializers.DecimalField(max_digits=10, decimal_places=2)

class PurchaseOrderSerializer(serializers.Serializer):
    _id = serializers.CharField(read_only=True)
    supplier_id = serializers.CharField(max_length=24)
    supplier_name = serializers.CharField(max_length=255, read_only=True)
    items = PurchaseOrderItemSerializer(many=True)
    total_cost = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    order_date = serializers.DateTimeField(read_only=True)
    status = serializers.ChoiceField(choices=['placed', 'received', 'cancelled'], default='placed')


