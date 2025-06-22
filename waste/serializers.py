from rest_framework import serializers

class WasteLogSerializer(serializers.Serializer):
    _id = serializers.CharField(read_only=True)
    product_id = serializers.CharField(max_length=24)
    product_name = serializers.CharField(read_only=True)
    quantity = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=255)
    logged_by_name = serializers.CharField(read_only=True)
    logged_at = serializers.DateTimeField(read_only=True)

