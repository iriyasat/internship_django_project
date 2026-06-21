import datetime
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


# ==========================================
# LOOKUP & CONFIGURATION MODELS
# ==========================================

class Employee_Role(models.Model):
    role_id = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return self.role_name

    class Meta:
        db_table = "Roles"


class Address(models.Model):
    address_id = models.AutoField(primary_key=True)
    street_address = models.CharField(max_length=150)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    postal_code = models.CharField(max_length=20)

    def __str__(self) -> str:
        return f"{self.street_address}"

    class Meta:
        db_table = "Addresses"


class Employee_Status(models.Model):
    status_id = models.AutoField(primary_key=True)
    employee_status_name = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return self.employee_status_name

    class Meta:
        db_table = "EmployeeStatuses"
        verbose_name = "01. Employee Status"
        verbose_name_plural = "01. Employee Statuses"


class Vehicle_Condition(models.Model):
    condition_id = models.AutoField(primary_key=True)
    vehicle_condition_name = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return self.vehicle_condition_name

    class Meta:
        db_table = "VehicleConditions"
        verbose_name = "02. Vehicle Condition"
        verbose_name_plural = "02. Vehicle Conditions"


class Vehicle_Status(models.Model):
    status_id = models.AutoField(primary_key=True)
    vehicle_status_name = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return self.vehicle_status_name

    class Meta:
        db_table = "VehicleStatuses"
        verbose_name = "03. Vehicle Status"
        verbose_name_plural = "03. Vehicle Statuses"


class Lead_Status(models.Model):
    status_id = models.AutoField(primary_key=True)
    lead_status_name = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return self.lead_status_name

    class Meta:
        db_table = "LeadStatuses"
        verbose_name = "04. Lead Status"
        verbose_name_plural = "04. Lead Statuses"


class Activity_Type(models.Model):
    type_id = models.AutoField(primary_key=True)
    activity_type_name = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return self.activity_type_name

    class Meta:
        db_table = "ActivityTypes"
        verbose_name = "05. Activity Type"
        verbose_name_plural = "05. Activity Types"


class Payment_Method(models.Model):
    method_id = models.AutoField(primary_key=True)
    payment_method_name = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return self.payment_method_name

    class Meta:
        db_table = "PaymentMethods"
        verbose_name = "06. Payment Method"
        verbose_name_plural = "06. Payment Methods"


class Payment_Status(models.Model):
    status_id = models.AutoField(primary_key=True)
    payment_status_name = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return self.payment_status_name

    class Meta:
        db_table = "PaymentStatuses"
        verbose_name = "07. Payment Status"
        verbose_name_plural = "07. Payment Statuses"


class Service_Status(models.Model):
    status_id = models.AutoField(primary_key=True)
    service_status_name = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return self.service_status_name

    class Meta:
        db_table = "ServiceStatuses"
        verbose_name = "08. Service Status"
        verbose_name_plural = "08. Service Statuses"


class Maintenance_Status(models.Model):
    status_id = models.AutoField(primary_key=True)
    maintenance_status_name = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return self.maintenance_status_name

    class Meta:
        db_table = "MaintenanceStatuses"
        verbose_name = "09. Maintenance Status"
        verbose_name_plural = "09. Maintenance Statuses"


# ==========================================
# MAIN ENTITY MODELS
# ==========================================

class Employee(models.Model):
    employee_id = models.AutoField(primary_key=True)
    role = models.ForeignKey(Employee_Role, on_delete=models.CASCADE, db_column="role_id", related_name="employees")
    first_name = models.CharField(max_length=50, blank=False, null=False, verbose_name="First Name")
    last_name = models.CharField(max_length=50, blank=False, null=False, verbose_name="Last Name")
    email = models.EmailField(max_length=100, unique=True, blank=False, null=False, verbose_name="Employee Email")
    phone = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True, verbose_name="Employee DOB")
    address = models.ForeignKey(Address, on_delete=models.CASCADE, db_column="address_id", null=True, blank=True, related_name="employees_address")
    status = models.ForeignKey(Employee_Status, on_delete=models.CASCADE, db_column="status_id", related_name="employees_status")
    hire_date = models.DateField(default=timezone.now)
    terminated_date = models.DateField(blank=True, null=True)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(Decimal("0.00"))])

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __str__(self) -> str:
        return self.full_name

    class Meta:
        db_table = "Employees"
        indexes = [
            models.Index(fields=["status"], name="Employees_status_idx"),
            models.Index(fields=["employee_id"], name="Employees_employee_id_idx"),
        ]


