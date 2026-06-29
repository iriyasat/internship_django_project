from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Avg, F, Q
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
from django.http import Http404, HttpResponseRedirect, JsonResponse
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


def employee_report_view(request):
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    total_employees = Employee.objects.count()
    active_employees = Employee.objects.filter(status__status='Active').count()
    
    # Setup date filters for annotations
    sales_filter = Q()
    if date_from:
        sales_filter &= Q(sales__selling_date__gte=date_from)
    if date_to:
        sales_filter &= Q(sales__selling_date__lte=date_to)
        
    # 1. Role distribution
    role_dist = Employee.objects.values('employee_role__role_name').annotate(
        count=Count('employee_id')
    ).order_by('-count')
    
    # 2. Store distribution
    store_dist = Employee.objects.values('store__store_name').annotate(
        count=Count('employee_id')
    ).order_by('-count')
    
    # 3. Leaderboard: Rank all employees by sales revenue in the filtered date range
    employee_leaderboard_qs = Employee.objects.annotate(
        sales_count=Count('sales', filter=sales_filter),
        sales_revenue=Sum('sales__selling_price', filter=sales_filter)
    ).order_by(F('sales_revenue').desc(nulls_last=True), '-sales_count', 'employee_id')
    
    # JSON download support
    if request.GET.get('download') == 'json':
        data = {
            'report_type': 'Employee Performance Report',
            'date_range': {'from': date_from, 'to': date_to},
            'summary': {
                'total_employees': total_employees,
                'active_employees': active_employees,
                'inactive_employees': total_employees - active_employees,
            },
            'employees': [
                {
                    'id': emp.employee_id,
                    'name': f"{emp.first_name} {emp.last_name}",
                    'role': emp.employee_role.role_name if emp.employee_role else None,
                    'store': emp.store.store_name if emp.store else None,
                    'sales_count': emp.sales_count,
                    'sales_revenue': float(emp.sales_revenue or 0),
                }
                for emp in employee_leaderboard_qs
            ]
        }
        response = JsonResponse(data, json_dumps_params={'indent': 2})
        response['Content-Disposition'] = f'attachment; filename="employee_report_{date_from}_to_{date_to}.json"'
        return response
    
    # For the chart: Top 10 performers
    top_performers = employee_leaderboard_qs[:10]
    chart_names = []
    chart_revenue = []
    chart_sales = []
    for emp in top_performers:
        chart_names.append(f"{emp.first_name} {emp.last_name}")
        chart_revenue.append(int(emp.sales_revenue or 0))
        chart_sales.append(emp.sales_count or 0)
        
    # Pagination for leaderboard table
    paginator = Paginator(employee_leaderboard_qs, 1000)  # 1000 employees per page
    page_number = request.GET.get('page')
    leaderboard_page = paginator.get_page(page_number)
    
    context = {
        'active_parent': 'reports',
        'active_tab': 'report_employee',
        'total_employees': total_employees,
        'active_employees': active_employees,
        'inactive_employees': total_employees - active_employees,
        'role_distribution': role_dist,
        'store_distribution': store_dist,
        'employee_leaderboard': leaderboard_page,
        'chart_names': chart_names,
        'chart_revenue': chart_revenue,
        'chart_sales': chart_sales,
        'date_from': date_from or '',
        'date_to': date_to or '',
    }
    return render(request, 'car_sales/employee_report.html', context)


