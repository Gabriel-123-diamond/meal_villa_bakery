from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from users.views import is_staff_member
from django.contrib.auth.decorators import user_passes_test

@login_required
def log_waste_view(request):
    """
    Renders the page for staff to log waste.
    """
    return render(request, 'waste/log_waste.html')

@login_required
@user_passes_test(is_staff_member)
def waste_report_view(request):
    """
    Renders the page for managers to view waste reports.
    """
    return render(request, 'waste/waste_report.html')

