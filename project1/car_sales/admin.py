from django.contrib import admin
from .models import *

# ==========================================
# 1. Geography
# ==========================================

class countryadmin(admin.ModelAdmin):
    list_display = ("country_id", "country_name", "created_at", "updated_at")
    search_fields = ("country_name",)
    readonly_fields = ("created_at", "updated_at")
    ordering = ("country_id",)

admin.site.register(Country, countryadmin)


class cityadmin(admin.ModelAdmin):
    list_display = ("city_id", "city_name", "country", "created_at", "updated_at")
    list_filter = ("country",)
    search_fields = ("city_name", "country__country_name")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("city_id",)

admin.site.register(City, cityadmin)


# ==========================================
# 2. Employees & HR
# ==========================================

class employeeroleadmin(admin.ModelAdmin):
    list_display = ("role_id", "role_name", "created_at", "updated_at")
    search_fields = ("role_name",)
    readonly_fields = ("created_at", "updated_at")
    ordering = ("role_id",)

admin.site.register(EmployeeRole, employeeroleadmin)


class employeestatusadmin(admin.ModelAdmin):
    list_display = ("status_id", "status_name", "created_at", "updated_at")
    search_fields = ("status_name",)
    readonly_fields = ("created_at", "updated_at")
    ordering = ("status_id",)

admin.site.register(EmployeeStatus, employeestatusadmin)


class employeeadmin(admin.ModelAdmin):
    list_display = (
        "employee_id",
        "first_name",
        "last_name",
        "email",
        "emp_phone",
        "role",
        "status",
        "hire_date",
        "assigned_task",
        "created_at",
        "updated_at",
    )
    list_filter = ("status", "role", "hire_date")
    search_fields = ("first_name", "last_name", "email", "emp_phone")
    raw_id_fields = ("emp_city", "emp_country", "role", "status")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("last_name", "first_name")

admin.site.register(Employee, employeeadmin)


class employeetargetadmin(admin.ModelAdmin):
    list_display = ("target_id", "employee", "target_goal", "commission_percentage", "start_date", "end_date", "created_at", "updated_at")
    list_filter = ("employee", "start_date", "end_date")
    search_fields = ("employee__first_name", "employee__last_name")
    raw_id_fields = ("employee",)
    readonly_fields = ("created_at", "updated_at")
    ordering = ("target_id",)

admin.site.register(EmployeeTarget, employeetargetadmin)


# # ==========================================
# # 3. Customers
# # ==========================================

# class customeradmin(admin.ModelAdmin):
#     list_display = ("customer_id", "first_name", "last_name", "email", "customer_phone", "created_at", "updated_at")
#     search_fields = ("first_name", "last_name", "email", "customer_phone")
#     raw_id_fields = ("customer_city", "customer_country")
#     readonly_fields = ("created_at", "updated_at")
#     ordering = ("last_name", "first_name")

# admin.site.register(Customer, customeradmin)


# # ==========================================
# # 4. Inventory (Vehicles & Models)
# # ==========================================

# class manufactureradmin(admin.ModelAdmin):
#     list_display = ("manufacturer_id", "manufacturer_name", "created_at", "updated_at")
#     search_fields = ("manufacturer_name",)
#     readonly_fields = ("created_at", "updated_at")
#     ordering = ("manufacturer_id",)

# admin.site.register(Manufacturer, manufactureradmin)


# class vehiclemodeladmin(admin.ModelAdmin):
#     list_display = ("model_id", "manufacturer", "vehicle_model", "trim", "body_type", "fuel_type", "created_at", "updated_at")
#     list_filter = ("manufacturer", "body_type", "fuel_type")
#     search_fields = ("manufacturer__manufacturer_name", "vehicle_model", "trim")
#     raw_id_fields = ("manufacturer",)
#     readonly_fields = ("created_at", "updated_at")
#     ordering = ("manufacturer__manufacturer_name", "vehicle_model")

# admin.site.register(VehicleModel, vehiclemodeladmin)


# class vehicleserviceinline(admin.TabularInline):
#     model = VehicleService
#     extra = 1
#     readonly_fields = ("created_at", "updated_at")


# class vehicleadmin(admin.ModelAdmin):
#     list_display = (
#         "vehicle_id",
#         "year",
#         "model",
#         "vin",
#         "color",
#         "mileage",
#         "selling_price",
#         "condition",
#         "status",
#         "date_acquired",
#         "date_listed",
#         "created_at",
#         "updated_at",
#     )
#     list_filter = ("status", "condition", "year", "date_acquired", "date_listed")
#     search_fields = ("vin", "model__manufacturer__manufacturer_name", "model__vehicle_model", "color")
#     raw_id_fields = ("model",)
#     readonly_fields = ("created_at", "updated_at")
#     inlines = [vehicleserviceinline]
#     ordering = ("-year", "model__manufacturer__manufacturer_name")

# admin.site.register(Vehicle, vehicleadmin)


# class vehicleserviceadmin(admin.ModelAdmin):
#     list_display = ("service_id", "vehicle", "service_date", "cost", "created_at", "updated_at")
#     list_filter = ("service_date",)
#     search_fields = ("vehicle__vin", "description")
#     raw_id_fields = ("vehicle",)
#     readonly_fields = ("created_at", "updated_at")
#     ordering = ("-service_date",)

# admin.site.register(VehicleService, vehicleserviceadmin)


# # ==========================================
# # 5. Leads & CRM
# # ==========================================

