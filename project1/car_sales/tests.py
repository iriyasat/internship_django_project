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

    def test_inventory_crud_api_endpoints(self):
        """Verify that the inventory CRUD API handles GET, POST, PUT, DELETE with auth restrictions."""
        list_url = reverse('inventory_api')
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, 401)

        # Create base models for testing
        from .models import Inventory, VehicleInfo
        make = IndustryInfo.objects.create(make_name="TestMake")
        vehicle = VehicleInfo.objects.create(vehicle_model="TestModel", make=make, mmr=15000, vin="TESTVIN1234567890")
        vehicle2 = VehicleInfo.objects.create(vehicle_model="TestModel2", make=make, mmr=16000, vin="TESTVIN0987654321")
        
        self.client.login(username=str(self.manager_employee.employee_id), password="CAr$@lse2014")
        
        item = Inventory.objects.create(
            vehicle=vehicle,
            store=self.store,
            employee=self.test_employee,
            status=4 # Available
        )
        
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['status'])
        self.assertGreaterEqual(data['total'], 1)
        
        detail_url = reverse('inventory_api_detail', kwargs={'pk': item.inventory_id})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['inventory_id'], item.inventory_id)

        post_data = {
            'vehicle': vehicle2.id,
            'store': self.store.store_id,
            'employee': self.test_employee.employee_id,
            'status': 4
        }
        response = self.client.post(list_url, post_data, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        new_item_id = response.json()['data']['inventory_id']
        
        put_data = {
            'status': 1 # Sold
        }
        detail_url_new = reverse('inventory_api_detail', kwargs={'pk': new_item_id})
        response = self.client.put(detail_url_new, put_data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Inventory.objects.get(pk=new_item_id).status, 1)

        response = self.client.delete(detail_url_new)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Inventory.objects.filter(pk=new_item_id).exists())

        self.client.logout()
        self.client.login(username=str(self.test_employee.employee_id), password="CAr$@lse2014")
        
        response = self.client.post(list_url, post_data, content_type='application/json')
        self.assertEqual(response.status_code, 403)


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


class RoleHierarchyPermissionTestCase(CarSalesBaseTestCase):
    """
    Test suite verifying the detailed role hierarchy, access controls,
    and CRUD permissions across Sales Executives, Branch Managers, and Admins.
    """

    def setUp(self):
        super().setUp()
        from .models import CustomerInfo, SellingInfo, IndustryInfo, VehicleInfo
        # Ensure we have active status
        self.status_in_service = EmployeeStatus.objects.get(status="In Service")
        
        # Create a second store and some employees for cross-store restriction tests
        self.other_city = City.objects.create(city_name="Other City", country=self.country)
        self.other_store = Store.objects.create(
            store_name="Other Store",
            store_code="ST99",
            city=self.other_city,
            country=self.country,
            address="99 Other St"
        )
        
        self.other_employee = Employee.objects.create(
            first_name="John",
            last_name="Smith",
            date_of_joining=datetime.date(2021, 1, 1),
            employee_addr="456 Other Rd",
            employee_role=self.role, # Sales Executive
            status=self.status_in_service,
            store=self.other_store,
            city=self.other_city,
            country=self.country,
            password="CAr$@lse2014"
        )

        # Create industry & vehicle
        self.make = IndustryInfo.objects.get_or_create(make_name="RoleTestMake")[0]
        self.vehicle = VehicleInfo.objects.get_or_create(
            vehicle_model="RoleTestModel",
            make=self.make,
            mmr=20000,
            vin="ROLEVIN1234567890"
        )[0]
        
    def test_sales_executive_crud_permissions(self):
        """Sales Executives can create customers and sales, but only for themselves/their store."""
        self.client.login(username=str(self.test_employee.employee_id), password="CAr$@lse2014")

        # 1. Can create customer info
        customer_data = {
            "firstname": "Role",
            "lastname": "Customer",
            "customer_status": "Active",
            "customer_address": "123 Main St",
            "city": self.city.city_id,
            "country": self.country.country_id
        }
        response = self.client.post(reverse('customer_api'), customer_data, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        customer_id = response.json()['data']['customer_id']

        # 2. Can create a sale for themselves and their store
        sale_data = {
            "customer": customer_id,
            "vehicle": self.vehicle.id,
            "employee": self.test_employee.employee_id,
            "store": self.store.store_id,
            "selling_price": 21000,
            "selling_date": "2026-07-15"
        }
        response = self.client.post(reverse('sales_api'), sale_data, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        sale_id = response.json()['data']['sell_id']

        # 3. Cannot create a sale for another employee/store
        bad_sale_data = {
            "customer": customer_id,
            "vehicle": self.vehicle.id,
            "employee": self.other_employee.employee_id,
            "store": self.other_store.store_id,
            "selling_price": 21000,
            "selling_date": "2026-07-15"
        }
        response = self.client.post(reverse('sales_api'), bad_sale_data, content_type='application/json')
        self.assertEqual(response.status_code, 403)

        # 4. Cannot delete the sale they just created (deletes restricted to managers/admins)
        response = self.client.delete(reverse('sales_api_detail', kwargs={'pk': sale_id}))
        self.assertEqual(response.status_code, 403)

        self.client.logout()

    def test_branch_manager_hierarchy_restrictions(self):
        """Branch Managers can view and manage sales in their store, but not in other stores."""
        # Log in as Branch Manager for self.store
        self.client.login(username=str(self.manager_employee.employee_id), password="CAr$@lse2014")

        # 1. Create a customer and sale for store 1 (manager's store)
        customer = CustomerInfo.objects.create(
            firstname="Cust", lastname="Store1", customer_status="Active", customer_address="Add", city=self.city, country=self.country
        )
        sale_store1 = SellingInfo.objects.create(
            customer=customer, vehicle=self.vehicle, employee=self.test_employee, store=self.store, selling_price=22000, selling_date=datetime.date(2026, 7, 15)
        )

        # 2. Create a sale for the other store
        sale_store2 = SellingInfo.objects.create(
            customer=customer, vehicle=self.vehicle, employee=self.other_employee, store=self.other_store, selling_price=23000, selling_date=datetime.date(2026, 7, 15)
        )

        # 3. Manager can view their store's sale
        response = self.client.get(reverse('sales_api_detail', kwargs={'pk': sale_store1.sell_id}))
        self.assertEqual(response.status_code, 200)

        # 4. Manager cannot view the other store's sale
        response = self.client.get(reverse('sales_api_detail', kwargs={'pk': sale_store2.sell_id}))
        self.assertEqual(response.status_code, 403)

        # 5. Manager cannot delete the other store's sale
        response = self.client.delete(reverse('sales_api_detail', kwargs={'pk': sale_store2.sell_id}))
        self.assertEqual(response.status_code, 403)

        self.client.logout()
