from rest_framework import serializers
from pos.serializers import OrderSerializer

class CustomerSerializer(serializers.Serializer):
    _id = serializers.CharField(read_only=True)
    name = serializers.CharField(max_length=100)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    joined_at = serializers.DateTimeField(read_only=True)
    loyalty_points = serializers.IntegerField(default=0)
    order_history = OrderSerializer(many=True, read_only=True)

