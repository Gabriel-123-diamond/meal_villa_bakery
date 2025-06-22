from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from users.views import is_staff_member
from django.contrib.auth.models import User

@login_required
@user_passes_test(is_staff_member)
def performance_review_view(request, user_id):
    """
    Renders the performance review page for a specific employee.
    """
    employee = get_object_or_404(User, id=user_id)
    context = {
        'employee': employee
    }
    return render(request, 'performance/review.html', context)

