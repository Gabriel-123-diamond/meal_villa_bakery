from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test # Corrected
from users.views import is_staff_member

@login_required
@user_passes_test(is_staff_member)
def accounting_management_view(request):
    """
    Renders the main accounting management page.
    Data is fetched client-side via API calls.
    """
    return render(request, 'accounting/management.html')

