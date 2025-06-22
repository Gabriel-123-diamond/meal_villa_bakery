from django.urls import path
from . import api_views

urlpatterns = [
    path('payroll/time-clock/', api_views.TimeClockAPIView.as_view(), name='time-clock'),
    path('payroll/profile/<int:user_id>/', api_views.PayrollProfileDetailAPIView.as_view(), name='payroll-profile-detail'),
    path('payroll/report/', api_views.PayrollReportAPIView.as_view(), name='payroll-report'),
    path('payroll/adjustments/', api_views.PayrollAdjustmentAPIView.as_view(), name='payroll-adjustment-create'),
    path('payroll/adjustments/log/', api_views.PayrollAdjustmentListAPIView.as_view(), name='payroll-adjustment-log'), # New
]

