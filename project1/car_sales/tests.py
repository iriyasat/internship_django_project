import datetime
from django.test import TestCase
from django.db import IntegrityError, transaction
from .models import (
    Country, City, Store, EmployeeRole, EmployeeStatus,
    Employee, IndustryInfo, VehicleInfo, CustomerInfo,
    SellingInfo, EmployeeBudget
)

class CarSalesModelTestCase(TestCase):
    """Test suite verifying the behavior, constraints, and relationships of the car sales models."""

    def setUp(self):
        # 1. Create Country & City
        self.country = Country.objects.create(country_name="United States")
        self.city = City.objects.create(city_name="New York", country=self.country)

        # 2. Create Store
        self.store = Store.objects.create(
            store_name="New York Motors",
            store_code="ST0001",
            city=self.city,
            country=self.country,
            address="26 Highway Rd, New York"
        )

        # 3. Create Employee Role and Status
        self.role = EmployeeRole.objects.create(role_name="Sales Executive")
        self.status = EmployeeStatus.objects.create(status="In Service")

        # 4. Create Employee
        self.employee = Employee.objects.create(
            first_name="Robert",
            last_name="Rossi",
            date_of_joining=datetime.date(2010, 1, 13),
            employee_addr="5863 Elm St, Osaka",
            employee_role=self.role,
            status=self.status,
            store=self.store,
            city=self.city,
            country=self.country
        )

        # 5. Create Industry Info (Make)
        self.make = IndustryInfo.objects.create(make_name="Toyota")

        # 6. Create Vehicle Info
        self.vehicle = VehicleInfo.objects.create(
            vehicle_model="Camry",
            make=self.make,
            mmr=16450,
            trim="XLE",
            body="Sedan",
            transmission="automatic",
            vin="4T1BF1FK3EU327266",
            state="SC",
            condition=3,
            odometer=33959,
            color="Gray",
            interior="Gray"
        )

        # 7. Create Customer Info
        self.customer = CustomerInfo.objects.create(
            firstname="Robert",
            lastname="Nguyen",
            customer_status="Regular",
            customer_address="6341 Broadway, Melbourne",
            city=self.city,
            country=self.country
        )

    def test_model_creation(self):
        """Verify that basic objects are created successfully with correct properties."""
        self.assertEqual(self.country.country_name, "United States")
        self.assertEqual(self.city.city_name, "New York")
        self.assertEqual(self.store.store_code, "ST0001")
        self.assertEqual(self.role.role_name, "Sales Executive")
        self.assertEqual(self.status.status, "In Service")
        self.assertEqual(self.employee.first_name, "Robert")
        self.assertEqual(self.make.make_name, "Toyota")
        self.assertEqual(self.vehicle.vehicle_model, "Camry")
        self.assertEqual(self.customer.firstname, "Robert")

    def test_unique_constraints(self):
        """Verify unique constraints are enforced by the database."""
        # 1. Duplicate country name
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Country.objects.create(country_name="United States")

        # 2. Duplicate employee role name
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                EmployeeRole.objects.create(role_name="Sales Executive")

        # 3. Duplicate employee status name
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                EmployeeStatus.objects.create(status="In Service")

        # 4. Duplicate store code
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Store.objects.create(
                    store_name="Another Store",
                    store_code="ST0001",
                    city=self.city,
                    country=self.country,
                    address="Somewhere"
                )

        # 5. Duplicate vehicle VIN
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                VehicleInfo.objects.create(
                    vehicle_model="Corolla",
                    make=self.make,
                    mmr=15000,
                    vin="4T1BF1FK3EU327266",  # Duplicate VIN
                )

    def test_selling_info_creation(self):
        """Verify creating a sale record works and links correctly to related models."""
        sale = SellingInfo.objects.create(
            customer=self.customer,
            vehicle=self.vehicle,
            employee=self.employee,
            store=self.store,
            selling_price=14800,
            selling_date=datetime.date(2014, 1, 1)
        )
        self.assertEqual(sale.selling_price, 14800)
        self.assertEqual(sale.customer, self.customer)
        self.assertEqual(sale.vehicle, self.vehicle)

    def test_employee_budget_creation_and_uniqueness(self):
        """Verify EmployeeBudget creation and unique_together constraint checks."""
        budget = EmployeeBudget.objects.create(
            employee=self.employee,
            budget_year=2014,
            budget_month=1,
            store=self.store,
            budget_qty=10,
            budget_amount=20000
        )
        self.assertEqual(budget.budget_qty, 10)

        # Attempt duplicate budget for same employee/year/month/store
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                EmployeeBudget.objects.create(
                    employee=self.employee,
                    budget_year=2014,
                    budget_month=1,
                    store=self.store,
                    budget_qty=5,
                    budget_amount=10000
                )


