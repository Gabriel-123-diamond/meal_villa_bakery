from rest_framework import serializers
from django.contrib.auth.models import User
from django.db import transaction
from .models import UserProfile
from payroll.models import PayrollProfile

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['role', 'staff_id']

class PayrollProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollProfile
        fields = ['hourly_rate']

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()
    payroll_profile = PayrollProfileSerializer(read_only=True) # Expose payroll data
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'is_active', 'is_staff', 'profile', 'payroll_profile', 'password']
    
    @transaction.atomic
    def create(self, validated_data):
        profile_data = validated_data.pop('profile')
        password = validated_data.pop('password')
        
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        
        # UserProfile and PayrollProfile are created by post_save signals
        UserProfile.objects.filter(user=user).update(role=profile_data['role'])
        
        return user

    @transaction.atomic
    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)
        
        instance.username = validated_data.get('username', instance.username)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.is_active = validated_data.get('is_active', instance.is_active)
        instance.is_staff = validated_data.get('is_staff', instance.is_staff)
        
        if 'password' in validated_data and validated_data['password']:
            instance.set_password(validated_data['password'])
            
        instance.save()
        
        if profile_data:
            profile = instance.profile
            profile.role = profile_data.get('role', profile.role)
            profile.staff_id = validated_data.get('username', profile.staff_id)
            profile.save()
        
        return instance

