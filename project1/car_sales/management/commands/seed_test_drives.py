import random
import time
from datetime import datetime, date, time as dt_time, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from car_sales.models import Customer, CustomerInfo, Store, Employee, VehicleInfo, Inventory
from ecommerce.models import TestDriveBooking


# Rich, logical customer test drive notes pool
NOTE_TEMPLATES = [
    "Customer requested highway speed acceleration test and lane-keep assist walkthrough.",
    "Customer interested in inspecting rear cargo capacity and child seat ISOFIX installation.",
    "Pre-purchase trial; customer requested EV fast-charging demonstration and battery health check.",
    "Customer requested quiet cabin test drive and trade-in appraisal consultation.",
    "Customer wants to test parallel parking assistant and 360-degree surround camera system.",
    "First-time buyer; customer requested detailed overview of dashboard infotainment and navigation.",
    "Customer testing towing capacity and hill-descent control features.",
    "Customer requested smooth suspension check on rough road conditions.",
    "Customer interested in comparing interior leather trim finish and ventilated seat performance.",
    "Customer requested evening test drive slot to check LED headlight illumination and automatic high beams."
]

TIME_SLOTS = [
    dt_time(9, 0), dt_time(10, 30), dt_time(11, 45),
    dt_time(13, 30), dt_time(15, 0), dt_time(16, 30), dt_time(17, 45)
]


class Command(BaseCommand):
    help = "Clear existing test drive bookings and seed 50,000-100,000 logical, fully linked TestDriveBooking records."

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=75000,
            help='Number of test drive bookings to seed (default: 75000)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=5000,
            help='Batch size for bulk_create (default: 5000)'
        )

    def handle(self, *args, **options):
        count = options['count']
        batch_size = options['batch_size']

        # 1. Clear existing test drive bookings
        self.stdout.write(self.style.NOTICE("Clearing all current test drive booking schedules..."))
        deleted_cnt, _ = TestDriveBooking.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f"Successfully cleared {deleted_cnt:,} existing test drive bookings."))

        self.stdout.write(self.style.NOTICE(f"Starting bulk seeding of {count:,} logical TestDriveBooking records..."))
        t_start = time.time()

        # 2. Fetch reference data in memory
        self.stdout.write("Fetching reference data (Customers, Stores, Employees, Inventories)...")
        customer_ids = list(Customer.objects.values_list('customer_id', flat=True))
        stores = list(Store.objects.values('store_id', 'country_id'))
        employees = list(Employee.objects.values('employee_id', 'store_id'))
        inventory_items = list(Inventory.objects.values('vehicle_id', 'store_id'))

        if not customer_ids or not stores or not employees or not inventory_items:
            self.stderr.write(self.style.ERROR("Database lacks required Customer, Store, Employee, or Inventory records."))
            return

        # Pre-group employees by store_id
        store_employees_map = {}
        for emp in employees:
            sid = emp['store_id']
            if sid not in store_employees_map:
                store_employees_map[sid] = []
            store_employees_map[sid].append(emp['employee_id'])

        # Pre-group vehicles by store_id
        store_vehicles_map = {}
        all_vehicle_ids = set()
        for inv in inventory_items:
            sid = inv['store_id']
            vid = inv['vehicle_id']
            all_vehicle_ids.add(vid)
            if sid not in store_vehicles_map:
                store_vehicles_map[sid] = []
            store_vehicles_map[sid].append(vid)

        all_vehicle_ids_list = list(all_vehicle_ids)
        store_ids_list = [s['store_id'] for s in stores]
        cust_country_map = dict(CustomerInfo.objects.filter(country_id__isnull=False).values_list('customer_id', 'country_id'))
        store_country_map = {s['store_id']: s['country_id'] for s in stores}
        country_stores_map = {}
        for s in stores:
            cid = s['country_id']
            country_stores_map.setdefault(cid, []).append(s['store_id'])

        self.stdout.write(f"Pre-loaded {len(customer_ids):,} Customers, {len(stores):,} Stores, {len(employees):,} Employees, and {len(all_vehicle_ids_list):,} Vehicles.")

        # 3. Generate logical TestDriveBooking records
        today = date.today()
        now = timezone.now()
        bookings_batch = []
        created_total = 0

        while created_total < count:
            current_batch_size = min(batch_size, count - created_total)
            batch = []

            for _ in range(current_batch_size):
                # Pick customer
                cust_id = random.choice(customer_ids)
                cust_country = cust_country_map.get(cust_id)

                # Pick store in customer country if available, else random store
                local_stores = country_stores_map.get(cust_country) if cust_country else None
                store_id = random.choice(local_stores) if local_stores else random.choice(store_ids_list)

                # Pick assigned employee at THIS store
                emp_pool = store_employees_map.get(store_id)
                assigned_emp_id = random.choice(emp_pool) if emp_pool else random.choice(employees)['employee_id']

                # Pick vehicle held in inventory at THIS store
                veh_pool = store_vehicles_map.get(store_id)
                vehicle_id = random.choice(veh_pool) if veh_pool else random.choice(all_vehicle_ids_list)

                # Date logic: 80% past dates (completed/cancelled), 20% future dates (scheduled)
                is_past = random.random() < 0.8
                if is_past:
                    days_diff = random.randint(1, 180)
                    b_date = today - timedelta(days=days_diff)
                    b_status = random.choices(
                        [TestDriveBooking.BookingStatus.COMPLETED, TestDriveBooking.BookingStatus.CANCELLED, TestDriveBooking.BookingStatus.NO_SHOW],
                        weights=[80, 10, 10]
                    )[0]
                else:
                    days_diff = random.randint(1, 30)
                    b_date = today + timedelta(days=days_diff)
                    b_status = TestDriveBooking.BookingStatus.SCHEDULED

                b_time = random.choice(TIME_SLOTS)
                b_note = random.choice(NOTE_TEMPLATES)

                created_dt = now - timedelta(days=random.randint(1, 180))

                batch.append(TestDriveBooking(
                    customer_id=cust_id,
                    vehicle_id=vehicle_id,
                    store_id=store_id,
                    assigned_employee_id=assigned_emp_id,
                    booking_date=b_date,
                    booking_time=b_time,
                    status=b_status,
                    notes=b_note,
                    created_at=created_dt,
                    updated_at=created_dt
                ))

            # Bulk insert batch
            with transaction.atomic():
                TestDriveBooking.objects.bulk_create(batch, batch_size=current_batch_size)

            created_total += current_batch_size
            pct = (created_total / count) * 100
            self.stdout.write(f"Progress: {created_total:,} / {count:,} ({pct:.1f}%) TestDriveBooking records seeded...")

        t_end = time.time()
        duration = t_end - t_start
        final_count = TestDriveBooking.objects.count()
        covered_custs = TestDriveBooking.objects.values('customer_id').distinct().count()

        self.stdout.write(self.style.SUCCESS(
            f"\n🎉 Successfully seeded {final_count:,} logical TestDriveBooking records in {duration:.2f} seconds!\n"
            f"  - Total Test Drive Bookings in Database: {final_count:,}\n"
            f"  - Customers with Test Drives: {covered_custs:,} out of {len(customer_ids):,} ({covered_custs/len(customer_ids)*100:.1f}% coverage)\n"
            f"  - All entries strictly link existing Customers, Stores, assigned Store Employees, and Inventory Vehicles with detailed notes."
        ))
