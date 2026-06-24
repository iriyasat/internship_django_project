import datetime
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone


# ==========================================
# 1. Geography
# ==========================================

class Country(models.Model):
    country_id = models.AutoField(primary_key=True)
    country_name = models.CharField(max_length=100, unique=True, verbose_name="Country Name")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self) -> str:
        return self.country_name

    class Meta:
        db_table = "Countries"
        verbose_name = "Country"
        verbose_name_plural = "Countries"


class City(models.Model):
    city_id = models.AutoField(primary_key=True)
    city_name = models.CharField(max_length=100, verbose_name="City Name")
    country = models.ForeignKey(Country, on_delete=models.CASCADE, db_column="country_id", related_name="cities", verbose_name="Country")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self) -> str:
        return f"{self.city_name}, {self.country.country_name}"

    class Meta:
        db_table = "Cities"
        verbose_name = "City"
        verbose_name_plural = "Cities"
        unique_together = (('city_name', 'country'),)


# ==========================================
# 2. Employees & HR
# ==========================================

class EmployeeRole(models.Model):
    role_id = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=50, unique=True, verbose_name="Role Name")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self) -> str:
        return self.role_name

    class Meta:
        db_table = "Roles"
        verbose_name = "Employee Role"
        verbose_name_plural = "Employee Roles"


class EmployeeStatus(models.Model):
    status_id = models.AutoField(primary_key=True)
    status_name = models.CharField(max_length=50, unique=True, verbose_name="Status Name")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self) -> str:
        return self.status_name

    class Meta:
        db_table = "EmployeeStatuses"
        verbose_name = "Employee Status"
        verbose_name_plural = "Employee Statuses"


class Employee(models.Model):
    employee_id = models.AutoField(primary_key=True)
    role = models.ForeignKey(EmployeeRole, on_delete=models.CASCADE, db_column="role_id", related_name="employees", verbose_name="Role")
    first_name = models.CharField(max_length=50, blank=False, null=False, verbose_name="First Name")
    last_name = models.CharField(max_length=50, blank=False, null=False, verbose_name="Last Name")
    email = models.EmailField(max_length=100, unique=True, blank=False, null=False, verbose_name="Employee Email")
    emp_phone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+8801[3-9]\d{8}$',
                message="Phone number must be in the format: '+8801XXXXXXXXX' (14 characters)."
            )
        ],
        verbose_name="Phone Number"
    )
    date_of_birth = models.DateField(blank=True, null=True, verbose_name="Employee DOB")
    emp_address = models.CharField(max_length=150, null=True, blank=True, verbose_name="Employee Address")
    emp_city = models.ForeignKey(City, on_delete=models.SET_NULL, db_column="city_id", null=True, blank=True, related_name="employees", verbose_name="Employee City")
    emp_country = models.ForeignKey(Country, on_delete=models.SET_NULL, db_column="country_id", null=True, blank=True, related_name="employees", verbose_name="Employee Country")
    status = models.ForeignKey(EmployeeStatus, on_delete=models.CASCADE, db_column="status_id", related_name="employees", verbose_name="Status")
    hire_date = models.DateField(default=timezone.now, verbose_name="Hire Date")
    leave_start_date = models.DateField(blank=True, null=True, verbose_name="Leave Start Date")
    leave_end_date = models.DateField(blank=True, null=True, verbose_name="Leave End Date")
    assigned_task = models.CharField(max_length=255, blank=True, null=True, verbose_name="Assigned Task")
    terminated_date = models.DateField(blank=True, null=True, verbose_name="Terminated Date")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def clean(self):
        super().clean()
        if self.terminated_date and self.hire_date and self.terminated_date < self.hire_date:
            raise ValidationError({"terminated_date": "Terminated date cannot be before hire date."})
        if self.leave_start_date and self.leave_end_date and self.leave_end_date < self.leave_start_date:
            raise ValidationError({"leave_end_date": "Leave end date cannot be before leave start date."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.full_name

    class Meta:
        db_table = "Employees"
        verbose_name = "Employee"
        verbose_name_plural = "Employees"
        indexes = [
            models.Index(fields=["status"], name="Employees_status_idx"),
        ]


class EmployeeTarget(models.Model):
    target_id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, db_column="employee_id", related_name="targets", verbose_name="Employee")
    target_goal = models.PositiveIntegerField(verbose_name="Target Goal (Products to Sell)")
    commission_percentage = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("100.00"))], verbose_name="Commission Percentage")
    start_date = models.DateField(verbose_name="Start Date")
    end_date = models.DateField(verbose_name="End Date")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def clean(self):
        super().clean()
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "End date cannot be before start date."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Target for {self.employee.full_name}: {self.target_goal} products ({self.commission_percentage}%)"

    class Meta:
        db_table = "EmployeeTargets"
        verbose_name = "Employee Target"
        verbose_name_plural = "Employee Targets"


