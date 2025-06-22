from rest_framework import serializers

class PerformanceLogSerializer(serializers.Serializer):
    _id = serializers.CharField(read_only=True)
    user_id = serializers.IntegerField()
    user_name = serializers.CharField(read_only=True)
    logged_by_id = serializers.IntegerField(read_only=True)
    logged_by_name = serializers.CharField(read_only=True)
    log_type = serializers.ChoiceField(choices=['positive', 'negative', 'neutral'])
    notes = serializers.CharField()
    created_at = serializers.DateTimeField(read_only=True)

