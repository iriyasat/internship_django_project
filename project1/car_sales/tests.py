import datetime
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import (
    Employee_Role,
    Address,
    Employee_Status,
    Vehicle_Condition,
    Vehicle_Status,
    Lead_Status,
    Activity_Type,
    Payment_Method,
    Payment_Status,
    Service_Status,
    Maintenance_Status,
    Employee,
    Customer,
    VehicleModel,
    Vehicle,
    Lead,
    LeadActivity,
    Sale,
    TradeIn,
    Payment,
    Supplier,
    ServiceRequest,
    MaintenanceSchedule,
)


class CarSalesModelTestCase(TestCase):
    """Test suite verifying the behavior of Django models mapping the dealership schema."""

    def setUp(self):
        # Create Lookup Tables Data
        self.employee_status = Employee_Status.objects.create(employee_status_name="Active")
        self.role = Employee_Role.objects.create(role_name="Sales Executive")
        
        self.vehicle_condition = Vehicle_Condition.objects.create(vehicle_condition_name="New")
        self.vehicle_status = Vehicle_Status.objects.create(vehicle_status_name="Available")
        
        self.lead_status = Lead_Status.objects.create(lead_status_name="Qualified")
        self.activity_type = Activity_Type.objects.create(activity_type_name="Call")
        
        self.payment_method_bank = Payment_Method.objects.create(payment_method_name="Bank Transfer")
        self.payment_method_cash = Payment_Method.objects.create(payment_method_name="Cash")
        self.payment_status_completed = Payment_Status.objects.create(payment_status_name="Completed")
        self.payment_status_pending = Payment_Status.objects.create(payment_status_name="Pending")
        
        self.service_status = Service_Status.objects.create(service_status_name="Pending")
        self.maintenance_status = Maintenance_Status.objects.create(maintenance_status_name="Scheduled")

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
            status=self.employee_status,
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
            condition=self.vehicle_condition,
            status=self.vehicle_status,
        )

        # Create a Lead
        self.lead = Lead.objects.create(
            customer=self.customer,
            vehicle=self.vehicle,
            employee=self.employee,
            source="Website",
            status=self.lead_status,
        )

    def test_str_representations(self):
        """Test the __str__ methods of various models."""
        self.assertEqual(str(self.role), "Sales Executive")
        self.assertEqual(str(self.employee_status), "Active")
        self.assertEqual(str(self.address), "123 Main St")
        self.assertEqual(str(self.employee), "Jane Doe")
        self.assertEqual(str(self.customer), "John Smith")
        self.assertEqual(str(self.vehicle_model), "Toyota Camry SE")
        self.assertEqual(str(self.vehicle), "2024 Toyota Camry (VIN: 1YV1Y111111111111)")
        self.assertEqual(str(self.lead), f"Lead #{self.lead.lead_id} - John Smith (Qualified)")

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
            activity_type=self.activity_type,
            details="Called the customer to discuss pricing details.",
        )
        self.assertEqual(activity.lead, self.lead)
        self.assertEqual(activity.employee, self.employee)
        self.assertEqual(activity.activity_type, self.activity_type)
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
            status=self.payment_status_completed,
        )
        self.assertEqual(payment.status, self.payment_status_completed)

        # Invalid Payment (amount <= 0) should fail model validation
        invalid_payment = Payment(
            sale=sale,
            amount=Decimal("0.00"),
            payment_method=self.payment_method_cash,
            status=self.payment_status_pending,
        )
        with self.assertRaises(ValidationError):
            invalid_payment.full_clean()
