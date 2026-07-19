from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.contrib.auth.backends import BaseBackend
from django.db import connections
import types

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from .models import *
from .serializers import *

# ─────────────────────────────────────────────
# Helper Functions for Role-Based Filtering
# ─────────────────────────────────────────────

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

from .utils import get_user_filters, is_manager as check_is_manager

def check_analytical_access_and_get_params(request):
    if not request.user.is_authenticated:
        return None, None, None, Response(
            {"status": False, "message": "Authentication required."},
            status=status.HTTP_401_UNAUTHORIZED
        )
    is_allowed = request.user.is_superuser or request.user.is_staff
    profile = get_employee_profile(request)
    if not is_allowed and profile:
        if check_is_manager(profile.employee_id):
            is_allowed = True
    if not is_allowed:
        return None, None, None, Response(
            {"status": False, "message": "Access Denied. Only administrators and store managers can fetch this API data."},
            status=status.HTTP_403_FORBIDDEN
        )
    dt_from = request.data.get('dt_from') if isinstance(request.data, dict) else None
    dt_to = request.data.get('dt_to') if isinstance(request.data, dict) else None
    if not dt_from:
        dt_from = request.GET.get('dt_from')
    if not dt_to:
        dt_to = request.GET.get('dt_to')
    if not dt_from or not dt_to:
        return None, None, None, Response(
            {"status": False, "message": "dt_from and dt_to parameters are required (YYYY-MM-DD)."},
            status=status.HTTP_400_BAD_REQUEST
        )
    store_id, employee_id = get_user_filters(request, profile)
    return dt_from, dt_to, (store_id, employee_id), None

def check_analytical_page_access(request):
    profile = get_employee_profile(request)
    is_allowed = request.user.is_superuser or request.user.is_staff
    if not is_allowed and profile:
        if check_is_manager(profile.employee_id):
            is_allowed = True
    return is_allowed


def render_analytical_page(request, template, active_tab):
    if not check_analytical_page_access(request):
        messages.error(request, "Permission denied. Only administrators and store managers can access this page.")
        return redirect('home')
    return render(request, template, {'active_parent': 'api_pages', 'active_tab': active_tab})

def check_record_permission(request, model_class, record):
    if not request.user.is_authenticated:
        return False
    if request.user.is_superuser:
        return True
    profile = get_employee_profile(request)
    store_id, employee_id = get_user_filters(request, profile)
    if store_id is None and employee_id is None:
        return True

    model_name = model_class.__name__

    if model_name == 'Store':
        r_store_id = record.get('store_id')
        if store_id is not None and r_store_id != store_id:
            return False

    elif model_name == 'Employee':
        r_employee_id = record.get('employee_id')
        r_store_id = record.get('store')
        if employee_id is not None:
            if isinstance(employee_id, (list, tuple, set)):
                if r_employee_id not in employee_id:
                    return False
            elif r_employee_id != employee_id:
                return False
        if store_id is not None and r_store_id != store_id:
            return False

    elif model_name == 'CustomerInfo':
        customer_id = record.get('customer_id')
        if employee_id is not None:
            has_sales = SellingInfo.objects.filter(customer_id=customer_id).exists()
            if has_sales:
                if isinstance(employee_id, (list, tuple, set)):
                    if not SellingInfo.objects.filter(customer_id=customer_id, employee_id__in=employee_id).exists():
                        return False
                elif not SellingInfo.objects.filter(customer_id=customer_id, employee_id=employee_id).exists():
                    return False
        elif store_id is not None:
            has_sales = SellingInfo.objects.filter(customer_id=customer_id).exists()
            if has_sales and not SellingInfo.objects.filter(customer_id=customer_id, store_id=store_id).exists():
                return False

    elif model_name == 'SellingInfo':
        r_employee_id = record.get('employee')
        r_store_id = record.get('store')
        if employee_id is not None:
            if isinstance(employee_id, (list, tuple, set)):
                if r_employee_id not in employee_id:
                    return False
            elif r_employee_id != employee_id:
                return False
        if store_id is not None and r_store_id != store_id:
            return False

    elif model_name == 'Invoice':
        r_employee_id = record.get('employee_id')
        r_store_id = record.get('store_id')
        if employee_id is not None:
            if isinstance(employee_id, (list, tuple, set)):
                if r_employee_id not in employee_id:
                    return False
            elif r_employee_id != employee_id:
                return False
        if store_id is not None and r_store_id != store_id:
            return False

    elif model_name == 'Inventory':
        r_store_id = record.get('store')
        if store_id is not None and r_store_id != store_id:
            return False

    elif model_name == 'EmployeeBudget':
        r_employee_id = record.get('employee')
        r_store_id = record.get('store')
        if employee_id is not None:
            if isinstance(employee_id, (list, tuple, set)):
                if r_employee_id not in employee_id:
                    return False
            elif r_employee_id != employee_id:
                return False
        if store_id is not None and r_store_id != store_id:
            return False

    return True

