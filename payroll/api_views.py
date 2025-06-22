from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics
from datetime import datetime, date
from django.utils import timezone
from decimal import Decimal
from django.db.models import Sum

from .models import PayrollProfile, TimeClockRecord, PayrollAdjustment
from .serializers import PayrollProfileSerializer, PayrollReportSerializer, PayrollAdjustmentSerializer
from users.api_views import IsAdminOrManager
from django.contrib.auth.models import User

class TimeClockAPIView(APIView):
    def post(self, request, format=None):
        user = request.user
        open_shift = TimeClockRecord.objects.filter(user=user, clock_out__isnull=True).first()
        if open_shift: return Response({"error": "You are already clocked in."}, status=status.HTTP_400_BAD_REQUEST)
        TimeClockRecord.objects.create(user=user, clock_in=timezone.now())
        return Response({"success": "Clocked in successfully."}, status=status.HTTP_201_CREATED)

    def put(self, request, format=None):
        user = request.user
        open_shift = TimeClockRecord.objects.filter(user=user, clock_out__isnull=True).first()
        if not open_shift: return Response({"error": "You are not clocked in."}, status=status.HTTP_400_BAD_REQUEST)
        open_shift.clock_out = timezone.now()
        open_shift.save()
        return Response({"success": "Clocked out successfully.", "hours_worked": round(open_shift.hours_worked, 2)})

class PayrollProfileDetailAPIView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAdminOrManager]
    queryset = PayrollProfile.objects.all()
    serializer_class = PayrollProfileSerializer
    lookup_field = 'user_id'

class PayrollAdjustmentAPIView(generics.CreateAPIView):
    permission_classes = [IsAdminOrManager]
    queryset = PayrollAdjustment.objects.all()
    serializer_class = PayrollAdjustmentSerializer

class PayrollAdjustmentListAPIView(generics.ListAPIView):
    """
    List all payroll adjustments within a given date range.
    """
    permission_classes = [IsAdminOrManager]
    serializer_class = PayrollAdjustmentSerializer

    def get_queryset(self):
        start_date_str = self.request.query_params.get('start_date')
        end_date_str = self.request.query_params.get('end_date')
        
        if not (start_date_str and end_date_str):
            return PayrollAdjustment.objects.none() # Return empty if no dates
            
        try:
            start_date = datetime.fromisoformat(start_date_str).date()
            end_date = datetime.fromisoformat(end_date_str).date()
            return PayrollAdjustment.objects.filter(date_applied__range=[start_date, end_date]).order_by('-date_applied')
        except:
            return PayrollAdjustment.objects.none()

class PayrollReportAPIView(APIView):
    permission_classes = [IsAdminOrManager]
    def get(self, request, format=None):
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        if not (start_date_str and end_date_str): return Response({"error": "start_date and end_date are required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            start_date = datetime.fromisoformat(start_date_str).date()
            end_date = datetime.fromisoformat(end_date_str).date()
        except: return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        users = User.objects.all().order_by('first_name')
        if not request.user.profile.role == 'developer':
            users = users.exclude(profile__role='developer')
            
        report_data = []
        for user in users:
            profile = user.payroll_profile
            monthly_salary = profile.monthly_salary if hasattr(user, 'payroll_profile') else Decimal('0.00')
            
            records = TimeClockRecord.objects.filter(user=user, clock_in__date__range=[start_date, end_date], clock_out__isnull=False)
            total_hours = sum(record.hours_worked for record in records)
            
            if monthly_salary > 0:
                gross_pay = monthly_salary
            else:
                hourly_rate = profile.hourly_rate if hasattr(user, 'payroll_profile') else Decimal('0.00')
                gross_pay = Decimal(str(total_hours)) * hourly_rate
            
            adjustments = PayrollAdjustment.objects.filter(user=user, date_applied__range=[start_date, end_date])
            total_bonuses = adjustments.filter(adjustment_type='bonus').aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
            total_deductions = adjustments.filter(adjustment_type='deduction').aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
            net_pay = gross_pay + total_bonuses - total_deductions

            report_data.append({
                "user_id": user.id, "user_name": user.get_full_name() or user.username, "staff_id": user.username,
                "total_hours": round(total_hours, 2), "monthly_salary": monthly_salary.quantize(Decimal('0.01')),
                "gross_pay": gross_pay.quantize(Decimal('0.01')), "bonuses": total_bonuses.quantize(Decimal('0.01')),
                "deductions": total_deductions.quantize(Decimal('0.01')), "net_pay": net_pay.quantize(Decimal('0.01'))
            })
        serializer = PayrollReportSerializer(report_data, many=True)
        return Response(serializer.data)

