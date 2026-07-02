import datetime
from django.test import TestCase
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.contrib.auth.models import User
from .models import (
    Country, City, Store, EmployeeRole, EmployeeStatus,
    Employee, IndustryInfo, VehicleInfo, CustomerInfo,
    SellingInfo, EmployeeBudget
)

class CarSalesBaseTestCase(TestCase):
    """
    Base test case containing shared setup data using setUpTestData.
    This class-level database setup runs once per test class for optimal performance.
    """

    @classmethod
    def setUpTestData(cls):
        # 1. Create Country & City
        cls.country = Country.objects.create(country_name="United States")
        cls.city = City.objects.create(city_name="New York", country=cls.country)

        # 2. Create Store
        cls.store = Store.objects.create(
            store_name="New York Motors",
            store_code="ST0001",
            city=cls.city,
            country=cls.country,
            address="26 Highway Rd, New York"
        )

        # 3. Create Employee Role and Statuses
        cls.role = EmployeeRole.objects.create(role_name="Sales Executive")
        cls.status_in_service = EmployeeStatus.objects.create(status="In Service")
        cls.status_active = EmployeeStatus.objects.create(status="Active")


class CarSalesModelTestCase(CarSalesBaseTestCase):
    """Test suite verifying basic model relationships and unique constraints."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # 4. Create Employee
        cls.employee = Employee.objects.create(
            first_name="Robert",
            last_name="Rossi",
            date_of_joining=datetime.date(2010, 1, 13),
            employee_addr="5863 Elm St, Osaka",
            employee_role=cls.role,
            status=cls.status_in_service,
            store=cls.store,
            city=cls.city,
            country=cls.country
        )

        # 5. Create Industry Info (Make)
        cls.make = IndustryInfo.objects.create(make_name="Toyota")

        # 6. Create Vehicle Info
        cls.vehicle = VehicleInfo.objects.create(
            vehicle_model="Camry",
            make=cls.make,
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
        cls.customer = CustomerInfo.objects.create(
            firstname="Robert",
            lastname="Nguyen",
            customer_status="Regular",
            customer_address="6341 Broadway, Melbourne",
            city=cls.city,
            country=cls.country
        )

    def test_model_creation(self):
        """Verify that basic objects are created successfully with correct properties."""
        self.assertEqual(self.country.country_name, "United States")
        self.assertEqual(self.city.city_name, "New York")
        self.assertEqual(self.store.store_code, "ST0001")
        self.assertEqual(self.role.role_name, "Sales Executive")
        self.assertEqual(self.status_in_service.status, "In Service")
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


class CarSalesCrudTestCase(CarSalesBaseTestCase):
    """Advanced test suite verifying permissions and CRUD validation on administrative views."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # Create users
        cls.admin_user = User.objects.create_user(username="admin", password="password123", is_staff=True)
        cls.regular_user = User.objects.create_user(username="regular", password="password123", is_staff=False)
        
        # Test targets
        cls.make = IndustryInfo.objects.create(make_name="Ford")
        cls.vehicle = VehicleInfo.objects.create(vehicle_model="F-150", make=cls.make, mmr=22000, vin="FORDVIN123")
        cls.customer = CustomerInfo.objects.create(firstname="Mark", lastname="Sloan", customer_status="Regular", city=cls.city, country=cls.country)
        cls.employee = Employee.objects.create(
            first_name="Jane", last_name="Doe", date_of_joining=datetime.date(2020, 1, 1),
            employee_role=cls.role, status=cls.status_active, store=cls.store, city=cls.city, country=cls.country
        )

    def test_anonymous_user_crud_denied(self):
        """Verify that anonymous users are redirected/blocked from CRUD endpoints."""
        for model in ['customerinfo', 'vehicleinfo', 'sellinginfo']:
            url = reverse('admin_crud', args=[model, 'create'])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn('login', response.url)

    def test_regular_user_crud_denied(self):
        """Verify that authenticated regular users are redirected/blocked from CRUD endpoints."""
        self.client.login(username="regular", password="password123")
        for model in ['customerinfo', 'vehicleinfo', 'sellinginfo']:
            url = reverse('admin_crud', args=[model, 'create'])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn('login', response.url)

    def test_staff_user_crud_allowed(self):
        """Verify that staff/admin users can access CRUD creation forms."""
        self.client.login(username="admin", password="password123")
        for model in ['customerinfo', 'vehicleinfo', 'sellinginfo']:
            url = reverse('admin_crud', args=[model, 'create'])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

    def test_admin_crud_nonexistent_model(self):
        """Verify requesting CRUD endpoints on a nonexistent model returns 404."""
        self.client.login(username="admin", password="password123")
        url = reverse('admin_crud', args=['invalidmodel', 'create'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_selling_info_custom_form_validation(self):
        """Verify custom SellingInfo form validation and record creation via POST."""
        self.client.login(username="admin", password="password123")
        url = reverse('admin_crud', args=['sellinginfo', 'create'])
        
        # 1. Invalid submit: Customer and Vehicle IDs do not exist
        invalid_data = {
            'customer': 9999,
            'vehicle': 9999,
            'employee': self.employee.employee_id,
            'store': self.store.store_id,
            'selling_price': 25000,
            'selling_date': '2026-06-01'
        }
        response = self.client.post(url, invalid_data)
        self.assertEqual(response.status_code, 200) # Returns 200 to render validation errors
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
        self.assertEqual(response.status_code, 302) # Redirects on success
        self.assertTrue(SellingInfo.objects.filter(selling_price=25000).exists())


class EmployeeReportTestCase(CarSalesBaseTestCase):
    """Test suite verifying the employee performance report views and pagination boundaries."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.test_user = User.objects.create_user(username="testuser", password="testpassword123")
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
        self.client.login(username="testuser", password="testpassword123")

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
        # 1. Non-integer page parameter
        response = self.client.get(self.url, {'page': 'notaninteger'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['employee_leaderboard'].number, 1)

        # 2. Page number out of bounds
        response = self.client.get(self.url, {'page': '99999'})
        self.assertEqual(response.status_code, 200)
        # Django paginator get_page returns the last page if out of bounds
        self.assertEqual(response.context['employee_leaderboard'].number, 1)


class ReportJsonExportTestCase(CarSalesBaseTestCase):
    """Test suite verifying the JSON export format and error handling on empty data filters."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.test_user = User.objects.create_user(username="testuser", password="testpassword123")
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

    def setUp(self):
        self.client.login(username="testuser", password="testpassword123")

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

    def test_json_download_date_filter_boundary_no_records(self):
        """Verify that JSON download works correctly and returns empty datasets when filters match no data."""
        # Query date range outside our setup sale date (2026-06-01)
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

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # Set up a staff user to test logged-in status if pages require login.
        cls.user = User.objects.create_user(username="testuser", password="testpassword123")
        cls.staff_user = User.objects.create_user(username="staffuser", password="testpassword123", is_staff=True)

    def test_frontend_pages_render_successfully(self):
        """Verify that all main dashboard, listing, and report pages load (status 200)."""
        self.client.login(username="testuser", password="testpassword123")
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
        ]
        for url_name in urls:
            url = reverse(url_name)
            response = self.client.get(url)
            self.assertEqual(
                response.status_code, 200,
                f"Page reverse('{url_name}') returned status code {response.status_code} instead of 200."
            )

        # Login as staff user for restricted API pages
        self.client.login(username="staffuser", password="testpassword123")
        restricted_urls = [
            'employee_sales_page_view',
            'store_sales_page_view',
            'store_vehicle_sales_page_view'
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
        
        # 1. Without login (should return 401)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
        
        # Log in as staff
        self.client.login(username="staffuser", password="testpassword123")
        
        # 2. No parameters (should return 400)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['status'])

        # 3. Valid range (should return 200)
        response = self.client.get(url, {'dt_from': '2014-01-01', 'dt_to': '2015-12-31'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['status'])
        self.assertIsInstance(data['data'], list)

    def test_store_sales_api_endpoints(self):
        """Verify that the store sales API returns 200 for valid ranges and 400 for bad ranges."""
        url = reverse('store_sales_api')
        
        # 1. Without login (should return 401)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
        
        # Log in as staff
        self.client.login(username="staffuser", password="testpassword123")
        
        # 2. No parameters (should return 400)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['status'])

        # 3. Valid range (should return 200)
        response = self.client.get(url, {'dt_from': '2014-01-01', 'dt_to': '2015-12-31'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['status'])
        self.assertIsInstance(data['data'], list)

    def test_store_vehicle_sales_api_endpoints(self):
        """Verify that the store vehicle sales API returns 200 for valid ranges and 400 for bad ranges."""
        url = reverse('store_vehicle_sales_api')
        
        # 1. Without login (should return 401)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
        
        # Log in as staff
        self.client.login(username="staffuser", password="testpassword123")
        
        # 2. No parameters (should return 400)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['status'])

        # 3. Valid range (should return 200)
        response = self.client.get(url, {'dt_from': '2014-01-01', 'dt_to': '2015-12-31'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['status'])
        self.assertIsInstance(data['data'], list)


class CustomAuthTestCase(CarSalesBaseTestCase):
    """Test suite verifying custom authentication, login, registration, and logout flows."""

    def setUp(self):
        self.login_url = reverse('login')
        self.register_url = reverse('register')
        self.logout_url = reverse('logout')
        self.user = User.objects.create_user(username="validuser", email="valid@example.com", password="password123")
        
        # Create a test employee with a default password
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

    def test_login_view_post_django_user_fallback_success(self):
        """POST with valid standard Django user credentials should authenticate and redirect to home."""
        response = self.client.post(self.login_url, {
            'username': 'validuser',
            'password': 'password123'
        })
        self.assertRedirects(response, reverse('home'))

    def test_login_terminated_employee_failure(self):
        """Terminated employee should not be allowed to log in."""
        terminated_status = EmployeeStatus.objects.create(status="Terminated")
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
        self.client.login(username="validuser", password="password123")
        response = self.client.post(self.logout_url)
        self.assertRedirects(response, self.login_url)


