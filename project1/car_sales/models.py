from django.db import models
import datetime

class TruncatedDateTimeField(models.DateTimeField):
    """
    A custom DateTimeField that truncates seconds and microseconds to zero,
    and maps to standard 'datetime' without fractional precision in MySQL.
    """
    def db_type(self, connection):
        if connection.settings_dict['ENGINE'] == 'django.db.backends.mysql':
            return 'datetime'
        return super().db_type(connection)

    def pre_save(self, model_instance, add):
        value = super().pre_save(model_instance, add)
        if value and isinstance(value, datetime.datetime):
            value = value.replace(second=0, microsecond=0)
            setattr(model_instance, self.attname, value)
        return value

class Country(models.Model):
    country_id = models.AutoField(primary_key=True, verbose_name="Country ID")
    country_name = models.CharField(max_length=100, unique=True, verbose_name="Country Name")
    created_at = TruncatedDateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = TruncatedDateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self):
        return self.country_name

    class Meta:
        db_table = 'country'
        verbose_name_plural = 'countries'


class City(models.Model):
    city_id = models.AutoField(primary_key=True, verbose_name="City ID")
    city_name = models.CharField(max_length=100, verbose_name="City Name")
    country = models.ForeignKey(Country, on_delete=models.CASCADE, db_column='country_id', related_name='cities', verbose_name="Country")
    created_at = TruncatedDateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = TruncatedDateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self):
        return f"{self.city_name}, {self.country.country_name}"

    class Meta:
        db_table = 'city'
        verbose_name_plural = 'cities'


class Store(models.Model):
    store_id = models.AutoField(primary_key=True, verbose_name="Store ID")
    store_name = models.CharField(max_length=150, verbose_name="Store Name")
    store_code = models.CharField(max_length=20, unique=True, verbose_name="Store Code")
    city = models.ForeignKey(City, on_delete=models.CASCADE, db_column='city_id', related_name='stores', verbose_name="City")
    country = models.ForeignKey(Country, on_delete=models.CASCADE, db_column='country_id', related_name='stores', verbose_name="Country")
    address = models.CharField(max_length=255, verbose_name="Address")
    created_at = TruncatedDateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = TruncatedDateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self):
        return f"{self.store_name} ({self.store_code})"

    class Meta:
        db_table = 'store'


class EmployeeRole(models.Model):
    role_id = models.AutoField(primary_key=True, verbose_name="Role ID")
    role_name = models.CharField(max_length=100, unique=True, verbose_name="Role Name")
    created_at = TruncatedDateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = TruncatedDateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self):
        return self.role_name

    class Meta:
        db_table = 'employee_role'


class EmployeeStatus(models.Model):
    status_id = models.AutoField(primary_key=True, verbose_name="Status ID")
    status = models.CharField(max_length=50, unique=True, verbose_name="Status Name")
    created_at = TruncatedDateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = TruncatedDateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self):
        return self.status

    class Meta:
        db_table = 'employee_status'
        verbose_name_plural = 'employee statuses'


class Employee(models.Model):
    employee_id = models.AutoField(primary_key=True, verbose_name="Employee ID")
    first_name = models.CharField(max_length=100, verbose_name="First Name")
    last_name = models.CharField(max_length=100, verbose_name="Last Name")
    date_of_joining = models.DateField(verbose_name="Date of Joining")
    employee_addr = models.CharField(max_length=255, verbose_name="Employee Address")
    employee_role = models.ForeignKey(EmployeeRole, on_delete=models.CASCADE, db_column='employee_role', related_name='employees', verbose_name="Employee Role")
    status = models.ForeignKey(EmployeeStatus, on_delete=models.CASCADE, db_column='status', related_name='employees', verbose_name="Employee Status")
    store = models.ForeignKey(Store, on_delete=models.CASCADE, db_column='store_id', related_name='employees', verbose_name="Store")
    city = models.ForeignKey(City, on_delete=models.CASCADE, db_column='city_id', related_name='employees', verbose_name="City")
    country = models.ForeignKey(Country, on_delete=models.CASCADE, db_column='country_id', related_name='employees', verbose_name="Country")
    password = models.CharField(max_length=25, blank = False, null = False, verbose_name="Password", default='CAr$@lse2014')
    created_at = TruncatedDateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = TruncatedDateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        db_table = 'employee'


