import random
import time
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from car_sales.models import Customer, CustomerInfo, VehicleInfo, Store, Inventory, SellingInfo
from ecommerce.models import Wishlist, Order, TestDriveBooking


class Command(BaseCommand):
    help = "Seed logical Wishlist data for ALL existing customers using existing vehicles and stores, without creating any new entities."

    def add_arguments(self, parser):
        parser.add_argument(
            '--items-per-customer',
            type=int,
            default=3,
            help='Target number of wishlist items per customer (default: 3)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=5000,
            help='Batch size for bulk_create (default: 5000)'
        )

    def handle(self, *args, **options):
        target_items = options['items_per_customer']
        batch_size = options['batch_size']

        self.stdout.write(self.style.NOTICE(f"Starting logical Wishlist seeding for ALL customers (target: ~{target_items} items/customer)..."))

        t_start = time.time()

        self.stdout.write("Fetching existing Customers and CustomerInfo...")
        all_customer_ids = list(Customer.objects.values_list('customer_id', flat=True))
        total_customers = len(all_customer_ids)

        if not total_customers:
            self.stderr.write(self.style.ERROR("No Customer records found in database."))
            return

        cust_country_map = dict(
            CustomerInfo.objects.filter(country_id__isnull=False).values_list('customer_id', 'country_id')
        )

        self.stdout.write("Mapping Inventory vehicles by country...")
        inventory_items = Inventory.objects.select_related('store').values_list('store__country_id', 'vehicle_id')

        country_vehicles_map = {}
        all_vehicle_ids = set()

        for country_id, vehicle_id in inventory_items:
            all_vehicle_ids.add(vehicle_id)
            if country_id not in country_vehicles_map:
                country_vehicles_map[country_id] = []
            country_vehicles_map[country_id].append(vehicle_id)

        all_vehicle_ids_list = list(all_vehicle_ids)
        if not all_vehicle_ids_list:
            all_vehicle_ids_list = list(VehicleInfo.objects.values_list('id', flat=True)[:50000])

        self.stdout.write("Mapping past customer vehicle interactions...")
        cust_interacted_vehicles = {}

        for cid, vid in SellingInfo.objects.values_list('customer_id', 'vehicle_id'):
            if cid not in cust_interacted_vehicles:
                cust_interacted_vehicles[cid] = set()
            cust_interacted_vehicles[cid].add(vid)

        for cid, vid in Order.objects.values_list('customer_id', 'inventory__vehicle_id'):
            if vid:
                if cid not in cust_interacted_vehicles:
                    cust_interacted_vehicles[cid] = set()
                cust_interacted_vehicles[cid].add(vid)

        for cid, vid in TestDriveBooking.objects.values_list('customer_id', 'vehicle_id'):
            if cid not in cust_interacted_vehicles:
                cust_interacted_vehicles[cid] = set()
            cust_interacted_vehicles[cid].add(vid)

        self.stdout.write("Fetching existing Wishlist entries...")
        existing_wishlists = Wishlist.objects.values_list('customer_id', 'vehicle_id')
        existing_set = set(existing_wishlists)
        cust_existing_counts = {}

        for cid, vid in existing_set:
            cust_existing_counts[cid] = cust_existing_counts.get(cid, 0) + 1

        self.stdout.write(f"Pre-loaded {total_customers:,} Customers, {len(all_vehicle_ids_list):,} Vehicles, and {len(existing_set):,} existing Wishlist links.")

        self.stdout.write("Generating logical Wishlist links for all customers...")
        wishlist_objs = []
        now = timezone.now()

        for idx, cid in enumerate(all_customer_ids):
            current_count = cust_existing_counts.get(cid, 0)
            needed = max(0, target_items - current_count)

            if needed <= 0:
                continue

            c_country = cust_country_map.get(cid)
            country_pool = country_vehicles_map.get(c_country) if c_country else None

            interacted_pool = list(cust_interacted_vehicles.get(cid, []))

            added_for_cust = 0
            attempts = 0

            while added_for_cust < needed and attempts < 15:
                attempts += 1

                rand_val = random.random()
                if rand_val < 0.4 and interacted_pool:
                    v_choice = random.choice(interacted_pool)
                elif rand_val < 0.8 and country_pool:
                    v_choice = random.choice(country_pool)
                else:
                    v_choice = random.choice(all_vehicle_ids_list)

                pair = (cid, v_choice)
                if pair not in existing_set:
                    existing_set.add(pair)

                    days_ago = random.randint(1, 180)
                    created_dt = now - timedelta(days=days_ago)

                    wishlist_objs.append(Wishlist(
                        customer_id=cid,
                        vehicle_id=v_choice,
                        created_at=created_dt
                    ))
                    added_for_cust += 1

        total_to_insert = len(wishlist_objs)
        self.stdout.write(f"Generated {total_to_insert:,} new logical Wishlist items to insert across {total_customers:,} customers.")

        inserted_total = 0
        for i in range(0, total_to_insert, batch_size):
            batch = wishlist_objs[i:i + batch_size]
            with transaction.atomic():
                Wishlist.objects.bulk_create(batch, ignore_conflicts=True, batch_size=batch_size)
            inserted_total += len(batch)
            pct = (inserted_total / total_to_insert) * 100 if total_to_insert > 0 else 100
            self.stdout.write(f"Progress: {inserted_total:,} / {total_to_insert:,} ({pct:.1f}%) Wishlist records created...")

        t_end = time.time()
        duration = t_end - t_start

        final_total_wishlists = Wishlist.objects.count()
        covered_customers = Wishlist.objects.values('customer_id').distinct().count()

        self.stdout.write(self.style.SUCCESS(
            f"\n🎉 Successfully completed Wishlist seeding in {duration:.2f} seconds!\n"
            f"  - Total Wishlist Records in Database: {final_total_wishlists:,}\n"
            f"  - Customers with Wishlist Entries: {covered_customers:,} out of {total_customers:,} ({covered_customers/total_customers*100:.1f}% coverage)\n"
            f"  - All items logically linked existing Customers to existing Vehicles in their region/interest pool."
        ))
