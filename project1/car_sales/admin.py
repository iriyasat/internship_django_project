from django.contrib import admin
from .models import (
    Employee_Role,
    Address,
    Employee_Status,
    Vehicle_Condition,
    Vehicle_Status,
    Lead_Status,
    Activity_Type,
    Payment_Method,
    Payment_Status,
    Service_Status,
    Maintenance_Status,
    Employee,
    Customer,
    VehicleModel,
    Vehicle,
    Lead,
    LeadActivity,
    Sale,
    TradeIn,
    Payment,
    Supplier,
    ServiceRequest,
    MaintenanceSchedule,
)

# ==========================================
# INLINES
# ==========================================

class LeadActivityInline(admin.TabularInline):
    model = LeadActivity
    extra = 1
    raw_id_fields = ("employee", "activity_type")


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 1
    raw_id_fields = ("payment_method", "status")
    readonly_fields = ("created_at", "updated_at")


class TradeInInline(admin.StackedInline):
    model = TradeIn
    extra = 0
    raw_id_fields = ("vehicle",)


# ==========================================
# LOOKUP / STATUS ADMINS
# ==========================================

@admin.register(Employee_Role)
class Employee_RoleAdmin(admin.ModelAdmin):
    list_display = ("role_id", "role_name")
    search_fields = ("role_name",)
    ordering = ("role_id",)


@admin.register(Employee_Status)
class Employee_StatusAdmin(admin.ModelAdmin):
    list_display = ("status_id", "employee_status_name")
    search_fields = ("employee_status_name",)
    ordering = ("status_id",)


@admin.register(Vehicle_Condition)
class Vehicle_ConditionAdmin(admin.ModelAdmin):
    list_display = ("condition_id", "vehicle_condition_name")
    search_fields = ("vehicle_condition_name",)
    ordering = ("condition_id",)


@admin.register(Vehicle_Status)
class Vehicle_StatusAdmin(admin.ModelAdmin):
    list_display = ("status_id", "vehicle_status_name")
    search_fields = ("vehicle_status_name",)
    ordering = ("status_id",)


@admin.register(Lead_Status)
class Lead_StatusAdmin(admin.ModelAdmin):
    list_display = ("status_id", "lead_status_name")
    search_fields = ("lead_status_name",)
    ordering = ("status_id",)


@admin.register(Activity_Type)
class Activity_TypeAdmin(admin.ModelAdmin):
    list_display = ("type_id", "activity_type_name")
    search_fields = ("activity_type_name",)
    ordering = ("type_id",)


@admin.register(Payment_Method)
class Payment_MethodAdmin(admin.ModelAdmin):
    list_display = ("method_id", "payment_method_name")
    search_fields = ("payment_method_name",)
    ordering = ("method_id",)


@admin.register(Payment_Status)
class Payment_StatusAdmin(admin.ModelAdmin):
    list_display = ("status_id", "payment_status_name")
    search_fields = ("payment_status_name",)
    ordering = ("status_id",)


@admin.register(Service_Status)
class Service_StatusAdmin(admin.ModelAdmin):
    list_display = ("status_id", "service_status_name")
    search_fields = ("service_status_name",)
    ordering = ("status_id",)


@admin.register(Maintenance_Status)
class Maintenance_StatusAdmin(admin.ModelAdmin):
    list_display = ("status_id", "maintenance_status_name")
    search_fields = ("maintenance_status_name",)
    ordering = ("status_id",)


# ==========================================
# MAIN ENTITY ADMINS
# ==========================================

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("address_id", "street_address", "city", "state", "postal_code")
    list_filter = ("state", "city")
    search_fields = ("street_address", "city", "state", "postal_code")
    ordering = ("address_id",)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        "employee_id",
        "first_name",
        "last_name",
        "email",
        "phone",
        "role",
        "status",
        "hire_date",
        "commission_rate",
    )
    list_filter = ("status", "role", "hire_date")
    search_fields = ("first_name", "last_name", "email", "phone")
    raw_id_fields = ("address", "role", "status")
    ordering = ("last_name", "first_name")


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("customer_id", "first_name", "last_name", "email", "phone")
    search_fields = ("first_name", "last_name", "email", "phone")
    raw_id_fields = ("address",)
    ordering = ("last_name", "first_name")