class IndustryInfo(models.Model):
    make_id = models.AutoField(primary_key=True, verbose_name="Make ID")
    make_name = models.CharField(max_length=100, unique=True, verbose_name="Make Name")
    created_at = TruncatedDateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = TruncatedDateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self):
        return self.make_name

    class Meta:
        db_table = 'industry_info'
        verbose_name_plural = 'industry info'


class VehicleInfo(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="Vehicle ID")
    vehicle_model = models.CharField(max_length=150, verbose_name="Vehicle Model")
    make = models.ForeignKey(IndustryInfo, on_delete=models.CASCADE, db_column='make_id', related_name='vehicles', verbose_name="Make")
    mmr = models.IntegerField(verbose_name="MMR (Manheim Market Report)")
    trim = models.CharField(max_length=100, null=True, blank=True, verbose_name="Trim")
    body = models.CharField(max_length=100, null=True, blank=True, verbose_name="Body")
    transmission = models.CharField(max_length=50, null=True, blank=True, verbose_name="Transmission")
    vin = models.CharField(max_length=20, unique=True, verbose_name="VIN")
    state = models.CharField(max_length=10, null=True, blank=True, verbose_name="State")
    condition = models.IntegerField(null=True, blank=True, verbose_name="Condition")
    odometer = models.IntegerField(null=True, blank=True, verbose_name="Odometer")
    color = models.CharField(max_length=50, null=True, blank=True, verbose_name="Color")
    interior = models.CharField(max_length=50, null=True, blank=True, verbose_name="Interior")
    created_at = TruncatedDateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = TruncatedDateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self):
        return f"{self.make.make_name} {self.vehicle_model} ({self.vin})"

    class Meta:
        db_table = 'vehicle_info'
        verbose_name_plural = 'vehicle info'
        indexes = [
            models.Index(fields=['make']),
        ]


class CustomerInfo(models.Model):
    customer_id = models.AutoField(primary_key=True, verbose_name="Customer ID")
    firstname = models.CharField(max_length=100, verbose_name="First Name")
    lastname = models.CharField(max_length=100, verbose_name="Last Name")
    customer_status = models.CharField(max_length=50, verbose_name="Customer Status")
    customer_address = models.CharField(max_length=255, verbose_name="Customer Address")
    city = models.ForeignKey(City, on_delete=models.CASCADE, db_column='city_id', related_name='customers', verbose_name="City")
    country = models.ForeignKey(Country, on_delete=models.CASCADE, db_column='country_id', related_name='customers', verbose_name="Country")
    created_at = TruncatedDateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = TruncatedDateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self):
        return f"{self.firstname} {self.lastname}"

    class Meta:
        db_table = 'customer_info'
        verbose_name_plural = 'customer info'


class SellingInfo(models.Model):
    sell_id = models.AutoField(primary_key=True, verbose_name="Sell ID")
    customer = models.ForeignKey(CustomerInfo, on_delete=models.CASCADE, db_column='customer_id', related_name='sales', verbose_name="Customer")
    vehicle = models.ForeignKey(VehicleInfo, on_delete=models.CASCADE, db_column='vehicle_id', related_name='sales', verbose_name="Vehicle")
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, db_column='employee_id', related_name='sales', verbose_name="Employee")
    store = models.ForeignKey(Store, on_delete=models.CASCADE, db_column='store_id', related_name='sales', verbose_name="Store")
    selling_price = models.IntegerField(verbose_name="Selling Price")
    selling_date = models.DateField(db_index=True, verbose_name="Selling Date")
    created_at = TruncatedDateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = TruncatedDateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self):
        return f"Sale {self.sell_id}: {self.vehicle} to {self.customer} ($ {self.selling_price})"

    class Meta:
        db_table = 'selling_info'
        verbose_name_plural = 'selling info'