def check_crud_permission(request, model_class, action, pk=None, data=None):
    if not request.user.is_authenticated:
        return False, "Authentication required."

    if request.user.is_superuser:
        return True, None

    profile = get_employee_profile(request)
    is_manager = False
    if profile:
        is_manager = check_is_manager(profile.employee_id) or request.user.is_staff or request.user.is_superuser

    # Get user filters
    store_id, employee_id = get_user_filters(request, profile)

    model_name = model_class.__name__

    if action == 'GET':
        return True, None

    if action == 'DELETE':
        if not is_manager:
            return False, f"Permission denied. Only managers and administrators can delete {model_class._meta.verbose_name} data."
        return True, None

    if action in ['POST', 'PUT']:
        admin_models = ['Country', 'City', 'Store', 'EmployeeRole', 'EmployeeStatus', 'IndustryInfo', 'VehicleInfo', 'EmployeeBudget']
        if model_name in admin_models:
            if not is_manager:
                return False, f"Permission denied. Only managers and administrators can modify {model_class._meta.verbose_name} data."
            return True, None

        if model_name == 'Employee':
            if is_manager:
                if store_id is not None and data:
                    emp_store = data.get('store')
                    if emp_store and int(emp_store) != store_id:
                        return False, "Permission denied. You cannot modify/create an employee for a different store."
                return True, None
            # Regular employees can only modify their own profile
            if action == 'PUT' and pk is not None and profile and pk == profile.employee_id:
                if data:
                    if 'employee_role' in data and int(data['employee_role']) != profile.employee_role.role_id:
                        return False, "Permission denied. You cannot change your own employee role."
                    if 'status' in data and int(data['status']) != profile.status.status_id:
                        return False, "Permission denied. You cannot change your own employee status."
                    if 'store' in data and int(data['store']) != profile.store.store_id:
                        return False, "Permission denied. You cannot change your own store."
                return True, None
            return False, "Permission denied. You can only modify your own employee profile."

        if model_name == 'CustomerInfo':
            # Any authenticated user can create or update customer info
            return True, None

        if model_name == 'SellingInfo':
            if data:
                posted_employee = data.get('employee')
                posted_store = data.get('store')
                if employee_id is not None and posted_employee is not None:
                    if isinstance(employee_id, (list, tuple, set)):
                        if int(posted_employee) not in employee_id:
                            return False, "Permission denied. You can only record sales for yourself or your subordinates."
                    elif int(posted_employee) != employee_id:
                        return False, "Permission denied. You can only record sales for yourself."
                if store_id is not None and posted_store is not None and int(posted_store) != store_id:
                    return False, "Permission denied. You can only record sales for your store."
            return True, None

        if model_name == 'Invoice':
            if data:
                posted_employee = data.get('employee')
                posted_inventory = data.get('inventory_id')
                if posted_inventory:
                    inv_item = inventoryserializer.fetch_one(posted_inventory)
                    if not inv_item:
                        return False, "Invalid inventory item referenced."
                    if employee_id is not None and posted_employee is not None:
                        if isinstance(employee_id, (list, tuple, set)):
                            if int(posted_employee) not in employee_id:
                                return False, "Permission denied. You can only record sales for yourself or your subordinates."
                        elif int(posted_employee) != employee_id:
                            return False, "Permission denied. You can only record sales for yourself."
                    if store_id is not None and inv_item['store'] != store_id:
                        return False, "Permission denied. You can only sell vehicles from your assigned store."
            return True, None

        if model_name == 'Inventory':
            # Creating inventory is restricted to managers
            if action == 'POST':
                if not is_manager:
                    return False, "Permission denied. Only staff members can modify inventory data."
            # PUT is allowed for all, but checked in view
            return True, None

    return True, None

