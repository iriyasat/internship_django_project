import random
import time
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from car_sales.models import Customer, CustomerInfo, CustomerMessage, Store, Employee, VehicleInfo


# Multi-turn back-and-forth conversation templates with logical progression & conclusions.
# Format spec:
#   Customer line: [TIME: HH:MM AM/PM] <customer text>
#   Staff reply line: [Reply from <Staff Name> | HH:MM AM/PM]: <staff reply text>

MULTI_TURN_TEMPLATES = [
    # 1. Test Drive Booking & Confirmation (6 Turns)
    [
        {"t_cust": "09:00 AM", "cust": "Hi, I am interested in testing the {vehicle_name} at {store_name}. Is this model currently available on your lot?"},
        {"t_reply": "09:05 AM", "reply": "Hi {cust_name}! Yes, we have the {vehicle_name} ready in our main showroom. Would you like to book a test drive today or tomorrow?"},
        {"t_cust": "09:12 AM", "cust": "Tomorrow afternoon around 2:30 PM would work best for me. What documents should I bring along?"},
        {"t_reply": "09:18 AM", "reply": "2:30 PM is confirmed! Please bring your valid driver's license and current auto insurance card for the test drive."},
        {"t_cust": "09:25 AM", "cust": "Perfect! I will see you tomorrow at 2:30 PM. Thank you for your help."},
        {"t_reply": "09:30 AM", "reply": "You're very welcome, {cust_name}! I have reserved the keys for your arrival. See you tomorrow at {store_name}!"}
    ],

    # 2. Financing, Trade-In & Appraisal (6 Turns)
    [
        {"t_cust": "10:00 AM", "cust": "Hello {emp_name}, I am looking to trade in my current vehicle towards a {vehicle_name}. Could you share current APR rates at {store_name}?"},
        {"t_reply": "10:08 AM", "reply": "Hello {cust_name}! We offer promotional APR financing starting at 2.9% for qualified buyers, plus a top-dollar trade-in appraisal bonus."},
        {"t_cust": "10:15 AM", "cust": "That sounds attractive! Can I get an estimated trade-in appraisal online or do I need to bring the car in?"},
        {"t_reply": "10:22 AM", "reply": "You can bring it in for a quick 15-minute physical inspection, or upload photos and mileage details for an instant initial estimate."},
        {"t_cust": "10:30 AM", "cust": "Great, I will stop by {store_name} this afternoon at 4:00 PM for the physical inspection."},
        {"t_reply": "10:35 AM", "reply": "Perfect! I have added you to our appraisal schedule for 4:00 PM today. Looking forward to meeting you!"}
    ],

    # 3. Pre-Delivery Inspection & Online Order Pickup (6 Turns)
    [
        {"t_cust": "11:10 AM", "cust": "Hi {emp_name}, I placed an online order for the {vehicle_name} assigned to {store_name}. Can you check the status of pre-delivery prep?"},
        {"t_reply": "11:18 AM", "reply": "Hi {cust_name}! Your {vehicle_name} is currently undergoing final detailing and safety inspection in our service bay."},
        {"t_cust": "11:25 AM", "cust": "Awesome! Will all requested accessory packages (all-weather floor mats and tinting) be installed by pickup?"},
        {"t_reply": "11:32 AM", "reply": "Yes, both accessory packages are fully installed and verified by our service master technician."},
        {"t_cust": "11:40 AM", "cust": "Wonderful, I will arrive at 5:00 PM to finalize the handover paperwork and pick up the keys."},
        {"t_reply": "11:45 AM", "reply": "Everything is set! We'll have your paperwork printed and keys ready at the front desk. Safe travels!"}
    ],

    # 4. EV Charging, Range & Home Setup (6 Turns)
    [
        {"t_cust": "01:15 PM", "cust": "Hello, I am considering the {vehicle_name} but have questions regarding EV home charger installation and battery warranty."},
        {"t_reply": "01:22 PM", "reply": "Hi {cust_name}! The {vehicle_name} comes with an 8-year/100,000-mile battery warranty and a Level 2 home charging adapter."},
        {"t_cust": "01:30 PM", "cust": "Does {store_name} partner with certified electricians for home charger installation?"},
        {"t_reply": "01:38 PM", "reply": "Yes! We partner directly with certified local technicians and can bundle installation costs into your vehicle financing."},
        {"t_cust": "01:45 PM", "cust": "That makes it super convenient. Please email me the installation brochure and vehicle quote."},
        {"t_reply": "01:50 PM", "reply": "I have just emailed the complete EV packet to your inbox. Let me know if you would like to test drive this week!"}
    ],

    # 5. Post-Purchase Service & Maintenance (6 Turns)
    [
        {"t_cust": "02:00 PM", "cust": "Hi {emp_name}, thank you for helping me purchase the {vehicle_name}! When should I schedule my first routine service?"},
        {"t_reply": "02:08 PM", "reply": "Hi {cust_name}! Congratulations again on your new {vehicle_name}. First maintenance is recommended at 5,000 miles or 6 months."},
        {"t_cust": "02:15 PM", "cust": "Does my purchase include complimentary oil change and tire rotation for the first year?"},
        {"t_reply": "02:22 PM", "reply": "Absolutely! Your first two service visits are 100% complimentary as part of our {store_name} customer care package."},
        {"t_cust": "02:30 PM", "cust": "That is fantastic news! I will set a calendar reminder for 5,000 miles. Thanks again for the great service!"},
        {"t_reply": "02:35 PM", "reply": "It was my pleasure, {cust_name}! Reach out anytime if you need assistance in the future."}
    ],

    # 6. Extended Warranty & Custom Protection (6 Turns)
    [
        {"t_cust": "03:10 PM", "cust": "Hello {emp_name}, what extended warranty options are available for the {vehicle_name} at {store_name}?"},
        {"t_reply": "03:18 PM", "reply": "Hi {cust_name}! We offer 5-year and 7-year bumper-to-bumper extended protection plans including 24/7 roadside assistance."},
        {"t_cust": "03:25 PM", "cust": "Does the 7-year plan cover electronic component breakdowns and touchscreen displays?"},
        {"t_reply": "03:32 PM", "reply": "Yes, the 7-year plan covers all electrical, computer module, and infotainment systems with $0 deductible."},
        {"t_cust": "03:40 PM", "cust": "Sounds great! Please add the 7-year plan to my purchase contract."},
        {"t_reply": "03:45 PM", "reply": "Updated! The contract now reflects the 7-year extended coverage. Thank you for your business, {cust_name}!"}
    ]
]


