import random
import uuid
from datetime import datetime, date, time, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Max

from car_sales.models import (
    Customer, CustomerInfo, Store, Employee, SellingInfo, Invoice,
    City, Country, VehicleInfo, Inventory, CustomerMessage
)
from ecommerce.models import (
    Wishlist, Cart, CartItem, TestDriveBooking, Order, PaymentTransaction
)


FIRST_NAMES = [
    "Alexander", "Sophia", "Marcus", "Elena", "David", "Olivia", "Lucas", "Maya",
    "Ethan", "Isabella", "Gabriel", "Chloe", "Julian", "Amelia", "Nathan", "Grace",
    "Benjamin", "Hannah", "Liam", "Zoe", "Daniel", "Victoria", "Samuel", "Mia",
    "Oliver", "Charlotte", "Matthew", "Harper", "Sebastian", "Evelyn"
]

LAST_NAMES = [
    "Wright", "Martinez", "Kim", "Rostova", "Dubois", "Patel", "Kowalski", "Johnson",
    "Brown", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin",
    "Thompson", "Garcia", "Robinson", "Clark", "Rodriguez", "Lewis", "Lee", "Walker",
    "Hall", "Allen", "Young", "Hernandez", "King", "Wright"
]

STREET_NAMES = [
    "Park Avenue", "5th Avenue", "Market Street", "Peachtree Road NW", "Sunset Blvd",
    "Oakridge Lane", "Michigan Avenue", "Bay Street", "Elm Street", "Pinehurst Blvd",
    "Ocean Drive", "Broadway", "Cedar Lane", "Washington Street", "Lexington Ave"
]

DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "icloud.com", "protonmail.com"]

MESSAGE_TEMPLATES = [
    "Hi, I would like to inquire about the warranty packages available for the {make} {model}.",
    "Good day, I am interested in scheduling a test drive this weekend. Please confirm staff availability.",
    "Hello {employee_name}, could you provide a price quote including local dealership fees?",
    "Hi team, I submitted an online order for the {make} {model} and wanted to check the status.",
    "Hello, I am looking to trade in my current vehicle and purchase a pre-owned model from {store_name}."
]

TEST_DRIVE_NOTES = [
    "Customer requested highway performance check and lane keep assist testing.",
    "Customer interested in inspecting rear cargo space and family seating comfort.",
    "Pre-purchase inspection scheduled; customer requested EV charging demonstration.",
    "Customer inquired about low interest financing plans during test drive.",
    "Smooth test drive completed; customer requested quote for trade-in evaluation."
]

ORDER_REJECTION_REASONS = [
    "Vehicle financing approval pending additional document submission.",
    "Requested trim is temporarily reserved for another client.",
    "Delivery address falls outside our standard local delivery zone."
]


