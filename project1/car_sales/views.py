from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import connections
from django.db.models import Count
from django.db.models import Count

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

from .auth import get_employee_profile

from .utils import get_user_filters, is_manager as check_is_manager, get_employee_level as _get_employee_level, can_delete
from project1.workspaces import is_car_sales_admin_user, is_car_sales_workspace_user


from .permissions import LEVEL_CRUD_DISPATCH, LEVEL_RECORD_DISPATCH


def _in_scope(value, allowed):
    """Return whether a scalar database value is included in an access filter."""
    if allowed is None:
        return True
    if isinstance(allowed, (list, tuple, set)):
        return value in allowed
    return value == allowed


def is_staff_user(request):
    """Check if request user is an Employee/Staff member or Superuser."""
    if not request.user.is_authenticated:
        return False
    if is_car_sales_workspace_user(request.user):
        return True
    profile = get_employee_profile(request)
    return profile is not None


def _has_scoped_access(request, store_id=None, employee_id=None):
    """Single source of truth for showroom/country and own-record checks."""
    return is_staff_user(request)


def _payload_is_in_scope(request, model_name, data):
    """Prevent a valid user from submitting another showroom's IDs in a write."""
    return is_staff_user(request)


def check_analytical_access_and_get_params(request):
    if not request.user.is_authenticated:
        return None, None, None, Response(
            {"status": False, "message": "Authentication required."},
            status=status.HTTP_401_UNAUTHORIZED
        )
    if not is_staff_user(request):
        return None, None, None, Response(
            {"status": False, "message": "Access Denied. Only staff members and store administrators can fetch this API data."},
            status=status.HTTP_403_FORBIDDEN
        )
    profile = get_employee_profile(request)
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
    return is_staff_user(request)


def render_analytical_page(request, template, active_tab):
    if not check_analytical_page_access(request):
        messages.error(request, "Permission denied. Only administrators and store managers can access this page.")
        return redirect('home')
    return render(request, template, {'active_parent': 'api_pages', 'active_tab': active_tab})

def check_record_permission(request, model_class, record):
    """Row-level visibility check — dispatches to dedicated level handler in permissions.py."""
    if not request.user.is_authenticated:
        return False
    if is_car_sales_admin_user(request.user):
        return True

    profile = get_employee_profile(request)
    if not profile:
        return False

    model_name = model_class.__name__
    level = _get_employee_level(profile.employee_id)
    if not level:
        return True

    handler = LEVEL_RECORD_DISPATCH.get(level)
    if handler:
        return handler(model_name, record, profile)
    return True


def check_crud_permission(request, model_class, action, pk=None, data=None):
    """Action-level permission check — dispatches to dedicated level handler in permissions.py."""
    if not request.user.is_authenticated:
        return False, "Authentication required."

    if is_car_sales_admin_user(request.user):
        return True, None

    if not is_staff_user(request):
        return False, "Permission denied. This action is restricted to the car sales workspace."

    if action == 'GET':
        return True, None

    profile = get_employee_profile(request)
    if not profile:
        return False, "Profile not found."

    level = _get_employee_level(profile.employee_id)
    model_name = model_class.__name__

    from .permissions import check_level_5_8_crud_permission
    handler = LEVEL_CRUD_DISPATCH.get(level, check_level_5_8_crud_permission)
    return handler(model_name, action, data)


# ─────────────────────────────────────────────
# Standard Views
# ─────────────────────────────────────────────

@login_required
def home_view(request):
    if not is_staff_user(request):
        messages.error(request, "Permission denied. Only staff members and store administrators can access the dealership dashboard.")
        return redirect('home')
    profile = get_employee_profile(request)
    store_id, employee_id = get_user_filters(request, profile)
    stats = SellingInfoSerializer.fetch_dashboard_stats(store_id, employee_id)
    return render(request, 'car_sales/dashboard.html', {
        'active_tab': 'dashboard',
        **stats
    })

dashboard_view = home_view