VEHICLE_NAMES = [
    "Ford F-150", "Chevrolet Silverado 1500", "Ram 1500", "Toyota Camry", "Honda Accord",
    "Toyota RAV4", "Honda CR-V", "Nissan Altima", "Chevrolet Equinox", "Ford Explorer",
    "Jeep Grand Cherokee", "Subaru Outback", "Toyota Highlander", "Hyundai Tucson",
    "Kia Telluride", "BMW 3 Series", "Mercedes-Benz C-Class", "Audi A4", "Lexus RX",
    "Tesla Model 3", "Tesla Model Y", "Porsche Macan", "Volvo XC90", "Cadillac Escalade"
]


class Command(BaseCommand):
    help = "Update existing CustomerMessage records in place with multi-turn back-and-forth chats and logical conclusions, preserving message_ids."

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=2000,
            help='Batch size for bulk_update (default: 2000)'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        self.stdout.write(self.style.NOTICE("Updating existing CustomerMessage records with logical multi-turn conversations..."))

        t_start = time.time()

        # 1. Fetch prerequisite data
        customer_infos = list(CustomerInfo.objects.values('customer_id', 'firstname', 'lastname'))
        customer_dict = {c['customer_id']: f"{c['firstname']} {c['lastname']}".strip() for c in customer_infos}

        stores = list(Store.objects.values('store_id', 'store_name'))
        store_dict = {s['store_id']: s['store_name'].strip() for s in stores}

        employees = list(Employee.objects.values('employee_id', 'first_name', 'last_name', 'store_id'))
        emp_dict = {e['employee_id']: f"{e['first_name']} {e['last_name']}".strip() for e in employees}

        vehicles = list(VehicleInfo.objects.select_related('make').values('vehicle_model', 'make__make_name')[:2000])
        vehicle_list = [f"{v['make__make_name']} {v['vehicle_model']}".strip() for v in vehicles] if vehicles else VEHICLE_NAMES

        # 2. Fetch all existing CustomerMessage records in primary-key order
        existing_msgs = list(CustomerMessage.objects.select_related('customer', 'store', 'employee').all().order_by('message_id'))
        total_msgs = len(existing_msgs)

        if not total_msgs:
            self.stderr.write(self.style.ERROR("No existing CustomerMessage records found to update."))
            return

        self.stdout.write(f"Found {total_msgs:,} existing CustomerMessage records. Keeping all message_ids intact.")

        updated_count = 0

        # Process in batches
        for i in range(0, total_msgs, batch_size):
            batch = existing_msgs[i:i + batch_size]

            for msg_obj in batch:
                # Lookup names
                cust_name = customer_dict.get(msg_obj.customer_id) or f"Customer #{msg_obj.customer_id}"
                store_name = store_dict.get(msg_obj.store_id) or (msg_obj.store.store_name.strip() if msg_obj.store else "Dealership")
                emp_name = emp_dict.get(msg_obj.employee_id) or (f"{msg_obj.employee.first_name} {msg_obj.employee.last_name}" if msg_obj.employee else "Store Staff")
                vehicle_name = random.choice(vehicle_list)

                # Pick a multi-turn template scenario
                turns = random.choice(MULTI_TURN_TEMPLATES)
                formatted_lines = []

                for turn in turns:
                    if "cust" in turn:
                        c_text = turn["cust"].format(cust_name=cust_name, emp_name=emp_name, store_name=store_name, vehicle_name=vehicle_name)
                        formatted_lines.append(f"[TIME: {turn['t_cust']}] {c_text}")
                    elif "reply" in turn:
                        r_text = turn["reply"].format(cust_name=cust_name, emp_name=emp_name, store_name=store_name, vehicle_name=vehicle_name)
                        formatted_lines.append(f"[Reply from {emp_name} | {turn['t_reply']}]: {r_text}")

                msg_obj.message = "\n".join(formatted_lines)

            # Bulk update message field in database preserving message_id PKs
            with transaction.atomic():
                CustomerMessage.objects.bulk_update(batch, ['message'], batch_size=len(batch))

            updated_count += len(batch)
            pct = (updated_count / total_msgs) * 100
            self.stdout.write(f"Updated {updated_count:,} / {total_msgs:,} ({pct:.1f}%) message threads...")

        t_end = time.time()
        duration = t_end - t_start

        self.stdout.write(self.style.SUCCESS(
            f"\n🎉 Successfully updated all {updated_count:,} CustomerMessage threads in {duration:.2f} seconds!\n"
            f"All message_ids remain unchanged while each thread now features 6-turn logical back-and-forth conversations with clear conclusions."
        ))