# ==========================================
# 3. Customers
# ==========================================

class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=50, verbose_name="First Name")
    last_name = models.CharField(max_length=50, verbose_name="Last Name")
    email = models.EmailField(max_length=100, unique=True, verbose_name="Email Address")
    customer_phone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+8801[3-9]\d{8}$',
                message="Phone number must be in the format: '+8801XXXXXXXXX' (14 characters)."
            )
        ],
        verbose_name="Phone Number"
    )
    customer_address = models.CharField(max_length=150, null=True, blank=True, verbose_name="Customer Address")
    customer_city = models.ForeignKey(City, on_delete=models.SET_NULL, db_column="city_id", null=True, blank=True, related_name="customers", verbose_name="Customer City")
    customer_country = models.ForeignKey(Country, on_delete=models.SET_NULL, db_column="country_id", null=True, blank=True, related_name="customers", verbose_name="Customer Country")
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

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


# ==========================================
# 4. Inventory (Vehicles & Models)
# ==========================================

class Manufacturer(models.Model):
    manufacturer_id = models.AutoField(primary_key=True)
    manufacturer_name = models.CharField(max_length=50, unique=True, verbose_name="Manufacturer Name")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self) -> str:
        return self.manufacturer_name

    class Meta:
        db_table = "Manufacturers"
        verbose_name = "Manufacturer"
        verbose_name_plural = "Manufacturers"


