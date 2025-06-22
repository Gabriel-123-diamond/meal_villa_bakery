from rest_framework import generics, permissions
from django.contrib.auth.models import User
from .serializers import UserSerializer

class IsAdminOrManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_staff

class UserListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrManager]
    
    def get_queryset(self):
        queryset = User.objects.all().order_by('first_name').select_related('profile', 'payroll_profile')
        # Hide the 'developer' from the list unless the logged-in user is a developer
        if not self.request.user.profile.role == 'developer':
            queryset = queryset.exclude(profile__role='developer')
        return queryset

class UserDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrManager]
    
    def get_queryset(self):
        # This ensures managers can't even access the developer's detail page via URL
        queryset = User.objects.all().select_related('profile', 'payroll_profile')
        if not self.request.user.profile.role == 'developer':
            queryset = queryset.exclude(profile__role='developer')
        return queryset

