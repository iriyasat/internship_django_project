import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST

from car_sales.models import Customer, CustomerInfo, Store, IndustryInfo, Inventory, Employee
from .models import Order, PaymentTransaction
from .serializers import (
    CatalogService, WishlistService, CartService, TestDriveService, OrderService,
    WishlistModelSerializer, CartItemModelSerializer, TestDriveBookingModelSerializer,
    OrderModelSerializer, PaymentTransactionModelSerializer
)


# Helper to get current authenticated customer or demo fallback
def get_customer_from_request(request):
    if hasattr(request, 'user') and request.user.is_authenticated:
        try:
            if request.user.username.startswith('cust_'):
                c_id = int(request.user.username.split('_')[1])
                return Customer.objects.filter(customer_id=c_id).first()
        except Exception:
            pass
        cust = Customer.objects.filter(email=request.user.email).first()
        if cust:
            return cust
    return Customer.objects.first()


# ==============================================================================
# 1. CATALOG & SEARCH VIEWS / APIS
# ==============================================================================

def catalog_view(request):
    """Render customer e-commerce vehicle catalog page."""
    makes = IndustryInfo.objects.all().order_by('make_name')
    stores = Store.objects.select_related('city', 'country').all().order_by('store_name')
    return render(request, 'ecommerce/catalog.html', {
        'makes': makes,
        'stores': stores,
    })


def api_catalog_vehicles(request):
    """JSON API for searching and filtering inventory vehicles."""
    vehicles = CatalogService.fetch_catalog_vehicles(
        make_id=request.GET.get('make_id'),
        store_id=request.GET.get('store_id'),
        search_q=request.GET.get('q'),
        min_price=request.GET.get('min_price'),
        max_price=request.GET.get('max_price')
    )
    return JsonResponse({'success': True, 'count': len(vehicles), 'vehicles': vehicles})


# ==============================================================================
# 2. WISHLIST VIEWS & APIS
# ==============================================================================

def wishlist_view(request):
    """Render customer wishlist page."""
    customer = get_customer_from_request(request)
    wishlist_items = WishlistService.fetch_customer_wishlist(customer)
    return render(request, 'ecommerce/wishlist.html', {
        'customer': customer,
        'wishlist_items': wishlist_items
    })


@require_POST
def api_toggle_wishlist(request):
    """Add or remove a vehicle from customer's wishlist."""
    customer = get_customer_from_request(request)
    if not customer:
        return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)

    try:
        data = json.loads(request.body)
        vehicle_id = data.get('vehicle_id')
    except Exception:
        vehicle_id = request.POST.get('vehicle_id')

    if not vehicle_id:
        return JsonResponse({'success': False, 'error': 'vehicle_id required'}, status=400)

    try:
        res = WishlistService.toggle_wishlist(customer, vehicle_id)
        return JsonResponse({'success': True, **res})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ==============================================================================
# 3. SHOPPING CART VIEWS & APIS
# ==============================================================================

def cart_view(request):
    """Render customer shopping cart page."""
    customer = get_customer_from_request(request)
    cart_items, total_price = CartService.fetch_customer_cart_items(customer)
    return render(request, 'ecommerce/cart.html', {
        'customer': customer,
        'cart_items': cart_items,
        'total_price': total_price
    })


@require_POST
def api_add_to_cart(request):
    """Add an inventory item to customer's cart."""
    customer = get_customer_from_request(request)
    if not customer:
        return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)

    try:
        data = json.loads(request.body)
        inventory_id = data.get('inventory_id')
    except Exception:
        inventory_id = request.POST.get('inventory_id')

    try:
        res = CartService.add_to_cart(customer, inventory_id)
        return JsonResponse({'success': True, **res})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_remove_from_cart(request):
    """Remove an item from customer's cart."""
    customer = get_customer_from_request(request)
    if not customer:
        return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)

    try:
        data = json.loads(request.body)
        inventory_id = data.get('inventory_id')
    except Exception:
        inventory_id = request.POST.get('inventory_id')

    try:
        res = CartService.remove_from_cart(customer, inventory_id)
        return JsonResponse({'success': True, **res})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ==============================================================================
# 4. TEST DRIVE BOOKING VIEWS & APIS
# ==============================================================================

def test_drive_view(request):
    """Render test drive booking page and user's scheduled test drives."""
    customer = get_customer_from_request(request)
    bookings = TestDriveService.fetch_customer_bookings(customer)
    stores = Store.objects.select_related('city', 'country').all()

    return render(request, 'ecommerce/test_drive.html', {
        'customer': customer,
        'bookings': bookings,
        'stores': stores
    })


