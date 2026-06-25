from django.contrib import admin
from .models import (
    Country, City, Store, EmployeeRole, EmployeeStatus,
    Employee, IndustryInfo, VehicleInfo, CustomerInfo,
    SellingInfo, EmployeeBudget
)

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('country_id', 'country_name', 'created_at', 'updated_at')
    search_fields = ('country_name',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('city_id', 'city_name', 'country', 'created_at', 'updated_at')
    list_filter = ('country',)
    search_fields = ('city_name',)
    readonly_fields = ('created_at', 'updated_at')
    list_select_related = ('country',)

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('store_id', 'store_name', 'store_code', 'city', 'country', 'address')
    list_filter = ('country', 'city')
    search_fields = ('store_name', 'store_code')
    list_select_related = ('city', 'country')

@admin.register(EmployeeRole)
class EmployeeRoleAdmin(admin.ModelAdmin):
    list_display = ('role_id', 'role_name')
    search_fields = ('role_name',)

@admin.register(EmployeeStatus)
class EmployeeStatusAdmin(admin.ModelAdmin):
    list_display = ('status_id', 'status')
    search_fields = ('status',)

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'first_name', 'last_name', 'employee_role', 'status', 'store', 'date_of_joining')
    list_filter = ('status', 'employee_role', 'store', 'country')
    search_fields = ('first_name', 'last_name', 'employee_addr')
    list_select_related = ('employee_role', 'status', 'store', 'city', 'country')

@admin.register(IndustryInfo)
class IndustryInfoAdmin(admin.ModelAdmin):
    list_display = ('make_id', 'make_name')
    search_fields = ('make_name',)

@admin.register(VehicleInfo)
class VehicleInfoAdmin(admin.ModelAdmin):
    list_display = ('id', 'make', 'vehicle_model', 'mmr', 'trim', 'body', 'transmission', 'vin', 'condition', 'odometer', 'color')
    list_filter = ('make', 'transmission', 'state', 'color')
    search_fields = ('vehicle_model', 'vin')
    list_select_related = ('make',)

@admin.register(CustomerInfo)
class CustomerInfoAdmin(admin.ModelAdmin):
    list_display = ('customer_id', 'firstname', 'lastname', 'customer_status', 'city', 'country')
    list_filter = ('customer_status', 'country', 'city')
    search_fields = ('firstname', 'lastname', 'customer_address')
    list_select_related = ('city', 'country')

@admin.register(SellingInfo)
class SellingInfoAdmin(admin.ModelAdmin):
    list_display = ('sell_id', 'customer', 'vehicle', 'employee', 'store', 'selling_price', 'selling_date')
    list_filter = ('store', 'selling_date')
    search_fields = ('sell_id', 'customer__firstname', 'customer__lastname', 'vehicle__vin', 'employee__first_name', 'employee__last_name')
    autocomplete_fields = ('customer', 'vehicle', 'employee')
    list_select_related = ('customer', 'vehicle__make', 'employee', 'store')

@admin.register(EmployeeBudget)
class EmployeeBudgetAdmin(admin.ModelAdmin):
    list_display = ('id', 'employee', 'budget_year', 'budget_month', 'store', 'budget_qty', 'budget_amount')
    list_filter = ('budget_year', 'budget_month', 'store')
    search_fields = ('employee__first_name', 'employee__last_name')
    autocomplete_fields = ('employee',)
    list_select_related = ('employee', 'store')