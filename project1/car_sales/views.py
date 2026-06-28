from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from .models import (
    Country, City, Store, EmployeeRole, EmployeeStatus,
    Employee, IndustryInfo, VehicleInfo, CustomerInfo,
    SellingInfo, EmployeeBudget
)

# Create your views here.
def home_view(request):
    # 1. Total statistics
    sales_count = SellingInfo.objects.count()
    total_revenue = SellingInfo.objects.aggregate(total=Sum('selling_price'))['total'] or 0
    customers_count = CustomerInfo.objects.count()
    
    # 2. Recent Sales (latest 5 sales)
    recent_sales = SellingInfo.objects.select_related('customer', 'vehicle__make', 'employee', 'store').order_by('-selling_date', '-sell_id')[:5]
    
    # 3. Top Selling vehicle makes
    top_selling = SellingInfo.objects.values('vehicle__make__make_name').annotate(
        count=Count('sell_id'),
        revenue=Sum('selling_price')
    ).order_by('-count')[:5]
    
    # 4. Chart series (grouped by month)
    monthly_sales = SellingInfo.objects.annotate(
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
    return render(request, 'car_sales/index.html', context)

def employee_view(request):
    employees_list = Employee.objects.select_related('employee_role', 'status', 'store', 'city', 'country').order_by('employee_id').all()
    context = {
        'active_tab': 'employees',
        'employees': employees_list
    }
    return render(request, 'car_sales/employee_view.html', context)

def country_view(request):
    countries_list = Country.objects.all()
    context = {
        'active_tab': 'countries',
        'countries': countries_list
    }
    return render(request, 'car_sales/country_view.html', context)

def city_view(request):
    cities_list = City.objects.select_related('country').all()
    context = {
        'active_tab': 'cities',
        'cities': cities_list
    }
    return render(request, 'car_sales/city_view.html', context)

def store_view(request):
    stores_list = Store.objects.select_related('city', 'country').all()
    context = {
        'active_tab': 'stores',
        'stores': stores_list
    }
    return render(request, 'car_sales/store_view.html', context)

def role_view(request):
    roles_list = EmployeeRole.objects.all()
    context = {
        'active_tab': 'roles',
        'roles': roles_list
    }
    return render(request, 'car_sales/role_view.html', context)

def status_view(request):
    statuses_list = EmployeeStatus.objects.all()
    context = {
        'active_tab': 'statuses',
        'statuses': statuses_list
    }
    return render(request, 'car_sales/status_view.html', context)

def industry_view(request):
    industries_list = IndustryInfo.objects.all()
    context = {
        'active_tab': 'industry',
        'industries': industries_list
    }
    return render(request, 'car_sales/industry_view.html', context)

def vehicle_view(request):
    vehicles_list = VehicleInfo.objects.select_related('make').order_by('id').all()
    # We display all vehicles using DataTables which handles pagination client-side,
    # but since the database is huge (100,000+ rows), server-side pagination with Paginator is kept.
    paginator = Paginator(vehicles_list, 1000)  # Show 1000 vehicles per page for good performance
    page_number = request.GET.get('page')
    vehicles_page = paginator.get_page(page_number)
    context = {
        'active_tab': 'vehicles',
        'vehicles': vehicles_page
    }
    return render(request, 'car_sales/vehicle_view.html', context)

def customer_view(request):
    customers_list = CustomerInfo.objects.select_related('city', 'country').order_by('customer_id').all()
    paginator = Paginator(customers_list, 1000)  # Show 1000 customers per page
    page_number = request.GET.get('page')
    customers_page = paginator.get_page(page_number)
    context = {
        'active_tab': 'customers',
        'customers': customers_page
    }
    return render(request, 'car_sales/customer_view.html', context)

def selling_view(request):
    sales_list = SellingInfo.objects.prefetch_related('customer', 'vehicle__make', 'employee', 'store').order_by('sell_id').all()
    paginator = Paginator(sales_list, 1000)  # Show 1000 sales per page
    page_number = request.GET.get('page')
    sales_page = paginator.get_page(page_number)
    context = {
        'active_tab': 'sales',
        'sales': sales_page
    }
    return render(request, 'car_sales/selling_view.html', context)

def budget_view(request):
    budgets_list = EmployeeBudget.objects.prefetch_related('employee', 'store').order_by('id').all()
    paginator = Paginator(budgets_list, 1000)  # Show 1000 budgets per page
    page_number = request.GET.get('page')
    budgets_page = paginator.get_page(page_number)
    context = {
        'active_tab': 'budgets',
        'budgets': budgets_page
    }
    return render(request, 'car_sales/budget_view.html', context)