# class leadsourceadmin(admin.ModelAdmin):
#     list_display = ("source_id", "source_name", "created_at", "updated_at")
#     search_fields = ("source_name",)
#     readonly_fields = ("created_at", "updated_at")
#     ordering = ("source_id",)

# admin.site.register(LeadSource, leadsourceadmin)


# class leadactivityinline(admin.TabularInline):
#     model = LeadActivity
#     extra = 1
#     raw_id_fields = ("employee", "activity_type")
#     readonly_fields = ("created_at", "updated_at")


# class leadadmin(admin.ModelAdmin):
#     list_display = (
#         "lead_id",
#         "customer",
#         "vehicle",
#         "employee",
#         "source",
#         "status",
#         "created_at",
#         "deleted_at",
#     )
#     list_filter = ("status", "source", "created_at")
#     search_fields = (
#         "customer__first_name",
#         "customer__last_name",
#         "employee__first_name",
#         "employee__last_name",
#         "vehicle__vin",
#     )
#     raw_id_fields = ("customer", "vehicle", "employee")
#     readonly_fields = ("created_at", "updated_at")
#     inlines = [leadactivityinline]
#     ordering = ("-created_at",)

# admin.site.register(Lead, leadadmin)


# class leadactivitytypeadmin(admin.ModelAdmin):
#     list_display = ("lead_activity_type_id", "lead_activity_type_name", "created_at", "updated_at")
#     search_fields = ("lead_activity_type_name",)
#     readonly_fields = ("created_at", "updated_at")
#     ordering = ("lead_activity_type_id",)

# admin.site.register(LeadActivityType, leadactivitytypeadmin)


# class leadactivityadmin(admin.ModelAdmin):
#     list_display = ("activity_id", "lead", "employee", "activity_type", "activity_date", "created_at", "updated_at")
#     list_filter = ("activity_type", "activity_date")
#     search_fields = (
#         "lead__customer__first_name",
#         "lead__customer__last_name",
#         "employee__first_name",
#         "employee__last_name",
#         "details",
#     )
#     raw_id_fields = ("lead", "employee", "activity_type")
#     readonly_fields = ("created_at", "updated_at")
#     ordering = ("-activity_date",)

# admin.site.register(LeadActivity, leadactivityadmin)


# # ==========================================
# # 6. Sales, Payments & Financing
# # ==========================================

# class tradeininline(admin.StackedInline):
#     model = TradeIn
#     extra = 0
#     raw_id_fields = ("vehicle",)
#     readonly_fields = ("created_at", "updated_at")


# class paymentinline(admin.TabularInline):
#     model = Payment
#     extra = 1
#     raw_id_fields = ("payment_method",)
#     readonly_fields = ("created_at", "updated_at")


# class saleadmin(admin.ModelAdmin):
#     list_display = (
#         "sale_id",
#         "customer",
#         "vehicle",
#         "employee",
#         "sale_date",
#         "base_price",
#         "discount_amount",
#         "tax_amount",
#         "total_price",
#         "commission_earned",
#         "status",
#     )
#     list_filter = ("sale_date", "employee", "status")
#     search_fields = (
#         "vehicle__vin",
#         "employee__first_name",
#         "employee__last_name",
#         "customer__first_name",
#         "customer__last_name",
#     )
#     raw_id_fields = ("customer", "lead", "employee", "vehicle")
#     readonly_fields = ("total_price", "commission_earned", "created_at", "updated_at")
#     inlines = [tradeininline, paymentinline]
#     ordering = ("-sale_date",)

# admin.site.register(Sale, saleadmin)


# class tradeinadmin(admin.ModelAdmin):
#     list_display = ("trade_in_id", "sale", "vehicle", "appraised_value", "allowance_amount", "created_at", "updated_at")
#     search_fields = ("vehicle__vin", "sale__vehicle__vin")
#     raw_id_fields = ("sale", "vehicle")
#     readonly_fields = ("created_at", "updated_at")
#     ordering = ("-trade_in_id",)

# admin.site.register(TradeIn, tradeinadmin)


# class paymentmethodadmin(admin.ModelAdmin):
#     list_display = ("method_id", "payment_method_name", "created_at", "updated_at")
#     search_fields = ("payment_method_name",)
#     readonly_fields = ("created_at", "updated_at")
#     ordering = ("method_id",)

# admin.site.register(PaymentMethod, paymentmethodadmin)


# class paymentadmin(admin.ModelAdmin):
#     list_display = (
#         "payment_id",
#         "sale",
#         "payment_date",
#         "amount",
#         "payment_method",
#         "status",
#         "transaction_reference",
#     )
#     list_filter = ("status", "payment_method", "payment_date")
#     search_fields = ("transaction_reference", "sale__vehicle__vin")
#     raw_id_fields = ("sale", "payment_method")
#     readonly_fields = ("created_at", "updated_at")
#     ordering = ("-payment_date",)

# admin.site.register(Payment, paymentadmin)


# class financeapplicationadmin(admin.ModelAdmin):
#     list_display = ("application_id", "customer", "sale", "loan_amount", "status", "created_at", "updated_at")
#     list_filter = ("status",)
#     search_fields = ("customer__first_name", "customer__last_name", "sale__vehicle__vin")
#     raw_id_fields = ("customer", "sale")
#     readonly_fields = ("created_at", "updated_at")
#     ordering = ("-application_id",)

# admin.site.register(FinanceApplication, financeapplicationadmin)