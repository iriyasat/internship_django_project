import datetime
import os
import pandas as pd
from django.conf import settings
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from .models import (
    Country, City, Store, EmployeeRole, EmployeeStatus,
    Employee, IndustryInfo, VehicleInfo, CustomerInfo,
    SellingInfo, EmployeeBudget
)

class CarSalesBaseTestCase(TestCase):
    """
    Base test case containing shared setup data read from the Excel datasheet.
    Tracks and cleans up any User or Employee objects created during individual tests.
    """

    @classmethod
    def setUpTestData(cls):
        # Locate the excel file path dynamically
        excel_path = os.path.join(settings.BASE_DIR, 'dataset', 'car_sales_dataset_v2_untouched.xlsx')

        with pd.ExcelFile(excel_path) as xls:
            df_country = pd.read_excel(xls, sheet_name='country', nrows=5)
            df_city = pd.read_excel(xls, sheet_name='city', nrows=5)
            df_store = pd.read_excel(xls, sheet_name='store', nrows=5)
            df_role = pd.read_excel(xls, sheet_name='employee_role')
            df_status = pd.read_excel(xls, sheet_name='employee_status')
            df_emp = pd.read_excel(xls, sheet_name='employee', nrows=5)

        # 1. Load Country & City
        countries = []
        for _, row in df_country.iterrows():
            c, _ = Country.objects.get_or_create(
                country_id=int(row['country_id']),
                defaults={'country_name': str(row['country_name'])}
            )
            countries.append(c)
        cls.country = countries[0]

        cities = []
        for _, row in df_city.iterrows():
            country_id = int(row['country_id'])
            country_obj, _ = Country.objects.get_or_create(country_id=country_id, defaults={'country_name': f"Country {country_id}"})
            c, _ = City.objects.get_or_create(
                city_id=int(row['city_id']),
                defaults={'city_name': str(row['city_name']), 'country': country_obj}
            )
            cities.append(c)
        cls.city = cities[0]

        # 2. Load Store
        stores = []
        for _, row in df_store.iterrows():
            city_id = int(row['city_id'])
            country_id = int(row['country_id'])
            country_obj, _ = Country.objects.get_or_create(country_id=country_id, defaults={'country_name': f"Country {country_id}"})
            city_obj, _ = City.objects.get_or_create(city_id=city_id, defaults={'city_name': f"City {city_id}", 'country': country_obj})
            s, _ = Store.objects.get_or_create(
                store_id=int(row['store_id']),
                defaults={
                    'store_name': str(row['store_name']),
                    'store_code': str(row['store_code']),
                    'city': city_obj,
                    'country': country_obj,
                    'address': str(row['address'])
                }
            )
            stores.append(s)
        cls.store = stores[0]

        # 3. Load Employee Roles and Statuses
        for _, row in df_role.iterrows():
            EmployeeRole.objects.get_or_create(
                role_id=int(row['role_id']),
                defaults={'role_name': str(row['role_name'])}
            )
        cls.role = EmployeeRole.objects.get(role_name="Sales Executive")
        cls.manager_role = EmployeeRole.objects.get(role_name="Branch Manager")

        for _, row in df_status.iterrows():
            EmployeeStatus.objects.get_or_create(
                status_id=int(row['status_id']),
                defaults={'status': str(row['status'])}
            )
        cls.status_active = EmployeeStatus.objects.get(status="In Service")
        cls.status_in_service = cls.status_active

        # 4. Load Base Employees
        employees = []
        for _, row in df_emp.iterrows():
            role_id = int(row['employee_role'])
            status_id = int(row['status'])
            store_id = int(row['store_id'])
            city_id = int(row['city_id'])
            country_id = int(row['country_id'])

            country_obj, _ = Country.objects.get_or_create(country_id=country_id, defaults={'country_name': f"Country {country_id}"})
            city_obj, _ = City.objects.get_or_create(city_id=city_id, defaults={'city_name': f"City {city_id}", 'country': country_obj})
            store_obj, _ = Store.objects.get_or_create(store_id=store_id, defaults={'store_name': f"Store {store_id}", 'store_code': f"ST{store_id}", 'city': city_obj, 'country': country_obj, 'address': 'Address'})
            role_obj, _ = EmployeeRole.objects.get_or_create(role_id=role_id, defaults={'role_name': f"Role {role_id}"})
            status_obj, _ = EmployeeStatus.objects.get_or_create(status_id=status_id, defaults={'status': f"Status {status_id}"})

            e, _ = Employee.objects.get_or_create(
                employee_id=int(row['employee_id']),
                defaults={
                    'first_name': str(row['first_name']),
                    'last_name': str(row['last_name']),
                    'date_of_joining': pd.to_datetime(row['date_of_joining']).date(),
                    'employee_addr': str(row['employee_addr']),
                    'employee_role': role_obj,
                    'status': status_obj,
                    'store': store_obj,
                    'city': city_obj,
                    'country': country_obj,
                    'password': 'CAr$@lse2014'
                }
            )
            employees.append(e)
        
        # Explicitly configure their roles and store to match existing test authorization logic
        cls.test_employee = employees[0]
        cls.test_employee.employee_role = cls.role
        cls.test_employee.store = cls.store
        cls.test_employee.city = cls.city
        cls.test_employee.country = cls.country
        cls.test_employee.save()

        cls.manager_employee = employees[1] if len(employees) > 1 else employees[0]
        cls.manager_employee.employee_role = cls.manager_role
        cls.manager_employee.status = cls.status_active
        cls.manager_employee.store = cls.store
        cls.manager_employee.city = cls.city
        cls.manager_employee.country = cls.country
        cls.manager_employee.save()

    def setUp(self):
        super().setUp()
        # Record pre-existing user and employee primary keys to detect new ones
        self._initial_user_pks = set(User.objects.values_list('pk', flat=True))
        self._initial_employee_pks = set(Employee.objects.values_list('pk', flat=True))

    def tearDown(self):
        # Identify users/employees created during this individual test method
        current_user_pks = set(User.objects.values_list('pk', flat=True))
        created_user_pks = current_user_pks - self._initial_user_pks

        current_employee_pks = set(Employee.objects.values_list('pk', flat=True))
        created_employee_pks = current_employee_pks - self._initial_employee_pks

        # Delete the created user objects
        if created_user_pks:
            User.objects.filter(pk__in=created_user_pks).delete()
        
        # Delete the created employee objects
        if created_employee_pks:
            Employee.objects.filter(pk__in=created_employee_pks).delete()

        # Verify they are completely deleted from the database
        remaining_users = User.objects.filter(pk__in=created_user_pks).count()
        remaining_employees = Employee.objects.filter(pk__in=created_employee_pks).count()

        self.assertEqual(remaining_users, 0, f"Failed to delete test-created Users: {created_user_pks}")
        self.assertEqual(remaining_employees, 0, f"Failed to delete test-created Employees: {created_employee_pks}")

        super().tearDown()


