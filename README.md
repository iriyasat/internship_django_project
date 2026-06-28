# Django Project (Car Sales)

## Setup Steps Completed

Below are the step-by-step instructions that were followed to get this Django project up and running on macOS.

### Step 1: Clone and Navigate to the Project
Open Terminal on macOS and navigate to the project directory:
```bash
cd "path/to/cloned/Django Project"
```

### Step 2: Set Up Python and Virtual Environment
1. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   ```
2. **Activate the virtual environment**:
   ```bash
   source venv/bin/activate
   ```
3. **Install the required packages**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

### Step 3: Set Up MySQL/MariaDB Database
We connect to the local MariaDB/MySQL instance running on port `33007`.
Create the `car_sales` database:
```sql
CREATE DATABASE car_sales CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
```

### Step 4: Extract and Import the SQL Dataset
1. **Unzip the dataset**:
   ```bash
   unzip project1/dataset/car_sales_final.zip -d project1/dataset/
   ```
2. **Import the SQL file**:
   ```bash
   /opt/homebrew/bin/mysql -h 127.0.0.1 -P 33007 -u root car_sales < project1/dataset/car_sales_final.sql
   ```

### Step 5: Verify Configurations
In [settings.py](file:///Users/iriyasat/Documents/WorkStation/internship_django_project/project1/project1/settings.py), the database settings are configured as follows:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'car_sales',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        'PORT': '33007',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        }
    }
}
```

### Step 6: Run the Server
1. Navigate to the inner `project1` directory (where `manage.py` is located):
   ```bash
   cd project1
   ```
2. Run the development server:
   ```bash
   python manage.py runserver
   ```
3. Open the browser and navigate to `http://127.0.0.1:8000`.

---

## Helper Script (`run.sh`)

A helper script [run.sh](file:///Users/iriyasat/Documents/WorkStation/internship_django_project/run.sh) is provided in the project root to automatically handle virtual environment activation and run Django commands.

### Usage:

- **Start the Development Server (default)**:
  ```bash
  ./run.sh
  ```

- **Run Database Migrations**:
  ```bash
  ./run.sh migrate
  ```

- **Open Django Shell**:
  ```bash
  ./run.sh shell
  ```

- **Run System Checks**:
  ```bash
  ./run.sh check
  ```

---

## Codebase Reference (`car_sales` App)

Here is a reference of the core files inside the `car_sales` application folder.

### 1. Models (`car_sales/models.py`)
This file defines the database schema for the Car Sales database.

<details>
<summary>Click to view models.py</summary>

```python
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
```
</details>

### 2. Admin Configuration (`car_sales/admin.py`)
This file registers the models with the Django Admin site, enabling lists, search, filters, and autocomplete fields.

<details>
<summary>Click to view admin.py</summary>

```python
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
```
</details>

### 3. URL Routing (`car_sales/urls.py`)
This file defines the URL routing/endpoints for the application views.

```python
from django.urls import path, include
from .views import *

urlpatterns = [
    path('', home_view, name='home'),
    path('employees/', employee_view, name='employee'),
    path('countries/', country_view, name='country'),
    path('cities/', city_view, name='city'),
    path('stores/', store_view, name='store'),
    path('emproles/', role_view, name='emprole'),
    path('statuses/', status_view, name='status'),
    path('industry/', industry_view, name='industry'),
    path('vehicles/', vehicle_view, name='vehicle'),
    path('customers/', customer_view, name='customer'),
    path('sales/', selling_view, name='selling'),
    path('budgets/', budget_view, name='budget'),
]
```
