from rest_framework import serializers

class InventoryItemSerializer(serializers.Serializer):
    # We define the fields manually because there is no Django model
    name = serializers.CharField(max_length=255)
    quantity = serializers.IntegerField()
    unit = serializers.CharField(max_length=50)
    updated_by_name = serializers.CharField(max_length=255, required=False)
    last_updated_utc = serializers.DateTimeField()

    def to_representation(self, instance):
        # Convert MongoDB's '_id' to a string if needed
        instance['id'] = str(instance['_id'])
        return super().to_representation(instance)


