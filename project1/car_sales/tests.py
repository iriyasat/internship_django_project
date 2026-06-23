import datetime
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import (
    Address,
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

        # Create an Address
        self.address = Address.objects.create(
            house_no="12/A",
            street_address="Main St",
            city=self.city_obj,
            state="NY",
            postal_code="10001",
        )

        # Create an Employee
        self.employee = Employee.objects.create(
            role=self.role,
            first_name="Jane",
            last_name="Doe",
            email="jane.doe@dealership.com",
            phone=self.phone_emp,
            address=self.address,
            status=self.status_active,
        )

        # Create a Customer
        self.customer = Customer.objects.create(
            first_name="John",
            last_name="Smith",
            email="john.smith@gmail.com",
            phone=self.phone_cust,
            address=self.address,
        )

        # Create a Vehicle Model
        self.vehicle_model = VehicleModel.objects.create(
            make="Toyota",
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
        )

        # Create LeadActivityType
        self.activity_call = LeadActivityType.objects.create(lead_activity_type_name="Call")

        # Create a Lead
        self.lead = Lead.objects.create(
            customer=self.customer,
            vehicle=self.vehicle,
            employee=self.employee,
            source="Website",
            status=Lead.Status.QUALIFIED,
        )

    def test_str_representations(self):
        """Test the __str__ methods of various models."""
        self.assertEqual(str(self.role), "Sales Executive")
        self.assertEqual(str(self.status_active), "Active")
        self.assertEqual(str(self.country), "USA")
        self.assertEqual(str(self.city_obj), "Metropolis, USA")
        self.assertEqual(str(self.address), "Main St")
        self.assertEqual(str(self.phone_emp), "+8801712345678")
        self.assertEqual(str(self.employee), "Jane Doe")
        self.assertEqual(str(self.customer), "John Smith")
        self.assertEqual(str(self.vehicle_model), "Toyota Camry SE")
        self.assertEqual(str(self.vehicle), "2024 Toyota Camry (VIN: 1YV1Y111111111111)")
        self.assertEqual(str(self.lead), f"Lead #{self.lead.lead_id} - John Smith (QUALIFIED)")

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
            address=self.address,
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
            address=self.address,
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