@require_POST
def api_book_test_drive(request):
    """Schedule a pre-purchase test drive."""
    customer = get_customer_from_request(request)
    if not customer:
        return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)

    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST

    vehicle_id = data.get('vehicle_id')
    store_id = data.get('store_id')
    booking_date_str = data.get('booking_date')
    booking_time_str = data.get('booking_time', '10:00')
    notes = data.get('notes', '')

    if not vehicle_id or not store_id or not booking_date_str:
        return JsonResponse({'success': False, 'error': 'vehicle_id, store_id, and booking_date are required'}, status=400)

    try:
        booking = TestDriveService.create_booking(customer, vehicle_id, store_id, booking_date_str, booking_time_str, notes)
        return JsonResponse({
            'success': True,
            'message': 'Test drive scheduled successfully',
            'booking_id': booking.booking_id,
            'booking_date': str(booking.booking_date),
            'booking_time': str(booking.booking_time)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ==============================================================================
# 5. CHECKOUT & ORDER SUBMISSION VIEWS & APIS
# ==============================================================================

def checkout_view(request):
    """Render checkout page."""
    customer = get_customer_from_request(request)
    customer_info = CustomerInfo.objects.filter(customer=customer).select_related('city', 'country').first() if customer else None
    
    cart_items, cart_total = CartService.fetch_customer_cart_items(customer)

    inventory_id = request.GET.get('inventory_id')
    buy_now_item = None
    if inventory_id:
        buy_now_item = Inventory.objects.select_related('vehicle__make', 'store').filter(pk=inventory_id).first()

    total_amount = buy_now_item.vehicle.mmr if buy_now_item else cart_total

    return render(request, 'ecommerce/checkout.html', {
        'customer': customer,
        'customer_info': customer_info,
        'cart_items': cart_items,
        'buy_now_item': buy_now_item,
        'total_amount': total_amount
    })


@require_POST
def api_submit_order(request):
    """Submit a new online order (enters NEEDS_APPROVAL status for store staff)."""
    customer = get_customer_from_request(request)
    if not customer:
        return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)

    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST

    inventory_id = data.get('inventory_id')
    fulfillment_type = data.get('fulfillment_type', Order.FulfillmentType.STORE_PICKUP)
    payment_preference = data.get('payment_preference', Order.PaymentPreference.ONLINE_CARD)
    delivery_address = data.get('delivery_address', '')

    if not inventory_id:
        return JsonResponse({'success': False, 'error': 'inventory_id is required'}, status=400)

    try:
        order = OrderService.submit_order(customer, inventory_id, fulfillment_type, payment_preference, delivery_address)
        return JsonResponse({
            'success': True,
            'message': 'Order submitted successfully and sent for store approval',
            'order_id': order.order_id,
            'order_status': order.get_order_status_display()
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def customer_orders_view(request):
    """View order history for customer."""
    customer = get_customer_from_request(request)
    orders = Order.objects.filter(customer=customer).select_related('inventory__vehicle__make', 'store', 'invoice', 'assigned_employee').order_by('-order_id') if customer else []
    return render(request, 'ecommerce/customer_orders.html', {
        'customer': customer,
        'orders': orders
    })


# ==============================================================================
# 6. STORE STAFF DASHBOARD & WORKFLOW APIS
# ==============================================================================

def store_staff_dashboard_view(request):
    """Store Staff Order Approval & Queue Dashboard."""
    store_id = request.GET.get('store_id')
    stores = Store.objects.select_related('city', 'country').all().order_by('store_name')

    selected_store = Store.objects.filter(pk=store_id).first() if store_id else stores.first()

    pending_orders = Order.objects.filter(
        store=selected_store, 
        order_status=Order.OrderStatus.NEEDS_APPROVAL
    ).select_related('customer', 'inventory__vehicle__make', 'assigned_employee').order_by('-order_id')

    approved_orders = Order.objects.filter(
        store=selected_store, 
        order_status__in=[Order.OrderStatus.APPROVED, Order.OrderStatus.PARTIALLY_PAID, Order.OrderStatus.PAID]
    ).select_related('customer', 'inventory__vehicle__make', 'assigned_employee', 'invoice').order_by('-order_id')

    return render(request, 'ecommerce/staff_dashboard.html', {
        'stores': stores,
        'selected_store': selected_store,
        'pending_orders': pending_orders,
        'approved_orders': approved_orders
    })


@require_POST
def api_review_order(request):
    """Store staff accepts or rejects an incoming order."""
    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST

    order_id = data.get('order_id')
    action = data.get('action') # 'ACCEPT' or 'REJECT'
    employee_id = data.get('employee_id')
    rejection_reason = data.get('rejection_reason', '')

    if not order_id or action not in ['ACCEPT', 'REJECT']:
        return JsonResponse({'success': False, 'error': 'order_id and valid action (ACCEPT/REJECT) required'}, status=400)

    try:
        order, msg = OrderService.review_order(order_id, action, employee_id, rejection_reason)
        return JsonResponse({
            'success': True, 
            'message': msg, 
            'order_id': order.order_id, 
            'order_status': order.get_order_status_display()
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_record_payment(request):
    """Store staff records in-person cash, card, or delivery payment."""
    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST

    order_id = data.get('order_id')
    amount = data.get('amount')
    payment_method = data.get('payment_method', PaymentTransaction.PaymentMethod.STORE_CASH)
    employee_id = data.get('employee_id')

    if not order_id or not amount:
        return JsonResponse({'success': False, 'error': 'order_id and amount are required'}, status=400)

    try:
        txn, order = OrderService.record_payment(order_id, amount, payment_method, employee_id)
        return JsonResponse({
            'success': True,
            'message': f"Payment of ${amount} recorded successfully",
            'transaction_id': txn.transaction_id,
            'order_status': order.get_order_status_display()
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def api_fulfill_order(request):
    """Staff completes vehicle handover -> Auto-creates SellingInfo record and updates Inventory to SOLD (1)."""
    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST

    order_id = data.get('order_id')
    employee_id = data.get('employee_id')

    if not order_id:
        return JsonResponse({'success': False, 'error': 'order_id required'}, status=400)

    try:
        selling_info, order = OrderService.fulfill_order(order_id, employee_id)
        return JsonResponse({
            'success': True,
            'message': f"Order #{order.order_id} fulfilled! Sales credit assigned to employee #{selling_info.employee_id}.",
            'sell_id': selling_info.sell_id,
            'order_status': order.get_order_status_display()
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
