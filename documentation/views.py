from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def documentation_view(request):
    """
    Renders the main documentation and help page.
    """
    return render(request, 'documentation/main.html')

