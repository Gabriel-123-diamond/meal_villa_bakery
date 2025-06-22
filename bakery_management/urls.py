from django.contrib import admin
from django.urls import path, include
from users import views as user_views
from django_otp.admin import OTPAdminSite

admin.site.__class__ = OTPAdminSite

urlpatterns = [
    path('admin/', admin.site.urls),
    # Web App URLs
    path('', user_views.dashboard_view, name='home'),
    path('accounts/', include('users.urls', namespace='users')),
    path('accounting/', include('accounting.urls', namespace='accounting')),
    path('pos/', include('pos.urls', namespace='pos')),
    path('reports/', include('reports.urls', namespace='reports')),
    path('feedback/', include('feedback.urls', namespace='feedback')),
    path('events/', include('events.urls', namespace='events')),
    path('compliance/', include('compliance.urls', namespace='compliance')),
    path('schedule/', include('scheduling.urls', namespace='scheduling')),
    path('payroll/', include('payroll.urls', namespace='payroll')),
    path('waste/', include('waste.urls', namespace='waste')),
    path('cart/', include('cart.urls', namespace='cart')),
    path('documentation/', include('documentation.urls', namespace='documentation')),
    path('performance/', include('performance.urls', namespace='performance')),
    path('production/', include('production.urls', namespace='production')),
    path('customers/', include('customers.urls', namespace='customers')),

    # API URLs
    path('api/', include('users.urls_api')),
    path('api/', include('inventory.urls_api')),
    path('api/', include('production.urls_api')),
    path('api/', include('pos.urls_api')),
    path('api/', include('customers.urls_api')),
    path('api/', include('reports.urls_api')),
    path('api/', include('accounting.urls_api')),
    path('api/', include('feedback.urls_api')),
    path('api/', include('events.urls_api')),
    path('api/', include('compliance.urls_api')),
    path('api/', include('scheduling.urls_api')),
    path('api/', include('payroll.urls_api')),
    path('api/', include('waste.urls_api')),
    path('api/', include('cart.urls_api')),
    path('api/', include('performance.urls_api')),
]

