from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import PasswordChangeForm
from .forms import LoginForm
from django_otp import devices_for_user
from django_otp.plugins.otp_totp.models import TOTPDevice
from bakery_management.db import get_mongo_db
import datetime
import pytz

def is_staff_member(user):
    return user.is_staff

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, 'Invalid Staff ID or password.')
    else:
        form = LoginForm()
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('users:login')

@login_required
def dashboard_view(request):
    db = get_mongo_db()
    context = {}
    if request.user.is_staff:
        context['product_count'] = db.products.count_documents({})
        context['customer_count'] = db.customers.count_documents({})
        context['order_count'] = db.orders.count_documents({})
        context['supplier_count'] = db.suppliers.count_documents({})
        pipeline = [{'$group': {'_id': None, 'total_revenue': {'$sum': '$total_price'}}}]
        revenue_result = list(db.orders.aggregate(pipeline))
        total_revenue = revenue_result[0]['total_revenue'] if revenue_result else 0
        context['total_revenue'] = f'₦{total_revenue:,.2f}'
    else:
        wat = pytz.timezone('Africa/Lagos')
        now_wat = datetime.datetime.now(wat)
        start_of_day_wat = wat.localize(datetime.datetime.combine(now_wat.date(), datetime.time.min))
        end_of_day_wat = wat.localize(datetime.datetime.combine(now_wat.date(), datetime.time.max))
        start_of_day_utc = start_of_day_wat.astimezone(pytz.utc)
        end_of_day_utc = end_of_day_wat.astimezone(pytz.utc)
        query = {"created_by_staff_id": request.user.id, "created_at": {"$gte": start_of_day_utc, "$lte": end_of_day_utc}}
        staff_orders = list(db.orders.find(query))
        total_revenue = sum(order.get('total_price', 0) for order in staff_orders)
        context['product_count'] = db.products.count_documents({})
        context['staff_order_count'] = len(staff_orders)
        context['staff_total_revenue'] = f'₦{total_revenue:,.2f}'
    return render(request, 'dashboard.html', context)

@login_required
@user_passes_test(is_staff_member)
def staff_management_view(request):
    return render(request, 'users/staff_management.html')

@login_required
def settings_view(request):
    password_form = PasswordChangeForm(request.user)
    
    # Get the primary, confirmed MFA device if one exists
    confirmed_device = TOTPDevice.objects.filter(user=request.user, confirmed=True).first()
    mfa_enabled = confirmed_device is not None

    if request.method == 'POST':
        if 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Your password was successfully updated!')
            else:
                messages.error(request, 'Please correct the password errors below.')
            return redirect('users:settings')
        
        elif 'enable_mfa' in request.POST:
            # Find the unconfirmed device we showed the user and confirm it
            unconfirmed_device = TOTPDevice.objects.filter(user=request.user, confirmed=False).first()
            if unconfirmed_device:
                unconfirmed_device.confirmed = True
                unconfirmed_device.save()
                messages.success(request, 'MFA has been enabled successfully.')
            else:
                messages.error(request, 'Could not find MFA setup device. Please try again.')
            return redirect('users:settings')

        elif 'disable_mfa' in request.POST:
            if confirmed_device:
                confirmed_device.delete()
                # Clean up any unconfirmed devices as well
                TOTPDevice.objects.filter(user=request.user, confirmed=False).delete()
                messages.success(request, 'MFA has been disabled.')
            return redirect('users:settings')

    # For GET requests, determine which device to show for the QR code
    device_for_qr = None
    if not mfa_enabled:
        # If MFA is not enabled, find or create an unconfirmed device to show its QR code
        device_for_qr, created = TOTPDevice.objects.get_or_create(
            user=request.user, 
            confirmed=False,
            defaults={'name': f"{request.user.username}_totp"}
        )
        
    context = {
        'form': password_form,
        'mfa_enabled': mfa_enabled,
        'mfa_device': device_for_qr
    }
    return render(request, 'users/settings.html', context)