class EmployeeBudget(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="Budget ID")
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, db_column='employee_id', related_name='budgets', verbose_name="Employee")
    budget_year = models.IntegerField(verbose_name="Budget Year")
    budget_month = models.IntegerField(verbose_name="Budget Month")
    store = models.ForeignKey(Store, on_delete=models.CASCADE, db_column='store_id', related_name='budgets', verbose_name="Store")
    budget_qty = models.IntegerField(verbose_name="Budget Quantity")
    budget_amount = models.IntegerField(verbose_name="Budget Amount")
    created_at = TruncatedDateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = TruncatedDateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self):
        return f"Budget for {self.employee} - {self.budget_year}/{self.budget_month}"

    class Meta:
        db_table = 'employee_budget'
        unique_together = ('employee', 'budget_year', 'budget_month', 'store')


class Inventory(models.Model):
    inventory_id = models.AutoField(primary_key=True, verbose_name="Inventory ID")
    vehicle = models.OneToOneField(
        VehicleInfo,
        on_delete=models.CASCADE,
        db_column='vehicle_id',
        related_name='inventory',
        verbose_name="Vehicle"
    )
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        db_column='store_id',
        related_name='inventory_items',
        verbose_name="Store"
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        db_column='employee_id',
        related_name='inventory_items',
        verbose_name="Employee"
    )
    selling_info = models.OneToOneField(
        SellingInfo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='sell_id',
        related_name='inventory_item',
        verbose_name="Selling Info"
    )
    class StatusChoices(models.IntegerChoices):
        SOLD = 1, 'Sold'
        PRE_ORDER = 2, 'Pre-order'
        UNAVAILABLE = 0, 'Unavailable'
        AVAILABLE = 4, 'Available'

    status = models.IntegerField(
        choices=StatusChoices.choices,
        default=StatusChoices.AVAILABLE,
        verbose_name="Status"
    )
    created_at = TruncatedDateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = TruncatedDateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self):
        return f"{self.vehicle} at {self.store} ({self.get_status_display()})"

    class Meta:
        db_table = 'inventory'
        verbose_name_plural = 'inventories'


class Invoice(models.Model):
    invoice_id = models.IntegerField(primary_key=True, verbose_name="Invoice ID")
    selling_info = models.OneToOneField(
        SellingInfo,
        on_delete=models.CASCADE,
        db_column='sell_id',
        related_name='invoice',
        verbose_name="Selling Info"
    )
    customer = models.ForeignKey(
        CustomerInfo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='customer_id',
        related_name='invoices',
        verbose_name="Customer"
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='employee_id',
        related_name='invoices',
        verbose_name="Employee"
    )
    store = models.ForeignKey(
        Store,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='store_id',
        related_name='invoices',
        verbose_name="Store"
    )
    invoice_date = models.DateField(verbose_name="Invoice Date")
    due_date = models.DateField(null=True, blank=True, verbose_name="Due Date")

    class PaymentStatusChoices(models.TextChoices):
        UNPAID = 'Unpaid', 'Unpaid'
        PAID = 'Paid', 'Paid'
        PENDING = 'Pending', 'Pending'
        OVERDUE = 'Overdue', 'Overdue'

    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatusChoices.choices,
        default=PaymentStatusChoices.PAID,
        verbose_name="Payment Status"
    )

    class PaymentMethodChoices(models.TextChoices):
        CASH = 'Cash', 'Cash'
        CARD = 'Card', 'Card'
        BANK_TRANSFER = 'Bank Transfer', 'Bank Transfer'
        FINANCING = 'Financing', 'Financing'

    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethodChoices.choices,
        default=PaymentMethodChoices.CASH,
        verbose_name="Payment Method"
    )
    discount_amount = models.IntegerField(default=0, verbose_name='Discount Amount')
    mmr = models.IntegerField(default=0, verbose_name='MMR Price')
    discount_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, verbose_name='Discount %')
    notes = models.TextField(null=True, blank=True, verbose_name='Notes')
    created_at = TruncatedDateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = TruncatedDateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self):
        return f"Invoice #{self.invoice_id} for Sale {self.selling_info_id}"

    class Meta:
        db_table = 'invoice'
        verbose_name_plural = 'invoices'