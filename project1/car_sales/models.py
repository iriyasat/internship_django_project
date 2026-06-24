from django.db import models

class Country(models.Model):
    country_id = models.AutoField(primary_key=True, verbose_name="Country ID")
    country_name = models.CharField(max_length=100, unique=True, verbose_name="Country Name")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self):
        return self.country_name

    class Meta:
        db_table = 'country'
        verbose_name_plural = 'countries'


class City(models.Model):
    city_id = models.AutoField(primary_key=True, verbose_name="City ID")
    city_name = models.CharField(max_length=100, verbose_name="City Name")
    country = models.ForeignKey(Country, on_delete=models.CASCADE, db_column='country_id', related_name='cities', verbose_name="Country")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

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
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self):
        return f"{self.store_name} ({self.store_code})"

    class Meta:
        db_table = 'store'


class EmployeeRole(models.Model):
    role_id = models.AutoField(primary_key=True, verbose_name="Role ID")
    role_name = models.CharField(max_length=100, unique=True, verbose_name="Role Name")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self):
        return self.role_name

    class Meta:
        db_table = 'employee_role'


class EmployeeStatus(models.Model):
    status_id = models.AutoField(primary_key=True, verbose_name="Status ID")
    status = models.CharField(max_length=50, unique=True, verbose_name="Status Name")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

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
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        db_table = 'employee'


class IndustryInfo(models.Model):
    make_id = models.AutoField(primary_key=True, verbose_name="Make ID")
    make_name = models.CharField(max_length=100, unique=True, verbose_name="Make Name")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

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
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

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
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

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
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

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
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self):
        return f"Budget for {self.employee} - {self.budget_year}/{self.budget_month}"

    class Meta:
        db_table = 'employee_budget'
        unique_together = ('employee', 'budget_year', 'budget_month', 'store')