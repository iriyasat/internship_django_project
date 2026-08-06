import random
from django.core.management.base import BaseCommand
from ecommerce.models import Order
from car_sales.models import Customer, Inventory

class Command(BaseCommand):
    help = 'Seed 500+ realistic pending order approval requests for current customers and available vehicles.'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=520, help='Number of pending orders to seed')

    def handle(self, *args, **options):
        count = options['count']
        customers = list(Customer.objects.all()[:count + 100])
        inventories = list(Inventory.objects.filter(status=Inventory.StatusChoices.AVAILABLE)[:count])

        if len(inventories) < count:
            count = len(inventories)

        self.stdout.write(f"Seeding {count} pending order requests...")

        fulfillment_types = [Order.FulfillmentType.STORE_PICKUP, Order.FulfillmentType.HOME_DELIVERY]
        payment_prefs = [Order.PaymentPreference.ONLINE_CARD, Order.PaymentPreference.STORE_PAYMENT, Order.PaymentPreference.CASH_ON_DELIVERY]

        orders_to_create = []
        inv_ids_to_update = []

        for i in range(count):
            cust = random.choice(customers)
            inv = inventories[i]
            inv_ids_to_update.append(inv.inventory_id)

            orders_to_create.append(Order(
                customer=cust,
                inventory=inv,
                store=inv.store,
                total_amount=inv.vehicle.mmr or 12000,
                deposit_amount=0,
                payment_preference=random.choice(payment_prefs),
                fulfillment_type=random.choice(fulfillment_types),
                order_status=Order.OrderStatus.NEEDS_APPROVAL
            ))

        Inventory.objects.filter(inventory_id__in=inv_ids_to_update).update(status=Inventory.StatusChoices.PRE_ORDER)

        Order.objects.bulk_create(orders_to_create, batch_size=200)

        total_pending = Order.objects.filter(order_status=Order.OrderStatus.NEEDS_APPROVAL).count()
        self.stdout.write(self.style.SUCCESS(f"Successfully created {count} pending order requests. Total pending orders in system: {total_pending}"))
