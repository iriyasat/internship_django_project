import json
import uuid
from datetime import datetime, date, time
from django.db import transaction, models, connections
from django.utils import timezone
from rest_framework import serializers

from car_sales.models import (
    Customer, CustomerInfo, Inventory, VehicleInfo, Store, 
    Employee, SellingInfo, Invoice, IndustryInfo
)
from .models import Wishlist, Cart, CartItem, TestDriveBooking, Order, PaymentTransaction


# ------------------------------------------------------------------------------
# REST Framework Model Serializers
# ------------------------------------------------------------------------------

class WishlistModelSerializer(serializers.ModelSerializer):
    vehicle_model = serializers.CharField(source='vehicle.vehicle_model', read_only=True)
    make_name = serializers.CharField(source='vehicle.make.make_name', read_only=True)
    price = serializers.IntegerField(source='vehicle.mmr', read_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'customer', 'vehicle', 'vehicle_model', 'make_name', 'price', 'created_at']


class CartItemModelSerializer(serializers.ModelSerializer):
    vehicle_model = serializers.CharField(source='inventory.vehicle.vehicle_model', read_only=True)
    make_name = serializers.CharField(source='inventory.vehicle.make.make_name', read_only=True)
    price = serializers.IntegerField(source='inventory.vehicle.mmr', read_only=True)
    store_name = serializers.CharField(source='inventory.store.store_name', read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'cart', 'inventory', 'vehicle_model', 'make_name', 'price', 'store_name', 'added_at']


class TestDriveBookingModelSerializer(serializers.ModelSerializer):
    vehicle_model = serializers.CharField(source='vehicle.vehicle_model', read_only=True)
    make_name = serializers.CharField(source='vehicle.make.make_name', read_only=True)
    store_name = serializers.CharField(source='store.store_name', read_only=True)

    class Meta:
        model = TestDriveBooking
        fields = [
            'booking_id', 'customer', 'vehicle', 'vehicle_model', 'make_name',
            'store', 'store_name', 'assigned_employee', 'booking_date', 
            'booking_time', 'status', 'notes', 'created_at'
        ]


class OrderModelSerializer(serializers.ModelSerializer):
    vehicle_model = serializers.CharField(source='inventory.vehicle.vehicle_model', read_only=True)
    make_name = serializers.CharField(source='inventory.vehicle.make.make_name', read_only=True)
    store_name = serializers.CharField(source='store.store_name', read_only=True)
    status_display = serializers.CharField(source='get_order_status_display', read_only=True)

    class Meta:
        model = Order
        fields = [
            'order_id', 'customer', 'inventory', 'vehicle_model', 'make_name',
            'store', 'store_name', 'assigned_employee', 'invoice',
            'total_amount', 'deposit_amount', 'payment_preference',
            'order_status', 'status_display', 'fulfillment_type', 
            'delivery_address', 'rejection_reason', 'reviewed_at', 'created_at'
        ]


class PaymentTransactionModelSerializer(serializers.ModelSerializer):
    method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    type_display = serializers.CharField(source='get_payment_type_display', read_only=True)

    class Meta:
        model = PaymentTransaction
        fields = [
            'transaction_id', 'gateway_transaction_id', 'order', 'invoice',
            'customer', 'recorded_by_employee', 'payment_method', 'method_display',
            'payment_type', 'type_display', 'amount', 'status', 'created_at'
        ]


# ------------------------------------------------------------------------------
# Encapsulated Business Query & Transaction Services
# ------------------------------------------------------------------------------

class CatalogService:
    @staticmethod
    def fetch_catalog_vehicles(make_id=None, store_id=None, search_q=None, min_price=None, max_price=None, limit=60):
        qs = Inventory.objects.select_related('vehicle__make', 'store', 'store__city', 'store__country').filter(
            status__in=[Inventory.StatusChoices.AVAILABLE, Inventory.StatusChoices.PRE_ORDER]
        )

        if make_id:
            qs = qs.filter(vehicle__make_id=make_id)
        if store_id:
            qs = qs.filter(store_id=store_id)
        if search_q:
            qs = qs.filter(
                models.Q(vehicle__vehicle_model__icontains=search_q) |
                models.Q(vehicle__make__make_name__icontains=search_q) |
                models.Q(vehicle__vin__icontains=search_q)
            )
        if min_price:
            qs = qs.filter(vehicle__mmr__gte=min_price)
        if max_price:
            qs = qs.filter(vehicle__mmr__lte=max_price)

        qs = qs.order_by('-inventory_id')[:limit]

        vehicles = []
        for item in qs:
            v = item.vehicle
            vehicles.append({
                'inventory_id': item.inventory_id,
                'vehicle_id': v.id,
                'make': v.make.make_name,
                'model': v.vehicle_model,
                'trim': v.trim or '',
                'body': v.body or '',
                'transmission': v.transmission or '',
                'color': v.color or '',
                'condition': v.condition or '',
                'odometer': v.odometer or '',
                'price': v.mmr,
                'vin': v.vin,
                'status': item.get_status_display(),
                'status_code': item.status,
                'store_id': item.store_id,
                'store_name': item.store.store_name,
                'city': item.store.city.city_name,
                'country': item.store.country.country_name,
            })
        return vehicles


