from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from users.views import is_staff_member
from django.contrib.auth.decorators import user_passes_test

@login_required
@user_passes_test(is_staff_member)
def recipe_management_view(request):
    """
    Renders the management dashboard for creating and editing recipes.
    """
    return render(request, 'production/recipe_management.html')

