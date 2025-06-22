from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test # Corrected
from users.views import is_staff_member

def feedback_form_view(request):
    return render(request, 'feedback/feedback_form.html')

@login_required
@user_passes_test(is_staff_member)
def feedback_management_view(request):
    return render(request, 'feedback/feedback_management.html')