class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=100, unique=True)
    phone = models.CharField(max_length=20)
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, db_column="address_id", null=True, blank=True, related_name="customers")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __str__(self) -> str:
        return self.full_name

    class Meta:
        db_table = "Customers"
        indexes = [
            models.Index(fields=["email"], name="Customers_email_idx"),
            models.Index(fields=["last_name"], name="Customers_lastname_idx"),
        ]


class VehicleModel(models.Model):
    model_id = models.AutoField(primary_key=True)
    make = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    trim = models.CharField(max_length=50, blank=True, null=True)
    body_type = models.CharField(max_length=30, blank=True, null=True)
    fuel_type = models.CharField(max_length=30, blank=True, null=True)

    def __str__(self) -> str:
        parts = [self.make, self.model]
        if self.trim:
            parts.append(self.trim)
        return " ".join(parts)

    class Meta:
        db_table = "VehicleModels"


class Vehicle(models.Model):
    vehicle_id = models.AutoField(primary_key=True)
    model = models.ForeignKey(VehicleModel, on_delete=models.PROTECT, db_column="model_id", related_name="vehicles")
    vin = models.CharField(max_length=17, unique=True)
    year = models.PositiveIntegerField(validators=[MinValueValidator(1900), MaxValueValidator(2100)])
    color = models.CharField(max_length=30, blank=True, null=True)
    mileage = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    acquisition_cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    condition = models.ForeignKey(Vehicle_Condition, on_delete=models.CASCADE, db_column="condition_id", related_name="vehicles_condition")
    status = models.ForeignKey(Vehicle_Status, on_delete=models.CASCADE, db_column="status_id", related_name="vehicles_status")

    def __str__(self) -> str:
        return f"{self.year} {self.model.make} {self.model.model} (VIN: {self.vin})"

    class Meta:
        db_table = "Vehicles"
        indexes = [
            models.Index(fields=["status"], name="Vehicles_status_idx"),
            models.Index(fields=["year"], name="Vehicles_year_idx"),
            models.Index(fields=["vin"], name="Vehicles_vin_idx"),
        ]


# ==========================================
# CUSTOM LEAD MANAGER & QUERYSET
# ==========================================

class LeadQuerySet(models.QuerySet):
    def active(self):
        return self.filter(deleted_at__isnull=True)

    def deleted(self):
        return self.filter(deleted_at__isnull=False)


class LeadManager(models.Manager):
    def get_queryset(self):
        return LeadQuerySet(self.model, using=self._db).active()

    def all_with_deleted(self):
        return LeadQuerySet(self.model, using=self._db)


class Lead(models.Model):
    lead_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, db_column="customer_id", related_name="leads")
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, db_column="vehicle_id", null=True, blank=True, related_name="leads")
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, db_column="employee_id", related_name="leads")
    source = models.CharField(max_length=50, blank=True, null=True)
    status = models.ForeignKey(Lead_Status, on_delete=models.CASCADE, db_column="status_id", related_name="leads_status")
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    objects = LeadManager()

    def delete(self, using=None, keep_parents=False) -> tuple[int, dict[str, int]]:
        self.deleted_at = timezone.now()
        self.save(using=using)
        return (1, {self._meta.label: 1})

    def hard_delete(self, using=None, keep_parents=False) -> tuple[int, dict[str, int]]:
        return super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        self.deleted_at = None
        self.save()

    def __str__(self) -> str:
        return f"Lead #{self.lead_id} - {self.customer.full_name} ({self.status})"

    class Meta:
        db_table = "Leads"
        indexes = [
            models.Index(fields=["status"], name="Leads_status_idx"),
            models.Index(fields=["created_at"], name="Leads_created_idx"),
        ]


class LeadActivity(models.Model):
    activity_id = models.AutoField(primary_key=True)
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, db_column="lead_id", related_name="activities")
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, db_column="employee_id", related_name="activities")
    activity_type = models.ForeignKey(Activity_Type, on_delete=models.CASCADE, db_column="type_id", related_name="activities_type")
    activity_date = models.DateTimeField(default=timezone.now)
    details = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.activity_type} on {self.activity_date.strftime('%Y-%m-%d %H:%M')} by {self.employee.full_name}"

    class Meta:
        db_table = "LeadActivities"


