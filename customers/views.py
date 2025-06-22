from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from users.views import is_staff_member

@login_required
@user_passes_test(is_staff_member)
def customer_management_view(request):
    """
    Renders the customer management dashboard.
    """
    return render(request, 'customers/management.html')

