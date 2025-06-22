from rest_framework import serializers

class ProductSerializer(serializers.Serializer):
    _id = serializers.CharField(read_only=True)
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    current_stock = serializers.IntegerField(default=0)
    sku = serializers.CharField(max_length=50, required=False)
    category = serializers.CharField(max_length=100, required=False)

class OrderItemSerializer(serializers.Serializer):
    product_id = serializers.CharField(max_length=24)
    name = serializers.CharField(max_length=255, read_only=True)
    quantity = serializers.IntegerField(min_value=1)
    price_at_sale = serializers.FloatField(read_only=True)

class OrderSerializer(serializers.Serializer):
    _id = serializers.CharField(read_only=True)
    created_by_staff_id = serializers.IntegerField(read_only=True, required=False)
    created_by_staff_name = serializers.CharField(read_only=True, required=False)
    customer_id = serializers.CharField(max_length=24, required=False, allow_null=True, allow_blank=True)
    customer_name = serializers.CharField(max_length=100, required=False, default="In-Store Customer")
    items = OrderItemSerializer(many=True)
    
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True, default=0)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    cost_of_goods_sold = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True, default=0)

    # This field is now optional and can be null.
    promo_code = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True, write_only=True)
    applied_promo_code = serializers.CharField(max_length=50, read_only=True, required=False, allow_blank=True)
    
    payment_method = serializers.ChoiceField(choices=["cash", "card", "mobile_payment"])
    
    # This field is now correctly set by the server, not required from the client.
    status = serializers.ChoiceField(choices=["pending", "in_progress", "ready_for_pickup", "completed", "cancelled"], read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

class PromotionSerializer(serializers.Serializer):
    _id = serializers.CharField(read_only=True)
    promo_code = serializers.CharField(max_length=50)
    description = serializers.CharField()
    discount_type = serializers.ChoiceField(choices=["percentage", "fixed_amount"])
    value = serializers.FloatField()
    usage_limit = serializers.IntegerField(min_value=0, default=0, help_text="0 for unlimited uses")
    times_used = serializers.IntegerField(read_only=True, default=0)
    is_active = serializers.BooleanField(default=True)

