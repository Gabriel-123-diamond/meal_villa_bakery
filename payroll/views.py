from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from users.views import is_staff_member

@login_required
@user_passes_test(is_staff_member)
def payroll_management_view(request):
    """
    Renders the management dashboard for payroll.
    """
    return render(request, 'payroll/management.html')

@login_required
@user_passes_test(is_staff_member)
def payroll_log_view(request):
    """
    Renders the page for viewing the payroll adjustments log.
    """
    return render(request, 'payroll/log.html')

