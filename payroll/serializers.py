from rest_framework import serializers
from .models import PayrollProfile, TimeClockRecord, PayrollAdjustment
from django.contrib.auth.models import User

class PayrollProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollProfile
        fields = ['user', 'hourly_rate', 'monthly_salary']
        read_only_fields = ['user']

class TimeClockRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeClockRecord
        fields = '__all__'

class PayrollAdjustmentSerializer(serializers.ModelSerializer):
    # This makes the API response include the user's name, but it's not required for writing.
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    # This explicitly tells the serializer to expect a User ID for this field when writing.
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = PayrollAdjustment
        fields = ['id', 'user', 'user_name', 'amount', 'adjustment_type', 'reason', 'date_applied']
        read_only_fields = ['id', 'date_applied', 'user_name']

class PayrollReportSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    user_name = serializers.CharField()
    staff_id = serializers.CharField()
    total_hours = serializers.FloatField()
    monthly_salary = serializers.DecimalField(max_digits=10, decimal_places=2)
    gross_pay = serializers.DecimalField(max_digits=10, decimal_places=2)
    bonuses = serializers.DecimalField(max_digits=10, decimal_places=2)
    deductions = serializers.DecimalField(max_digits=10, decimal_places=2)
    net_pay = serializers.DecimalField(max_digits=10, decimal_places=2)

