import datetime
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


# ==========================================
# LOOKUP & CONFIGURATION MODELS
# ==========================================

class EmployeeRole(models.Model):
    role_id = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=50, unique=True, verbose_name="Role Name")

    def __str__(self) -> str:
        return self.role_name

    class Meta:
        db_table = "Roles"
        verbose_name = "Employee Role"
        verbose_name_plural = "Employee Roles"


class Address(models.Model):
    address_id = models.AutoField(primary_key=True)
    street_address = models.CharField(max_length=150, verbose_name="Street Address")
    city = models.CharField(max_length=50, verbose_name="City")
    state = models.CharField(max_length=50, verbose_name="State")
    postal_code = models.CharField(max_length=20, verbose_name="Postal Code")

    def __str__(self) -> str:
        return f"{self.street_address}"

    class Meta:
        db_table = "Addresses"
        verbose_name = "Address"
        verbose_name_plural = "Addresses"


class PaymentMethod(models.Model):
    method_id = models.AutoField(primary_key=True)
    payment_method_name = models.CharField(max_length=50, unique=True, verbose_name="Payment Method Name")

    def __str__(self) -> str:
        return self.payment_method_name

    class Meta:
        db_table = "PaymentMethods"
        verbose_name = "Payment Method"
        verbose_name_plural = "Payment Methods"


# ==========================================
# MAIN ENTITY MODELS
# ==========================================

class Employee(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        ON_LEAVE = "ON_LEAVE", "On Leave"
        TERMINATED = "TERMINATED", "Terminated"

    employee_id = models.AutoField(primary_key=True)
    role = models.ForeignKey(EmployeeRole, on_delete=models.PROTECT, db_column="role_id", related_name="employees", verbose_name="Role")
    first_name = models.CharField(max_length=50, blank=False, null=False, verbose_name="First Name")
    last_name = models.CharField(max_length=50, blank=False, null=False, verbose_name="Last Name")
    email = models.EmailField(max_length=100, unique=True, blank=False, null=False, verbose_name="Employee Email")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Phone Number")
    date_of_birth = models.DateField(blank=True, null=True, verbose_name="Employee DOB")
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, db_column="address_id", null=True, blank=True, related_name="employees", verbose_name="Address")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, verbose_name="Status")
    hire_date = models.DateField(default=timezone.now, verbose_name="Hire Date")
    terminated_date = models.DateField(blank=True, null=True, verbose_name="Terminated Date")
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(Decimal("0.00"))], verbose_name="Commission Rate")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __str__(self) -> str:
        return self.full_name

    class Meta:
        db_table = "Employees"
        verbose_name = "Employee"
        verbose_name_plural = "Employees"
        indexes = [
            models.Index(fields=["status"], name="Employees_status_idx"),
        ]


class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=50, verbose_name="First Name")
    last_name = models.CharField(max_length=50, verbose_name="Last Name")
    email = models.EmailField(max_length=100, unique=True, verbose_name="Email Address")
    phone = models.CharField(max_length=20, verbose_name="Phone Number")
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, db_column="address_id", null=True, blank=True, related_name="customers", verbose_name="Address")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __str__(self) -> str:
        return self.full_name

    class Meta:
        db_table = "Customers"
        verbose_name = "Customer"
        verbose_name_plural = "Customers"
        indexes = [
            models.Index(fields=["last_name"], name="Customers_lastname_idx"),
        ]


class VehicleModel(models.Model):
    model_id = models.AutoField(primary_key=True)
    make = models.CharField(max_length=50, verbose_name="Make")
    model = models.CharField(max_length=50, verbose_name="Model")
    trim = models.CharField(max_length=50, blank=True, null=True, verbose_name="Trim")
    body_type = models.CharField(max_length=30, blank=True, null=True, verbose_name="Body Type")
    fuel_type = models.CharField(max_length=30, blank=True, null=True, verbose_name="Fuel Type")

    def __str__(self) -> str:
        parts = [self.make, self.model]
        if self.trim:
            parts.append(self.trim)
        return " ".join(parts)

    class Meta:
        db_table = "VehicleModels"
        verbose_name = "Vehicle Model"
        verbose_name_plural = "Vehicle Models"