class WishlistService:
    @staticmethod
    def fetch_customer_wishlist(customer):
        if not customer:
            return []
        return Wishlist.objects.filter(customer=customer).select_related('vehicle__make')

    @staticmethod
    def toggle_wishlist(customer, vehicle_id):
        if not customer:
            raise ValueError("Authentication required")
        vehicle = VehicleInfo.objects.get(pk=vehicle_id)
        item, created = Wishlist.objects.get_or_create(customer=customer, vehicle=vehicle)
        if not created:
            item.delete()
            added = False
            msg = "Removed from Wishlist"
        else:
            added = True
            msg = "Added to Wishlist"
        count = Wishlist.objects.filter(customer=customer).count()
        return {'added': added, 'message': msg, 'wishlist_count': count}


class CartService:
    @staticmethod
    def fetch_customer_cart_items(customer):
        if not customer:
            return [], 0
        cart, _ = Cart.objects.get_or_create(customer=customer)
        items = list(cart.items.select_related('inventory__vehicle__make', 'inventory__store').all())
        total_price = sum(item.inventory.vehicle.mmr for item in items)
        return items, total_price

    @staticmethod
    def add_to_cart(customer, inventory_id):
        if not customer:
            raise ValueError("Authentication required")
        inventory = Inventory.objects.get(pk=inventory_id)
        if inventory.status not in [Inventory.StatusChoices.AVAILABLE, Inventory.StatusChoices.PRE_ORDER]:
            raise ValueError("Item is no longer available")

        cart, _ = Cart.objects.get_or_create(customer=customer)
        item, created = CartItem.objects.get_or_create(cart=cart, inventory=inventory)
        count = cart.items.count()
        return {'created': created, 'message': 'Added to Cart' if created else 'Item already in Cart', 'cart_count': count}

    @staticmethod
    def remove_from_cart(customer, inventory_id):
        if not customer:
            raise ValueError("Authentication required")
        cart = Cart.objects.filter(customer=customer).first()
        if cart:
            CartItem.objects.filter(cart=cart, inventory_id=inventory_id).delete()
            count = cart.items.count()
        else:
            count = 0
        return {'message': 'Item removed from cart', 'cart_count': count}


class TestDriveService:
    @staticmethod
    def fetch_customer_bookings(customer):
        if not customer:
            return []
        return TestDriveBooking.objects.filter(customer=customer).select_related('vehicle__make', 'store', 'assigned_employee').order_by('-booking_date')

    @staticmethod
    def create_booking(customer, vehicle_id, store_id, booking_date_str, booking_time_str='10:00', notes=''):
        if not customer:
            raise ValueError("Authentication required")
        vehicle = VehicleInfo.objects.get(pk=vehicle_id)
        store = Store.objects.get(pk=store_id)

        booking = TestDriveBooking.objects.create(
            customer=customer,
            vehicle=vehicle,
            store=store,
            booking_date=booking_date_str,
            booking_time=booking_time_str,
            notes=notes,
            status=TestDriveBooking.BookingStatus.SCHEDULED
        )
        return booking