class Command(BaseCommand):
    help = "Seed logical, highly realistic customer data linked with stores, employees, sales, orders, test drives, invoices, and messages."

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=30,
            help='Number of new customer profiles to seed (default: 30)'
        )

    def handle(self, *args, **options):
        count = options['count']
        self.stdout.write(self.style.NOTICE(f"Starting seeding process for {count} realistic customers..."))

        # Fetch prerequisite reference data
        stores = list(Store.objects.select_related('city', 'country').all())
        if not stores:
            self.stderr.write(self.style.ERROR("No Stores found in database."))
            return

        cities = list(City.objects.select_related('country').all())
        max_inv_res = Invoice.objects.aggregate(Max('invoice_id'))['invoice_id__max']
        next_invoice_id = (max_inv_res or 444394) + 1

        created_customers_count = 0
        created_sales_count = 0
        created_invoices_count = 0
        created_orders_count = 0
        created_test_drives_count = 0
        created_messages_count = 0

        statuses = ['Active', 'VIP', 'Regular', 'New', 'Corporate']

        for i in range(count):
            with transaction.atomic():
                fname = random.choice(FIRST_NAMES)
                lname = random.choice(LAST_NAMES)
                domain = random.choice(DOMAINS)
                email = f"{fname.lower()}.{lname.lower()}_{uuid.uuid4().hex[:5]}@{domain}"

                # Generate clean phone number
                area_code = random.randint(201, 989)
                prefix = random.randint(200, 999)
                line = random.randint(1000, 9999)
                phone = f"+1 ({area_code}) {prefix}-{line}"

                # Pick a logical City & Country pair
                city_obj = random.choice(cities)
                country_obj = city_obj.country

                # Generate logical street address
                street_num = random.randint(100, 9999)
                street_name = random.choice(STREET_NAMES)
                customer_address = f"{street_num} {street_name}, Suite {random.randint(10, 500)}"

                # Create Customer
                customer = Customer.objects.create(
                    email=email,
                    password="pbkdf2_sha256$260000$seed_hashed_pass_" + uuid.uuid4().hex[:12],
                    phone=phone
                )

                # Create CustomerInfo
                cust_status = random.choice(statuses)
                CustomerInfo.objects.create(
                    customer=customer,
                    firstname=fname,
                    lastname=lname,
                    customer_status=cust_status,
                    customer_address=customer_address,
                    city=city_obj,
                    country=country_obj
                )
                created_customers_count += 1

                # Select a Store (preferably matching customer country if available, else random)
                matching_stores = [s for s in stores if s.country_id == country_obj.country_id]
                store = random.choice(matching_stores) if matching_stores else random.choice(stores)

                # Select an Employee working at THIS specific store
                store_employees = list(Employee.objects.filter(store=store))
                if not store_employees:
                    # fallback to any employee if store has no employee
                    store_employees = list(Employee.objects.all()[:10])
                employee = random.choice(store_employees)

                # Select Inventory available at THIS store
                store_inventories = list(Inventory.objects.select_related('vehicle', 'vehicle__make').filter(store=store)[:50])
                if not store_inventories:
                    store_inventories = list(Inventory.objects.select_related('vehicle', 'vehicle__make').all()[:50])

                inventory = random.choice(store_inventories)
                vehicle = inventory.vehicle

                # 1. Seed Car Sale (SellingInfo) & Invoice
                if random.random() < 0.7:  # 70% of new customers have a car sale record
                    sale_date = date.today() - timedelta(days=random.randint(5, 365))
                    mmr_val = vehicle.mmr or 25000
                    # Price negotiated around MMR (+/- 8%)
                    selling_price = int(mmr_val * random.uniform(0.92, 1.08))

                    sale = SellingInfo.objects.create(
                        customer=customer,
                        vehicle=vehicle,
                        employee=employee,
                        store=store,
                        selling_price=selling_price,
                        selling_date=sale_date
                    )
                    created_sales_count += 1

                    # Invoice
                    discount = max(0, mmr_val - selling_price)
                    discount_pct = round((discount / mmr_val) * 100, 2) if mmr_val > 0 else 0.0

                    Invoice.objects.create(
                        invoice_id=next_invoice_id,
                        selling_info=sale,
                        customer=customer,
                        employee=employee,
                        store=store,
                        invoice_date=sale_date,
                        due_date=sale_date + timedelta(days=30),
                        payment_status='Paid' if random.random() > 0.15 else 'Pending',
                        payment_method=random.choice(['Card', 'Bank Transfer', 'Financing', 'Cash']),
                        discount_amount=discount,
                        mmr=mmr_val,
                        discount_pct=discount_pct,
                        notes=f"Sale processed by {employee.first_name} {employee.last_name} at {store.store_name}."
                    )
                    next_invoice_id += 1
                    created_invoices_count += 1

                # 2. Seed eCommerce Order & PaymentTransaction
                if random.random() < 0.6:  # 60% have an eCommerce order
                    ord_status = random.choice([
                        Order.OrderStatus.APPROVED, Order.OrderStatus.PAID,
                        Order.OrderStatus.FULFILLED, Order.OrderStatus.NEEDS_APPROVAL
                    ])
                    total_amt = vehicle.mmr or 30000
                    deposit_amt = int(total_amt * 0.10)

                    order = Order.objects.create(
                        customer=customer,
                        inventory=inventory,
                        store=store,
                        assigned_employee=employee,
                        total_amount=total_amt,
                        deposit_amount=deposit_amt,
                        payment_preference=random.choice([
                            Order.PaymentPreference.ONLINE_CARD,
                            Order.PaymentPreference.FINANCING,
                            Order.PaymentPreference.STORE_PAYMENT
                        ]),
                        order_status=ord_status,
                        fulfillment_type=random.choice([
                            Order.FulfillmentType.STORE_PICKUP,
                            Order.FulfillmentType.HOME_DELIVERY
                        ]),
                        delivery_address=customer_address if random.random() > 0.3 else None
                    )
                    created_orders_count += 1

                    # PaymentTransaction
                    PaymentTransaction.objects.create(
                        gateway_transaction_id=f"txn_{uuid.uuid4().hex[:14]}",
                        order=order,
                        customer=customer,
                        recorded_by_employee=employee,
                        payment_method=PaymentTransaction.PaymentMethod.ONLINE_CARD,
                        payment_type=PaymentTransaction.PaymentType.FULL_PAYMENT if ord_status == Order.OrderStatus.PAID else PaymentTransaction.PaymentType.HOLD_DEPOSIT,
                        amount=total_amt if ord_status == Order.OrderStatus.PAID else deposit_amt,
                        status=PaymentTransaction.PaymentStatus.SUCCESS
                    )

                # 3. Seed Test Drive Booking
                if random.random() < 0.65:
                    td_date = date.today() + timedelta(days=random.randint(-30, 14))
                    td_time = time(random.choice([9, 10, 11, 13, 14, 15, 16]), random.choice([0, 30]))
                    td_status = TestDriveBooking.BookingStatus.COMPLETED if td_date < date.today() else TestDriveBooking.BookingStatus.SCHEDULED

                    TestDriveBooking.objects.create(
                        customer=customer,
                        vehicle=vehicle,
                        store=store,
                        assigned_employee=employee,
                        booking_date=td_date,
                        booking_time=td_time,
                        status=td_status,
                        notes=random.choice(TEST_DRIVE_NOTES)
                    )
                    created_test_drives_count += 1

                # 4. Seed Customer Message
                if random.random() < 0.5:
                    make_name = vehicle.make.make_name if vehicle.make else "Vehicle"
                    msg_text = random.choice(MESSAGE_TEMPLATES).format(
                        make=make_name,
                        model=vehicle.vehicle_model,
                        employee_name=f"{employee.first_name} {employee.last_name}",
                        store_name=store.store_name
                    )
                    CustomerMessage.objects.create(
                        customer=customer,
                        store=store,
                        employee=employee,
                        message=msg_text
                    )
                    created_messages_count += 1

                # 5. Seed Wishlist / Cart
                Wishlist.objects.create(customer=customer, vehicle=vehicle)
                cart = Cart.objects.create(customer=customer)
                CartItem.objects.create(cart=cart, inventory=inventory)

        self.style.SUCCESS
        self.stdout.write(self.style.SUCCESS(
            f"Successfully seeded:\n"
            f"  - {created_customers_count} Customers & CustomerInfo records\n"
            f"  - {created_sales_count} SellingInfo records\n"
            f"  - {created_invoices_count} Invoice records\n"
            f"  - {created_orders_count} Order & PaymentTransaction records\n"
            f"  - {created_test_drives_count} TestDriveBooking records\n"
            f"  - {created_messages_count} CustomerMessage records\n"
            f"  - {created_customers_count} Wishlist, Cart & CartItem records\n"
            f"All entries strictly linked between Customer, Store ({store.store_name}), and Employee ({employee.first_name} {employee.last_name})."
        ))