class Vehicle(models.Model):
    class Condition(models.TextChoices):
        NEW = "NEW", "New"
        USED = "USED", "Used"
        CERTIFIED_PRE_OWNED = "CPO", "Certified Pre-Owned"

    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        RESERVED = "RESERVED", "Reserved"
        SOLD = "SOLD", "Sold"
        IN_SERVICE = "IN_SERVICE", "In Service"

    vehicle_id = models.AutoField(primary_key=True)
    model = models.ForeignKey(VehicleModel, on_delete=models.PROTECT, db_column="model_id", related_name="vehicles", verbose_name="Vehicle Model")
    vin = models.CharField(max_length=17, unique=True, verbose_name="VIN")
    year = models.PositiveIntegerField(validators=[MinValueValidator(1900), MaxValueValidator(2100)], verbose_name="Year")
    color = models.CharField(max_length=30, blank=True, null=True, verbose_name="Color")
    mileage = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Mileage")
    acquisition_cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))], verbose_name="Acquisition Cost")
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))], verbose_name="Selling Price")
    condition = models.CharField(max_length=20, choices=Condition.choices, verbose_name="Condition")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE, verbose_name="Status")

    def __str__(self) -> str:
        return f"{self.year} {self.model.make} {self.model.model} (VIN: {self.vin})"

    class Meta:
        db_table = "Vehicles"
        verbose_name = "Vehicle"
        verbose_name_plural = "Vehicles"
        indexes = [
            models.Index(fields=["status"], name="Vehicles_status_idx"),
            models.Index(fields=["year"], name="Vehicles_year_idx"),
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
    class Status(models.TextChoices):
        NEW = "NEW", "New"
        CONTACTED = "CONTACTED", "Contacted"
        QUALIFIED = "QUALIFIED", "Qualified"
        NEGOTIATING = "NEGOTIATING", "Negotiating"
        WON = "WON", "Won"
        LOST = "LOST", "Lost"

    lead_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, db_column="customer_id", related_name="leads", verbose_name="Customer")
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, db_column="vehicle_id", null=True, blank=True, related_name="leads", verbose_name="Vehicle")
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, db_column="employee_id", related_name="leads", verbose_name="Assigned Employee")
    source = models.CharField(max_length=50, blank=True, null=True, verbose_name="Source")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW, verbose_name="Status")
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    deleted_at = models.DateTimeField(blank=True, null=True, verbose_name="Deleted At")

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
        verbose_name = "Lead"
        verbose_name_plural = "Leads"
        indexes = [
            models.Index(fields=["status"], name="Leads_status_idx"),
            models.Index(fields=["created_at"], name="Leads_created_idx"),
        ]


class LeadActivity(models.Model):
    class ActivityType(models.TextChoices):
        CALL = "CALL", "Call"
        EMAIL = "EMAIL", "Email"
        TEST_DRIVE = "TEST_DRIVE", "Test Drive"
        MEETING = "MEETING", "Meeting"
        FOLLOW_UP = "FOLLOW_UP", "Follow-Up"
        NOTE = "NOTE", "Note"

    activity_id = models.AutoField(primary_key=True)
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, db_column="lead_id", related_name="activities", verbose_name="Lead")
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, db_column="employee_id", related_name="activities", verbose_name="Employee")
    activity_type = models.CharField(max_length=20, choices=ActivityType.choices, verbose_name="Activity Type")
    activity_date = models.DateTimeField(default=timezone.now, verbose_name="Activity Date")
    details = models.TextField(blank=True, null=True, verbose_name="Details")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    def __str__(self) -> str:
        return f"{self.activity_type} on {self.activity_date.strftime('%Y-%m-%d %H:%M')} by {self.employee.full_name}"

    class Meta:
        db_table = "LeadActivities"
        verbose_name = "Lead Activity"
        verbose_name_plural = "Lead Activities"


class Sale(models.Model):
    sale_id = models.AutoField(primary_key=True)
    lead = models.OneToOneField(Lead, on_delete=models.SET_NULL, db_column="lead_id", null=True, blank=True, related_name="sale", verbose_name="Lead")
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, db_column="employee_id", related_name="sales", verbose_name="Employee")
    vehicle = models.OneToOneField(Vehicle, on_delete=models.PROTECT, db_column="vehicle_id", related_name="sale", verbose_name="Vehicle")
    sale_date = models.DateTimeField(default=timezone.now, verbose_name="Sale Date")
    base_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))], verbose_name="Base Price")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(Decimal("0.00"))], verbose_name="Discount Amount")
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(Decimal("0.00"))], verbose_name="Tax Amount")
    commission_rate_applied = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))], verbose_name="Commission Rate Applied")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

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
        verbose_name = "Sale"
        verbose_name_plural = "Sales"
        indexes = [
            models.Index(fields=["sale_date"], name="Sales_date_idx"),
        ]


class TradeIn(models.Model):
    trade_in_id = models.AutoField(primary_key=True)
    sale = models.OneToOneField(Sale, on_delete=models.SET_NULL, db_column="sale_id", null=True, blank=True, related_name="trade_in", verbose_name="Sale")
    vehicle = models.OneToOneField(Vehicle, on_delete=models.PROTECT, db_column="vehicle_id", related_name="trade_in", verbose_name="Vehicle")
    appraised_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal("0.00"))], verbose_name="Appraised Value")
    allowance_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal("0.00"))], verbose_name="Allowance Amount")
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")

    def __str__(self) -> str:
        return f"Trade-In #{self.trade_in_id} - Value: ${self.appraised_value or 0.00}"

    class Meta:
        db_table = "TradeIns"
        verbose_name = "Trade-In"
        verbose_name_plural = "Trade-Ins"


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"
        REFUNDED = "REFUNDED", "Refunded"

    payment_id = models.AutoField(primary_key=True)
    sale = models.ForeignKey(Sale, on_delete=models.PROTECT, db_column="sale_id", related_name="payments", verbose_name="Sale")
    payment_date = models.DateTimeField(default=timezone.now, verbose_name="Payment Date")
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))], verbose_name="Amount")
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, db_column="method_id", null=True, blank=True, related_name="payments", verbose_name="Payment Method")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, verbose_name="Payment Status")
    transaction_reference = models.CharField(max_length=100, blank=True, null=True, verbose_name="Transaction Reference")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self) -> str:
        return f"Payment #{self.payment_id} - Sale #{self.sale.sale_id} (${self.amount})"

    class Meta:
        db_table = "Payments"
        verbose_name = "Payment"
        verbose_name_plural = "Payments"