from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test # Corrected
from users.views import is_staff_member

def event_list_view(request):
    return render(request, 'events/event_list.html')

@login_required
@user_passes_test(is_staff_member)
def event_management_view(request):
    return render(request, 'events/event_management.html')

