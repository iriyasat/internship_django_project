import datetime
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import (
    City,
    Country,
    Customer,
    Employee,
    EmployeeRole,
    EmployeeStatus,
    EmployeeTarget,
    Lead,
    LeadActivity,
    LeadActivityType,
    Payment,
    PaymentMethod,
    Phone,
    Sale,
    TradeIn,
    Vehicle,
    VehicleModel,
    LeadSource,
    VehicleImage,
    VehicleService,
    FinanceApplication,
    Manufacturer,
)


class CarSalesModelTestCase(TestCase):
    """Test suite verifying the behavior of Django models mapping the dealership schema."""

    def setUp(self):
        # Create Lookup Tables Data
        self.role = EmployeeRole.objects.create(role_name="Sales Executive")
        self.status_active = EmployeeStatus.objects.create(status_name="Active")
        
        self.payment_method_bank = PaymentMethod.objects.create(payment_method_name="Bank Transfer")
        self.payment_method_cash = PaymentMethod.objects.create(payment_method_name="Cash")

        # Create Country and City
        self.country = Country.objects.create(country_name="USA")
        self.city_obj = City.objects.create(city_name="Metropolis", country=self.country)

        # Create Phone Numbers
        self.phone_emp = Phone.objects.create(phone_number="+8801712345678")
        self.phone_cust = Phone.objects.create(phone_number="+8801812345678")

        # Create an Employee
        self.employee = Employee.objects.create(
            role=self.role,
            first_name="Jane",
            last_name="Doe",
            email="jane.doe@dealership.com",
            phone=self.phone_emp,
            emp_address="12/A Main St",
            emp_city=self.city_obj,
            emp_country=self.country,
            status=self.status_active,
        )

        # Create a Customer
        self.customer = Customer.objects.create(
            first_name="John",
            last_name="Smith",
            email="john.smith@gmail.com",
            phone=self.phone_cust,
            customer_address="12/A Main St",
            customer_city=self.city_obj,
            customer_country=self.country,
        )

        # Create a Manufacturer
        self.manufacturer = Manufacturer.objects.create(manufacturer_name="Toyota")

        # Create a Vehicle Model
        self.vehicle_model = VehicleModel.objects.create(
            manufacturer=self.manufacturer,
            model="Camry",
            trim="SE",
            body_type="Sedan",
            fuel_type="Gasoline",
        )

        # Create a Vehicle
        self.vehicle = Vehicle.objects.create(
            model=self.vehicle_model,
            vin="1YV1Y111111111111",
            year=2024,
            color="Silver",
            mileage=50,
            acquisition_cost=Decimal("20000.00"),
            selling_price=Decimal("25000.00"),
            condition=Vehicle.Condition.NEW,
            status=Vehicle.Status.AVAILABLE,
            date_acquired=datetime.date(2026, 6, 1),
            date_listed=datetime.date(2026, 6, 5),
        )

        # Create LeadActivityType
        self.activity_call = LeadActivityType.objects.create(lead_activity_type_name="Call")

        # Create LeadSource
        self.lead_source = LeadSource.objects.create(source_name="Website")

        # Create a Lead
        self.lead = Lead.objects.create(
            customer=self.customer,
            vehicle=self.vehicle,
            employee=self.employee,
            source=self.lead_source,
            status=Lead.Status.QUALIFIED,
        )

    def test_str_representations(self):
        """Test the __str__ methods of various models."""
        self.assertEqual(str(self.role), "Sales Executive")
        self.assertEqual(str(self.status_active), "Active")
        self.assertEqual(str(self.country), "USA")
        self.assertEqual(str(self.city_obj), "Metropolis, USA")
        self.assertEqual(str(self.phone_emp), "+8801712345678")
        self.assertEqual(str(self.employee), "Jane Doe")
        self.assertEqual(str(self.customer), "John Smith")
        self.assertEqual(str(self.manufacturer), "Toyota")
        self.assertEqual(str(self.vehicle_model), "Toyota Camry SE")
        self.assertEqual(str(self.vehicle), "2024 Toyota Camry (VIN: 1YV1Y111111111111)")
        self.assertEqual(str(self.lead), f"Lead #{self.lead.lead_id} - John Smith (QUALIFIED)")
        self.assertEqual(str(self.lead_source), "Website")

    def test_employee_properties(self):
        """Test properties defined on the Employee model."""
        self.assertEqual(self.employee.full_name, "Jane Doe")

    def test_customer_properties(self):
        """Test properties defined on the Customer model."""
        self.assertEqual(self.customer.full_name, "John Smith")

    def test_lead_soft_delete(self):
        """Test soft-delete functionality on the Lead model."""
        lead_id = self.lead.lead_id
        # Confirm it exists in active leads
        self.assertTrue(Lead.objects.filter(pk=lead_id).exists())

        # Perform soft delete
        self.lead.delete()

        # Confirm it is no longer in the default manager's active leads
        self.assertFalse(Lead.objects.filter(pk=lead_id).exists())

        # Confirm it is present in all_with_deleted queryset
        self.assertTrue(Lead.objects.all_with_deleted().filter(pk=lead_id).exists())
        deleted_lead = Lead.objects.all_with_deleted().get(pk=lead_id)
        self.assertIsNotNone(deleted_lead.deleted_at)

        # Restore lead
        deleted_lead.restore()
        self.assertIsNone(deleted_lead.deleted_at)
        self.assertTrue(Lead.objects.filter(pk=lead_id).exists())

        # Perform permanent hard delete
        deleted_lead.hard_delete()
        self.assertFalse(Lead.objects.all_with_deleted().filter(pk=lead_id).exists())

    def test_lead_activity_creation(self):
        """Test that lead activities are properly logged and mapped."""
        activity = LeadActivity.objects.create(
            lead=self.lead,
            employee=self.employee,
            activity_type=self.activity_call,
            details="Called the customer to discuss pricing details.",
        )
        self.assertEqual(activity.lead, self.lead)
        self.assertEqual(activity.employee, self.employee)
        self.assertEqual(activity.activity_type, self.activity_call)
        self.assertIn("Call on", str(activity))

    def test_sale_financial_properties(self):
        """Test pricing and commission calculations on the Sale model."""
        # Create a Sale
        sale = Sale.objects.create(
            lead=self.lead,
            employee=self.employee,
            vehicle=self.vehicle,
            base_price=Decimal("24500.00"),
            discount_amount=Decimal("1000.00"),
            tax_amount=Decimal("1500.00"),
            commission_rate_applied=Decimal("4.50"),  # 4.5%
        )

        # total_price = base_price - discount_amount + tax_amount
        # 24500 - 1000 + 1500 = 25000
        self.assertEqual(sale.total_price, Decimal("25000.00"))

        # commission_earned = (base_price - discount_amount) * commission_rate_applied / 100
        # (24500 - 1000) * 4.5 / 100 = 23500 * 0.045 = 1057.50
        self.assertEqual(sale.commission_earned, Decimal("1057.50"))

    def test_payment_validation(self):
        """Test constraints and custom validation rules on the Payment model."""
        sale = Sale.objects.create(
            lead=self.lead,
            employee=self.employee,
            vehicle=self.vehicle,
            base_price=Decimal("24500.00"),
            commission_rate_applied=Decimal("5.00"),
        )

        # Valid Payment
        payment = Payment.objects.create(
            sale=sale,
            amount=Decimal("5000.00"),
            payment_method=self.payment_method_bank,
            status=Payment.Status.COMPLETED,
        )
        self.assertEqual(payment.status, Payment.Status.COMPLETED)

        # Invalid Payment (amount <= 0) should fail model validation
        invalid_payment = Payment(
            sale=sale,
            amount=Decimal("0.00"),
            payment_method=self.payment_method_cash,
            status=Payment.Status.PENDING,
        )
        with self.assertRaises(ValidationError):
            invalid_payment.full_clean()

    def test_phone_validation(self):
        """Test constraints and validation rules on the Phone model."""
        # Valid Phone Number
        valid_phone = Phone(phone_number="+8801912345678")
        try:
            valid_phone.full_clean()
        except ValidationError:
            self.fail("ValidationError raised on a valid Bangladesh phone number")

        # Invalid Phone Number (Format check)
        invalid_phone = Phone(phone_number="01712345678")
        with self.assertRaises(ValidationError):
            invalid_phone.full_clean()

        # Invalid Phone Number (Length check)
        invalid_phone_long = Phone(phone_number="+88017123456789")
        with self.assertRaises(ValidationError):
            invalid_phone_long.full_clean()

    def test_employee_dates_validation(self):
        """Test validation rules for employee hire/termination dates and leave dates."""
        # 1. Invalid Terminated Date (before hire_date)
        invalid_employee_termination = Employee(
            role=self.role,
            first_name="John",
            last_name="Doe",
            email="john.doe.invalid@dealership.com",
            phone=self.phone_emp,
            emp_address="12/A Main St",
            emp_city=self.city_obj,
            emp_country=self.country,
            status=self.status_active,
            hire_date=datetime.date(2026, 6, 20),
            terminated_date=datetime.date(2026, 6, 19),
        )
        with self.assertRaises(ValidationError):
            invalid_employee_termination.full_clean()

        # 2. Invalid Leave Dates (leave_end_date before leave_start_date)
        invalid_employee_leave = Employee(
            role=self.role,
            first_name="Jane",
            last_name="Smith",
            email="jane.smith.invalid@dealership.com",
            phone=self.phone_emp,
            emp_address="12/A Main St",
            emp_city=self.city_obj,
            emp_country=self.country,
            status=self.status_active,
            hire_date=datetime.date(2026, 6, 20),
            leave_start_date=datetime.date(2026, 6, 25),
            leave_end_date=datetime.date(2026, 6, 24),
        )
        with self.assertRaises(ValidationError):
            invalid_employee_leave.full_clean()

    def test_employee_target_validation(self):
        """Test validation rules for EmployeeTarget dates and constraint checks."""
        # 1. Valid EmployeeTarget creation
        target = EmployeeTarget.objects.create(
            employee=self.employee,
            target_goal=10,
            commission_percentage=Decimal("5.00"),
            start_date=datetime.date(2026, 6, 1),
            end_date=datetime.date(2026, 6, 30),
        )
        self.assertEqual(target.employee, self.employee)
        self.assertEqual(target.target_goal, 10)
        self.assertEqual(target.commission_percentage, Decimal("5.00"))
        self.assertEqual(str(target), "Target for Jane Doe: 10 products (5.00%)")

        # 2. Invalid EmployeeTarget dates (end_date before start_date)
        invalid_target = EmployeeTarget(
            employee=self.employee,
            target_goal=10,
            commission_percentage=Decimal("5.00"),
            start_date=datetime.date(2026, 6, 30),
            end_date=datetime.date(2026, 6, 1),
        )
        with self.assertRaises(ValidationError):
            invalid_target.full_clean()

        # 3. Invalid commission percentage (out of range [0, 100])
        invalid_percentage_high = EmployeeTarget(
            employee=self.employee,
            target_goal=5,
            commission_percentage=Decimal("101.50"),
            start_date=datetime.date(2026, 6, 1),
            end_date=datetime.date(2026, 6, 30),
        )
        with self.assertRaises(ValidationError):
            invalid_percentage_high.full_clean()

        invalid_percentage_low = EmployeeTarget(
            employee=self.employee,
            target_goal=5,
            commission_percentage=Decimal("-1.00"),
            start_date=datetime.date(2026, 6, 1),
            end_date=datetime.date(2026, 6, 30),
        )
        with self.assertRaises(ValidationError):
            invalid_percentage_low.full_clean()

    def test_vehicle_dates_validation(self):
        """Test validation rules for vehicle acquisition and list dates."""
        # Invalid date_listed (before date_acquired)
        invalid_vehicle = Vehicle(
            model=self.vehicle_model,
            vin="2YV2Y222222222222",
            year=2024,
            color="Red",
            mileage=100,
            acquisition_cost=Decimal("15000.00"),
            selling_price=Decimal("18000.00"),
            condition=Vehicle.Condition.USED,
            status=Vehicle.Status.AVAILABLE,
            date_acquired=datetime.date(2026, 6, 10),
            date_listed=datetime.date(2026, 6, 9),
        )
        with self.assertRaises(ValidationError):
            invalid_vehicle.full_clean()

    def test_new_schema_enhancements(self):
        """Test the new fields, validation, and models added to the schema."""
        # 1. Test VIN pattern validation (RegexValidator)
        # Invalid VIN: contains 'I' (invalid character)
        invalid_vin_vehicle = Vehicle(
            model=self.vehicle_model,
            vin="1YV1Y1I1111111111",  # 'I' is invalid
            year=2024,
            color="Silver",
            mileage=50,
            acquisition_cost=Decimal("20000.00"),
            selling_price=Decimal("25000.00"),
            condition=Vehicle.Condition.NEW,
            status=Vehicle.Status.AVAILABLE,
            date_acquired=datetime.date(2026, 6, 1),
        )
        with self.assertRaises(ValidationError) as ctx:
            invalid_vin_vehicle.full_clean()
        self.assertIn("vin", ctx.exception.message_dict)

        # 2. Test Customer Notes
        self.customer.notes = "Looking for a family SUV."
        self.customer.save()
        self.assertEqual(Customer.objects.get(pk=self.customer.pk).notes, "Looking for a family SUV.")

        # 3. Test Audit Fields
        self.assertIsNotNone(self.customer.created_at)
        self.assertIsNotNone(self.customer.updated_at)
        self.assertIsNotNone(self.employee.created_at)
        self.assertIsNotNone(self.employee.updated_at)
        self.assertIsNotNone(self.vehicle.created_at)
        self.assertIsNotNone(self.vehicle.updated_at)

        # 4. Test Sale customer auto-population and status
        sale = Sale.objects.create(
            lead=self.lead,
            employee=self.employee,
            vehicle=self.vehicle,
            base_price=Decimal("24500.00"),
            discount_amount=Decimal("1000.00"),
            tax_amount=Decimal("1500.00"),
            commission_rate_applied=Decimal("4.50"),
        )
        # Verify customer was automatically set from lead
        self.assertEqual(sale.customer, self.customer)
        # Verify default status is PENDING
        self.assertEqual(sale.status, Sale.Status.PENDING)
        # Verify commission_amount is auto-calculated: (24500 - 1000) * 4.5 / 100 = 1057.50
        self.assertEqual(sale.commission_amount, Decimal("1057.50"))
        self.assertEqual(sale.commission_earned, Decimal("1057.50"))

        # Test pre-calculated commission amount behavior
        vehicle2 = Vehicle.objects.create(
            model=self.vehicle_model,
            vin="1YV1Y222222222222",
            year=2024,
            color="Blue",
            mileage=150,
            acquisition_cost=Decimal("18000.00"),
            selling_price=Decimal("22000.00"),
            condition=Vehicle.Condition.USED,
            status=Vehicle.Status.AVAILABLE,
            date_acquired=datetime.date(2026, 6, 1),
        )
        sale_with_manual_comm = Sale.objects.create(
            customer=self.customer,
            employee=self.employee,
            vehicle=vehicle2,
            base_price=Decimal("20000.00"),
            commission_rate_applied=Decimal("5.00"),
            commission_amount=Decimal("1200.00"),  # manual amount overriding formula
        )
        self.assertEqual(sale_with_manual_comm.commission_earned, Decimal("1200.00"))

        # 5. Test VehicleImage creation
        vehicle_image = VehicleImage.objects.create(
            vehicle=self.vehicle,
            image="vehicles/toyota_camry.jpg",
            is_primary=True,
        )
        self.assertEqual(str(vehicle_image), f"Image #{vehicle_image.image_id} for Vehicle VIN: {self.vehicle.vin}")

        # 6. Test VehicleService creation
        service = VehicleService.objects.create(
            vehicle=self.vehicle,
            service_date=datetime.date(2026, 6, 20),
            description="Routine oil change and multi-point inspection.",
            cost=Decimal("79.99"),
        )
        self.assertEqual(str(service), f"Service #{service.service_id} for Vehicle VIN: {self.vehicle.vin} ($79.99)")

        # 7. Test FinanceApplication creation
        finance = FinanceApplication.objects.create(
            customer=self.customer,
            sale=sale,
            loan_amount=Decimal("15000.00"),
            status="APPROVED",
        )
        self.assertEqual(str(finance), f"Finance Application #{finance.application_id} - Loan: $15000.00 (APPROVED)")