def vehicle_report_view(request):
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    total_vehicles = VehicleInfo.objects.count()
    avg_mmr = VehicleInfo.objects.aggregate(avg_mmr=Avg('mmr'))['avg_mmr'] or 0
    
    # Filter sales by date range
    sales_qs = SellingInfo.objects.all()
    if date_from:
        sales_qs = sales_qs.filter(selling_date__gte=date_from)
    if date_to:
        sales_qs = sales_qs.filter(selling_date__lte=date_to)
        
    # 1. Top Selling makes
    brand_sales = sales_qs.values('vehicle__make__make_name').annotate(
        sold_count=Count('sell_id'),
        revenue=Sum('selling_price'),
        avg_price=Avg('selling_price')
    ).order_by('-revenue')[:10]
    
    # 2. Vehicle Condition stats
    condition_stats = VehicleInfo.objects.aggregate(
        avg_condition=Avg('condition'),
        avg_odometer=Avg('odometer')
    )
    if condition_stats['avg_condition'] is not None:
        condition_stats['avg_condition'] /= 10.0

    
    # 3. Premium transactions (expensive sold vehicles, paginated)
    expensive_sold_qs = sales_qs.select_related('vehicle__make', 'customer', 'store').annotate(
        margin=F('selling_price') - F('vehicle__mmr')
    ).order_by('-selling_price')
    
    # JSON download support
    if request.GET.get('download') == 'json':
        data = {
            'report_type': 'Vehicle Report',
            'date_range': {'from': date_from, 'to': date_to},
            'summary': {
                'total_vehicles': total_vehicles,
                'average_mmr': float(avg_mmr),
                'average_condition': float(condition_stats['avg_condition'] or 0),
                'average_odometer': float(condition_stats['avg_odometer'] or 0),
            },
            'transactions': [
                {
                    'selling_date': sale.selling_date.strftime('%Y-%m-%d') if sale.selling_date else None,
                    'make': sale.vehicle.make.make_name if sale.vehicle and sale.vehicle.make else None,
                    'model': sale.vehicle.vehicle_model if sale.vehicle else None,
                    'vin': sale.vehicle.vin if sale.vehicle else None,
                    'customer': f"{sale.customer.firstname} {sale.customer.lastname}" if sale.customer else None,
                    'store': sale.store.store_name if sale.store else None,
                    'mmr': float(sale.vehicle.mmr or 0) if sale.vehicle else 0.0,
                    'selling_price': float(sale.selling_price or 0),
                    'margin': float(sale.margin or 0),
                }
                for sale in expensive_sold_qs
            ]
        }
        response = JsonResponse(data, json_dumps_params={'indent': 2})
        response['Content-Disposition'] = f'attachment; filename="vehicle_report_{date_from}_to_{date_to}.json"'
        return response
    
    # Pagination for premium sales table
    paginator = Paginator(expensive_sold_qs, 1000)  # 1000 records per page
    page_number = request.GET.get('page')
    expensive_sold_page = paginator.get_page(page_number)
    
    for sale in expensive_sold_page:
        sale.abs_margin = abs(sale.margin or 0)
        
    # 4. Make distribution in inventory
    make_inventory = VehicleInfo.objects.values('make__make_name').annotate(
        count=Count('id'),
        avg_mmr=Avg('mmr')
    ).order_by('-count')[:10]
    
    # Pre-format chart data
    chart_makes = [item['vehicle__make__make_name'] for item in brand_sales]
    chart_sold_count = [item['sold_count'] for item in brand_sales]
    chart_revenue = [int(item['revenue'] or 0) for item in brand_sales]
    
    context = {
        'active_parent': 'reports',
        'active_tab': 'report_vehicle',
        'total_vehicles': total_vehicles,
        'avg_mmr': avg_mmr,
        'brand_sales': brand_sales,
        'condition_stats': condition_stats,
        'expensive_sold': expensive_sold_page,
        'make_inventory': make_inventory,
        'chart_makes': chart_makes,
        'chart_sold_count': chart_sold_count,
        'chart_revenue': chart_revenue,
        'date_from': date_from or '',
        'date_to': date_to or '',
    }
    return render(request, 'car_sales/vehicle_report.html', context)


