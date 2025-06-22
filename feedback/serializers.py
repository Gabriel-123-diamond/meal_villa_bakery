from rest_framework import serializers

class FeedbackSerializer(serializers.Serializer):
    _id = serializers.CharField(read_only=True)
    customer_name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    subject = serializers.CharField(max_length=200)
    message = serializers.CharField()
    submitted_at = serializers.DateTimeField(read_only=True)
    is_resolved = serializers.BooleanField(default=False)

