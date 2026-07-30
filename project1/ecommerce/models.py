from django.db import models
from car_sales.models import Customer, Inventory, VehicleInfo, Store, Employee, Invoice, TruncatedDateTimeField


class Wishlist(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='wishlists', verbose_name="Customer")
    vehicle = models.ForeignKey(VehicleInfo, on_delete=models.CASCADE, related_name='wishlisted_by', verbose_name="Vehicle")
    created_at = TruncatedDateTimeField(auto_now_add=True, verbose_name="Created At")

    class Meta:
        db_table = 'wishlist'
        unique_together = ('customer', 'vehicle')
        verbose_name_plural = 'wishlists'

    def __str__(self):
        return f"{self.customer} - {self.vehicle}"


class Cart(models.Model):
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, related_name='cart', verbose_name="Customer")
    created_at = TruncatedDateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = TruncatedDateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        db_table = 'cart'
        verbose_name_plural = 'carts'

    def __str__(self):
        return f"Cart for {self.customer}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', verbose_name="Cart")
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name='cart_items', verbose_name="Inventory Item")
    added_at = TruncatedDateTimeField(auto_now_add=True, verbose_name="Added At")

    class Meta:
        db_table = 'cart_item'
        unique_together = ('cart', 'inventory')
        verbose_name_plural = 'cart items'

    def __str__(self):
        return f"{self.inventory} in {self.cart}"


class TestDriveBooking(models.Model):
    class BookingStatus(models.TextChoices):
        SCHEDULED = 'SCHEDULED', 'Scheduled'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        NO_SHOW = 'NO_SHOW', 'No Show'

    booking_id = models.AutoField(primary_key=True, verbose_name="Booking ID")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='test_drives', verbose_name="Customer")
    vehicle = models.ForeignKey(VehicleInfo, on_delete=models.CASCADE, related_name='test_drives', verbose_name="Vehicle")
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='test_drives', verbose_name="Store")
    assigned_employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='hosted_test_drives',
        verbose_name="Assigned Staff"
    )
    booking_date = models.DateField(verbose_name="Booking Date")
    booking_time = models.TimeField(verbose_name="Booking Time")
    status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices,
        default=BookingStatus.SCHEDULED,
        verbose_name="Status"
    )
    notes = models.TextField(null=True, blank=True, verbose_name="Notes")
    created_at = TruncatedDateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = TruncatedDateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        db_table = 'test_drive_booking'
        verbose_name_plural = 'test drive bookings'

    def __str__(self):
        return f"Booking #{self.booking_id} - {self.customer} for {self.vehicle} on {self.booking_date}"