class CarSalesCrudPermissionTestCase(TestCase):
    """Test suite verifying that only admin/staff users can perform CRUD operations on models."""

    def setUp(self):
        from django.contrib.auth.models import User
        # Create users
        self.admin_user = User.objects.create_user(username="admin", password="password123", is_staff=True)
        self.regular_user = User.objects.create_user(username="regular", password="password123", is_staff=False)

    def test_anonymous_user_crud_denied(self):
        """Verify that anonymous users are redirected/blocked from CRUD endpoints."""
        from django.urls import reverse
        for model in ['customerinfo', 'vehicleinfo', 'sellinginfo']:
            url = reverse('admin_crud', args=[model, 'create'])
            response = self.client.get(url)
            # Should redirect to login since they are anonymous (handled by @staff_member_required)
            self.assertEqual(response.status_code, 302)
            self.assertIn('login', response.url)

    def test_regular_user_crud_denied(self):
        """Verify that authenticated regular users are redirected/blocked from CRUD endpoints."""
        from django.urls import reverse
        self.client.login(username="regular", password="password123")
        for model in ['customerinfo', 'vehicleinfo', 'sellinginfo']:
            url = reverse('admin_crud', args=[model, 'create'])
            response = self.client.get(url)
            # Should redirect to login since they are not staff (handled by @staff_member_required)
            self.assertEqual(response.status_code, 302)
            self.assertIn('login', response.url)

    def test_staff_user_crud_allowed(self):
        """Verify that staff/admin users can access CRUD endpoints."""
        from django.urls import reverse
        self.client.login(username="admin", password="password123")
        for model in ['customerinfo', 'vehicleinfo', 'sellinginfo']:
            url = reverse('admin_crud', args=[model, 'create'])
            response = self.client.get(url)
            # Staff user should get the page
            self.assertEqual(response.status_code, 200)


