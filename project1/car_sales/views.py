from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
import json
import logging
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import connection, connections, transaction, DatabaseError
from rest_framework.views import APIView
from django.utils.datastructures import MultiValueDictKeyError
from django.apps import apps
from .models import *
from django.views.decorators.csrf import csrf_exempt
from django.http import Http404, JsonResponse, HttpResponseRedirect, HttpResponseForbidden, StreamingHttpResponse, HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .serializers import *
from rest_framework import status
from django_redis import cache
# from django.core.cache import cache
from collections import defaultdict
from django.urls import reverse
from django.contrib.auth.models import User
# from django.forms.model import model_to_dict

# Required imports for the original views
from django.db.models import Sum, Count, Avg, F, Q
from django.db.models.functions import TruncMonth
from django import forms
from django.forms import ModelForm, IntegerField
from django.forms import modelform_factory
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required

from django.contrib.auth.backends import BaseBackend
import types

# Helper functions for Role-Based Hierarchy System
def get_employee_profile(request):
    if not request.user.is_authenticated:
        return None
    username = request.user.username
    if username.startswith('emp_'):
        try:
            emp_id = int(username.split('_')[1])
            return Employee.objects.select_related('employee_role', 'status', 'store').filter(employee_id=emp_id).first()
        except (ValueError, IndexError):
            return None
    return None

def filter_by_hierarchy(queryset, request, employee_profile, store_field='store', employee_field='employee'):
    if not employee_profile or request.user.is_superuser:
        return queryset
        
    role = employee_profile.employee_role.role_name if employee_profile.employee_role else ""
    
    # 1. Global Roles: see all
    if role in ["Regional Sales Manager"]:
        return queryset
    # 2. Store-Level Roles: filter by store
    elif role in ["Branch Manager", "Showroom Manager", "Sales Manager", "Finance & Insurance Officer"]:
        if store_field == 'self':
            return queryset.filter(store_id=employee_profile.store.store_id)
        elif store_field:
            return queryset.filter(**{store_field: employee_profile.store})
        return queryset
    # 3. Employee-Level Roles: filter by self
    else:
        if employee_field == 'self':
            return queryset.filter(employee_id=employee_profile.employee_id)
        elif employee_field:
            return queryset.filter(**{employee_field: employee_profile})
        elif store_field == 'self':
            return queryset.filter(store_id=employee_profile.store.store_id)
        elif store_field:
            return queryset.filter(**{store_field: employee_profile.store})
        return queryset


# Create your views here.
@login_required
def home_view(request):
    profile = get_employee_profile(request)
    
    # Filter base querysets
    sales_qs = filter_by_hierarchy(SellingInfo.objects.all(), request, profile, 'store', 'employee')
    customers_qs = filter_by_hierarchy(CustomerInfo.objects.all(), request, profile, 'sales__store', 'sales__employee').distinct()

    # 1. Total statistics
    sales_count = sales_qs.count()
    total_revenue = sales_qs.aggregate(total=Sum('selling_price'))['total'] or 0
    customers_count = customers_qs.count()
    
    # 2. Recent Sales (latest 5 sales)
    recent_sales = sales_qs.select_related('customer', 'vehicle__make', 'employee', 'store').order_by('-selling_date', '-sell_id')[:5]
    
    # 3. Top Selling vehicle makes
    top_selling = sales_qs.values('vehicle__make__make_name').annotate(
        count=Count('sell_id'),
        revenue=Sum('selling_price')
    ).order_by('-count')[:5]
    
    # 4. Chart series (grouped by month)
    monthly_sales = sales_qs.annotate(
        month=TruncMonth('selling_date')
    ).values('month').annotate(
        count=Count('sell_id'),
        revenue=Sum('selling_price')
    ).order_by('month')
    
    chart_dates = [item['month'].strftime('%b %Y') for item in monthly_sales]
    chart_sales = [item['count'] for item in monthly_sales]
    chart_revenue = [item['revenue'] for item in monthly_sales]
    
    context = {
        'active_tab': 'dashboard',
        'sales_count': sales_count,
        'total_revenue': total_revenue,
        'customers_count': customers_count,
        'recent_sales': recent_sales,
        'top_selling': top_selling,
        'chart_dates': chart_dates,
        'chart_sales': chart_sales,
        'chart_revenue': chart_revenue,
    }
    return render(request, 'car_sales/dashboard.html', context)

# Alias to support dashboard name referencing
dashboard_view = home_view

def index_view(request):
    """Public landing page at /"""
    return render(request, 'car_sales/index.html')

@login_required
def employee_view(request):
    profile = get_employee_profile(request)
    roles = EmployeeRole.objects.all()
    statuses = EmployeeStatus.objects.all()
    stores = filter_by_hierarchy(Store.objects.all(), request, profile, 'self', None)
    cities = City.objects.all()
    countries = Country.objects.all()
    context = {
        'active_tab': 'employees',
        'roles': roles,
        'statuses': statuses,
        'stores': stores,
        'cities': cities,
        'countries': countries,
    }
    return render(request, 'car_sales/employee_view.html', context)

@login_required
def country_view(request):
    context = {
        'active_tab': 'countries',
    }
    return render(request, 'car_sales/country_view.html', context)

@login_required
def city_view(request):
    countries = Country.objects.all()
    context = {
        'active_tab': 'cities',
        'countries': countries,
    }
    return render(request, 'car_sales/city_view.html', context)

@login_required
def store_view(request):
    cities = City.objects.all()
    countries = Country.objects.all()
    context = {
        'active_tab': 'stores',
        'cities': cities,
        'countries': countries,
    }
    return render(request, 'car_sales/store_view.html', context)

@login_required
def role_view(request):
    context = {
        'active_tab': 'roles',
    }
    return render(request, 'car_sales/role_view.html', context)

@login_required
def status_view(request):
    context = {
        'active_tab': 'statuses',
    }
    return render(request, 'car_sales/status_view.html', context)

@login_required
def industry_view(request):
    context = {
        'active_tab': 'industry',
    }
    return render(request, 'car_sales/industry_view.html', context)

@login_required
def vehicle_view(request):
    makes = IndustryInfo.objects.all()
    context = {
        'active_tab': 'vehicles',
        'makes': makes,
    }
    return render(request, 'car_sales/vehicle_view.html', context)

@login_required
def customer_view(request):
    cities = City.objects.all()
    countries = Country.objects.all()
    context = {
        'active_tab': 'customers',
        'cities': cities,
        'countries': countries,
    }
    return render(request, 'car_sales/customer_view.html', context)

@login_required
def selling_view(request):
    profile = get_employee_profile(request)
    employees = filter_by_hierarchy(Employee.objects.all(), request, profile, 'store', 'self')
    stores = filter_by_hierarchy(Store.objects.all(), request, profile, 'self', None)
    context = {
        'active_tab': 'sales',
        'employees': employees,
        'stores': stores,
    }
    return render(request, 'car_sales/selling_view.html', context)

