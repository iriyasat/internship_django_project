from django.contrib import admin
from .models import (
    City,
    Country,
    Customer,
    Employee,
    EmployeeRole,
    EmployeeStatus,
    EmployeeTarget,
    Lead,
    LeadActivity,
    LeadActivityType,
    Payment,
    PaymentMethod,
    Sale,
    TradeIn,
    Vehicle,
    VehicleModel,
    LeadSource,
    VehicleImage,
    VehicleService,
    FinanceApplication,
    Manufacturer,
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
    raw_id_fields = ("payment_method",)
    readonly_fields = ("created_at", "updated_at")


class TradeInInline(admin.StackedInline):
    model = TradeIn
    extra = 0
    raw_id_fields = ("vehicle",)


# ==========================================
# LOOKUP / STATUS ADMINS
# ==========================================

@admin.register(EmployeeRole)
class EmployeeRoleAdmin(admin.ModelAdmin):
    list_display = ("role_id", "role_name")
    search_fields = ("role_name",)
    ordering = ("role_id",)


@admin.register(EmployeeStatus)
class EmployeeStatusAdmin(admin.ModelAdmin):
    list_display = ("status_id", "status_name")
    search_fields = ("status_name",)
    ordering = ("status_id",)


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ("method_id", "payment_method_name")
    search_fields = ("payment_method_name",)
    ordering = ("method_id",)


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("country_id", "country_name")
    search_fields = ("country_name",)
    ordering = ("country_id",)


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("city_id", "city_name", "country")
    list_filter = ("country",)
    search_fields = ("city_name", "country__country_name")
    ordering = ("city_id",)


@admin.register(LeadActivityType)
class LeadActivityTypeAdmin(admin.ModelAdmin):
    list_display = ("lead_activity_type_id", "lead_activity_type_name")
    search_fields = ("lead_activity_type_name",)
    ordering = ("lead_activity_type_id",)


@admin.register(LeadSource)
class LeadSourceAdmin(admin.ModelAdmin):
    list_display = ("source_id", "source_name")
    search_fields = ("source_name",)
    ordering = ("source_id",)



@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ("manufacturer_id", "manufacturer_name")
    search_fields = ("manufacturer_name",)
    ordering = ("manufacturer_id",)


# ==========================================
# MAIN ENTITY ADMINS
# ==========================================


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
        "assigned_task",
    )
    list_filter = ("status", "role", "hire_date")
    search_fields = ("first_name", "last_name", "email", "phone")
    raw_id_fields = ("emp_city", "emp_country", "role", "status")
    ordering = ("last_name", "first_name")


@admin.register(EmployeeTarget)
class EmployeeTargetAdmin(admin.ModelAdmin):
    list_display = ("target_id", "employee", "target_goal", "commission_percentage", "start_date", "end_date")
    list_filter = ("employee", "start_date", "end_date")
    search_fields = ("employee__first_name", "employee__last_name")
    raw_id_fields = ("employee",)
    ordering = ("target_id",)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("customer_id", "first_name", "last_name", "email", "phone")
    search_fields = ("first_name", "last_name", "email", "phone")
    raw_id_fields = ("customer_city", "customer_country")
    ordering = ("last_name", "first_name")


@admin.register(VehicleModel)
class VehicleModelAdmin(admin.ModelAdmin):
    list_display = ("model_id", "manufacturer", "model", "trim", "body_type", "fuel_type")
    list_filter = ("manufacturer", "body_type", "fuel_type")
    search_fields = ("manufacturer__manufacturer_name", "model", "trim")
    raw_id_fields = ("manufacturer",)
    ordering = ("manufacturer__manufacturer_name", "model")


class VehicleImageInline(admin.TabularInline):
    model = VehicleImage
    extra = 1


class VehicleServiceInline(admin.TabularInline):
    model = VehicleService
    extra = 1


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
        "date_acquired",
        "date_listed",
    )
    list_filter = ("status", "condition", "year", "date_acquired", "date_listed")
    search_fields = ("vin", "model__manufacturer__manufacturer_name", "model__model", "color")
    raw_id_fields = ("model",)
    inlines = [VehicleImageInline, VehicleServiceInline]
    ordering = ("-year", "model__manufacturer__manufacturer_name")


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
    raw_id_fields = ("customer", "vehicle", "employee")
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
        "customer",
        "vehicle",
        "employee",
        "sale_date",
        "base_price",
        "discount_amount",
        "tax_amount",
        "total_price",
        "commission_earned",
        "status",
    )
    list_filter = ("sale_date", "employee", "status")
    search_fields = (
        "vehicle__vin",
        "employee__first_name",
        "employee__last_name",
        "customer__first_name",
        "customer__last_name",
    )
    raw_id_fields = ("customer", "lead", "employee", "vehicle")
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
    raw_id_fields = ("sale", "payment_method")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-payment_date",)


@admin.register(VehicleImage)
class VehicleImageAdmin(admin.ModelAdmin):
    list_display = ("image_id", "vehicle", "is_primary")
    list_filter = ("is_primary",)
    search_fields = ("vehicle__vin",)
    raw_id_fields = ("vehicle",)
    ordering = ("-image_id",)


@admin.register(VehicleService)
class VehicleServiceAdmin(admin.ModelAdmin):
    list_display = ("service_id", "vehicle", "service_date", "cost")
    list_filter = ("service_date",)
    search_fields = ("vehicle__vin", "description")
    raw_id_fields = ("vehicle",)
    ordering = ("-service_date",)


@admin.register(FinanceApplication)
class FinanceApplicationAdmin(admin.ModelAdmin):
    list_display = ("application_id", "customer", "sale", "loan_amount", "status")
    list_filter = ("status",)
    search_fields = ("customer__first_name", "customer__last_name", "sale__vehicle__vin")
    raw_id_fields = ("customer", "sale")
    ordering = ("-application_id",)