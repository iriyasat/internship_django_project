from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from .models import (
    Country, City, Store, EmployeeRole, EmployeeStatus,
    Employee, IndustryInfo, VehicleInfo, CustomerInfo,
    SellingInfo, EmployeeBudget
)
from django import forms
from django.forms import ModelForm, IntegerField
from django.apps import apps
from django.forms import modelform_factory
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required


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


class SellingInfoForm(ModelForm):
    customer = IntegerField(label="Customer ID", widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter Customer ID (e.g. 5)'}))
    vehicle = IntegerField(label="Vehicle ID", widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter Vehicle ID (e.g. 12)'}))

    class Meta:
        model = SellingInfo
        exclude = ['created_at', 'updated_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            if self.instance.customer:
                self.initial['customer'] = self.instance.customer.customer_id
            if self.instance.vehicle:
                self.initial['vehicle'] = self.instance.vehicle.id

    def clean_customer(self):
        customer_id = self.cleaned_data['customer']
        try:
            return CustomerInfo.objects.get(pk=customer_id)
        except CustomerInfo.DoesNotExist:
            raise forms.ValidationError("Customer with this ID does not exist.")

    def clean_vehicle(self):
        vehicle_id = self.cleaned_data['vehicle']
        try:
            return VehicleInfo.objects.get(pk=vehicle_id)
        except VehicleInfo.DoesNotExist:
            raise forms.ValidationError("Vehicle with this ID does not exist.")

@staff_member_required
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
        'budgets': {'name': 'Employee Budgets', 'count': EmployeeBudget.objects.count(), 'url': '/budgets/', 'slug': 'employeebudget'},
    }
    context = {
        'active_tab': 'admin_panel',
        'stats': stats,
    }
    return render(request, 'car_sales/admin_panel.html', context)

@staff_member_required
def admin_crud_view(request, model_name, action, pk=None):
    model_mapping = {
        'country': 'Country',
        'city': 'City',
        'store': 'Store',
        'employeerole': 'EmployeeRole',
        'employeestatus': 'EmployeeStatus',
        'employee': 'Employee',
        'industryinfo': 'IndustryInfo',
        'vehicleinfo': 'VehicleInfo',
        'customerinfo': 'CustomerInfo',
        'sellinginfo': 'SellingInfo',
        'employeebudget': 'EmployeeBudget'
    }
    actual_model_name = model_mapping.get(model_name.lower())
    if not actual_model_name:
        raise Http404("Model not found")

    try:
        model = apps.get_model('car_sales', actual_model_name)
    except LookupError:
        raise Http404("Model not found")

    instance = None
    if pk:
        try:
            instance = model.objects.get(pk=pk)
        except model.DoesNotExist:
            raise Http404("Record not found")

    exclude_fields = ['created_at', 'updated_at']

    if action == 'delete':
        next_url = request.GET.get('next') or request.POST.get('next') or reverse('admin_panel')
        if request.method == 'POST':
            instance.delete()
            messages.success(request, f"Successfully deleted {model._meta.verbose_name} record.")
            return HttpResponseRedirect(next_url)
        context = {
            'action': action,
            'model_name': model._meta.verbose_name,
            'instance': instance,
            'next': next_url
        }
        return render(request, 'car_sales/admin_crud.html', context)

    if actual_model_name == 'SellingInfo':
        form_class = SellingInfoForm
    else:
        form_class = modelform_factory(model, exclude=exclude_fields)

    next_url = request.GET.get('next') or request.POST.get('next') or reverse('admin_panel')
    
    if request.method == 'POST':
        form = form_class(request.POST, instance=instance)
        for name, field in form.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            else:
                field.widget.attrs.update({'class': 'form-control'})
                
        if form.is_valid():
            form.save()
            messages.success(request, f"Successfully {'updated' if instance else 'created'} {model._meta.verbose_name} record.")
            return HttpResponseRedirect(next_url)
    else:
        form = form_class(instance=instance)
        for name, field in form.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            else:
                field.widget.attrs.update({'class': 'form-control'})

    context = {
        'form': form,
        'action': action,
        'model_name': model._meta.verbose_name,
        'instance': instance,
        'next': next_url
    }
    return render(request, 'car_sales/admin_crud.html', context)

