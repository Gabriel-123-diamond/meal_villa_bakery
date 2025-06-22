from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test # Corrected
from users.views import is_staff_member

@login_required
@user_passes_test(is_staff_member)
def reporting_dashboard_view(request):
    return render(request, 'reports/dashboard.html')

@login_required
@user_passes_test(is_staff_member)
def demand_forecast_view(request):
    return render(request, 'reports/demand_forecast.html')

@login_required
@user_passes_test(is_staff_member)
def profit_loss_view(request):
    return render(request, 'reports/profit_loss.html')

