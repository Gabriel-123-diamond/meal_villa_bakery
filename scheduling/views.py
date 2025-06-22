from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test # Corrected
from users.views import is_staff_member

@login_required
@user_passes_test(is_staff_member)
def schedule_management_view(request):
    return render(request, 'scheduling/management.html')