class OrderService:
    @staticmethod
    def submit_order(customer, inventory_id, fulfillment_type, payment_preference, delivery_address=''):
        if not customer:
            raise ValueError("Authentication required")

        inventory = Inventory.objects.get(pk=inventory_id)
        if inventory.status not in [Inventory.StatusChoices.AVAILABLE, Inventory.StatusChoices.PRE_ORDER]:
            raise ValueError("Vehicle is no longer available for purchase")

        with transaction.atomic():
            total_price = inventory.vehicle.mmr
            deposit = 500 if payment_preference != Order.PaymentPreference.STORE_PAYMENT else 0

            order = Order.objects.create(
                customer=customer,
                inventory=inventory,
                store=inventory.store,
                total_amount=total_price,
                deposit_amount=deposit,
                payment_preference=payment_preference,
                fulfillment_type=fulfillment_type,
                delivery_address=delivery_address if fulfillment_type == Order.FulfillmentType.HOME_DELIVERY else None,
                order_status=Order.OrderStatus.NEEDS_APPROVAL
            )

            # Update inventory status to PRE_ORDER (2)
            inventory.status = Inventory.StatusChoices.PRE_ORDER
            inventory.save()

            # Record online card deposit if applicable
            if deposit > 0 and payment_preference == Order.PaymentPreference.ONLINE_CARD:
                PaymentTransaction.objects.create(
                    gateway_transaction_id=f"TXN-DEP-{uuid.uuid4().hex[:12].upper()}",
                    order=order,
                    customer=customer,
                    payment_method=PaymentTransaction.PaymentMethod.ONLINE_CARD,
                    payment_type=PaymentTransaction.PaymentType.HOLD_DEPOSIT,
                    amount=deposit,
                    status=PaymentTransaction.PaymentStatus.SUCCESS
                )
                order.order_status = Order.OrderStatus.PARTIALLY_PAID
                order.save()

            # Clear cart item if present
            cart = Cart.objects.filter(customer=customer).first()
            if cart:
                CartItem.objects.filter(cart=cart, inventory=inventory).delete()

        return order

    @staticmethod
    def review_order(order_id, action, employee_id=None, rejection_reason=''):
        order = Order.objects.get(pk=order_id)
        employee = Employee.objects.filter(pk=employee_id).first() if employee_id else Employee.objects.first()

        with transaction.atomic():
            order.assigned_employee = employee
            order.reviewed_at = timezone.now().replace(second=0, microsecond=0)

            if action == 'ACCEPT':
                order.order_status = Order.OrderStatus.APPROVED

                # Generate Invoice if missing
                if not order.invoice:
                    inv_id = (Invoice.objects.all().order_by('-invoice_id').first().invoice_id + 1) if Invoice.objects.exists() else 4000
                    invoice = Invoice.objects.create(
                        invoice_id=inv_id,
                        customer=order.customer,
                        employee=employee,
                        store=order.store,
                        invoice_date=date.today(),
                        payment_status=Invoice.PaymentStatusChoices.PENDING,
                        payment_method=Invoice.PaymentMethodChoices.CARD if order.payment_preference == Order.PaymentPreference.ONLINE_CARD else Invoice.PaymentMethodChoices.CASH,
                        mmr=order.inventory.vehicle.mmr,
                        discount_amount=0,
                        notes=f"Generated from Online Order #{order.order_id}"
                    )
                    order.invoice = invoice

                order.save()
                msg = f"Order #{order.order_id} accepted and assigned to {employee}."

            else: # REJECT
                order.order_status = Order.OrderStatus.REJECTED
                order.rejection_reason = rejection_reason
                order.save()

                # Revert inventory status back to AVAILABLE (4)
                order.inventory.status = Inventory.StatusChoices.AVAILABLE
                order.inventory.save()

                # Process refund if deposit was paid
                if order.deposit_amount > 0:
                    PaymentTransaction.objects.create(
                        gateway_transaction_id=f"TXN-REF-{uuid.uuid4().hex[:12].upper()}",
                        order=order,
                        invoice=order.invoice,
                        customer=order.customer,
                        recorded_by_employee=employee,
                        payment_method=PaymentTransaction.PaymentMethod.ONLINE_CARD,
                        payment_type=PaymentTransaction.PaymentType.REFUND,
                        amount=order.deposit_amount,
                        status=PaymentTransaction.PaymentStatus.REFUNDED
                    )
                msg = f"Order #{order.order_id} rejected. Inventory restored to Available."

        return order, msg

    @staticmethod
    def record_payment(order_id, amount, payment_method=PaymentTransaction.PaymentMethod.STORE_CASH, employee_id=None):
        order = Order.objects.get(pk=order_id)
        employee = Employee.objects.filter(pk=employee_id).first() if employee_id else order.assigned_employee

        with transaction.atomic():
            txn = PaymentTransaction.objects.create(
                gateway_transaction_id=f"TXN-REC-{uuid.uuid4().hex[:12].upper()}",
                order=order,
                invoice=order.invoice,
                customer=order.customer,
                recorded_by_employee=employee,
                payment_method=payment_method,
                payment_type=PaymentTransaction.PaymentType.BALANCE_PAYMENT,
                amount=int(amount),
                status=PaymentTransaction.PaymentStatus.SUCCESS
            )

            order.order_status = Order.OrderStatus.PAID
            order.save()

            if order.invoice:
                order.invoice.payment_status = Invoice.PaymentStatusChoices.PAID
                order.invoice.save()

        return txn, order

    @staticmethod
    def fulfill_order(order_id, employee_id=None):
        order = Order.objects.get(pk=order_id)
        employee = Employee.objects.filter(pk=employee_id).first() if employee_id else order.assigned_employee

        if not employee:
            raise ValueError("No employee assigned for sales handover credit")

        with transaction.atomic():
            # 1. Create official SellingInfo record credited to employee
            selling_info = SellingInfo.objects.create(
                customer=order.customer,
                vehicle=order.inventory.vehicle,
                employee=employee,
                store=order.store,
                selling_price=order.total_amount,
                selling_date=date.today()
            )

            # 2. Update Inventory to SOLD (1)
            order.inventory.status = Inventory.StatusChoices.SOLD
            order.inventory.selling_info = selling_info
            order.inventory.save()

            # 3. Update Invoice if present
            if order.invoice:
                order.invoice.selling_info = selling_info
                order.invoice.payment_status = Invoice.PaymentStatusChoices.PAID
                order.invoice.save()

            # 4. Update Order to FULFILLED
            order.order_status = Order.OrderStatus.FULFILLED
            order.assigned_employee = employee
            order.save()

        return selling_info, order