def index_view(request):
    inventory_count = Inventory.objects.count()
    available_inventory_count = Inventory.objects.filter(
        status__in=[Inventory.StatusChoices.AVAILABLE, Inventory.StatusChoices.PRE_ORDER]
    ).count()
    sold_inventory_count = Inventory.objects.filter(
        status=Inventory.StatusChoices.SOLD
    ).count()
    store_count = Store.objects.count()
    customer_count = Customer.objects.count()
    makes = IndustryInfo.objects.all().order_by('make_name')[:12]
    brand_showcase = []
    brand_rows = (
        Inventory.objects.filter(
            status__in=[Inventory.StatusChoices.AVAILABLE, Inventory.StatusChoices.PRE_ORDER],
            vehicle__make__isnull=False,
        )
        .values('vehicle__make__make_name')
        .annotate(vehicle_count=Count('inventory_id'))
        .order_by('-vehicle_count', 'vehicle__make__make_name')[:12]
    )
    for row in brand_rows:
        make_name = row['vehicle__make__make_name']
        slug = ''.join(ch for ch in make_name.lower() if ch.isalnum())
        if 'mercedes' in slug:
            slug = 'mercedes'
        elif 'landrover' in slug:
            slug = 'landrover'
        brand_showcase.append({
            'make_name': make_name,
            'vehicle_count': row['vehicle_count'],
            'logo_url': f"/static/logos/{slug}.png",
        })
    stores = Store.objects.select_related('city', 'country').all().order_by('store_name')[:15]
    
    # Query top available vehicles from inventory database
    featured_inventory = Inventory.objects.select_related(
        'vehicle__make', 'store', 'store__city'
    ).filter(
        status__in=[Inventory.StatusChoices.AVAILABLE, Inventory.StatusChoices.PRE_ORDER]
    ).order_by('-inventory_id')[:8]

    # Fetch dynamic vehicle body categories and condition tabs from DB via ecommerce serializers
    try:
        from ecommerce.serializers import VehicleBodyService, VehicleConditionService
        vehicle_bodies = VehicleBodyService.fetch_vehicle_bodies()
        condition_tabs = VehicleConditionService.fetch_condition_tabs(active_condition=request.GET.get('condition', 'all'))
    except Exception:
        vehicle_bodies = []
        condition_tabs = []

    return render(request, 'car_sales/index.html', {
        'inventory_count': inventory_count,
        'available_inventory_count': available_inventory_count,
        'sold_inventory_count': sold_inventory_count,
        'store_count': store_count,
        'customer_count': customer_count,
        'makes': makes,
        'brand_showcase': brand_showcase,
        'stores': stores,
        'featured_inventory': featured_inventory,
        'vehicle_bodies': vehicle_bodies,
        'condition_tabs': condition_tabs,
    })

@login_required
def employee_view(request):
    profile = get_employee_profile(request)
    is_admin = is_car_sales_admin_user(request.user)
    is_manager = check_is_manager(profile.employee_id) if profile else False
    if not (is_admin or is_manager):
        return HttpResponseForbidden("Permission denied. Only managers and administrators can access this page.")
        
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
    is_admin = is_car_sales_admin_user(request.user)
    if not is_admin:
        return HttpResponseForbidden("Permission denied. Only administrators can access this page.")
    return render(request, 'car_sales/country_view.html', {'active_tab': 'countries'})

@login_required
def city_view(request):
    is_admin = is_car_sales_admin_user(request.user)
    if not is_admin:
        return HttpResponseForbidden("Permission denied. Only administrators can access this page.")
    _, countries = CountrySerializer.fetch(limit=-1)
    return render(request, 'car_sales/city_view.html', {
        'active_tab': 'cities',
        'countries': countries,
    })

@login_required
def store_view(request):
    profile = get_employee_profile(request)
    is_admin = is_car_sales_admin_user(request.user)
    is_manager = check_is_manager(profile.employee_id) if profile else False
    if not (is_admin or is_manager):
        return HttpResponseForbidden("Permission denied. Only managers and administrators can access this page.")
    _, cities = CitySerializer.fetch(limit=-1)
    _, countries = CountrySerializer.fetch(limit=-1)
    return render(request, 'car_sales/store_view.html', {
        'active_tab': 'stores',
        'cities': cities,
        'countries': countries,
    })

@login_required
def role_view(request):
    is_admin = is_car_sales_admin_user(request.user)
    if not is_admin:
        return HttpResponseForbidden("Permission denied. Only administrators can access this page.")
    return render(request, 'car_sales/role_view.html', {'active_tab': 'roles'})

@login_required
def hierarchy_view(request):
    is_admin = is_car_sales_admin_user(request.user)
    if not is_admin:
        return HttpResponseForbidden("Permission denied. Only administrators can access this page.")
    return render(request, 'car_sales/hierarchy_view.html', {'active_tab': 'hierarchy'})

@login_required
def status_view(request):
    is_admin = is_car_sales_admin_user(request.user)
    if not is_admin:
        return HttpResponseForbidden("Permission denied. Only administrators can access this page.")
    return render(request, 'car_sales/status_view.html', {'active_tab': 'statuses'})

