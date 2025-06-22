from rest_framework import serializers

class ComplianceTaskSerializer(serializers.Serializer):
    _id = serializers.CharField(read_only=True)
    task_name = serializers.CharField(max_length=200)
    description = serializers.CharField(style={'base_template': 'textarea.html'})
    frequency = serializers.ChoiceField(choices=['daily', 'weekly', 'monthly'])
    
class ComplianceLogSerializer(serializers.Serializer):
    _id = serializers.CharField(read_only=True)
    task_id = serializers.CharField(max_length=24)
    task_name = serializers.CharField(read_only=True)
    completed_by_id = serializers.IntegerField()
    completed_by_name = serializers.CharField(read_only=True)
    completed_at = serializers.DateTimeField(read_only=True)
    notes = serializers.CharField(required=False, allow_blank=True)

