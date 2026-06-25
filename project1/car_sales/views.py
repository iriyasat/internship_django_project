from django.shortcuts import render
from .models import *

# Create your views here.
def home_view(request):
    return render(request, 'car_sales/index.html')

def employee_view(request):
    employees_list = Employee.objects.select_related('employee_role', 'status', 'store', 'city', 'country').all()[:200]
    context = {
        'employees': employees_list
    }
    return render(request, 'car_sales/employee_view.html', context)

def country_view(request):
    countries_list = Country.objects.all()
    context = {
        'countries': countries_list
    }
    return render(request, 'car_sales/country_view.html', context)

def city_view(request):
    cities_list = City.objects.select_related('country').all()
    context = {
        'cities': cities_list
    }
    return render(request, 'car_sales/city_view.html', context)

def store_view(request):
    stores_list = Store.objects.select_related('city', 'country').all()
    context = {
        'stores': stores_list
    }
    return render(request, 'car_sales/store_view.html', context)

def role_view(request):
    roles_list = EmployeeRole.objects.all()
    context = {
        'roles': roles_list
    }
    return render(request, 'car_sales/role_view.html', context)

def status_view(request):
    statuses_list = EmployeeStatus.objects.all()
    context = {
        'statuses': statuses_list
    }
    return render(request, 'car_sales/status_view.html', context)

def industry_view(request):
    industries_list = IndustryInfo.objects.all()
    context = {
        'industries': industries_list
    }
    return render(request, 'car_sales/industry_view.html', context)

def vehicle_view(request):
    vehicles_list = VehicleInfo.objects.select_related('make').all()[:200]
    context = {
        'vehicles': vehicles_list
    }
    return render(request, 'car_sales/vehicle_view.html', context)

def customer_view(request):
    customers_list = CustomerInfo.objects.select_related('city', 'country').all()[:200]
    context = {
        'customers': customers_list
    }
    return render(request, 'car_sales/customer_view.html', context)

def selling_view(request):
    sales_list = SellingInfo.objects.select_related('customer', 'vehicle__make', 'employee', 'store').all()[:200]
    context = {
        'sales': sales_list
    }
    return render(request, 'car_sales/selling_view.html', context)

def budget_view(request):
    budgets_list = EmployeeBudget.objects.select_related('employee', 'store').all()[:200]
    context = {
        'budgets': budgets_list
    }
    return render(request, 'car_sales/budget_view.html', context)