class VehicleModel(models.Model):
    model_id = models.AutoField(primary_key=True)
    manufacturer = models.ForeignKey(
        Manufacturer,
        on_delete=models.CASCADE,
        db_column="manufacturer_id",
        related_name="vehicle_models",
        verbose_name="Manufacturer"
    )
    vehicle_model = models.CharField(max_length=50, verbose_name="Vehicle Model")
    trim = models.CharField(max_length=50, blank=True, null=True, verbose_name="Trim")
    body_type = models.CharField(max_length=30, blank=True, null=True, verbose_name="Body Type")
    fuel_type = models.CharField(max_length=30, blank=True, null=True, verbose_name="Fuel Type")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self) -> str:
        parts = [self.manufacturer.manufacturer_name, self.vehicle_model]
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
    model = models.ForeignKey(VehicleModel, on_delete=models.CASCADE, db_column="model_id", related_name="vehicles", verbose_name="Vehicle Model")
    vin = models.CharField(
        max_length=17,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[A-HJ-NPR-Z0-9]{17}$',
                message='Invalid VIN format'
            )
        ],
        verbose_name="VIN"
    )
    year = models.PositiveIntegerField(validators=[MinValueValidator(1900), MaxValueValidator(2100)], verbose_name="Year")
    color = models.CharField(max_length=30, blank=True, null=True, verbose_name="Color")
    mileage = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Mileage")
    acquisition_cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))], verbose_name="Acquisition Cost")
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))], verbose_name="Selling Price")
    condition = models.CharField(max_length=20, choices=Condition.choices, verbose_name="Condition")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE, verbose_name="Status")
    date_acquired = models.DateField(verbose_name="Date Acquired")
    date_listed = models.DateField(null=True, blank=True, verbose_name="Date Listed")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def clean(self):
        super().clean()
        if self.date_acquired and self.date_listed and self.date_listed < self.date_acquired:
            raise ValidationError({"date_listed": "Date listed cannot be before date acquired."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.year} {self.model.manufacturer.manufacturer_name} {self.model.vehicle_model} (VIN: {self.vin})"

    class Meta:
        db_table = "Vehicles"
        verbose_name = "Vehicle"
        verbose_name_plural = "Vehicles"
        indexes = [
            models.Index(fields=["status"], name="Vehicles_status_idx"),
            models.Index(fields=["year"], name="Vehicles_year_idx"),
        ]


# class VehicleImage(models.Model):
#     image_id = models.AutoField(primary_key=True)
#     vehicle = models.ForeignKey(
#         Vehicle,
#         on_delete=models.CASCADE,
#         db_column="vehicle_id",
#         related_name="images",
#         verbose_name="Vehicle"
#     )
#     image = models.ImageField(
#         upload_to="vehicles/",
#         verbose_name="Image"
#     )
#     is_primary = models.BooleanField(
#         default=False,
#         verbose_name="Is Primary"
#     )

#     def __str__(self) -> str:
#         return f"Image #{self.image_id} for Vehicle VIN: {self.vehicle.vin}"

#     class Meta:
#         db_table = "VehicleImages"
#         verbose_name = "Vehicle Image"
#         verbose_name_plural = "Vehicle Images"


class VehicleService(models.Model):
    service_id = models.AutoField(primary_key=True)
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        db_column="vehicle_id",
        related_name="services",
        verbose_name="Vehicle"
    )
    service_date = models.DateField(verbose_name="Service Date")
    description = models.TextField(verbose_name="Description")
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Cost"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self) -> str:
        return f"Service #{self.service_id} for Vehicle VIN: {self.vehicle.vin} (${self.cost})"

    class Meta:
        db_table = "VehicleServices"
        verbose_name = "Vehicle Service"
        verbose_name_plural = "Vehicle Services"


# ==========================================
# 5. Leads & CRM
# ==========================================

class LeadSource(models.Model):
    source_id = models.AutoField(primary_key=True)
    source_name = models.CharField(max_length=50, unique=True, verbose_name="Source Name")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self) -> str:
        return self.source_name

    class Meta:
        db_table = "LeadSources"
        verbose_name = "Lead Source"
        verbose_name_plural = "Lead Sources"


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
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, db_column="customer_id", related_name="leads", verbose_name="Customer")
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, db_column="vehicle_id", null=True, blank=True, related_name="leads", verbose_name="Vehicle")
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, db_column="employee_id", related_name="leads", verbose_name="Assigned Employee")
    source = models.ForeignKey(LeadSource, on_delete=models.SET_NULL, db_column="source_id", null=True, blank=True, related_name="leads", verbose_name="Source")
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


class LeadActivityType(models.Model):
    lead_activity_type_id = models.AutoField(primary_key=True)
    lead_activity_type_name = models.CharField(max_length=50, unique=True, verbose_name="Lead Activity Type Name")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self) -> str:
        return self.lead_activity_type_name

    class Meta:
        db_table = "LeadActivityTypes"
        verbose_name = "Lead Activity Type"
        verbose_name_plural = "Lead Activity Types"


class LeadActivity(models.Model):
    activity_id = models.AutoField(primary_key=True)
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, db_column="lead_id", related_name="activities", verbose_name="Lead")
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, db_column="employee_id", related_name="activities", verbose_name="Employee")
    activity_type = models.ForeignKey(LeadActivityType, on_delete=models.CASCADE, db_column="lead_activity_type_id", related_name="lead_activities", verbose_name="Lead Activity Type")
    activity_date = models.DateTimeField(default=timezone.now, verbose_name="Activity Date")
    details = models.TextField(blank=True, null=True, verbose_name="Details")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self) -> str:
        return f"{self.activity_type.lead_activity_type_name} on {self.activity_date.strftime('%Y-%m-%d %H:%M')} by {self.employee.full_name}"

    class Meta:
        db_table = "LeadActivities"
        verbose_name = "Lead Activity"
        verbose_name_plural = "Lead Activities"


