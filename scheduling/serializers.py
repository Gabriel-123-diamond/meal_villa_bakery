from rest_framework import serializers

class ShiftSerializer(serializers.Serializer):
    _id = serializers.CharField(read_only=True)
    user_id = serializers.IntegerField()
    user_name = serializers.CharField(read_only=True)
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        """
        Check that the start is before the end.
        """
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError("End time must be after start time.")
        return data

