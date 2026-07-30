from django.contrib import admin
from project1.admin_sites import car_sales_admin_site
from .models import (
    Country, City, Store, EmployeeRole, EmployeeStatus,
    Employee, IndustryInfo, VehicleInfo, Customer, CustomerInfo,
    SellingInfo, EmployeeBudget, Inventory, Invoice,
    EmployeeHierarchy, EmployeeLevel
)

class CountryAdmin(admin.ModelAdmin):
    list_display = ('country_id', 'country_name', 'created_at', 'updated_at')
    search_fields = ('country_name',)
    readonly_fields = ('created_at', 'updated_at')

class CityAdmin(admin.ModelAdmin):
    list_display = ('city_id', 'city_name', 'country', 'created_at', 'updated_at')
    list_filter = ('country',)
    search_fields = ('city_name',)
    readonly_fields = ('created_at', 'updated_at')
    list_select_related = ('country',)

class StoreAdmin(admin.ModelAdmin):
    list_display = ('store_id', 'store_name', 'store_code', 'city', 'country', 'address')
    list_filter = ('country', 'city')
    search_fields = ('store_name', 'store_code')
    list_select_related = ('city', 'country')

class EmployeeRoleAdmin(admin.ModelAdmin):
    list_display = ('role_id', 'role_name')
    search_fields = ('role_name',)

class EmployeeLevelAdmin(admin.ModelAdmin):
    list_display = ('level', 'notes')
    search_fields = ('level', 'notes')

class EmployeeStatusAdmin(admin.ModelAdmin):
    list_display = ('status_id', 'status')
    search_fields = ('status',)

class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'first_name', 'last_name', 'employee_role', 'status', 'store', 'date_of_joining')
    list_filter = ('status', 'employee_role', 'store', 'country')
    search_fields = ('first_name', 'last_name', 'employee_addr')
    list_select_related = ('employee_role', 'status', 'store', 'city', 'country')

class IndustryInfoAdmin(admin.ModelAdmin):
    list_display = ('make_id', 'make_name')
    search_fields = ('make_name',)

class VehicleInfoAdmin(admin.ModelAdmin):
    list_display = ('id', 'make', 'vehicle_model', 'mmr', 'trim', 'body', 'transmission', 'vin', 'condition', 'odometer', 'color')
    list_filter = ('make', 'transmission', 'state', 'color')
    search_fields = ('vehicle_model', 'vin')
    list_select_related = ('make',)

class CustomerAdmin(admin.ModelAdmin):
    list_display = ('customer_id', 'email', 'phone', 'created_at', 'updated_at')
    search_fields = ('email', 'phone')

class CustomerInfoAdmin(admin.ModelAdmin):
    list_display = ('customer', 'firstname', 'lastname', 'customer_status', 'city', 'country')
    list_filter = ('customer_status', 'country', 'city')
    search_fields = ('firstname', 'lastname', 'customer_address')
    list_select_related = ('city', 'country')

class SellingInfoAdmin(admin.ModelAdmin):
    list_display = ('sell_id', 'customer', 'vehicle', 'employee', 'store', 'selling_price', 'selling_date')
    list_filter = ('store', 'selling_date')
    search_fields = ('sell_id', 'customer__firstname', 'customer__lastname', 'vehicle__vin', 'employee__first_name', 'employee__last_name')
    autocomplete_fields = ('customer', 'vehicle', 'employee')
    list_select_related = ('customer', 'vehicle__make', 'employee', 'store')

class EmployeeBudgetAdmin(admin.ModelAdmin):
    list_display = ('id', 'employee', 'budget_year', 'budget_month', 'store', 'budget_qty', 'budget_amount')
    list_filter = ('budget_year', 'budget_month', 'store')
    search_fields = ('employee__first_name', 'employee__last_name')
    autocomplete_fields = ('employee',)
    list_select_related = ('employee', 'store')

class InventoryAdmin(admin.ModelAdmin):
    list_display = ('inventory_id', 'vehicle', 'store', 'employee', 'selling_info', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'store', 'employee')
    search_fields = ('vehicle__vin', 'vehicle__vehicle_model', 'employee__first_name', 'employee__last_name')
    autocomplete_fields = ('vehicle', 'selling_info', 'employee')
    list_select_related = ('vehicle__make', 'store', 'selling_info', 'employee')

class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_id', 'selling_info', 'invoice_date', 'due_date', 'payment_status', 'payment_method', 'discount_amount', 'created_at', 'updated_at')
    list_filter = ('payment_status', 'payment_method', 'invoice_date')
    search_fields = ('invoice_id', 'selling_info__sell_id', 'selling_info__customer__firstname', 'selling_info__customer__lastname')
    autocomplete_fields = ('selling_info',)
    list_select_related = ('selling_info__customer', 'selling_info__vehicle__make', 'selling_info__store')
    readonly_fields = ('created_at', 'updated_at')

class EmployeeHierarchyAdmin(admin.ModelAdmin):
    list_display = ('employee', 'role', 'level', 'status', 'supervisor')
    list_filter = ('role', 'level', 'status')
    search_fields = ('employee__first_name', 'employee__last_name', 'supervisor__first_name', 'supervisor__last_name')
    list_select_related = ('employee', 'role', 'status', 'supervisor')

# Register to both standard admin.site and dedicated car_sales_admin_site
models_and_admins = [
    (Country, CountryAdmin),
    (City, CityAdmin),
    (Store, StoreAdmin),
    (EmployeeRole, EmployeeRoleAdmin),
    (EmployeeLevel, EmployeeLevelAdmin),
    (EmployeeStatus, EmployeeStatusAdmin),
    (Employee, EmployeeAdmin),
    (IndustryInfo, IndustryInfoAdmin),
    (VehicleInfo, VehicleInfoAdmin),
    (Customer, CustomerAdmin),
    (CustomerInfo, CustomerInfoAdmin),
    (SellingInfo, SellingInfoAdmin),
    (EmployeeBudget, EmployeeBudgetAdmin),
    (Inventory, InventoryAdmin),
    (Invoice, InvoiceAdmin),
    (EmployeeHierarchy, EmployeeHierarchyAdmin),
]

for model, admin_class in models_and_admins:
    admin.site.register(model, admin_class)
    car_sales_admin_site.register(model, admin_class)