@admin.register(VehicleModel)
class VehicleModelAdmin(admin.ModelAdmin):
    list_display = ("model_id", "make", "model", "trim", "body_type", "fuel_type")
    list_filter = ("make", "body_type", "fuel_type")
    search_fields = ("make", "model", "trim")
    ordering = ("make", "model")


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        "vehicle_id",
        "year",
        "model",
        "vin",
        "color",
        "mileage",
        "selling_price",
        "condition",
        "status",
    )
    list_filter = ("status", "condition", "year")
    search_fields = ("vin", "model__make", "model__model", "color")
    raw_id_fields = ("model", "condition", "status")
    ordering = ("-year", "model__make")


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = (
        "lead_id",
        "customer",
        "vehicle",
        "employee",
        "source",
        "status",
        "created_at",
        "deleted_at",
    )
    list_filter = ("status", "source", "created_at")
    search_fields = (
        "customer__first_name",
        "customer__last_name",
        "employee__first_name",
        "employee__last_name",
        "vehicle__vin",
    )
    raw_id_fields = ("customer", "vehicle", "employee", "status")
    inlines = [LeadActivityInline]
    ordering = ("-created_at",)


@admin.register(LeadActivity)
class LeadActivityAdmin(admin.ModelAdmin):
    list_display = ("activity_id", "lead", "employee", "activity_type", "activity_date")
    list_filter = ("activity_type", "activity_date")
    search_fields = (
        "lead__customer__first_name",
        "lead__customer__last_name",
        "employee__first_name",
        "employee__last_name",
        "details",
    )
    raw_id_fields = ("lead", "employee", "activity_type")
    ordering = ("-activity_date",)


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = (
        "sale_id",
        "vehicle",
        "employee",
        "sale_date",
        "base_price",
        "discount_amount",
        "tax_amount",
        "total_price",
        "commission_earned",
    )
    list_filter = ("sale_date", "employee")
    search_fields = (
        "vehicle__vin",
        "employee__first_name",
        "employee__last_name",
        "lead__customer__first_name",
        "lead__customer__last_name",
    )
    raw_id_fields = ("lead", "employee", "vehicle")
    readonly_fields = ("total_price", "commission_earned", "created_at", "updated_at")
    inlines = [TradeInInline, PaymentInline]
    ordering = ("-sale_date",)


@admin.register(TradeIn)
class TradeInAdmin(admin.ModelAdmin):
    list_display = ("trade_in_id", "sale", "vehicle", "appraised_value", "allowance_amount")
    search_fields = ("vehicle__vin", "sale__vehicle__vin")
    raw_id_fields = ("sale", "vehicle")
    ordering = ("-trade_in_id",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "payment_id",
        "sale",
        "payment_date",
        "amount",
        "payment_method",
        "status",
        "transaction_reference",
    )
    list_filter = ("status", "payment_method", "payment_date")
    search_fields = ("transaction_reference", "sale__vehicle__vin")
    raw_id_fields = ("sale", "payment_method", "status")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-payment_date",)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("supplier_id", "name", "contact_person", "contact_number", "email")
    search_fields = ("name", "contact_person", "email")
    raw_id_fields = ("address",)
    ordering = ("name",)


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ("request_id", "vehicle", "supplier", "request_date", "status")
    list_filter = ("status", "request_date")
    search_fields = ("vehicle__vin", "supplier__name", "issue_description")
    raw_id_fields = ("vehicle", "supplier", "status")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-request_date",)


@admin.register(MaintenanceSchedule)
class MaintenanceScheduleAdmin(admin.ModelAdmin):
    list_display = ("schedule_id", "vehicle", "maintenance_type", "schedule_date", "status")
    list_filter = ("status", "schedule_date", "maintenance_type")
    search_fields = ("vehicle__vin", "maintenance_type")
    raw_id_fields = ("vehicle", "status")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("schedule_date",)