# ─────────────────────────────────────────────
# Standard Views
# ─────────────────────────────────────────────

@login_required
def home_view(request):
    profile = get_employee_profile(request)
    store_id, employee_id = get_user_filters(request, profile)
    stats = SellingInfoSerializer.fetch_dashboard_stats(store_id, employee_id)
    return render(request, 'car_sales/dashboard.html', {
        'active_tab': 'dashboard',
        **stats
    })

dashboard_view = home_view

def index_view(request):
    return render(request, 'car_sales/index.html')

@login_required
def employee_view(request):
    profile = get_employee_profile(request)
    store_id, _ = get_user_filters(request, profile)
    _, roles = EmployeeRoleSerializer.fetch(limit=-1)
    _, statuses = EmployeeStatusSerializer.fetch(limit=-1)
    _, stores = StoreSerializer.fetch(limit=-1, store_id=store_id)
    _, cities = CitySerializer.fetch(limit=-1)
    _, countries = CountrySerializer.fetch(limit=-1)
    return render(request, 'car_sales/employee_view.html', {
        'active_tab': 'employees',
        'roles': roles,
        'statuses': statuses,
        'stores': stores,
        'cities': cities,
        'countries': countries,
    })

@login_required
def country_view(request):
    return render(request, 'car_sales/country_view.html', {'active_tab': 'countries'})

@login_required
def city_view(request):
    _, countries = CountrySerializer.fetch(limit=-1)
    return render(request, 'car_sales/city_view.html', {
        'active_tab': 'cities',
        'countries': countries,
    })

@login_required
def store_view(request):
    _, cities = CitySerializer.fetch(limit=-1)
    _, countries = CountrySerializer.fetch(limit=-1)
    return render(request, 'car_sales/store_view.html', {
        'active_tab': 'stores',
        'cities': cities,
        'countries': countries,
    })

@login_required
def role_view(request):
    return render(request, 'car_sales/role_view.html', {'active_tab': 'roles'})

@login_required
def status_view(request):
    return render(request, 'car_sales/status_view.html', {'active_tab': 'statuses'})

@login_required
def industry_view(request):
    return render(request, 'car_sales/industry_view.html', {'active_tab': 'industry'})

@login_required
def vehicle_view(request):
    _, makes = IndustryInfoSerializer.fetch(limit=-1)
    return render(request, 'car_sales/vehicle_view.html', {
        'active_tab': 'vehicles',
        'makes': makes,
    })

@login_required
def customer_view(request):
    _, cities = CitySerializer.fetch(limit=-1)
    _, countries = CountrySerializer.fetch(limit=-1)
    return render(request, 'car_sales/customer_view.html', {
        'active_tab': 'customers',
        'cities': cities,
        'countries': countries,
    })

@login_required
def selling_view(request):
    profile = get_employee_profile(request)
    store_id, employee_id = get_user_filters(request, profile)
    _, employees = EmployeeSerializer.fetch(limit=-1, store_id=store_id, employee_id=employee_id)
    _, stores = StoreSerializer.fetch(limit=-1, store_id=store_id)
    return render(request, 'car_sales/selling_view.html', {
        'active_tab': 'sales',
        'employees': employees,
        'stores': stores,
    })

@login_required
def budget_view(request):
    profile = get_employee_profile(request)
    store_id, employee_id = get_user_filters(request, profile)
    _, employees = EmployeeSerializer.fetch(limit=-1, store_id=store_id, employee_id=employee_id)
    _, stores = StoreSerializer.fetch(limit=-1, store_id=store_id)
    years = EmployeeBudgetSerializer.get_distinct_years()
    import datetime
    current_year = datetime.date.today().year
    if current_year not in years:
        years.insert(0, current_year)
    return render(request, 'car_sales/budget_view.html', {
        'active_tab': 'budgets',
        'employees': employees,
        'stores': stores,
        'years': years,
        'current_year': current_year,
    })