def sales_report_view(request):
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Filter sales by date range
    sales_qs = SellingInfo.objects.all()
    if date_from:
        sales_qs = sales_qs.filter(selling_date__gte=date_from)
    if date_to:
        sales_qs = sales_qs.filter(selling_date__lte=date_to)
        
    total_sales = sales_qs.count()
    total_revenue = sales_qs.aggregate(total=Sum('selling_price'))['total'] or 0
    avg_price = sales_qs.aggregate(avg=Avg('selling_price'))['avg'] or 0
    
    # Margin analysis (selling_price - mmr)
    margin_stats = sales_qs.annotate(
        margin=F('selling_price') - F('vehicle__mmr')
    ).aggregate(
        total_margin=Sum('margin'),
        avg_margin=Avg('margin')
    )
    total_margin = margin_stats['total_margin'] or 0
    avg_margin = margin_stats['avg_margin'] or 0
    
    # 1. Sales by Store
    store_sales = sales_qs.values('store__store_name').annotate(
        sales_count=Count('sell_id'),
        revenue=Sum('selling_price'),
        avg_price=Avg('selling_price')
    ).order_by('-revenue')
    
    # 2. Top Customers by purchases
    top_customers = sales_qs.values(
        'customer__customer_id', 'customer__firstname', 'customer__lastname', 'customer__city__city_name'
    ).annotate(
        purchase_count=Count('sell_id'),
        total_spent=Sum('selling_price')
    ).order_by('-total_spent')[:10]
    
    # 3. Monthly Trend
    monthly_sales = sales_qs.annotate(
        month=TruncMonth('selling_date')
    ).values('month').annotate(
        count=Count('sell_id'),
        revenue=Sum('selling_price')
    ).order_by('month')
    
    chart_dates = [item['month'].strftime('%b %Y') for item in monthly_sales]
    chart_sales = [item['count'] for item in monthly_sales]
    chart_revenue = [int(item['revenue'] or 0) for item in monthly_sales]
    
    # 4. Detailed Sales Transactions (paginated)
    detailed_sales_qs = sales_qs.select_related('customer', 'vehicle__make', 'employee').order_by('-selling_date', '-sell_id')
    
    # JSON download support
    if request.GET.get('download') == 'json':
        data = {
            'report_type': 'Sales Revenue Report',
            'date_range': {'from': date_from, 'to': date_to},
            'summary': {
                'total_sales': total_sales,
                'total_revenue': float(total_revenue),
                'average_price': float(avg_price),
                'total_margin': float(total_margin),
                'average_margin': float(avg_margin),
            },
            'transactions': [
                {
                    'sale_id': sale.sell_id,
                    'selling_date': sale.selling_date.strftime('%Y-%m-%d') if sale.selling_date else None,
                    'customer': f"{sale.customer.firstname} {sale.customer.lastname}" if sale.customer else None,
                    'make': sale.vehicle.make.make_name if sale.vehicle and sale.vehicle.make else None,
                    'model': sale.vehicle.vehicle_model if sale.vehicle else None,
                    'employee': f"{sale.employee.first_name} {sale.employee.last_name}" if sale.employee else None,
                    'selling_price': float(sale.selling_price or 0),
                }
                for sale in detailed_sales_qs
            ]
        }
        response = JsonResponse(data, json_dumps_params={'indent': 2})
        response['Content-Disposition'] = f'attachment; filename="sales_report_{date_from}_to_{date_to}.json"'
        return response
    paginator = Paginator(detailed_sales_qs, 1000)  # 1000 records per page
    page_number = request.GET.get('page')
    sales_page = paginator.get_page(page_number)
    
    context = {
        'active_parent': 'reports',
        'active_tab': 'report_sales',
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'avg_price': avg_price,
        'total_margin': total_margin,
        'avg_margin': avg_margin,
        'total_margin_abs': abs(total_margin),
        'avg_margin_abs': abs(avg_margin),
        'store_sales': store_sales,
        'top_customers': top_customers,
        'chart_dates': chart_dates,
        'chart_sales': chart_sales,
        'chart_revenue': chart_revenue,
        'detailed_sales': sales_page,
        'date_from': date_from or '',
        'date_to': date_to or '',
    }
    return render(request, 'car_sales/sales_report.html', context)


