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