@staff_member_required(login_url='login')
def admin_panel_view(request):
    if not request.user.is_superuser:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    stats = {
        'countries': {'name': 'Countries', 'count': CountrySerializer.fetch(limit=0)[0], 'url': '/countries/', 'slug': 'country'},
        'cities': {'name': 'Cities', 'count': CitySerializer.fetch(limit=0)[0], 'url': '/cities/', 'slug': 'city'},
        'stores': {'name': 'Stores', 'count': StoreSerializer.fetch(limit=0)[0], 'url': '/stores/', 'slug': 'store'},
        'roles': {'name': 'Employee Roles', 'count': EmployeeRoleSerializer.fetch(limit=0)[0], 'url': '/emproles/', 'slug': 'employeerole'},
        'statuses': {'name': 'Employee Statuses', 'count': EmployeeStatusSerializer.fetch(limit=0)[0], 'url': '/statuses/', 'slug': 'employeestatus'},
        'employees': {'name': 'Employees', 'count': EmployeeSerializer.fetch(limit=0)[0], 'url': '/employees/', 'slug': 'employee'},
        'industry': {'name': 'Vehicle Makes', 'count': IndustryInfoSerializer.fetch(limit=0)[0], 'url': '/industry/', 'slug': 'industryinfo'},
        'vehicles': {'name': 'Vehicles', 'count': VehicleInfoSerializer.fetch(limit=0)[0], 'url': '/vehicles/', 'slug': 'vehicleinfo'},
        'customers': {'name': 'Customers', 'count': CustomerInfoSerializer.fetch(limit=0)[0], 'url': '/customers/', 'slug': 'customerinfo'},
        'sales': {'name': 'Sales Transactions', 'count': SellingInfoSerializer.fetch(limit=0)[0], 'url': '/sales/', 'slug': 'sellinginfo'},
        'budgets': {'name': 'Employee Budget', 'count': EmployeeBudgetSerializer.fetch(limit=0)[0], 'url': '/budgets/', 'slug': 'employeebudget'},
        'invoices': {'name': 'Invoices', 'count': InvoiceSerializer.fetch(limit=0)[0], 'url': '/invoices/', 'slug': 'invoice'},
    }
    return render(request, 'car_sales/admin_panel.html', {
        'active_tab': 'admin_panel',
        'stats': stats,
    })

# ─────────────────────────────────────────────
# Analytical API Views
# ─────────────────────────────────────────────