class DatabaseVerificationAndCleanupTestCase(CarSalesBaseTestCase):
    """
    Dedicated test case verifying:
    1. Life cycle (create, delete, verify deleted) of User and Employee records.
    2. Validation of all DB model fields using values from the excel datasheet sheets.
    """

    def test_user_and_employee_lifecycle(self):
        """Create users and custom employees, delete them, and verify they are gone."""
        # 1. Create a Django standard User
        user = User.objects.create_user(username="temp_user_test", email="temp@test.com", password="pass")
        self.assertTrue(User.objects.filter(username="temp_user_test").exists())

        # 2. Create a custom Employee
        emp = Employee.objects.create(
            first_name="Temp",
            last_name="Emp",
            date_of_joining=datetime.date(2026, 1, 1),
            employee_addr="123 Temp St",
            employee_role=self.role,
            status=self.status_active,
            store=self.store,
            city=self.city,
            country=self.country
        )
        self.assertTrue(Employee.objects.filter(employee_id=emp.employee_id).exists())

        # 3. Explicitly delete them
        user.delete()
        emp.delete()

        # 4. Verify they are deleted from the database
        self.assertFalse(User.objects.filter(username="temp_user_test").exists())
        self.assertFalse(Employee.objects.filter(employee_id=emp.employee_id).exists())

    def test_verify_database_with_datasheet_xlsx(self):
        """
        Verify that database structures and models correctly load and store details
        from the untouched Excel datasheet.
        """
        excel_path = os.path.join(settings.BASE_DIR, 'dataset', 'car_sales_dataset_v2_untouched.xlsx')
        self.assertTrue(os.path.exists(excel_path))

        with pd.ExcelFile(excel_path) as xls:
            df_make = pd.read_excel(xls, sheet_name='industry_info', nrows=2)
            df_vehicle = pd.read_excel(xls, sheet_name='vehicle_info', nrows=2)
            df_customer = pd.read_excel(xls, sheet_name='customer_info', nrows=2)
            df_sale = pd.read_excel(xls, sheet_name='selling_info', nrows=2)
            df_budget = pd.read_excel(xls, sheet_name='employee_budget', nrows=2)

        # Test loading and verifying details of IndustryInfo and VehicleInfo from Excel
        make_row = df_make.iloc[0]
        make, _ = IndustryInfo.objects.get_or_create(
            make_id=int(make_row['make_id']),
            defaults={'make_name': str(make_row['make_name'])}
        )
        # Verify
        db_make = IndustryInfo.objects.get(make_id=make.make_id)
        self.assertEqual(db_make.make_name, str(make_row['make_name']))

        v_row = df_vehicle.iloc[0]
        vehicle, _ = VehicleInfo.objects.get_or_create(
            id=int(v_row['id']),
            defaults={
                'vehicle_model': str(v_row['vehicle_model']),
                'make': make,
                'mmr': int(v_row['mmr']),
                'trim': str(v_row['trim']) if pd.notna(v_row['trim']) else None,
                'body': str(v_row['body']) if pd.notna(v_row['body']) else None,
                'transmission': str(v_row['transmission']) if pd.notna(v_row['transmission']) else None,
                'vin': str(v_row['vin']),
                'state': str(v_row['state']) if pd.notna(v_row['state']) else None,
                'condition': int(v_row['condition']) if pd.notna(v_row['condition']) else None,
                'odometer': int(v_row['odometer']) if pd.notna(v_row['odometer']) else None,
                'color': str(v_row['color']) if pd.notna(v_row['color']) else None,
                'interior': str(v_row['interior']) if pd.notna(v_row['interior']) else None
            }
        )
        # Verify
        db_vehicle = VehicleInfo.objects.get(id=vehicle.id)
        self.assertEqual(db_vehicle.vin, str(v_row['vin']))
        self.assertEqual(db_vehicle.vehicle_model, str(v_row['vehicle_model']))
        self.assertEqual(db_vehicle.mmr, int(v_row['mmr']))

        # Test CustomerInfo sheet verification
        c_row = df_customer.iloc[0]
        customer, _ = CustomerInfo.objects.get_or_create(
            customer_id=int(c_row['customer_id']),
            defaults={
                'firstname': str(c_row['firstname']),
                'lastname': str(c_row['lastname']),
                'customer_status': str(c_row['customer_status']),
                'customer_address': str(c_row['customer_address']),
                'city': self.city,
                'country': self.country
            }
        )
        # Verify
        db_customer = CustomerInfo.objects.get(customer_id=customer.customer_id)
        self.assertEqual(db_customer.firstname, str(c_row['firstname']))
        self.assertEqual(db_customer.lastname, str(c_row['lastname']))
        self.assertEqual(db_customer.customer_status, str(c_row['customer_status']))

        # Test SellingInfo sheet verification
        s_row = df_sale.iloc[0]
        sale, _ = SellingInfo.objects.get_or_create(
            sell_id=int(s_row['sell_id']),
            defaults={
                'customer': customer,
                'vehicle': vehicle,
                'employee': self.test_employee,
                'store': self.store,
                'selling_price': int(s_row['selling_price']),
                'selling_date': pd.to_datetime(s_row['selling_date']).date()
            }
        )
        # Verify
        db_sale = SellingInfo.objects.get(sell_id=sale.sell_id)
        self.assertEqual(db_sale.selling_price, int(s_row['selling_price']))
        self.assertEqual(db_sale.selling_date, pd.to_datetime(s_row['selling_date']).date())

        # Test EmployeeBudget sheet verification
        b_row = df_budget.iloc[0]
        budget, _ = EmployeeBudget.objects.get_or_create(
            employee=self.test_employee,
            budget_year=int(b_row['budget_year']),
            budget_month=int(b_row['budget_month']),
            store=self.store,
            defaults={
                'budget_qty': int(b_row['budget_qty']),
                'budget_amount': int(b_row['budget_amount'])
            }
        )
        # Verify
        db_budget = EmployeeBudget.objects.get(pk=budget.pk)
        self.assertEqual(db_budget.budget_year, int(b_row['budget_year']))
        self.assertEqual(db_budget.budget_qty, int(b_row['budget_qty']))
        self.assertEqual(db_budget.budget_amount, int(b_row['budget_amount']))