@login_required
def budget_view(request):
    profile = get_employee_profile(request)
    employees = filter_by_hierarchy(Employee.objects.all(), request, profile, 'store', 'self')
    stores = filter_by_hierarchy(Store.objects.all(), request, profile, 'self', None)
    
    # Get distinct budget years from database
    years = list(EmployeeBudget.objects.values_list('budget_year', flat=True).distinct().order_by('-budget_year'))
    import datetime
    current_year = datetime.date.today().year
    if current_year not in years:
        years.insert(0, current_year)
        
    context = {
        'active_tab': 'budgets',
        'employees': employees,
        'stores': stores,
        'years': years,
        'current_year': current_year,
    }
    return render(request, 'car_sales/budget_view.html', context)




@staff_member_required(login_url='login')
def admin_panel_view(request):
    stats = {
        'countries': {'name': 'Countries', 'count': Country.objects.count(), 'url': '/countries/', 'slug': 'country'},
        'cities': {'name': 'Cities', 'count': City.objects.count(), 'url': '/cities/', 'slug': 'city'},
        'stores': {'name': 'Stores', 'count': Store.objects.count(), 'url': '/stores/', 'slug': 'store'},
        'roles': {'name': 'Employee Roles', 'count': EmployeeRole.objects.count(), 'url': '/emproles/', 'slug': 'employeerole'},
        'statuses': {'name': 'Employee Statuses', 'count': EmployeeStatus.objects.count(), 'url': '/statuses/', 'slug': 'employeestatus'},
        'employees': {'name': 'Employees', 'count': Employee.objects.count(), 'url': '/employees/', 'slug': 'employee'},
        'industry': {'name': 'Vehicle Makes', 'count': IndustryInfo.objects.count(), 'url': '/industry/', 'slug': 'industryinfo'},
        'vehicles': {'name': 'Vehicles', 'count': VehicleInfo.objects.count(), 'url': '/vehicles/', 'slug': 'vehicleinfo'},
        'customers': {'name': 'Customers', 'count': CustomerInfo.objects.count(), 'url': '/customers/', 'slug': 'customerinfo'},
        'sales': {'name': 'Sales Transactions', 'count': SellingInfo.objects.count(), 'url': '/sales/', 'slug': 'sellinginfo'},
        'budgets': {'name': 'Employee Budget', 'count': EmployeeBudget.objects.count(), 'url': '/budgets/', 'slug': 'employeebudget'},
        'invoices': {'name': 'Invoices', 'count': Invoice.objects.count(), 'url': '/invoices/', 'slug': 'invoice'},

    }
    context = {
        'active_tab': 'admin_panel',
        'stats': stats,
    }
    return render(request, 'car_sales/admin_panel.html', context)