@api_view(['GET', 'POST'])
def employee_sales_api(request):
    res = check_analytical_access_and_get_params(request)
    if isinstance(res[-1], Response):
        return res[-1]
    dt_from, dt_to, (store_id, employee_id), _ = res
    try:
        data = employeesalesserializers.fetch(dt_from, dt_to, store_id=store_id, employee_id=employee_id)
        return Response({"status": True, "data": data}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET', 'POST'])
def store_sales_api(request):
    res = check_analytical_access_and_get_params(request)
    if isinstance(res[-1], Response):
        return res[-1]
    dt_from, dt_to, (store_id, employee_id), _ = res
    try:
        data = storesalesserializer.fetch(dt_from, dt_to, store_id=store_id, employee_id=employee_id)
        return Response({"status": True, "data": data}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@login_required
def employee_sales_page_view(request):
    return render_analytical_page(request, 'car_sales/api_employee_sales.html', 'api_employee_sales')

@login_required
def store_sales_page_view(request):
    return render_analytical_page(request, 'car_sales/api_store_sales.html', 'api_store_sales')

@api_view(['GET', 'POST'])
def store_vehicle_sales_api(request):
    res = check_analytical_access_and_get_params(request)
    if isinstance(res[-1], Response):
        return res[-1]
    dt_from, dt_to, (store_id, employee_id), _ = res
    try:
        data = storevehiclesalesserializer.fetch(dt_from, dt_to, store_id=store_id, employee_id=employee_id)
        return Response({"status": True, "data": data}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@login_required
def store_vehicle_sales_page_view(request):
    return render_analytical_page(request, 'car_sales/api_store_vehicle_sales.html', 'api_store_vehicle_sales')

@api_view(['GET', 'POST'])
def customer_vehicle_sales_api(request):
    res = check_analytical_access_and_get_params(request)
    if isinstance(res[-1], Response):
        return res[-1]
    dt_from, dt_to, (store_id, employee_id), _ = res
    try:
        data = customervehiclesalesserializer.fetch(dt_from, dt_to, store_id=store_id, employee_id=employee_id)
        return Response({"status": True, "data": data}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@login_required
def customer_vehicle_sales_page_view(request):
    return render_analytical_page(request, 'car_sales/api_customer_vehicle_sales.html', 'api_customer_vehicle_sales')

@api_view(['GET', 'POST'])
def customer_store_spending_api(request):
    res = check_analytical_access_and_get_params(request)
    if isinstance(res[-1], Response):
        return res[-1]
    dt_from, dt_to, (store_id, employee_id), _ = res
    try:
        data = customerstorespendingserializer.fetch(dt_from, dt_to, store_id=store_id, employee_id=employee_id)
        return Response({"status": True, "data": data}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@login_required
def customer_store_spending_page_view(request):
    return render_analytical_page(request, 'car_sales/api_customer_store_spending.html', 'api_customer_store_spending')

@api_view(['GET', 'POST'])
def budget_vs_sales_api(request):
    res = check_analytical_access_and_get_params(request)
    if isinstance(res[-1], Response):
        return res[-1]
    dt_from, dt_to, _, _ = res
    try:
        data = budgetvssalesserializer.fetch(dt_from, dt_to)
        return Response({"status": True, "data": data}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@login_required
def budget_vs_sales_page_view(request):
    return render_analytical_page(request, 'car_sales/api_budget_vs_sales.html', 'api_budget_vs_sales')

@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def inventory_api(request, pk=None):
    if not request.user.is_authenticated:
        return Response({"status": False, "message": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)
    
    action_map = {'GET': 'GET', 'POST': 'POST', 'PUT': 'PUT', 'DELETE': 'DELETE'}
    action = action_map.get(request.method)
    
    is_allowed, err_msg = check_crud_permission(request, Inventory, action, pk, request.data if request.method in ['POST', 'PUT'] else None)
    if not is_allowed:
        return Response({"status": False, "message": err_msg}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        if pk is not None:
            item = inventoryserializer.fetch_one(pk)
            if item:
                if not check_record_permission(request, Inventory, item):
                    return Response({"status": False, "message": "Permission denied. You do not have access to this record."}, status=status.HTTP_403_FORBIDDEN)
                return Response({"status": True, "data": item}, status=status.HTTP_200_OK)
            return Response({"status": False, "message": "Record not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 25))
        except ValueError:
            page, page_size = 1, 25
        offset = (page - 1) * page_size
        search = request.GET.get('search', '').strip()
        profile = get_employee_profile(request)
        store_id, employee_id = get_user_filters(request, profile)
        total, data = inventoryserializer.fetch(limit=page_size, offset=offset, search=search, store_id=store_id, employee_id=employee_id)
        return Response({"status": True, "total": total, "page": page, "page_size": page_size, "data": data}, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        try:
            new_item = inventoryserializer.create_from_request(request.data)
            return Response({"status": True, "message": "Inventory record created successfully.", "data": new_item}, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"status": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"status": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'PUT':
        item = inventoryserializer.fetch_one(pk)
        if not item:
            return Response({"status": False, "message": "Record not found."}, status=status.HTTP_404_NOT_FOUND)
        if not check_record_permission(request, Inventory, item):
            return Response({"status": False, "message": "Permission denied. You do not have access to modify this record."}, status=status.HTTP_403_FORBIDDEN)
        try:
            updated_item = inventoryserializer.update_from_request(pk, request.data)
            if not updated_item:
                return Response({"status": False, "message": "Record not found."}, status=status.HTTP_404_NOT_FOUND)
            return Response({"status": True, "message": "Inventory record updated successfully.", "data": updated_item}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        item = inventoryserializer.fetch_one(pk)
        if not item:
            return Response({"status": False, "message": "Record not found."}, status=status.HTTP_404_NOT_FOUND)
        if not check_record_permission(request, Inventory, item):
            return Response({"status": False, "message": "Permission denied. You do not have access to delete this record."}, status=status.HTTP_403_FORBIDDEN)
        try:
            success = inventoryserializer.delete_by_id(pk)
            if not success:
                return Response({"status": False, "message": "Record not found."}, status=status.HTTP_404_NOT_FOUND)
            return Response({"status": True, "message": "Inventory record deleted successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@login_required
def inventory_api_page_view(request):
    _, vehicles = VehicleInfoSerializer.fetch(limit=1000)
    _, stores = StoreSerializer.fetch(limit=-1)
    _, employees = EmployeeSerializer.fetch(limit=-1)
    _, selling_infos = SellingInfoSerializer.fetch(limit=1000)
    return render(request, 'car_sales/api_inventory.html', {
        'active_parent': 'api_pages',
        'active_tab': 'api_inventory',
        'vehicles': vehicles,
        'stores': stores,
        'employees': employees,
        'selling_infos': selling_infos,
        'status_choices': Inventory.StatusChoices.choices,
    })

# ─────────────────────────────────────────────
# Generic REST API Handler & Model Handlers
# ─────────────────────────────────────────────

def generic_model_api(request, model_class, serializer_class, search_fields, pk=None, store_field=None, employee_field=None):
    action_map = {'GET': 'GET', 'POST': 'POST', 'PUT': 'PUT', 'DELETE': 'DELETE'}
    action = action_map.get(request.method)

    is_allowed, err_msg = check_crud_permission(request, model_class, action, pk, request.data if request.method in ['POST', 'PUT'] else None)
    if not is_allowed:
        return Response({"status": False, "message": err_msg}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        if pk is not None:
            data = serializer_class.fetch_one(pk)
            if data:
                if not check_record_permission(request, model_class, data):
                    return Response({"status": False, "message": "Permission denied. You do not have access to this record."}, status=status.HTTP_403_FORBIDDEN)
                return Response({"status": True, "data": data}, status=status.HTTP_200_OK)
            return Response({"status": False, "message": "Record not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 25))
        except ValueError:
            page, page_size = 1, 25
        limit = None if page_size < 0 else page_size
        offset = 0 if page_size < 0 else (page - 1) * page_size
        search = request.GET.get('search', '').strip()
        store_id, employee_id = None, None
        if store_field or employee_field:
            profile = get_employee_profile(request)
            if profile and not request.user.is_superuser:
                role = profile.employee_role.role_name if profile.employee_role else ""
                if role not in ["Regional Sales Manager", "Customer Relations Officer"]:
                    if role in ["Branch Manager", "Showroom Manager", "Sales Manager", "Finance & Insurance Officer"]:
                        if store_field:
                            store_id = profile.store.store_id
                    else:
                        if employee_field:
                            employee_id = profile.employee_id
                        elif store_field:
                            store_id = profile.store.store_id
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
        total, data = serializer_class.fetch(limit=limit, offset=offset, search=search, store_id=store_id, employee_id=employee_id, **filters)
        return Response({"status": True, "total": total, "page": page, "page_size": page_size, "data": data}, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        import inspect
        sig = inspect.signature(serializer_class.create)
        create_params = {p: request.data[p] for p in sig.parameters if p in request.data}
        for p, param in sig.parameters.items():
            if p not in create_params:
                create_params[p] = param.default if param.default is not inspect.Parameter.empty else None
        try:
            new_id = serializer_class.create(**create_params)
            new_item = serializer_class.fetch_one(new_id)
            return Response({"status": True, "message": f"{model_class._meta.verbose_name.title()} record created successfully.", "data": new_item}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"status": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'PUT':
        item = serializer_class.fetch_one(pk)
        if not item:
            return Response({"status": False, "message": "Record not found."}, status=status.HTTP_404_NOT_FOUND)
        if not check_record_permission(request, model_class, item):
            return Response({"status": False, "message": "Permission denied. You do not have access to modify this record."}, status=status.HTTP_403_FORBIDDEN)
        import inspect
        sig = inspect.signature(serializer_class.update)
        pk_param_name = list(sig.parameters.keys())[0]
        update_params = {}
        for p in sig.parameters:
            if p in (pk_param_name, model_class._meta.pk.name):
                continue
            update_params[p] = request.data.get(p, item.get(p))
        try:
            update_kwargs = {pk_param_name: pk}
            update_kwargs.update(update_params)
            serializer_class.update(**update_kwargs)
            updated_item = serializer_class.fetch_one(pk)
            return Response({"status": True, "message": f"{model_class._meta.verbose_name.title()} record updated successfully.", "data": updated_item}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        item = serializer_class.fetch_one(pk)
        if not item:
            return Response({"status": False, "message": "Record not found."}, status=status.HTTP_404_NOT_FOUND)
        if not check_record_permission(request, model_class, item):
            return Response({"status": False, "message": "Permission denied. You do not have access to delete this record."}, status=status.HTTP_403_FORBIDDEN)
        try:
            serializer_class.delete(pk)
            return Response({"status": True, "message": f"{model_class._meta.verbose_name.title()} record deleted successfully."}, status=status.HTTP_200_OK)
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
        return Response({'status': False, 'message': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)
    action_map = {'GET': 'GET', 'POST': 'POST', 'PUT': 'PUT', 'DELETE': 'DELETE'}
    action = action_map.get(request.method)
    is_allowed, err_msg = check_crud_permission(request, SellingInfo, action, pk, request.data if request.method in ['POST', 'PUT'] else None)
    if not is_allowed:
        return Response({"status": False, "message": err_msg}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'POST':
        import inspect
        sig = inspect.signature(SellingInfoSerializer.create)
        create_params = {p: request.data[p] for p in sig.parameters if p in request.data}
        for p, param in sig.parameters.items():
            if p not in create_params:
                create_params[p] = param.default if param.default is not inspect.Parameter.empty else None
        try:
            new_sell_id = SellingInfoSerializer.create(**create_params)
            new_item = SellingInfoSerializer.fetch_one(new_sell_id)
            selling_date = new_item.get('selling_date') if new_item else None
            try:
                InvoiceSerializer.create(sell_id=new_sell_id, invoice_date=selling_date, payment_status='Paid', payment_method='Cash', discount_amount=0, notes=None, due_date=None)
            except Exception:
                pass
            return Response({'status': True, 'message': 'Sale Info record created successfully.', 'data': new_item}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    return generic_model_api(request, SellingInfo, SellingInfoSerializer, ['customer__firstname', 'customer__lastname', 'vehicle__vehicle_model', 'vehicle__make__make_name'], pk, 'store', 'employee')

@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def budget_api(request, pk=None):
    return generic_model_api(request, EmployeeBudget, EmployeeBudgetSerializer, ['employee__first_name', 'employee__last_name', 'store__store_name', 'budget_year'], pk, 'store', 'employee')

@api_view(['GET'])
def budget_stats_api(request):
    if not request.user.is_authenticated:
        return Response({"status": False, "message": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)
    year = request.GET.get('budget_year')
    stats_data = EmployeeBudgetSerializer.fetch_stats(year)
    return Response({"status": True, **stats_data}, status=status.HTTP_200_OK)

@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def employee_api(request, pk=None):
    return generic_model_api(request, Employee, EmployeeSerializer, ['first_name', 'last_name', 'employee_addr', 'employee_role__role_name', 'store__store_name'], pk, 'store', 'self')

# ─────────────────────────────────────────────
# Authentication Views
# ─────────────────────────────────────────────

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
            return redirect(request.GET.get('next') or 'home')
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
            first_name, last_name = name.split(' ', 1) if ' ' in name else (name, '')
            user = User.objects.create_user(username=username, email=email, password=password, first_name=first_name, last_name=last_name)
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
    def _create_in_memory_user(self, employee, uid):
        is_manager_user = check_is_manager(employee.employee_id)
        user = User(id=uid, username=f"emp_{employee.employee_id}", first_name=employee.first_name, last_name=employee.last_name, is_staff=is_manager_user, is_superuser=False, is_active=True, password=employee.password)
        user.save = types.MethodType(lambda self, *args, **kwargs: None, user)
        user.delete = types.MethodType(lambda self, *args, **kwargs: (0, {}), user)
        return user

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not str(username).isdigit():
            return None
        try:
            employee = Employee.objects.select_related('status').filter(employee_id=int(username)).first()
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
            employee = Employee.objects.select_related('employee_role', 'status', 'store').filter(employee_id=-uid).first()
            if not employee or (employee.status and employee.status.status == 'Terminated'):
                return None
            return self._create_in_memory_user(employee, uid)
        try:
            return User.objects.get(pk=uid)
        except User.DoesNotExist:
            return None

# ─────────────────────────────────────────────
# Invoice & PDF Views
# ─────────────────────────────────────────────

@login_required
def invoice_view(request):
    profile = get_employee_profile(request)
    store_id, employee_id = get_user_filters(request, profile)
    _, stores = StoreSerializer.fetch(limit=-1, store_id=store_id)
    _, employees = EmployeeSerializer.fetch(limit=-1, store_id=store_id, employee_id=employee_id)
    _, cities = CitySerializer.fetch(limit=-1)
    _, countries = CountrySerializer.fetch(limit=-1)
    return render(request, 'car_sales/invoice_view.html', {
        'active_tab': 'invoices',
        'stores': stores,
        'employees': employees,
        'cities': cities,
        'countries': countries,
        'payment_status_choices': Invoice.PaymentStatusChoices.choices,
        'payment_method_choices': Invoice.PaymentMethodChoices.choices,
        'current_employee_id': profile.employee_id if profile else None,
    })

invoice_api_page_view = invoice_view

@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def invoice_api(request, pk=None):
    if not request.user.is_authenticated:
        return Response({'status': False, 'message': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)
    
    action_map = {'GET': 'GET', 'POST': 'POST', 'PUT': 'PUT', 'DELETE': 'DELETE'}
    action = action_map.get(request.method)
    
    is_allowed, err_msg = check_crud_permission(request, Invoice, action, pk, request.data if request.method in ['POST', 'PUT'] else None)
    if not is_allowed:
        return Response({"status": False, "message": err_msg}, status=status.HTTP_403_FORBIDDEN)

    profile = get_employee_profile(request)

    if request.method == 'GET':
        sell_id_param = request.GET.get('sell_id')
        if sell_id_param:
            item = InvoiceSerializer.fetch_by_sell_id(sell_id_param)
            if item:
                # Need to fetch the full invoice to verify permission
                full_item = InvoiceSerializer.fetch_one(item.get('invoice_id'))
                if full_item and not check_record_permission(request, Invoice, full_item):
                    return Response({"status": False, "message": "Permission denied. You do not have access to this record."}, status=status.HTTP_403_FORBIDDEN)
                return Response({'status': True, 'data': item}, status=status.HTTP_200_OK)
            return Response({'status': False, 'message': 'No invoice found for that sale.'}, status=status.HTTP_404_NOT_FOUND)
        if pk is not None:
            item = InvoiceSerializer.fetch_one(pk)
            if item:
                if not check_record_permission(request, Invoice, item):
                    return Response({"status": False, "message": "Permission denied. You do not have access to this record."}, status=status.HTTP_403_FORBIDDEN)
                return Response({'status': True, 'data': item}, status=status.HTTP_200_OK)
            return Response({'status': False, 'message': 'Record not found.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            page, page_size = int(request.GET.get('page', 1)), int(request.GET.get('page_size', 25))
        except ValueError:
            page, page_size = 1, 25
        offset = (page - 1) * page_size
        search = request.GET.get('search', '').strip()
        store_id, employee_id = get_user_filters(request, profile)
        filters = {k: request.GET.get(k) for k in ('payment_status', 'payment_method') if request.GET.get(k)}
        total, data = InvoiceSerializer.fetch(limit=page_size, offset=offset, search=search, store_id=store_id, employee_id=employee_id, **filters)
        return Response({'status': True, 'total': total, 'page': page, 'page_size': page_size, 'data': data}, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        try:
            item = InvoiceSerializer.create_from_request(request.data)
            return Response({'status': True, 'message': 'Invoice created successfully.', 'data': item}, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'PUT':
        item = InvoiceSerializer.fetch_one(pk)
        if not item:
            return Response({"status": False, "message": "Record not found."}, status=status.HTTP_404_NOT_FOUND)
        if not check_record_permission(request, Invoice, item):
            return Response({"status": False, "message": "Permission denied. You do not have access to modify this record."}, status=status.HTTP_403_FORBIDDEN)
        try:
            updated = InvoiceSerializer.update_from_request(pk, request.data)
            if not updated:
                return Response({'status': False, 'message': 'Record not found.'}, status=status.HTTP_404_NOT_FOUND)
            return Response({'status': True, 'message': 'Invoice updated successfully.', 'data': updated}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        item = InvoiceSerializer.fetch_one(pk)
        if not item:
            return Response({"status": False, "message": "Record not found."}, status=status.HTTP_404_NOT_FOUND)
        if not check_record_permission(request, Invoice, item):
            return Response({"status": False, "message": "Permission denied. You do not have access to delete this record."}, status=status.HTTP_403_FORBIDDEN)
        try:
            success = InvoiceSerializer.delete_by_id(pk)
            if not success:
                return Response({'status': False, 'message': 'Record not found.'}, status=status.HTTP_404_NOT_FOUND)
            return Response({'status': True, 'message': 'Invoice deleted successfully.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@login_required
def documentation_view(request):
    if not request.user.is_superuser:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    base_url = request.build_absolute_uri('/')[:-1]
    return render(request, 'car_sales/documentation.html', {
        'active_tab': 'documentation',
        'base_url': base_url,
    })