@login_required
def industry_view(request):
    is_admin = is_car_sales_admin_user(request.user)
    if not is_admin:
        return HttpResponseForbidden("Permission denied. Only administrators can access this page.")
    return render(request, 'car_sales/industry_view.html', {'active_tab': 'industry'})

@login_required
def vehicle_view(request):
    if not is_staff_user(request):
        return HttpResponseForbidden("Permission denied. Only staff members and administrators can access this page.")
    _, makes = IndustryInfoSerializer.fetch(limit=-1)
    return render(request, 'car_sales/vehicle_view.html', {
        'active_tab': 'vehicles',
        'makes': makes,
    })

@login_required
def customer_view(request):
    if not is_staff_user(request):
        return HttpResponseForbidden("Permission denied. Only staff members and administrators can access this page.")
    _, cities = CitySerializer.fetch(limit=-1)
    _, countries = CountrySerializer.fetch(limit=-1)
    return render(request, 'car_sales/customer_view.html', {
        'active_tab': 'customers',
        'cities': cities,
        'countries': countries,
    })

@login_required
def selling_view(request):
    if not is_staff_user(request):
        return HttpResponseForbidden("Permission denied. Only staff members and administrators can access this page.")
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
    if not is_staff_user(request):
        return HttpResponseForbidden("Permission denied. Only staff members and administrators can access this page.")
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
    if not is_car_sales_admin_user(request.user):
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
    if not is_staff_user(request):
        return HttpResponseForbidden("Permission denied. Only staff members and administrators can access this page.")
    _, vehicles = VehicleInfoSerializer.fetch(limit=1000)
    _, stores = StoreSerializer.fetch(limit=-1)
    _, employees = EmployeeSerializer.fetch(limit=-1)
    _, selling_infos = SellingInfoSerializer.fetch(limit=1000)
    _, makes = IndustryInfoSerializer.fetch(limit=-1)
    return render(request, 'car_sales/api_inventory.html', {
        'active_parent': 'api_pages',
        'active_tab': 'api_inventory',
        'vehicles': vehicles,
        'stores': stores,
        'employees': employees,
        'selling_infos': selling_infos,
        'makes': makes,
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
            page_size_param = request.GET.get('page_size') or request.GET.get('limit')
            page_size = int(page_size_param) if page_size_param is not None else 25
        except ValueError:
            page, page_size = 1, 25
        limit = None if page_size < 0 else page_size
        offset = 0 if page_size < 0 else (page - 1) * page_size
        search = request.GET.get('search', '').strip()
        store_id, employee_id = None, None
        if store_field or employee_field:
            profile = get_employee_profile(request)
            if profile and not is_car_sales_admin_user(request.user):
                allowed_stores, allowed_employees = get_user_filters(request, profile)
                if store_field:
                    store_id = allowed_stores
                if employee_field:
                    employee_id = allowed_employees
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
        
        # Intercept and override for Level 9 users when creating Sales records
        if model_class == SellingInfo:
            profile = get_employee_profile(request)
            if profile and _get_employee_level(profile.employee_id) == 9:
                request.data['employee'] = profile.employee_id
                request.data['store'] = profile.store_id

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

@api_view(['GET'])
def hierarchy_api(request, pk=None):
    return generic_model_api(request, EmployeeHierarchy, EmployeeHierarchySerializer, ['employee__first_name', 'employee__last_name', 'role__role_name'], pk)

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
    if not is_staff_user(request):
        return Response({"status": False, "message": "Permission denied. This action is restricted to the car sales workspace."}, status=status.HTTP_403_FORBIDDEN)
    year = request.GET.get('budget_year')
    stats_data = EmployeeBudgetSerializer.fetch_stats(year)
    return Response({"status": True, **stats_data}, status=status.HTTP_200_OK)

@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def employee_api(request, pk=None):
    return generic_model_api(request, Employee, EmployeeSerializer, ['first_name', 'last_name', 'employee_addr', 'employee_role__role_name', 'store__store_name'], pk, 'store', 'self')



# ─────────────────────────────────────────────
# Invoice & PDF Views
# ─────────────────────────────────────────────

@login_required
def invoice_view(request):
    if not is_staff_user(request):
        return HttpResponseForbidden("Permission denied. Only staff members and administrators can access this page.")
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
    if not is_car_sales_admin_user(request.user):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    base_url = request.build_absolute_uri('/')[:-1]
    return render(request, 'car_sales/documentation.html', {
        'active_tab': 'documentation',
        'base_url': base_url,
    })