class EmployeeReportTestCase(TestCase):
    """Test suite verifying the employee performance report views and templates."""

    def setUp(self):
        from django.urls import reverse
        # Create standard location, store, role, status, employee
        self.country = Country.objects.create(country_name="United States")
        self.city = City.objects.create(city_name="New York", country=self.country)
        self.store = Store.objects.create(
            store_name="New York Motors",
            store_code="ST0001",
            city=self.city,
            country=self.country,
            address="26 Highway Rd, New York"
        )
        self.role = EmployeeRole.objects.create(role_name="Sales Executive")
        self.status = EmployeeStatus.objects.create(status="Active")
        
        # Create three employees to see 1st, 2nd, 3rd ranking badges
        self.emp1 = Employee.objects.create(
            first_name="Alice", last_name="Smith", date_of_joining=datetime.date(2020, 1, 1),
            employee_role=self.role, status=self.status, store=self.store, city=self.city, country=self.country
        )
        self.emp2 = Employee.objects.create(
            first_name="Bob", last_name="Jones", date_of_joining=datetime.date(2020, 1, 1),
            employee_role=self.role, status=self.status, store=self.store, city=self.city, country=self.country
        )
        self.emp3 = Employee.objects.create(
            first_name="Charlie", last_name="Brown", date_of_joining=datetime.date(2020, 1, 1),
            employee_role=self.role, status=self.status, store=self.store, city=self.city, country=self.country
        )

        # Let's create sales records to rank them: emp1 > emp2 > emp3
        self.make = IndustryInfo.objects.create(make_name="Toyota")
        self.vehicle1 = VehicleInfo.objects.create(vehicle_model="Camry", make=self.make, mmr=16000, vin="VIN111")
        self.vehicle2 = VehicleInfo.objects.create(vehicle_model="Camry", make=self.make, mmr=16000, vin="VIN222")
        self.vehicle3 = VehicleInfo.objects.create(vehicle_model="Camry", make=self.make, mmr=16000, vin="VIN333")
        self.customer = CustomerInfo.objects.create(firstname="John", lastname="Doe", customer_status="Regular", city=self.city, country=self.country)

        # Sales
        SellingInfo.objects.create(
            customer=self.customer, vehicle=self.vehicle1, employee=self.emp1, store=self.store,
            selling_price=30000, selling_date=datetime.date(2026, 6, 1)
        )
        SellingInfo.objects.create(
            customer=self.customer, vehicle=self.vehicle2, employee=self.emp2, store=self.store,
            selling_price=20000, selling_date=datetime.date(2026, 6, 1)
        )
        SellingInfo.objects.create(
            customer=self.customer, vehicle=self.vehicle3, employee=self.emp3, store=self.store,
            selling_price=10000, selling_date=datetime.date(2026, 6, 1)
        )

        self.url = reverse('employee_report')

    def test_employee_report_view_renders_correctly(self):
        """Verify the employee performance report lists and ranks employees correctly."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('employee_leaderboard', response.context)
        
        # Verify pagination start index displays correctly
        self.assertEqual(response.context['employee_leaderboard'].start_index(), 1)
        
        # Check rendered HTML for the top 3 ranking badges
        content = response.content.decode('utf-8')
        self.assertIn('1st', content)
        self.assertIn('2nd', content)
        self.assertIn('3rd', content)


class ReportJsonExportTestCase(TestCase):
    """Test suite verifying the JSON export functionality of report pages."""

    def setUp(self):
        from django.urls import reverse
        self.country = Country.objects.create(country_name="United States")
        self.city = City.objects.create(city_name="New York", country=self.country)
        self.store = Store.objects.create(
            store_name="New York Motors",
            store_code="ST0001",
            city=self.city,
            country=self.country,
            address="26 Highway Rd, New York"
        )
        self.role = EmployeeRole.objects.create(role_name="Sales Executive")
        self.status = EmployeeStatus.objects.create(status="Active")
        self.emp = Employee.objects.create(
            first_name="Alice", last_name="Smith", date_of_joining=datetime.date(2020, 1, 1),
            employee_role=self.role, status=self.status, store=self.store, city=self.city, country=self.country
        )
        self.make = IndustryInfo.objects.create(make_name="Toyota")
        self.vehicle = VehicleInfo.objects.create(vehicle_model="Camry", make=self.make, mmr=16000, vin="VIN111")
        self.customer = CustomerInfo.objects.create(firstname="John", lastname="Doe", customer_status="Regular", city=self.city, country=self.country)

        # Sales
        SellingInfo.objects.create(
            customer=self.customer, vehicle=self.vehicle, employee=self.emp, store=self.store,
            selling_price=30000, selling_date=datetime.date(2026, 6, 1)
        )

        self.employee_report_url = reverse('employee_report')
        self.vehicle_report_url = reverse('vehicle_report')
        self.sales_report_url = reverse('sales_report')

    def test_employee_report_json_download(self):
        """Verify employee report returns JSON data with download=json query parameter."""
        response = self.client.get(self.employee_report_url, {'download': 'json'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertEqual(data['report_type'], 'Employee Performance Report')
        self.assertTrue(len(data['employees']) > 0)
        self.assertEqual(data['employees'][0]['name'], "Alice Smith")

    def test_vehicle_report_json_download(self):
        """Verify vehicle report returns JSON data with download=json query parameter."""
        response = self.client.get(self.vehicle_report_url, {'download': 'json'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertEqual(data['report_type'], 'Vehicle Report')
        self.assertTrue(len(data['transactions']) > 0)
        self.assertEqual(data['transactions'][0]['model'], "Camry")

    def test_sales_report_json_download(self):
        """Verify sales report returns JSON data with download=json query parameter."""
        response = self.client.get(self.sales_report_url, {'download': 'json'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertEqual(data['report_type'], 'Sales Revenue Report')
        self.assertTrue(len(data['transactions']) > 0)
        self.assertEqual(data['transactions'][0]['selling_price'], 30000.0)