# --- API Endpoint implementing Supervisor's Stored-Procedure/Raw SQL approach ---
@api_view(['GET', 'POST'])
def employee_sales_api(request):
    if not request.user.is_authenticated:
        return Response(
            {"status": False, "message": "Authentication required."},
            status=status.HTTP_401_UNAUTHORIZED
        )
        
    is_allowed = request.user.is_superuser or request.user.is_staff
    if not is_allowed:
        profile = get_employee_profile(request)
        if profile and profile.employee_role:
            role = profile.employee_role.role_name.lower()
            if "manager" in role or "admin" in role:
                is_allowed = True
                
    if not is_allowed:
        return Response(
            {"status": False, "message": "Access Denied. Only administrators and store managers can fetch this API data."},
            status=status.HTTP_403_FORBIDDEN
        )

    dt_from = None
    dt_to = None

    # Try parsing from request body first
    if hasattr(request, 'data') and request.data:
        if isinstance(request.data, dict) or hasattr(request.data, 'get'):
            dt_from = request.data.get('dt_from')
            dt_to = request.data.get('dt_to')

    # Fall back to query parameters
    if not dt_from:
        dt_from = request.GET.get('dt_from')
    if not dt_to:
        dt_to = request.GET.get('dt_to')

    if not dt_from or not dt_to:
        return Response(
            {"status": False, "message": "dt_from and dt_to parameters are required (YYYY-MM-DD)."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Determine store/employee level filtering based on hierarchy roles
    store_id = None
    employee_id = None
    profile = get_employee_profile(request)
    
    if not request.user.is_superuser and profile and profile.employee_role:
        role = profile.employee_role.role_name
        
        # Store-Level Roles: filter by their store
        if role in ["Branch Manager", "Showroom Manager", "Sales Manager", "Finance & Insurance Officer"]:
            store_id = profile.store.store_id
        # Employee-Level Roles: filter by themselves
        elif role not in ["Regional Sales Manager", "Customer Relations Officer"]:
            employee_id = profile.employee_id

    try:
        data = employeesalesserializers.fetch(dt_from, dt_to, store_id=store_id, employee_id=employee_id)
        return Response({"status": True, "data": data}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
def store_sales_api(request):
    if not request.user.is_authenticated:
        return Response(
            {"status": False, "message": "Authentication required."},
            status=status.HTTP_401_UNAUTHORIZED
        )
        
    is_allowed = request.user.is_superuser or request.user.is_staff
    if not is_allowed:
        profile = get_employee_profile(request)
        if profile and profile.employee_role:
            role = profile.employee_role.role_name.lower()
            if "manager" in role or "admin" in role:
                is_allowed = True
                
    if not is_allowed:
        return Response(
            {"status": False, "message": "Access Denied. Only administrators and store managers can fetch this API data."},
            status=status.HTTP_403_FORBIDDEN
        )

    dt_from = None
    dt_to = None

    # Try parsing from request body first
    if hasattr(request, 'data') and request.data:
        if isinstance(request.data, dict) or hasattr(request.data, 'get'):
            dt_from = request.data.get('dt_from')
            dt_to = request.data.get('dt_to')

    # Fall back to query parameters
    if not dt_from:
        dt_from = request.GET.get('dt_from')
    if not dt_to:
        dt_to = request.GET.get('dt_to')

    if not dt_from or not dt_to:
        return Response(
            {"status": False, "message": "dt_from and dt_to parameters are required (YYYY-MM-DD)."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Determine store/employee level filtering based on hierarchy roles
    store_id = None
    employee_id = None
    profile = get_employee_profile(request)
    
    if not request.user.is_superuser and profile and profile.employee_role:
        role = profile.employee_role.role_name
        
        # Store-Level Roles: filter by their store
        if role in ["Branch Manager", "Showroom Manager", "Sales Manager", "Finance & Insurance Officer"]:
            store_id = profile.store.store_id
        # Employee-Level Roles: filter by themselves
        elif role not in ["Regional Sales Manager", "Customer Relations Officer"]:
            employee_id = profile.employee_id

    try:
        data = storesalesserializer.fetch(dt_from, dt_to, store_id=store_id, employee_id=employee_id)
        return Response({"status": True, "data": data}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@login_required
def employee_sales_page_view(request):
    profile = get_employee_profile(request)
    is_allowed = request.user.is_superuser or request.user.is_staff
    if not is_allowed and profile and profile.employee_role:
        role = profile.employee_role.role_name.lower()
        if "manager" in role or "admin" in role:
            is_allowed = True
            
    if not is_allowed:
        messages.error(request, "Permission denied. Only administrators and store managers can access this page.")
        return redirect('home')
        
    context = {
        'active_parent': 'api_pages',
        'active_tab': 'api_employee_sales',
    }
    return render(request, 'car_sales/api_employee_sales.html', context)


@login_required
def store_sales_page_view(request):
    profile = get_employee_profile(request)
    is_allowed = request.user.is_superuser or request.user.is_staff
    if not is_allowed and profile and profile.employee_role:
        role = profile.employee_role.role_name.lower()
        if "manager" in role or "admin" in role:
            is_allowed = True
            
    if not is_allowed:
        messages.error(request, "Permission denied. Only administrators and store managers can access this page.")
        return redirect('home')
        
    context = {
        'active_parent': 'api_pages',
        'active_tab': 'api_store_sales',
    }
    return render(request, 'car_sales/api_store_sales.html', context)


@api_view(['GET', 'POST'])
def store_vehicle_sales_api(request):
    if not request.user.is_authenticated:
        return Response(
            {"status": False, "message": "Authentication required."},
            status=status.HTTP_401_UNAUTHORIZED
        )
        
    is_allowed = request.user.is_superuser or request.user.is_staff
    profile = get_employee_profile(request)
    if not is_allowed and profile and profile.employee_role:
        role = profile.employee_role.role_name.lower()
        if "manager" in role or "admin" in role:
            is_allowed = True
            
    if not is_allowed:
        return Response(
            {"status": False, "message": "Access Denied. Only administrators and store managers can fetch this API data."},
            status=status.HTTP_403_FORBIDDEN
        )

    dt_from = None
    dt_to = None

    if hasattr(request, 'data') and request.data:
        if isinstance(request.data, dict) or hasattr(request.data, 'get'):
            dt_from = request.data.get('dt_from')
            dt_to = request.data.get('dt_to')

    if not dt_from:
        dt_from = request.GET.get('dt_from')
    if not dt_to:
        dt_to = request.GET.get('dt_to')

    if not dt_from or not dt_to:
        return Response(
            {"status": False, "message": "dt_from and dt_to parameters are required (YYYY-MM-DD)."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Determine store/employee level filtering based on hierarchy roles
    store_id = None
    employee_id = None
    
    if not request.user.is_superuser and profile and profile.employee_role:
        role = profile.employee_role.role_name
        
        # Store-Level Roles: filter by their store
        if role in ["Branch Manager", "Showroom Manager", "Sales Manager", "Finance & Insurance Officer"]:
            store_id = profile.store.store_id
        # Employee-Level Roles: filter by themselves
        elif role not in ["Regional Sales Manager", "Customer Relations Officer"]:
            employee_id = profile.employee_id

    try:
        data = storevehiclesalesserializer.fetch(dt_from, dt_to, store_id=store_id, employee_id=employee_id)
        return Response({"status": True, "data": data}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@login_required
def store_vehicle_sales_page_view(request):
    profile = get_employee_profile(request)
    is_allowed = request.user.is_superuser or request.user.is_staff
    if not is_allowed and profile and profile.employee_role:
        role = profile.employee_role.role_name.lower()
        if "manager" in role or "admin" in role:
            is_allowed = True
            
    if not is_allowed:
        messages.error(request, "Permission denied. Only administrators and store managers can access this page.")
        return redirect('home')
        
    context = {
        'active_parent': 'api_pages',
        'active_tab': 'api_store_vehicle_sales',
    }
    return render(request, 'car_sales/api_store_vehicle_sales.html', context)


@api_view(['GET', 'POST'])
def customer_vehicle_sales_api(request):
    if not request.user.is_authenticated:
        return Response(
            {"status": False, "message": "Authentication required."},
            status=status.HTTP_401_UNAUTHORIZED
        )
        
    is_allowed = request.user.is_superuser or request.user.is_staff
    profile = get_employee_profile(request)
    if not is_allowed and profile and profile.employee_role:
        role = profile.employee_role.role_name.lower()
        if "manager" in role or "admin" in role:
            is_allowed = True
            
    if not is_allowed:
        return Response(
            {"status": False, "message": "Access Denied. Only administrators and store managers can fetch this API data."},
            status=status.HTTP_403_FORBIDDEN
        )

    dt_from = None
    dt_to = None

    if hasattr(request, 'data') and request.data:
        if isinstance(request.data, dict) or hasattr(request.data, 'get'):
            dt_from = request.data.get('dt_from')
            dt_to = request.data.get('dt_to')

    if not dt_from:
        dt_from = request.GET.get('dt_from')
    if not dt_to:
        dt_to = request.GET.get('dt_to')

    if not dt_from or not dt_to:
        return Response(
            {"status": False, "message": "dt_from and dt_to parameters are required (YYYY-MM-DD)."},
            status=status.HTTP_400_BAD_REQUEST
        )

    store_id = None
    employee_id = None
    
    if not request.user.is_superuser and profile and profile.employee_role:
        role = profile.employee_role.role_name
        
        # Store-Level Roles: filter by their store
        if role in ["Branch Manager", "Showroom Manager", "Sales Manager", "Finance & Insurance Officer"]:
            store_id = profile.store.store_id
        # Employee-Level Roles: filter by themselves
        elif role not in ["Regional Sales Manager", "Customer Relations Officer"]:
            employee_id = profile.employee_id

    try:
        data = customervehiclesalesserializer.fetch(dt_from, dt_to, store_id=store_id, employee_id=employee_id)
        return Response({"status": True, "data": data}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@login_required
def customer_vehicle_sales_page_view(request):
    profile = get_employee_profile(request)
    is_allowed = request.user.is_superuser or request.user.is_staff
    if not is_allowed and profile and profile.employee_role:
        role = profile.employee_role.role_name.lower()
        if "manager" in role or "admin" in role:
            is_allowed = True
            
    if not is_allowed:
        messages.error(request, "Permission denied. Only administrators and store managers can access this page.")
        return redirect('home')
        
    context = {
        'active_parent': 'api_pages',
        'active_tab': 'api_customer_vehicle_sales',
    }
    return render(request, 'car_sales/api_customer_vehicle_sales.html', context)


@api_view(['GET', 'POST'])
def customer_store_spending_api(request):
    if not request.user.is_authenticated:
        return Response(
            {"status": False, "message": "Authentication required."},
            status=status.HTTP_401_UNAUTHORIZED
        )
        
    is_allowed = request.user.is_superuser or request.user.is_staff
    profile = get_employee_profile(request)
    if not is_allowed and profile and profile.employee_role:
        role = profile.employee_role.role_name.lower()
        if "manager" in role or "admin" in role:
            is_allowed = True
            
    if not is_allowed:
        return Response(
            {"status": False, "message": "Access Denied. Only administrators and store managers can fetch this API data."},
            status=status.HTTP_403_FORBIDDEN
        )

    dt_from = None
    dt_to = None

    if hasattr(request, 'data') and request.data:
        if isinstance(request.data, dict) or hasattr(request.data, 'get'):
            dt_from = request.data.get('dt_from')
            dt_to = request.data.get('dt_to')

    if not dt_from:
        dt_from = request.GET.get('dt_from')
    if not dt_to:
        dt_to = request.GET.get('dt_to')

    if not dt_from or not dt_to:
        return Response(
            {"status": False, "message": "dt_from and dt_to parameters are required (YYYY-MM-DD)."},
            status=status.HTTP_400_BAD_REQUEST
        )

    store_id = None
    employee_id = None
    
    if not request.user.is_superuser and profile and profile.employee_role:
        role = profile.employee_role.role_name
        
        # Store-Level Roles: filter by their store
        if role in ["Branch Manager", "Showroom Manager", "Sales Manager", "Finance & Insurance Officer"]:
            store_id = profile.store.store_id
        # Employee-Level Roles: filter by themselves
        elif role not in ["Regional Sales Manager", "Customer Relations Officer"]:
            employee_id = profile.employee_id

    try:
        data = customerstorespendingserializer.fetch(dt_from, dt_to, store_id=store_id, employee_id=employee_id)
        return Response({"status": True, "data": data}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@login_required
def customer_store_spending_page_view(request):
    profile = get_employee_profile(request)
    is_allowed = request.user.is_superuser or request.user.is_staff
    if not is_allowed and profile and profile.employee_role:
        role = profile.employee_role.role_name.lower()
        if "manager" in role or "admin" in role:
            is_allowed = True
            
    if not is_allowed:
        messages.error(request, "Permission denied. Only administrators and store managers can access this page.")
        return redirect('home')
        
    context = {
        'active_parent': 'api_pages',
        'active_tab': 'api_customer_store_spending',
    }
    return render(request, 'car_sales/api_customer_store_spending.html', context)


@api_view(['GET', 'POST'])
def budget_vs_sales_api(request):
    if not request.user.is_authenticated:
        return Response(
            {"status": False, "message": "Authentication required."},
            status=status.HTTP_401_UNAUTHORIZED
        )
        
    is_allowed = request.user.is_superuser or request.user.is_staff
    if not is_allowed:
        profile = get_employee_profile(request)
        if profile and profile.employee_role:
            role = profile.employee_role.role_name.lower()
            if "manager" in role or "admin" in role:
                is_allowed = True
                
    if not is_allowed:
        return Response(
            {"status": False, "message": "Access Denied. Only administrators and store managers can fetch this API data."},
            status=status.HTTP_403_FORBIDDEN
        )

    dt_from = None
    dt_to = None

    if hasattr(request, 'data') and request.data:
        if isinstance(request.data, dict) or hasattr(request.data, 'get'):
            dt_from = request.data.get('dt_from')
            dt_to = request.data.get('dt_to')

    if not dt_from:
        dt_from = request.GET.get('dt_from')
    if not dt_to:
        dt_to = request.GET.get('dt_to')

    if not dt_from or not dt_to:
        return Response(
            {"status": False, "message": "dt_from and dt_to parameters are required (YYYY-MM-DD)."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        data = budgetvssalesserializer.fetch(dt_from, dt_to)
        return Response({"status": True, "data": data}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@login_required
def budget_vs_sales_page_view(request):
    profile = get_employee_profile(request)
    is_allowed = request.user.is_superuser or request.user.is_staff
    if not is_allowed and profile and profile.employee_role:
        role = profile.employee_role.role_name.lower()
        if "manager" in role or "admin" in role:
            is_allowed = True
            
    if not is_allowed:
        messages.error(request, "Permission denied. Only administrators and store managers can access this page.")
        return redirect('home')
        
    context = {
        'active_parent': 'api_pages',
        'active_tab': 'api_budget_vs_sales',
    }
    return render(request, 'car_sales/api_budget_vs_sales.html', context)


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def inventory_api(request, pk=None):
    if not request.user.is_authenticated:
        return Response(
            {"status": False, "message": "Authentication required."},
            status=status.HTTP_401_UNAUTHORIZED
        )
        
    is_staff = request.user.is_superuser or request.user.is_staff
    
    if request.method in ['POST', 'PUT', 'DELETE'] and not is_staff:
        return Response(
            {"status": False, "message": "Permission denied. Only staff members can modify inventory data."},
            status=status.HTTP_403_FORBIDDEN
        )

    if request.method == 'GET':
        if pk is not None:
            item = inventoryserializer.fetch_one(pk)
            if item:
                return Response({"status": True, "data": item}, status=status.HTTP_200_OK)
            return Response({"status": False, "message": "Record not found."}, status=status.HTTP_404_NOT_FOUND)
            
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 25))
        except ValueError:
            page = 1
            page_size = 25
            
        offset = (page - 1) * page_size
        search = request.GET.get('search', '').strip()
        
        store_id = None
        employee_id = None
        profile = get_employee_profile(request)
        if not request.user.is_superuser and profile and profile.employee_role:
            role = profile.employee_role.role_name
            if role in ["Branch Manager", "Showroom Manager", "Sales Manager", "Finance & Insurance Officer"]:
                store_id = profile.store.store_id
            elif role not in ["Regional Sales Manager", "Customer Relations Officer"]:
                employee_id = profile.employee_id

        total, data = inventoryserializer.fetch(limit=page_size, offset=offset, search=search, store_id=store_id, employee_id=employee_id)
        return Response({
            "status": True,
            "total": total,
            "page": page,
            "page_size": page_size,
            "data": data
        }, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        vehicle = request.data.get('vehicle')
        store = request.data.get('store')
        employee = request.data.get('employee')
        status_val = request.data.get('status')
        selling_info = request.data.get('selling_info') or None

        if not vehicle or not store or not employee or status_val is None:
            return Response({"status": False, "message": "Vehicle, store, employee, and status are required fields."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            new_id = inventoryserializer.create(vehicle, store, employee, status_val, selling_info)
            new_item = inventoryserializer.fetch_one(new_id)
            return Response({
                "status": True,
                "message": "Inventory record created successfully.",
                "data": new_item
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"status": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'PUT':
        item = inventoryserializer.fetch_one(pk)
        if not item:
            return Response({"status": False, "message": "Record not found."}, status=status.HTTP_404_NOT_FOUND)

        vehicle = request.data.get('vehicle', item['vehicle'])
        store = request.data.get('store', item['store'])
        employee = request.data.get('employee', item['employee'])
        status_val = request.data.get('status', item['status'])
        selling_info = request.data.get('selling_info', item['selling_info'])

        try:
            inventoryserializer.update(pk, vehicle, store, employee, status_val, selling_info)
            updated_item = inventoryserializer.fetch_one(pk)
            return Response({
                "status": True,
                "message": "Inventory record updated successfully.",
                "data": updated_item
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        item = inventoryserializer.fetch_one(pk)
        if not item:
            return Response({"status": False, "message": "Record not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            inventoryserializer.delete(pk)
            return Response({
                "status": True,
                "message": "Inventory record deleted successfully."
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@login_required
def inventory_api_page_view(request):
    vehicles = VehicleInfo.objects.select_related('make').all()[:1000]
    stores = Store.objects.all()
    employees = Employee.objects.all()
    selling_infos = SellingInfo.objects.select_related('vehicle__make', 'customer').all()[:1000]
    
    context = {
        'active_parent': 'api_pages',
        'active_tab': 'api_inventory',
        'vehicles': vehicles,
        'stores': stores,
        'employees': employees,
        'selling_infos': selling_infos,
        'status_choices': Inventory.StatusChoices.choices,
    }
    return render(request, 'car_sales/api_inventory.html', context)





def generic_model_api(request, model_class, serializer_class, search_fields, pk=None, store_field=None, employee_field=None):
    if not request.user.is_authenticated:
        return Response(
            {"status": False, "message": "Authentication required."},
            status=status.HTTP_401_UNAUTHORIZED
        )
        
    is_staff = request.user.is_superuser or request.user.is_staff
    
    if request.method in ['POST', 'PUT', 'DELETE'] and not is_staff:
        return Response(
            {"status": False, "message": f"Permission denied. Only staff members can modify {model_class._meta.verbose_name} data."},
            status=status.HTTP_403_FORBIDDEN
        )

    if request.method == 'GET':
        if pk is not None:
            data = serializer_class.fetch_one(pk)
            if data:
                return Response({"status": True, "data": data}, status=status.HTTP_200_OK)
            return Response({"status": False, "message": "Record not found."}, status=status.HTTP_404_NOT_FOUND)
            
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 25))
        except ValueError:
            page = 1
            page_size = 25
            
        if page_size < 0:
            limit = None
            offset = 0
        else:
            limit = page_size
            offset = (page - 1) * page_size

        search = request.GET.get('search', '').strip()
        
        # Apply role-based hierarchy filters if applicable
        store_id = None
        employee_id = None
        if store_field or employee_field:
            profile = get_employee_profile(request)
            if profile and not request.user.is_superuser:
                role = profile.employee_role.role_name if profile.employee_role else ""
                if role not in ["Regional Sales Manager"]:
                    # Store-Level Roles: filter by store
                    if role in ["Branch Manager", "Showroom Manager", "Sales Manager", "Finance & Insurance Officer"]:
                        if store_field:
                            store_id = profile.store.store_id
                    # Employee-Level Roles: filter by themselves
                    else:
                        if employee_field:
                            employee_id = profile.employee_id
                        elif store_field:
                            store_id = profile.store.store_id
 
        # Filter by direct fields if present in GET parameters
        filters = {}
        for key, value in request.GET.items():
            if key in ['page', 'page_size', 'search']:
                continue
            try:
                model_class._meta.get_field(key)
                if value:
                    filters[key] = value
            except Exception:
                pass
 
        total, data = serializer_class.fetch(
            limit=limit,
            offset=offset,
            search=search,
            store_id=store_id,
            employee_id=employee_id,
            **filters
        )
        
        return Response({
            "status": True,
            "total": total,
            "page": page,
            "page_size": page_size,
            "data": data
        }, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        import inspect
        sig = inspect.signature(serializer_class.create)
        create_params = {}
        for param_name, param in sig.parameters.items():
            if param_name in request.data:
                create_params[param_name] = request.data[param_name]
            elif param.default is not inspect.Parameter.empty:
                create_params[param_name] = param.default
            else:
                create_params[param_name] = None
                
        try:
            new_id = serializer_class.create(**create_params)
            new_item = serializer_class.fetch_one(new_id)
            return Response({
                "status": True,
                "message": f"{model_class._meta.verbose_name.title()} record created successfully.",
                "data": new_item
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"status": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'PUT':
        item = serializer_class.fetch_one(pk)
        if not item:
            return Response({"status": False, "message": "Record not found."}, status=status.HTTP_404_NOT_FOUND)
            
        import inspect
        sig = inspect.signature(serializer_class.update)
        update_params = {}
        for param_name, param in sig.parameters.items():
            if param_name == 'pk' or param_name == f"{model_class._meta.pk.name}":
                continue
            if param_name in request.data:
                update_params[param_name] = request.data[param_name]
            else:
                update_params[param_name] = item.get(param_name)
                
        try:
            pk_param_name = list(sig.parameters.keys())[0]
            update_kwargs = {pk_param_name: pk}
            update_kwargs.update(update_params)
            
            serializer_class.update(**update_kwargs)
            updated_item = serializer_class.fetch_one(pk)
            return Response({
                "status": True,
                "message": f"{model_class._meta.verbose_name.title()} record updated successfully.",
                "data": updated_item
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        item = serializer_class.fetch_one(pk)
        if not item:
            return Response({"status": False, "message": "Record not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            serializer_class.delete(pk)
            return Response({
                "status": True,
                "message": f"{model_class._meta.verbose_name.title()} record deleted successfully."
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def country_api(request, pk=None):
    return generic_model_api(request, Country, CountrySerializer, ['country_name'], pk)


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def city_api(request, pk=None):
    return generic_model_api(request, City, CitySerializer, ['city_name', 'country__country_name'], pk)


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def store_api(request, pk=None):
    return generic_model_api(request, Store, StoreSerializer, ['store_name', 'store_code', 'city__city_name', 'address'], pk, 'self', None)


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def role_api(request, pk=None):
    return generic_model_api(request, EmployeeRole, EmployeeRoleSerializer, ['role_name'], pk)


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def status_api(request, pk=None):
    return generic_model_api(request, EmployeeStatus, EmployeeStatusSerializer, ['status'], pk)


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def industry_api(request, pk=None):
    return generic_model_api(request, IndustryInfo, IndustryInfoSerializer, ['make_name'], pk)


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def vehicle_api(request, pk=None):
    return generic_model_api(request, VehicleInfo, VehicleInfoSerializer, ['vehicle_model', 'make__make_name', 'vin', 'color'], pk)


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def customer_api(request, pk=None):
    return generic_model_api(request, CustomerInfo, CustomerInfoSerializer, ['firstname', 'lastname', 'customer_status', 'customer_address'], pk, 'sales__store', 'sales__employee')


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def sales_api(request, pk=None):
    if not request.user.is_authenticated:
        return Response({'status': False, 'message': 'Authentication required.'},
                        status=status.HTTP_401_UNAUTHORIZED)

    is_staff = request.user.is_superuser or request.user.is_staff

    if request.method in ['POST', 'PUT', 'DELETE'] and not is_staff:
        return Response(
            {'status': False, 'message': 'Permission denied. Only staff members can modify selling info data.'},
            status=status.HTTP_403_FORBIDDEN
        )

    if request.method == 'POST':
        # Extract fields
        import inspect
        sig = inspect.signature(SellingInfoSerializer.create)
        create_params = {}
        for param_name, param in sig.parameters.items():
            if param_name in request.data:
                create_params[param_name] = request.data[param_name]
            elif param.default is not inspect.Parameter.empty:
                create_params[param_name] = param.default
            else:
                create_params[param_name] = None

        try:
            new_sell_id = SellingInfoSerializer.create(**create_params)
            new_item = SellingInfoSerializer.fetch_one(new_sell_id)

            # ── Auto-create invoice for this new sale ──
            selling_date = new_item.get('selling_date') if new_item else None
            try:
                InvoiceSerializer.create(
                    sell_id=new_sell_id,
                    invoice_date=selling_date,
                    payment_status='Paid',
                    payment_method='Cash',
                    discount_amount=0,
                    notes=None,
                    due_date=None,
                )
            except Exception:
                pass  # Invoice creation failure should not block the sale

            return Response({
                'status': True,
                'message': 'Sale Info record created successfully.',
                'data': new_item,
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # Delegate all other methods to the generic handler
    return generic_model_api(request, SellingInfo, SellingInfoSerializer,
                             ['customer__firstname', 'customer__lastname',
                              'vehicle__vehicle_model', 'vehicle__make__make_name'],
                             pk, 'store', 'employee')



@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def budget_api(request, pk=None):
    return generic_model_api(request, EmployeeBudget, EmployeeBudgetSerializer, ['employee__first_name', 'employee__last_name', 'store__store_name', 'budget_year'], pk, 'store', 'employee')


@api_view(['GET'])
def budget_stats_api(request):
    """Lightweight endpoint: returns count, total_sum, and avg for a given budget_year."""
    if not request.user.is_authenticated:
        return Response({"status": False, "message": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)

    from django.db.models import Count, Sum, Avg
    year = request.GET.get('budget_year')
    qs = EmployeeBudget.objects.all()
    if year:
        qs = qs.filter(budget_year=year)

    agg = qs.aggregate(
        total_count=Count('id'),
        total_sum=Sum('budget_amount'),
        avg_amount=Avg('budget_amount')
    )

    return Response({
        "status": True,
        "total_count": agg['total_count'] or 0,
        "total_sum": float(agg['total_sum'] or 0),
        "avg_amount": float(agg['avg_amount'] or 0),
    }, status=status.HTTP_200_OK)


# --- API Endpoint implementing Supervisor's Stored-Procedure/Raw SQL approach ---

@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def employee_api(request, pk=None):
    return generic_model_api(request, Employee, EmployeeSerializer, ['first_name', 'last_name', 'employee_addr', 'employee_role__role_name', 'store__store_name'], pk, 'store', 'self')



def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    error_message = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('remember') == 'true'
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if not remember:
                request.session.set_expiry(0)
            messages.success(request, f"Welcome back, {user.username}!")
            next_url = request.GET.get('next') or 'home'
            return redirect(next_url)
        else:
            error_message = "Invalid username or password."
            messages.error(request, error_message)
            
    return render(request, 'car_sales/login.html', {'error_message': error_message})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    error_message = None
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        terms = request.POST.get('terms')
        
        if not terms:
            error_message = "You must agree to the terms and conditions."
        elif not name or not email or not username or not password:
            error_message = "All fields are required."
        elif User.objects.filter(username=username).exists():
            error_message = "Username already exists."
        elif User.objects.filter(email=email).exists():
            error_message = "Email already registered."
        else:
            first_name = ""
            last_name = ""
            if ' ' in name:
                first_name, last_name = name.split(' ', 1)
            else:
                first_name = name
                
            user = User.objects.create_user(
                username=username, 
                email=email, 
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            messages.success(request, f"Registration successful. Welcome, {user.username}!")
            return redirect('home')
            
        if error_message:
            messages.error(request, error_message)
            
    return render(request, 'car_sales/register.html', {'error_message': error_message})


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')



class EmployeeBackend(BaseBackend):
    """
    Custom Django authentication backend to authenticate users using their
    Employee ID and plain-text password from the employee table.
    """
    def _create_in_memory_user(self, employee, uid):
        role_name = employee.employee_role.role_name.lower() if employee.employee_role else ""
        is_manager = "manager" in role_name or "admin" in role_name
        
        user = User(
            id=uid,
            username=f"emp_{employee.employee_id}",
            first_name=employee.first_name,
            last_name=employee.last_name,
            is_staff=is_manager,
            is_superuser=False,
            is_active=True,
            password=employee.password
        )
        # Bypass DB operations to prevent writing to auth_user table
        user.save = types.MethodType(lambda self, *args, **kwargs: None, user)
        user.delete = types.MethodType(lambda self, *args, **kwargs: (0, {}), user)
        return user

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not str(username).isdigit():
            return None
            
        try:
            employee_id = int(username)
            employee = Employee.objects.select_related('status').filter(employee_id=employee_id).first()
        except (ValueError, TypeError):
            return None
            
        if employee and employee.status and employee.status.status == 'Terminated':
            return None
            
        if employee and employee.password == password:
            return self._create_in_memory_user(employee, -employee.employee_id)
            
        return None

    def get_user(self, user_id):
        try:
            uid = int(user_id)
        except (ValueError, TypeError):
            return None

        if uid < 0:
            employee_id = -uid
            try:
                employee = Employee.objects.select_related('employee_role', 'status', 'store').filter(employee_id=employee_id).first()
            except Exception:
                return None
            if not employee or (employee.status and employee.status.status == 'Terminated'):
                return None
                
            return self._create_in_memory_user(employee, uid)
            
        try:
            return User.objects.get(pk=uid)
        except User.DoesNotExist:
            return None


# ─────────────────────────────────────────────
# Invoice Views
# ─────────────────────────────────────────────

@login_required
def invoice_view(request):
    profile = get_employee_profile(request)
    stores = filter_by_hierarchy(Store.objects.all(), request, profile, 'self', None)
    context = {
        'active_tab': 'invoices',
        'stores': stores,
        'payment_status_choices': Invoice.PaymentStatusChoices.choices,
        'payment_method_choices': Invoice.PaymentMethodChoices.choices,
    }
    return render(request, 'car_sales/invoice_view.html', context)


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def invoice_api(request, pk=None):
    if not request.user.is_authenticated:
        return Response({'status': False, 'message': 'Authentication required.'},
                        status=status.HTTP_401_UNAUTHORIZED)

    is_staff = request.user.is_superuser or request.user.is_staff
    profile = get_employee_profile(request)

    if request.method in ['POST', 'PUT', 'DELETE'] and not is_staff:
        return Response({'status': False, 'message': 'Permission denied. Only staff members can modify invoice data.'},
                        status=status.HTTP_403_FORBIDDEN)

    # ── GET ──────────────────────────────────────
    if request.method == 'GET':
        # Fetch by sell_id convenience lookup
        sell_id_param = request.GET.get('sell_id')
        if sell_id_param:
            item = InvoiceSerializer.fetch_by_sell_id(sell_id_param)
            if item:
                return Response({'status': True, 'data': item}, status=status.HTTP_200_OK)
            return Response({'status': False, 'message': 'No invoice found for that sale.'},
                            status=status.HTTP_404_NOT_FOUND)

        if pk is not None:
            item = InvoiceSerializer.fetch_one(pk)
            if item:
                return Response({'status': True, 'data': item}, status=status.HTTP_200_OK)
            return Response({'status': False, 'message': 'Record not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            page      = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 25))
        except ValueError:
            page, page_size = 1, 25

        offset = (page - 1) * page_size
        search = request.GET.get('search', '').strip()

        store_id    = None
        employee_id = None
        if not request.user.is_superuser and profile and profile.employee_role:
            role = profile.employee_role.role_name
            if role in ['Branch Manager', 'Showroom Manager', 'Sales Manager', 'Finance & Insurance Officer']:
                store_id = profile.store.store_id
            elif role not in ['Regional Sales Manager', 'Customer Relations Officer']:
                employee_id = profile.employee_id

        # Optional filter by payment_status passed as query param
        filters = {}
        for key in ('payment_status', 'payment_method'):
            val = request.GET.get(key)
            if val:
                filters[key] = val

        total, data = InvoiceSerializer.fetch(
            limit=page_size, offset=offset, search=search,
            store_id=store_id, employee_id=employee_id, **filters
        )
        return Response({'status': True, 'total': total, 'page': page, 'page_size': page_size, 'data': data},
                        status=status.HTTP_200_OK)

    # ── POST (manual invoice creation) ──────────
    elif request.method == 'POST':
        sell_id        = request.data.get('sell_id')
        invoice_date   = request.data.get('invoice_date')
        due_date       = request.data.get('due_date') or None
        payment_status_val  = request.data.get('payment_status', 'Paid')
        payment_method_val  = request.data.get('payment_method', 'Cash')
        discount_amount = request.data.get('discount_amount', 0)
        notes           = request.data.get('notes') or None

        if not sell_id or not invoice_date:
            return Response({'status': False, 'message': 'sell_id and invoice_date are required.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Check no duplicate invoice for this sale
        existing = InvoiceSerializer.fetch_by_sell_id(sell_id)
        if existing:
            return Response({'status': False, 'message': f'An invoice (#{existing["invoice_id"]}) already exists for sale #{sell_id}.'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            new_id = InvoiceSerializer.create(
                sell_id=sell_id,
                invoice_date=invoice_date,
                due_date=due_date,
                payment_status=payment_status_val,
                payment_method=payment_method_val,
                discount_amount=discount_amount,
                notes=notes,
            )
            item = InvoiceSerializer.fetch_one(new_id)
            return Response({'status': True, 'message': 'Invoice created successfully.', 'data': item},
                            status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # ── PUT ──────────────────────────────────────
    elif request.method == 'PUT':
        item = InvoiceSerializer.fetch_one(pk)
        if not item:
            return Response({'status': False, 'message': 'Record not found.'}, status=status.HTTP_404_NOT_FOUND)

        invoice_date    = request.data.get('invoice_date',   item['invoice_date'])
        due_date        = request.data.get('due_date',        item.get('due_date')) or None
        payment_status_val  = request.data.get('payment_status',  item['payment_status'])
        payment_method_val  = request.data.get('payment_method',  item['payment_method'])
        discount_amount = request.data.get('discount_amount', item['discount_amount'])
        notes           = request.data.get('notes',           item.get('notes')) or None

        try:
            InvoiceSerializer.update(pk, invoice_date, due_date, payment_status_val,
                                     payment_method_val, discount_amount, notes)
            updated = InvoiceSerializer.fetch_one(pk)
            return Response({'status': True, 'message': 'Invoice updated successfully.', 'data': updated},
                            status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # ── DELETE ───────────────────────────────────
    elif request.method == 'DELETE':
        item = InvoiceSerializer.fetch_one(pk)
        if not item:
            return Response({'status': False, 'message': 'Record not found.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            InvoiceSerializer.delete(pk)
            return Response({'status': True, 'message': 'Invoice deleted successfully.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@login_required
def invoice_api_page_view(request):
    profile = get_employee_profile(request)
    stores = filter_by_hierarchy(Store.objects.all(), request, profile, 'self', None)
    sales = SellingInfo.objects.select_related('customer', 'vehicle__make').all()[:2000]
    context = {
        'active_tab': 'invoices',
        'stores': stores,
        'sales': sales,
        'payment_status_choices': Invoice.PaymentStatusChoices.choices,
        'payment_method_choices': Invoice.PaymentMethodChoices.choices,
    }
    return render(request, 'car_sales/invoice_view.html', context)


@login_required
def download_invoice_pdf(request, invoice_id):
    r = InvoiceSerializer.fetch_one(invoice_id)
    if not r:
        raise Http404("Invoice not found")

    is_staff = request.user.is_superuser or request.user.is_staff
    if not is_staff:
        profile = get_employee_profile(request)
        if profile and profile.employee_role:
            role = profile.employee_role.role_name
            if role in ['Branch Manager', 'Showroom Manager', 'Sales Manager', 'Finance & Insurance Officer']:
                if r.get('store_id') != profile.store.store_id:
                    return HttpResponse("Permission denied", status=403)
            elif role not in ['Regional Sales Manager', 'Customer Relations Officer']:
                if r.get('employee_id') != profile.employee_id:
                    return HttpResponse("Permission denied", status=403)

    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="INV_{invoice_id}.pdf"'

    doc = SimpleDocTemplate(
        response,
        pagesize=letter,
        rightMargin=45,
        leftMargin=45,
        topMargin=45,
        bottomMargin=45
    )
    story = []

    styles = getSampleStyleSheet()

    # Premium Brand Colors
    PRIMARY = colors.HexColor('#4F46E5')      # Royal Indigo
    TEXT_DARK = colors.HexColor('#1E293B')    # Slate 800
    TEXT_MUTED = colors.HexColor('#64748B')   # Slate 500
    BG_LIGHT = colors.HexColor('#F8FAFC')     # Slate 50
    BORDER_COLOR = colors.HexColor('#E2E8F0') # Slate 200

    title_style = ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=PRIMARY,
        spaceAfter=5
    )

    brand_style = ParagraphStyle(
        'BrandText',
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=TEXT_DARK
    )

    section_hdr_style = ParagraphStyle(
        'SectionHeader',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=13,
        textColor=TEXT_MUTED,
        spaceAfter=4
    )

    meta_val_style = ParagraphStyle(
        'MetaValue',
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=TEXT_DARK
    )

    meta_val_bold = ParagraphStyle(
        'MetaValueBold',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=13,
        textColor=TEXT_DARK
    )

    body_normal = ParagraphStyle(
        'BodyNormal',
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=TEXT_DARK
    )

    body_bold = ParagraphStyle(
        'BodyBold',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=13,
        textColor=TEXT_DARK
    )

    header_style = ParagraphStyle(
        'TableHeader',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=13,
        textColor=colors.white
    )

    # 1. Invoice Title & Metadata Header
    meta_content = (
        f"<b>Invoice #:</b> {r['invoice_id']}<br/>"
        f"<b>Date:</b> {r['invoice_date']}<br/>"
        f"<b>Status:</b> {r['payment_status'].upper()}<br/>"
        f"<b>Method:</b> {r['payment_method']}"
    )
    if r.get('due_date'):
        meta_content += f"<br/><b>Due Date:</b> {r['due_date']}"

    header_data = [
        [
            [Paragraph("CAR SALES INC.", brand_style), Paragraph("Premium Automotive Registry", meta_val_style)],
            [Paragraph("INVOICE", title_style), Paragraph(meta_content, meta_val_style)]
        ]
    ]
    header_table = Table(header_data, colWidths=[260, 260])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 15),
    ]))
    story.append(header_table)

    # Primary colored divider line
    line_table = Table([[""]], colWidths=[520], rowHeights=[2])
    line_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), PRIMARY),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(line_table)
    story.append(Spacer(1, 15))

    # 2. FROM / TO address columns
    address_data = [
        [Paragraph("FROM STORE", section_hdr_style), Paragraph("TO CUSTOMER", section_hdr_style)],
        [Paragraph(f"<b>{r['store_name']}</b><br/>{r['store_address'] or ''}", meta_val_style),
         Paragraph(f"<b>{r['customer_name']}</b><br/>{r['customer_address'] or ''}", meta_val_style)]
    ]
    address_table = Table(address_data, colWidths=[260, 260])
    address_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(address_table)
    story.append(Spacer(1, 10))

    # 3. Spec sheet for transaction details
    detail_headers = [
        Paragraph("VEHICLE MODEL", section_hdr_style),
        Paragraph("VIN / CHASSIS NUMBER", section_hdr_style),
        Paragraph("SALES AGENT", section_hdr_style)
    ]
    detail_vals = [
        Paragraph(r['vehicle_name'], meta_val_bold),
        Paragraph(r['vin'] or '—', meta_val_style),
        Paragraph(f"{r['employee_name']}<br/><font color='#64748B'>{r['employee_role'] or 'Staff'}</font>", meta_val_style)
    ]
    detail_table = Table([detail_headers, detail_vals], colWidths=[180, 180, 160])
    detail_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(detail_table)
    story.append(Spacer(1, 20))

    # 4. Item details and financial totals
    discount_detail = "No discount"
    if r['discount_amount'] > 0:
        discount_detail = f"-${int(r['discount_amount']):,} ({float(r['discount_pct'] or 0):.2f}% off MMR Price: ${int(r['mmr'] or 0):,})"

    fin_headers = [
        Paragraph("DESCRIPTION", header_style),
        Paragraph("REFERENCE DETAILS", header_style),
        Paragraph("AMOUNT", header_style)
    ]
    fin_rows = [
        fin_headers,
        [Paragraph("Vehicle Base Selling Price", body_bold), Paragraph(r['vehicle_name'], body_normal), Paragraph(f"${int(r['selling_price'] or 0):,}", body_normal)],
        [Paragraph("MMR Comparison Discount", body_bold), Paragraph(discount_detail, body_normal), Paragraph(f"-${int(r['discount_amount'] or 0):,}", body_normal)],
        [Paragraph("Total Amount Paid", body_bold), Paragraph(f"Payment Method: {r['payment_method']} | Status: {r['payment_status']}", body_bold), Paragraph(f"${int(r['final_amount'] or 0):,}", body_bold)]
    ]

    fin_table = Table(fin_rows, colWidths=[160, 240, 120])
    fin_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F172A')), # Dark slate header
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 10),

        ('LINEBELOW', (0,1), (-1,1), 0.5, BORDER_COLOR),
        ('LINEBELOW', (0,2), (-1,2), 0.5, BORDER_COLOR),

        ('TOPPADDING', (0,1), (-1,-1), 10),
        ('BOTTOMPADDING', (0,1), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),

        ('ALIGN', (2,0), (2,-1), 'RIGHT'),

        ('BACKGROUND', (0,3), (-1,3), colors.HexColor('#EEF2F6')), # Highlight row
        ('LINEBELOW', (0,3), (-1,3), 1.5, PRIMARY),
        ('TOPPADDING', (0,3), (-1,3), 12),
        ('BOTTOMPADDING', (0,3), (-1,3), 12),
    ]))
    story.append(fin_table)

    # Notes
    if r.get('notes'):
        story.append(Spacer(1, 20))
        story.append(Paragraph("NOTES / TERMS", section_hdr_style))
        story.append(Spacer(1, 4))
        story.append(Paragraph(r['notes'], body_normal))

    # 5. Clean footer thank you message
    story.append(Spacer(1, 40))
    footer_divider = Table([[""]], colWidths=[520], rowHeights=[0.5])
    footer_divider.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BORDER_COLOR),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(footer_divider)
    story.append(Spacer(1, 10))

    thank_you_style = ParagraphStyle(
        'ThankYouText',
        fontName='Helvetica-Oblique',
        fontSize=10,
        leading=14,
        textColor=TEXT_MUTED,
        alignment=1
    )
    story.append(Paragraph("Thank you for choosing Car Sales Inc. for your premium vehicle purchase!", thank_you_style))

    doc.build(story)
    return response