class Order(models.Model):
    class OrderStatus(models.TextChoices):
        NEEDS_APPROVAL = 'NEEDS_APPROVAL', 'Needs Approval'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        PARTIALLY_PAID = 'PARTIALLY_PAID', 'Partially Paid'
        PAID = 'PAID', 'Paid'
        FULFILLED = 'FULFILLED', 'Fulfilled'
        CANCELLED = 'CANCELLED', 'Cancelled'

    class FulfillmentType(models.TextChoices):
        STORE_PICKUP = 'STORE_PICKUP', 'Store Pickup'
        HOME_DELIVERY = 'HOME_DELIVERY', 'Home Delivery'

    class PaymentPreference(models.TextChoices):
        ONLINE_CARD = 'ONLINE_CARD', 'Online Card (Upfront)'
        STORE_PAYMENT = 'STORE_PAYMENT', 'Pay Upfront at Store (Cash/Card)'
        CASH_ON_DELIVERY = 'CASH_ON_DELIVERY', 'Cash on Delivery (COD)'
        FINANCING = 'FINANCING', 'Financing / Bank Transfer'

    order_id = models.AutoField(primary_key=True, verbose_name="Order ID")
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='orders', verbose_name="Customer")
    inventory = models.ForeignKey(Inventory, on_delete=models.PROTECT, related_name='orders', verbose_name="Inventory Item")
    store = models.ForeignKey(Store, on_delete=models.PROTECT, related_name='ecommerce_orders', verbose_name="Store")
    
    assigned_employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_orders',
        verbose_name="Assigned Store Employee"
    )
    reviewed_at = TruncatedDateTimeField(null=True, blank=True, verbose_name="Reviewed At")
    rejection_reason = models.TextField(null=True, blank=True, verbose_name="Rejection Reason")

    invoice = models.OneToOneField(
        Invoice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ecommerce_order',
        verbose_name="Invoice"
    )
    
    total_amount = models.IntegerField(verbose_name="Total Amount")
    deposit_amount = models.IntegerField(default=0, verbose_name="Deposit Amount")
    
    payment_preference = models.CharField(
        max_length=30,
        choices=PaymentPreference.choices,
        default=PaymentPreference.ONLINE_CARD,
        verbose_name="Payment Preference"
    )
    order_status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.NEEDS_APPROVAL,
        verbose_name="Order Status"
    )
    fulfillment_type = models.CharField(
        max_length=20,
        choices=FulfillmentType.choices,
        default=FulfillmentType.STORE_PICKUP,
        verbose_name="Fulfillment Type"
    )
    delivery_address = models.CharField(max_length=255, null=True, blank=True, verbose_name="Delivery Address")
    
    created_at = TruncatedDateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = TruncatedDateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        db_table = 'order'
        verbose_name_plural = 'orders'

    def __str__(self):
        return f"Order #{self.order_id} ({self.get_order_status_display()})"


class PaymentTransaction(models.Model):
    class PaymentMethod(models.TextChoices):
        ONLINE_CARD = 'ONLINE_CARD', 'Online Card'
        STORE_CARD = 'STORE_CARD', 'Card (at Store)'
        STORE_CASH = 'STORE_CASH', 'Cash (at Store)'
        CASH_ON_DELIVERY = 'CASH_ON_DELIVERY', 'Cash on Delivery (COD)'
        BANK_TRANSFER = 'BANK_TRANSFER', 'Bank Transfer / Wire'
        FINANCING = 'FINANCING', 'Dealership Financing'

    class PaymentType(models.TextChoices):
        HOLD_DEPOSIT = 'HOLD_DEPOSIT', 'Hold Deposit'
        FULL_PAYMENT = 'FULL_PAYMENT', 'Full Payment'
        BALANCE_PAYMENT = 'BALANCE_PAYMENT', 'Remaining Balance'
        REFUND = 'REFUND', 'Refund'

    class PaymentStatus(models.TextChoices):
        SUCCESS = 'SUCCESS', 'Success'
        FAILED = 'FAILED', 'Failed'
        PENDING = 'PENDING', 'Pending'
        REFUNDED = 'REFUNDED', 'Refunded'

    transaction_id = models.AutoField(primary_key=True, verbose_name="Transaction ID")
    gateway_transaction_id = models.CharField(max_length=100, null=True, blank=True, unique=True, verbose_name="Gateway Transaction ID")
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='transactions', verbose_name="Order")
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments', verbose_name="Invoice")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True, related_name='payments', verbose_name="Customer")
    
    recorded_by_employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_payments',
        verbose_name="Recorded By Employee"
    )
    
    payment_method = models.CharField(
        max_length=30,
        choices=PaymentMethod.choices,
        default=PaymentMethod.ONLINE_CARD,
        verbose_name="Payment Method"
    )
    payment_type = models.CharField(
        max_length=20,
        choices=PaymentType.choices,
        default=PaymentType.FULL_PAYMENT,
        verbose_name="Payment Type"
    )
    amount = models.IntegerField(verbose_name="Amount Paid")
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        verbose_name="Status"
    )

    created_at = TruncatedDateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = TruncatedDateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        db_table = 'payment'
        verbose_name_plural = 'payment transactions'

    def __str__(self):
        return f"Txn #{self.transaction_id} - ${self.amount} ({self.get_payment_method_display()}) [{self.status}]"
