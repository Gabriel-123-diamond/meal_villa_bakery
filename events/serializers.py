from rest_framework import serializers

class AttendeeSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    registered_at = serializers.DateTimeField(read_only=True)

class EventSerializer(serializers.Serializer):
    _id = serializers.CharField(read_only=True)
    title = serializers.CharField(max_length=200)
    description = serializers.CharField()
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()
    location = serializers.CharField(max_length=255)
    max_attendees = serializers.IntegerField(min_value=1)
    registered_attendees = AttendeeSerializer(many=True, read_only=True, default=[])

class EventRegistrationSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    email = serializers.EmailField()