# ==========================================
# 6. Sales, Payments & Financing
# ==========================================

class Sale(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PENDING = "PENDING", "Pending"
        FINANCING = "FINANCING", "Financing"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"
        REFUNDED = "REFUNDED", "Refunded"

    sale_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, db_column="customer_id", related_name="sales", verbose_name="Customer")
    lead = models.OneToOneField(Lead, on_delete=models.SET_NULL, db_column="lead_id", null=True, blank=True, related_name="sale", verbose_name="Lead")
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, db_column="employee_id", related_name="sales", verbose_name="Employee")
    vehicle = models.OneToOneField(Vehicle, on_delete=models.CASCADE, db_column="vehicle_id", related_name="sale", verbose_name="Vehicle")
    sale_date = models.DateTimeField(default=timezone.now, verbose_name="Sale Date")
    base_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))], verbose_name="Base Price")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(Decimal("0.00"))], verbose_name="Discount Amount")
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(Decimal("0.00"))], verbose_name="Tax Amount")
    commission_rate_applied = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))], verbose_name="Commission Rate Applied")
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal("0.00"))], verbose_name="Commission Amount")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, verbose_name="Status")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    @property
    def total_price(self) -> Decimal:
        return self.base_price - self.discount_amount + self.tax_amount

    @property
    def commission_earned(self) -> Decimal:
        if self.commission_amount is not None:
            return self.commission_amount
        net_amount = self.base_price - self.discount_amount
        return (net_amount * self.commission_rate_applied) / Decimal("100.00")

    def clean_fields(self, exclude=None):
        if not hasattr(self, 'customer') or self.customer is None:
            if self.lead and self.lead.customer:
                self.customer = self.lead.customer
        super().clean_fields(exclude=exclude)

    def clean(self):
        super().clean()
        if not hasattr(self, 'customer') or self.customer is None:
            if self.lead and self.lead.customer:
                self.customer = self.lead.customer
        
        if self.base_price is not None and self.discount_amount is not None and self.commission_rate_applied is not None:
            net_amount = self.base_price - self.discount_amount
            calculated_comm = (net_amount * self.commission_rate_applied) / Decimal("100.00")
            if self.commission_amount is None:
                self.commission_amount = calculated_comm

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

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
    vehicle = models.OneToOneField(Vehicle, on_delete=models.CASCADE, db_column="vehicle_id", related_name="trade_in", verbose_name="Vehicle")
    appraised_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal("0.00"))], verbose_name="Appraised Value")
    allowance_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal("0.00"))], verbose_name="Allowance Amount")
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self) -> str:
        return f"Trade-In #{self.trade_in_id} - Value: ${self.appraised_value or 0.00}"

    class Meta:
        db_table = "TradeIns"
        verbose_name = "Trade-In"
        verbose_name_plural = "Trade-Ins"


class PaymentMethod(models.Model):
    method_id = models.AutoField(primary_key=True)
    payment_method_name = models.CharField(max_length=50, unique=True, verbose_name="Payment Method Name")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self) -> str:
        return self.payment_method_name

    class Meta:
        db_table = "PaymentMethods"
        verbose_name = "Payment Method"
        verbose_name_plural = "Payment Methods"


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"
        REFUNDED = "REFUNDED", "Refunded"

    payment_id = models.AutoField(primary_key=True)
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, db_column="sale_id", related_name="payments", verbose_name="Sale")
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


class FinanceApplication(models.Model):
    application_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        db_column="customer_id",
        related_name="finance_applications",
        verbose_name="Customer"
    )
    sale = models.OneToOneField(
        Sale,
        on_delete=models.CASCADE,
        db_column="sale_id",
        related_name="finance_application",
        verbose_name="Sale"
    )
    loan_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Loan Amount"
    )
    status = models.CharField(
        max_length=20,
        verbose_name="Status"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self) -> str:
        return f"Finance Application #{self.application_id} - Loan: ${self.loan_amount} ({self.status})"

    class Meta:
        db_table = "FinanceApplications"
        verbose_name = "Finance Application"
        verbose_name_plural = "Finance Applications"