class Sale(models.Model):
    sale_id = models.AutoField(primary_key=True)
    lead = models.OneToOneField(Lead, on_delete=models.PROTECT, db_column="lead_id", related_name="sale")
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, db_column="employee_id", related_name="sales")
    vehicle = models.OneToOneField(Vehicle, on_delete=models.PROTECT, db_column="vehicle_id", related_name="sale")
    sale_date = models.DateTimeField(default=timezone.now)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(Decimal("0.00"))])
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(Decimal("0.00"))])
    commission_rate_applied = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_price(self) -> Decimal:
        return self.base_price - self.discount_amount + self.tax_amount

    @property
    def commission_earned(self) -> Decimal:
        net_amount = self.base_price - self.discount_amount
        return (net_amount * self.commission_rate_applied) / Decimal("100.00")

    def __str__(self) -> str:
        return f"Sale #{self.sale_id} - Vehicle VIN: {self.vehicle.vin} (${self.total_price})"

    class Meta:
        db_table = "Sales"
        indexes = [
            models.Index(fields=["sale_date"], name="Sales_date_idx"),
        ]


class TradeIn(models.Model):
    trade_in_id = models.AutoField(primary_key=True)
    sale = models.OneToOneField(Sale, on_delete=models.SET_NULL, db_column="sale_id", null=True, blank=True, related_name="trade_in")
    vehicle = models.OneToOneField(Vehicle, on_delete=models.PROTECT, db_column="vehicle_id", related_name="trade_in_record")
    appraised_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal("0.00"))])
    allowance_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal("0.00"))])
    notes = models.TextField(blank=True, null=True)

    def __str__(self) -> str:
        return f"Trade-In #{self.trade_in_id} - Value: ${self.appraised_value or 0.00}"

    class Meta:
        db_table = "TradeIns"


class Payment(models.Model):
    payment_id = models.AutoField(primary_key=True)
    sale = models.ForeignKey(Sale, on_delete=models.PROTECT, db_column="sale_id", related_name="payments")
    payment_date = models.DateTimeField(default=timezone.now)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    payment_method = models.ForeignKey(Payment_Method, on_delete=models.CASCADE, db_column="method_id", null=True, blank=True, related_name="payments_method")
    status = models.ForeignKey(Payment_Status, on_delete=models.CASCADE, db_column="status_id", related_name="payments_status")
    transaction_reference = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Payment #{self.payment_id} - Sale #{self.sale.sale_id} (${self.amount})"

    class Meta:
        db_table = "Payments"
        indexes = [
            models.Index(fields=["sale"], name="Payments_sale_idx"),
        ]


class Supplier(models.Model):
    supplier_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(max_length=100, blank=True, null=True)
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, db_column="address_id", null=True, blank=True, related_name="suppliers")

    def __str__(self) -> str:
        return self.name

    class Meta:
        db_table = "Suppliers"


class ServiceRequest(models.Model):
    request_id = models.AutoField(primary_key=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, db_column="vehicle_id", related_name="service_requests")
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, db_column="supplier_id", null=True, blank=True, related_name="service_requests")
    request_date = models.DateTimeField(default=timezone.now)
    issue_description = models.TextField(blank=True, null=True)
    status = models.ForeignKey(Service_Status, on_delete=models.CASCADE, db_column="status_id", related_name="service_requests_status")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Service #{self.request_id} - Vehicle: {self.vehicle.vin} ({self.status})"

    class Meta:
        db_table = "ServiceRequests"


class MaintenanceSchedule(models.Model):
    schedule_id = models.AutoField(primary_key=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, db_column="vehicle_id", related_name="maintenance_schedules")
    maintenance_type = models.CharField(max_length=50)
    schedule_date = models.DateTimeField()
    status = models.ForeignKey(Maintenance_Status, on_delete=models.CASCADE, db_column="status_id", related_name="maintenance_schedules_status")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.maintenance_type} for Vehicle VIN: {self.vehicle.vin} on {self.schedule_date.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        db_table = "MaintenanceSchedules"