class CarSalesModelTestCase(CarSalesBaseTestCase):
    """Test suite verifying basic model relationships and unique constraints."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        excel_path = os.path.join(settings.BASE_DIR, 'dataset', 'car_sales_dataset_v2_untouched.xlsx')

        cls.employee = cls.test_employee

        with pd.ExcelFile(excel_path) as xls:
            df_make = pd.read_excel(xls, sheet_name='industry_info', nrows=2)
            df_vehicle = pd.read_excel(xls, sheet_name='vehicle_info', nrows=2)
            df_customer = pd.read_excel(xls, sheet_name='customer_info', nrows=2)

        # Create Make
        cls.make, _ = IndustryInfo.objects.get_or_create(
            make_id=int(df_make.iloc[0]['make_id']),
            defaults={'make_name': str(df_make.iloc[0]['make_name'])}
        )

        # Create Vehicle
        v_row = df_vehicle.iloc[0]
        cls.vehicle, _ = VehicleInfo.objects.get_or_create(
            id=int(v_row['id']),
            defaults={
                'vehicle_model': str(v_row['vehicle_model']),
                'make': cls.make,
                'mmr': int(v_row['mmr']),
                'trim': str(v_row['trim']) if pd.notna(v_row['trim']) else None,
                'body': str(v_row['body']) if pd.notna(v_row['body']) else None,
                'transmission': str(v_row['transmission']) if pd.notna(v_row['transmission']) else None,
                'vin': str(v_row['vin']),
                'state': str(v_row['state']) if pd.notna(v_row['state']) else None,
                'condition': int(v_row['condition']) if pd.notna(v_row['condition']) else None,
                'odometer': int(v_row['odometer']) if pd.notna(v_row['odometer']) else None,
                'color': str(v_row['color']) if pd.notna(v_row['color']) else None,
                'interior': str(v_row['interior']) if pd.notna(v_row['interior']) else None
            }
        )

        # Create Customer
        c_row = df_customer.iloc[0]
        cls.customer, _ = CustomerInfo.objects.get_or_create(
            customer_id=int(c_row['customer_id']),
            defaults={
                'firstname': str(c_row['firstname']),
                'lastname': str(c_row['lastname']),
                'customer_status': str(c_row['customer_status']),
                'customer_address': str(c_row['customer_address']),
                'city': cls.city,
                'country': cls.country
            }
        )

    def test_model_creation(self):
        """Verify that basic objects are created successfully with correct properties."""
        self.assertEqual(self.country.country_name, "United States")
        self.assertEqual(self.city.city_name, "New York")
        self.assertEqual(self.store.store_code, "ST0001")
        self.assertEqual(self.role.role_name, "Sales Executive")
        self.assertEqual(self.employee.first_name, "Robert")
        self.assertEqual(self.vehicle.vehicle_model, "F-250 Super Duty")
        self.assertEqual(self.customer.firstname, "Robert")
        self.assertEqual(self.make.make_name, "Acura")

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
                    vin=self.vehicle.vin,
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


class CarSalesCrudTestCase(CarSalesBaseTestCase):
    """Advanced test suite verifying permissions and CRUD validation on administrative views."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        excel_path = os.path.join(settings.BASE_DIR, 'dataset', 'car_sales_dataset_v2_untouched.xlsx')

        with pd.ExcelFile(excel_path) as xls:
            df_make = pd.read_excel(xls, sheet_name='industry_info', nrows=3)
            df_vehicle = pd.read_excel(xls, sheet_name='vehicle_info', nrows=3)
            df_customer = pd.read_excel(xls, sheet_name='customer_info', nrows=3)

        cls.make, _ = IndustryInfo.objects.get_or_create(
            make_id=int(df_make.iloc[1]['make_id']),
            defaults={'make_name': str(df_make.iloc[1]['make_name'])}
        )

        v_row = df_vehicle.iloc[1]
        cls.vehicle, _ = VehicleInfo.objects.get_or_create(
            id=int(v_row['id']),
            defaults={
                'vehicle_model': str(v_row['vehicle_model']),
                'make': cls.make,
                'mmr': int(v_row['mmr']),
                'vin': str(v_row['vin'])
            }
        )

        c_row = df_customer.iloc[1]
        cls.customer, _ = CustomerInfo.objects.get_or_create(
            customer_id=int(c_row['customer_id']),
            defaults={
                'firstname': str(c_row['firstname']),
                'lastname': str(c_row['lastname']),
                'customer_status': str(c_row['customer_status']),
                'city': cls.city,
                'country': cls.country
            }
        )

        cls.employee = cls.test_employee

    def test_anonymous_user_crud_denied(self):
        """Verify that anonymous users are redirected/blocked from CRUD endpoints."""
        for model in ['customerinfo', 'vehicleinfo', 'sellinginfo']:
            url = reverse('admin_crud', args=[model, 'create'])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn('login', response.url)

    def test_regular_user_crud_denied(self):
        """Verify that authenticated regular users are redirected/blocked from CRUD endpoints."""
        self.client.login(username=str(self.test_employee.employee_id), password="CAr$@lse2014")
        for model in ['customerinfo', 'vehicleinfo', 'sellinginfo']:
            url = reverse('admin_crud', args=[model, 'create'])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn('login', response.url)

    def test_staff_user_crud_allowed(self):
        """Verify that staff/admin users can access CRUD creation forms."""
        self.client.login(username=str(self.manager_employee.employee_id), password="CAr$@lse2014")
        for model in ['customerinfo', 'vehicleinfo', 'sellinginfo']:
            url = reverse('admin_crud', args=[model, 'create'])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

    def test_admin_crud_nonexistent_model(self):
        """Verify requesting CRUD endpoints on a nonexistent model returns 404."""
        self.client.login(username=str(self.manager_employee.employee_id), password="CAr$@lse2014")
        url = reverse('admin_crud', args=['invalidmodel', 'create'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_selling_info_custom_form_validation(self):
        """Verify custom SellingInfo form validation and record creation via POST."""
        self.client.login(username=str(self.manager_employee.employee_id), password="CAr$@lse2014")
        url = reverse('admin_crud', args=['sellinginfo', 'create'])
        
        # 1. Invalid submit: Customer and Vehicle IDs do not exist
        invalid_data = {
            'customer': 999999,
            'vehicle': 999999,
            'employee': self.employee.employee_id,
            'store': self.store.store_id,
            'selling_price': 25000,
            'selling_date': '2026-06-01'
        }
        response = self.client.post(url, invalid_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'customer', "Customer with this ID does not exist.")
        self.assertFormError(response.context['form'], 'vehicle', "Vehicle with this ID does not exist.")

        # 2. Valid submit: Creates record and redirects
        valid_data = {
            'customer': self.customer.customer_id,
            'vehicle': self.vehicle.id,
            'employee': self.employee.employee_id,
            'store': self.store.store_id,
            'selling_price': 25000,
            'selling_date': '2026-06-01'
        }
        response = self.client.post(url, valid_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(SellingInfo.objects.filter(selling_price=25000).exists())


class EmployeeReportTestCase(CarSalesBaseTestCase):
    """Test suite verifying the employee performance report views and pagination boundaries."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # Create three employees
        cls.emp1 = Employee.objects.create(
            first_name="Alice", last_name="Smith", date_of_joining=datetime.date(2020, 1, 1),
            employee_role=cls.role, status=cls.status_active, store=cls.store, city=cls.city, country=cls.country
        )
        cls.emp2 = Employee.objects.create(
            first_name="Bob", last_name="Jones", date_of_joining=datetime.date(2020, 1, 1),
            employee_role=cls.role, status=cls.status_active, store=cls.store, city=cls.city, country=cls.country
        )
        cls.emp3 = Employee.objects.create(
            first_name="Charlie", last_name="Brown", date_of_joining=datetime.date(2020, 1, 1),
            employee_role=cls.role, status=cls.status_active, store=cls.store, city=cls.city, country=cls.country
        )

        cls.make = IndustryInfo.objects.create(make_name="Honda")
        cls.vehicle1 = VehicleInfo.objects.create(vehicle_model="Civic", make=cls.make, mmr=14000, vin="HONDA11")
        cls.vehicle2 = VehicleInfo.objects.create(vehicle_model="Civic", make=cls.make, mmr=14000, vin="HONDA22")
        cls.vehicle3 = VehicleInfo.objects.create(vehicle_model="Civic", make=cls.make, mmr=14000, vin="HONDA33")
        cls.customer = CustomerInfo.objects.create(firstname="John", lastname="Doe", customer_status="Regular", city=cls.city, country=cls.country)
        
        # Sales records to establish leaderboard ranks (emp1 > emp2 > emp3)
        SellingInfo.objects.create(
            customer=cls.customer, vehicle=cls.vehicle1, employee=cls.emp1, store=cls.store,
            selling_price=30000, selling_date=datetime.date(2026, 6, 1)
        )
        SellingInfo.objects.create(
            customer=cls.customer, vehicle=cls.vehicle2, employee=cls.emp2, store=cls.store,
            selling_price=20000, selling_date=datetime.date(2026, 6, 1)
        )
        SellingInfo.objects.create(
            customer=cls.customer, vehicle=cls.vehicle3, employee=cls.emp3, store=cls.store,
            selling_price=10000, selling_date=datetime.date(2026, 6, 1)
        )

        cls.url = reverse('employee_report')

    def setUp(self):
        super().setUp()
        self.client.login(username=str(self.manager_employee.employee_id), password="CAr$@lse2014")

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

    def test_employee_report_pagination_invalid_page(self):
        """Verify that pagination falls back to page 1 for invalid or empty page parameters."""
        response = self.client.get(self.url, {'page': 'notaninteger'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['employee_leaderboard'].number, 1)

        response = self.client.get(self.url, {'page': '99999'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['employee_leaderboard'].number, 1)


class ReportJsonExportTestCase(CarSalesBaseTestCase):
    """Test suite verifying the JSON export format and error handling on empty data filters."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.emp = Employee.objects.create(
            first_name="Alice", last_name="Smith", date_of_joining=datetime.date(2020, 1, 1),
            employee_role=cls.role, status=cls.status_active, store=cls.store, city=cls.city, country=cls.country
        )
        cls.make = IndustryInfo.objects.create(make_name="Subaru")
        cls.vehicle = VehicleInfo.objects.create(vehicle_model="Outback", make=cls.make, mmr=18000, vin="SUBARU123")
        cls.customer = CustomerInfo.objects.create(firstname="John", lastname="Doe", customer_status="Regular", city=cls.city, country=cls.country)

        # Sale
        SellingInfo.objects.create(
            customer=cls.customer, vehicle=cls.vehicle, employee=cls.emp, store=cls.store,
            selling_price=30000, selling_date=datetime.date(2026, 6, 1)
        )

        cls.employee_report_url = reverse('employee_report')
        cls.vehicle_report_url = reverse('vehicle_report')
        cls.sales_report_url = reverse('sales_report')
        cls.customer_vehicle_report_url = reverse('customer_vehicle_report')

    def setUp(self):
        super().setUp()
        self.client.login(username=str(self.manager_employee.employee_id), password="CAr$@lse2014")

    def test_employee_report_json_download(self):
        """Verify employee report returns valid structured JSON with correct fields."""
        response = self.client.get(self.employee_report_url, {'download': 'json'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertEqual(data['report_type'], 'Employee Performance Report')
        self.assertTrue(len(data['employees']) > 0)
        self.assertEqual(data['employees'][0]['name'], "Alice Smith")

    def test_vehicle_report_json_download(self):
        """Verify vehicle report returns valid structured JSON with correct fields."""
        response = self.client.get(self.vehicle_report_url, {'download': 'json'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertEqual(data['report_type'], 'Vehicle Report')
        self.assertTrue(len(data['transactions']) > 0)
        self.assertEqual(data['transactions'][0]['model'], "Outback")

    def test_sales_report_json_download(self):
        """Verify sales report returns valid structured JSON with correct fields."""
        response = self.client.get(self.sales_report_url, {'download': 'json'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertEqual(data['report_type'], 'Sales Revenue Report')
        self.assertTrue(len(data['transactions']) > 0)
        self.assertEqual(data['transactions'][0]['selling_price'], 30000.0)

    def test_customer_vehicle_report_json_download(self):
        """Verify customer vehicle report returns valid structured JSON with correct fields."""
        response = self.client.get(self.customer_vehicle_report_url, {'download': 'json'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertEqual(data['report_type'], 'Customer & Vehicle Sales Report')
        self.assertTrue(len(data['transactions']) > 0)
        self.assertEqual(data['transactions'][0]['customer_name'], "John Doe")
        self.assertEqual(data['transactions'][0]['vehicle_info'], "Subaru Outback")
        self.assertEqual(data['transactions'][0]['selling_price'], 30000.0)

    def test_json_download_date_filter_boundary_no_records(self):
        """Verify that JSON download works correctly and returns empty datasets when filters match no data."""
        response = self.client.get(self.sales_report_url, {
            'download': 'json',
            'date_from': '2026-07-01',
            'date_to': '2026-07-31'
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['summary']['total_sales'], 0)
        self.assertEqual(data['summary']['total_revenue'], 0.0)
        self.assertEqual(len(data['transactions']), 0)


class AllPagesAndApiTestCase(CarSalesBaseTestCase):
    """Test suite ensuring all HTML views and JSON API endpoints load correctly."""

    def test_frontend_pages_render_successfully(self):
        """Verify that all main dashboard, listing, and report pages load (status 200)."""
        self.client.login(username=str(self.test_employee.employee_id), password="CAr$@lse2014")
        urls = [
            'home',
            'employee',
            'country',
            'city',
            'store',
            'emprole',
            'status',
            'industry',
            'vehicle',
            'customer',
            'selling',
            'budget',
            'employee_report',
            'vehicle_report',
            'sales_report',
            'customer_vehicle_report',
        ]
        for url_name in urls:
            url = reverse(url_name)
            response = self.client.get(url)
            self.assertEqual(
                response.status_code, 200,
                f"Page reverse('{url_name}') returned status code {response.status_code} instead of 200."
            )

        # Login as staff user for restricted API pages
        self.client.login(username=str(self.manager_employee.employee_id), password="CAr$@lse2014")
        restricted_urls = [
            'employee_sales_page_view',
            'store_sales_page_view',
            'store_vehicle_sales_page_view',
            'customer_vehicle_sales_page_view',
            'customer_store_spending_page_view'
        ]
        for url_name in restricted_urls:
            url = reverse(url_name)
            response = self.client.get(url)
            self.assertEqual(
                response.status_code, 200,
                f"Restricted page reverse('{url_name}') returned status code {response.status_code} instead of 200."
            )

    def test_employee_sales_api_endpoints(self):
        """Verify that the employee sales API returns 200 for valid ranges and 400 for bad ranges."""
        url = reverse('employee_sales_api')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
        
        self.client.login(username=str(self.manager_employee.employee_id), password="CAr$@lse2014")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['status'])

        response = self.client.get(url, {'dt_from': '2014-01-01', 'dt_to': '2015-12-31'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['status'])
        self.assertIsInstance(data['data'], list)

    def test_store_sales_api_endpoints(self):
        """Verify that the store sales API returns 200 for valid ranges and 400 for bad ranges."""
        url = reverse('store_sales_api')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
        
        self.client.login(username=str(self.manager_employee.employee_id), password="CAr$@lse2014")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['status'])

        response = self.client.get(url, {'dt_from': '2014-01-01', 'dt_to': '2015-12-31'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['status'])
        self.assertIsInstance(data['data'], list)

    def test_store_vehicle_sales_api_endpoints(self):
        """Verify that the store vehicle sales API returns 200 for valid ranges and 400 for bad ranges."""
        url = reverse('store_vehicle_sales_api')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
        
        self.client.login(username=str(self.manager_employee.employee_id), password="CAr$@lse2014")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['status'])

        response = self.client.get(url, {'dt_from': '2014-01-01', 'dt_to': '2015-12-31'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['status'])
        self.assertIsInstance(data['data'], list)

    def test_customer_vehicle_sales_api_endpoints(self):
        """Verify that the customer vehicle sales API returns 200 for valid ranges and 400 for bad ranges."""
        url = reverse('customer_vehicle_sales_api')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
        
        self.client.login(username=str(self.manager_employee.employee_id), password="CAr$@lse2014")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['status'])

        response = self.client.get(url, {'dt_from': '2014-01-01', 'dt_to': '2015-12-31'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['status'])
        self.assertIsInstance(data['data'], list)

    def test_customer_store_spending_api_endpoints(self):
        """Verify that the customer store spending API returns 200 for valid ranges and 400 for bad ranges."""
        url = reverse('customer_store_spending_api')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
        
        self.client.login(username=str(self.manager_employee.employee_id), password="CAr$@lse2014")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['status'])

        response = self.client.get(url, {'dt_from': '2014-01-01', 'dt_to': '2015-12-31'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['status'])
        self.assertIsInstance(data['data'], list)


class CustomAuthTestCase(CarSalesBaseTestCase):
    """Test suite verifying custom authentication, login, registration, and logout flows."""

    def setUp(self):
        super().setUp()
        self.login_url = reverse('login')
        self.register_url = reverse('register')
        self.logout_url = reverse('logout')
        
        self.employee = Employee.objects.create(
            first_name="Jane",
            last_name="Doe",
            date_of_joining=datetime.date(2020, 1, 1),
            employee_addr="123 Test St",
            employee_role=self.role,
            status=self.status_active,
            store=self.store,
            city=self.city,
            country=self.country,
            password="CAr$@lse2014"
        )

    def test_login_view_get(self):
        """GET request to login page should render login form."""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'car_sales/login.html')

    def test_login_view_post_employee_id_success(self):
        """POST with valid Employee ID and password should authenticate and redirect to home."""
        response = self.client.post(self.login_url, {
            'username': str(self.employee.employee_id),
            'password': 'CAr$@lse2014'
        })
        self.assertRedirects(response, reverse('home'))

    def test_login_view_post_employee_id_failure(self):
        """POST with valid Employee ID but incorrect password should fail."""
        response = self.client.post(self.login_url, {
            'username': str(self.employee.employee_id),
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'car_sales/login.html')
        self.assertContains(response, "Invalid username or password.")

    def test_login_terminated_employee_failure(self):
        """Terminated employee should not be allowed to log in."""
        terminated_status, _ = EmployeeStatus.objects.get_or_create(status="Terminated")
        term_employee = Employee.objects.create(
            first_name="Terminated",
            last_name="User",
            date_of_joining=datetime.date(2020, 1, 1),
            employee_addr="123 Test St",
            employee_role=self.role,
            status=terminated_status,
            store=self.store,
            city=self.city,
            country=self.country,
            password="CAr$@lse2014"
        )
        response = self.client.post(self.login_url, {
            'username': str(term_employee.employee_id),
            'password': 'CAr$@lse2014'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'car_sales/login.html')
        self.assertContains(response, "Invalid username or password.")

    def test_logout_view(self):
        """Request to logout view should terminate session and redirect to login."""
        self.client.post(self.login_url, {
            'username': str(self.employee.employee_id),
            'password': 'CAr$@lse2014'
        })
        response = self.client.post(self.logout_url)
        self.assertRedirects(response, self.login_url)

    def test_create_employee_view_denied_for_non_staff(self):
        """Non-staff user should be redirected to login when trying to access create employee page."""
        response = self.client.get(reverse('create_employee'))
        self.assertEqual(response.status_code, 302)

    def test_create_employee_view_get_success_for_staff(self):
        """Staff user should be able to load the create employee form."""
        self.client.login(username=str(self.manager_employee.employee_id), password="CAr$@lse2014")
        response = self.client.get(reverse('create_employee'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'car_sales/create_employee.html')

    def test_create_employee_view_post_success(self):
        """Staff user can successfully create a new employee."""
        self.client.login(username=str(self.manager_employee.employee_id), password="CAr$@lse2014")
        
        post_data = {
            'first_name': 'John',
            'last_name': 'Smith',
            'date_of_joining': '2026-07-05',
            'employee_addr': '456 Elm St',
            'employee_role': self.role.role_id,
            'status': self.status_active.status_id,
            'store': self.store.store_id,
            'city': self.city.city_id,
            'country': self.country.country_id,
            'password': 'SecurePassword123'
        }
        response = self.client.post(reverse('create_employee'), post_data)
        self.assertRedirects(response, reverse('employee'))
        
        # Verify employee is created
        emp = Employee.objects.filter(first_name='John', last_name='Smith').first()
        self.assertIsNotNone(emp)
        self.assertEqual(emp.employee_addr, '456 Elm St')
        self.assertEqual(emp.password, 'SecurePassword123')

    def test_user_registration_via_view(self):
        """Standard user registration view creates a User and logs them in."""
        response = self.client.post(self.register_url, {
            'name': 'Register User',
            'email': 'register@test.com',
            'username': 'register_user',
            'password': 'Password123',
            'terms': 'on'
        })
        self.assertRedirects(response, reverse('home'))
        
        # Verify User was created
        user_exists = User.objects.filter(username='register_user').exists()
        self.assertTrue(user_exists)
