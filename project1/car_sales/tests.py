import datetime
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import (
    EmployeeRole,
    Address,
    PaymentMethod,
    Employee,
    Customer,
    VehicleModel,
    Vehicle,
    Lead,
    LeadActivity,
    Sale,
    TradeIn,
    Payment,
)


class CarSalesModelTestCase(TestCase):
    """Test suite verifying the behavior of Django models mapping the dealership schema."""

    def setUp(self):
        # Create Lookup Tables Data
        self.role = EmployeeRole.objects.create(role_name="Sales Executive")
        
        self.payment_method_bank = PaymentMethod.objects.create(payment_method_name="Bank Transfer")
        self.payment_method_cash = PaymentMethod.objects.create(payment_method_name="Cash")

        # Create an Address
        self.address = Address.objects.create(
            street_address="123 Main St",
            city="Metropolis",
            state="NY",
            postal_code="10001",
        )

        # Create an Employee
        self.employee = Employee.objects.create(
            role=self.role,
            first_name="Jane",
            last_name="Doe",
            email="jane.doe@dealership.com",
            phone="555-0199",
            address=self.address,
            status=Employee.Status.ACTIVE,
            commission_rate=Decimal("5.50"),
        )

        # Create a Customer
        self.customer = Customer.objects.create(
            first_name="John",
            last_name="Smith",
            email="john.smith@gmail.com",
            phone="555-0144",
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
        self.assertEqual(str(self.address), "123 Main St")
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
            activity_type=LeadActivity.ActivityType.CALL,
            details="Called the customer to discuss pricing details.",
        )
        self.assertEqual(activity.lead, self.lead)
        self.assertEqual(activity.employee, self.employee)
        self.assertEqual(activity.activity_type, LeadActivity.ActivityType.CALL)
        self.assertIn("CALL on", str(activity))

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
