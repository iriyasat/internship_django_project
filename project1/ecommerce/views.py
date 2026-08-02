import json
from django.db import connection

from django.shortcuts import render, redirect

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages

from .models import Order
from .db import (
    WISHLIST_TABLE,
    ORDER_TABLE,
    TEST_DRIVE_TABLE,
    fetch_customer_nav_counts,
)
from .serializers import (
    CatalogService, WishlistService, CartService, TestDriveService, OrderService,
    VehicleBodyService, VehicleBodySerializer, VehicleConditionService, VehicleConditionSerializer,
    VehicleDetailService,
    WishlistModelSerializer, CartItemModelSerializer, TestDriveBookingModelSerializer,
    OrderModelSerializer, PaymentTransactionModelSerializer
)


# Strictly secure helper to get current authenticated customer record
# Strictly secure helper to get current authenticated customer record
def get_customer_from_request(request):
    if not (hasattr(request, 'user') and request.user.is_authenticated):
        return None

    with connection.cursor() as cursor:
        # 1. Check cust_<id> username format
        if request.user.username.startswith('cust_'):
            try:
                c_id = int(request.user.username.split('_')[1])
                cursor.execute(
                    "SELECT customer_id, email, phone FROM customer WHERE customer_id = %s",
                    [c_id]
                )
                row = cursor.fetchone()
                if row:
                    from car_sales.models import Customer as CustomerModel
                    cust = CustomerModel()
                    cust.customer_id = row[0]
                    cust.email = row[1]
                    cust.phone = row[2]
                    return cust
            except Exception:
                pass

        # 2. Check matching email
        if request.user.email:
            cursor.execute(
                "SELECT customer_id, email, phone FROM customer WHERE email = %s",
                [request.user.email]
            )
            row = cursor.fetchone()
            if row:
                from car_sales.models import Customer as CustomerModel
                cust = CustomerModel()
                cust.customer_id = row[0]
                cust.email = row[1]
                cust.phone = row[2]
                return cust

        # 3. Create new customer record
        try:
            email = request.user.email or f"{request.user.username}@customer.com"
            cursor.execute(
                "INSERT INTO customer (email, password, phone) VALUES (%s, %s, %s)",
                [email, request.user.password or "securepass", "+1-555-0199"]
            )
            new_id = cursor.lastrowid
            cursor.execute(
                """INSERT INTO customer_info
                   (customer_id, firstname, lastname, customer_status, customer_address, city_id, country_id)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                [
                    new_id,
                    request.user.first_name or "Customer",
                    request.user.last_name or str(new_id),
                    "Active", "Registered Address", 1, 1
                ]
            )
            cursor.execute(
                "SELECT customer_id, email, phone FROM customer WHERE customer_id = %s",
                [new_id]
            )
            row = cursor.fetchone()
            if row:
                from car_sales.models import Customer as CustomerModel
                cust = CustomerModel()
                cust.customer_id = row[0]
                cust.email = row[1]
                cust.phone = row[2]
                return cust
        except Exception:
            # Fallback: try email lookup again
            cursor.execute(
                "SELECT customer_id, email, phone FROM customer WHERE email = %s",
                [request.user.email]
            )
            row = cursor.fetchone()
            if row:
                from car_sales.models import Customer as CustomerModel
                cust = CustomerModel()
                cust.customer_id = row[0]
                cust.email = row[1]
                cust.phone = row[2]
                return cust

    return None



# ==============================================================================
# 1. CATALOG & SEARCH VIEWS / APIS
# ==============================================================================

def catalog_view(request):
    """Customer vehicle catalog page."""
    meta = CatalogService.fetch_catalog_meta(active_condition=request.GET.get('condition', 'all'))
    customer = get_customer_from_request(request)
    if customer:
        wishlist_count, cart_count = fetch_customer_nav_counts(customer.customer_id)
    else:
        wishlist_count = 0
        cart_count = 0

    return render(request, 'ecommerce/catalog.html', {
        'customer': customer,
        'wishlist_count': wishlist_count,
        'cart_count': cart_count,
        'active_condition': request.GET.get('condition', 'all'),
        **meta
    })


def vehicle_detail_view(request, inventory_id):
    """View to display detailed vehicle information, specs, gallery, financing calculator, and dealer contact."""
    detail_data = VehicleDetailService.fetch_detail_data(inventory_id)
    customer = get_customer_from_request(request)
    if customer:
        wishlist_count, cart_count = fetch_customer_nav_counts(customer.customer_id)
    else:
        wishlist_count = 0
        cart_count = 0

    return render(request, 'ecommerce/vehicle_detail.html', {
        'customer': customer,
        'wishlist_count': wishlist_count,
        'cart_count': cart_count,
        **detail_data
    })


def api_catalog_vehicles(request):
    """JSON API for searching and filtering inventory vehicles."""
    vehicles, total_count, total_pages, current_page, available_filters = CatalogService.fetch_catalog_vehicles(
        make_id=request.GET.get('make_id'),
        brand=request.GET.get('brand') or request.GET.get('make'),
        store_id=request.GET.get('store_id'),
        search_q=request.GET.get('q'),
        min_price=request.GET.get('min_price'),
        max_price=request.GET.get('max_price'),
        min_miles=request.GET.get('min_miles'),
        max_miles=request.GET.get('max_miles'),
        body=request.GET.get('body'),
        condition=request.GET.get('condition'),
        transmission=request.GET.get('transmission'),
        color=request.GET.get('color'),
        interior=request.GET.get('interior'),
        state=request.GET.get('state'),
        trim=request.GET.get('trim'),
        sort=request.GET.get('sort'),
        page=request.GET.get('page', 1),
        page_size=request.GET.get('page_size', 24)
    )

    vehicles_only = str(request.GET.get('vehicles_only', '')).lower() in ['1', 'true', 'yes']
    if vehicles_only:
        return JsonResponse({'vehicles': vehicles})

    return JsonResponse({
        'success': True,
        'count': total_count,
        'total_pages': total_pages,
        'current_page': current_page,
        'vehicles': vehicles,
        'filters': available_filters
    })


def api_vehicle_bodies(request):
    """JSON API for fetching vehicle body types serialized from database via serializers.py."""
    bodies = VehicleBodyService.fetch_vehicle_bodies()
    return JsonResponse({'success': True, 'count': len(bodies), 'bodies': bodies})


def api_vehicle_conditions(request):
    """JSON API for fetching vehicle condition tabs (All Car, New Car, Used Car) serialized from database via serializers.py."""
    active_condition = request.GET.get('condition', 'all')
    tabs = VehicleConditionService.fetch_condition_tabs(active_condition=active_condition)
    return JsonResponse({'success': True, 'count': len(tabs), 'conditions': tabs})


def api_vehicle_models(request):
    """JSON API for fetching distinct vehicle models for a selected brand/make via serializers.py."""
    brand = request.GET.get('brand') or request.GET.get('make')
    make_id = request.GET.get('make_id')
    models_list = CatalogService.fetch_vehicle_models(brand=brand, make_id=make_id)
    return JsonResponse({'success': True, 'count': len(models_list), 'models': models_list})




# ==============================================================================
# 2. WISHLIST VIEWS & APIS
# ==============================================================================

def wishlist_view(request):
    """Customer wishlist page."""
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to access your saved wishlist.")
        return redirect('login')

    customer = get_customer_from_request(request)
    wishlist_items = WishlistService.fetch_customer_wishlist(customer) if customer else []
    return render(request, 'ecommerce/wishlist.html', {
        'customer': customer,
        'wishlist_items': wishlist_items
    })


@require_POST
def api_toggle_wishlist(request):
    """Add or remove a vehicle from customer's wishlist."""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required. Please log in.'}, status=401)

    customer = get_customer_from_request(request)
    if not customer:
        return JsonResponse({'success': False, 'error': 'Customer account profile not found.'}, status=400)

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
    """Customer shopping cart page."""
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to view your shopping cart.")
        return redirect('login')

    customer = get_customer_from_request(request)
    cart_items, total_price = CartService.fetch_customer_cart_items(customer) if customer else ([], 0)
    return render(request, 'ecommerce/cart.html', {
        'customer': customer,
        'cart_items': cart_items,
        'total_price': total_price
    })


@require_POST
def api_add_to_cart(request):
    """Add an inventory item to customer's cart."""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required. Please log in.'}, status=401)

    customer = get_customer_from_request(request)
    if not customer:
        return JsonResponse({'success': False, 'error': 'Customer profile not found.'}, status=400)

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
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required. Please log in.'}, status=401)

    customer = get_customer_from_request(request)
    if not customer:
        return JsonResponse({'success': False, 'error': 'Customer profile not found.'}, status=400)

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
    """Test drive booking page and user's scheduled test drives."""
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to schedule or view your test drive bookings.")
        return redirect('login')

    customer = get_customer_from_request(request)
    bookings = TestDriveService.fetch_customer_bookings(customer) if customer else []
    inventory_id = request.GET.get('inventory_id') or request.GET.get('vehicle_id')
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT s.store_id, s.store_name, c.city_name, co.country_name
            FROM store s
            JOIN city c ON s.city_id = c.city_id
            JOIN country co ON s.country_id = co.country_id
            ORDER BY s.store_name
        """)
        stores = [{'store_id': r[0], 'store_name': r[1], 'city': {'city_name': r[2]}, 'country': {'country_name': r[3]}} for r in cursor.fetchall()]

        selected_inventory = None
        if inventory_id and str(inventory_id).isdigit():
            cursor.execute("""
                SELECT i.inventory_id, v.vehicle_model, v.trim, m.make_name, s.store_name, c.city_name
                FROM inventory i
                JOIN vehicle_info v ON i.vehicle_id = v.id
                LEFT JOIN industry_info m ON v.make_id = m.make_id
                JOIN store s ON i.store_id = s.store_id
                JOIN city c ON s.city_id = c.city_id
                WHERE i.inventory_id = %s
            """, [inventory_id])
            row = cursor.fetchone()
            if row:
                class _Obj:
                    def __init__(self, **kw):
                        self.__dict__.update(kw)
                class _Inv:
                    def __init__(self, r):
                        self.inventory_id = r[0]
                        self.vehicle = _Obj(vehicle_model=r[1], trim=r[2], make=_Obj(make_name=r[3]))
                        self.store = _Obj(store_name=r[4], city=_Obj(city_name=r[5]))
                selected_inventory = _Inv(row)

        cursor.execute("""
            SELECT i.inventory_id, v.vehicle_model, v.trim, m.make_name, s.store_name, c.city_name
            FROM inventory i
            JOIN vehicle_info v ON i.vehicle_id = v.id
            LEFT JOIN industry_info m ON v.make_id = m.make_id
            JOIN store s ON i.store_id = s.store_id
            JOIN city c ON s.city_id = c.city_id
            WHERE i.status = 1
            LIMIT 60
        """)
        class _Obj:
            def __init__(self, **kw): self.__dict__.update(kw)
        avail_rows = cursor.fetchall()
        available_inventories = []
        for r in avail_rows:
            class _Inv:
                def __init__(self, row):
                    self.inventory_id = row[0]
                    self.vehicle = _Obj(vehicle_model=row[1], trim=row[2], make=_Obj(make_name=row[3]))
                    self.store = _Obj(store_name=row[4], city=_Obj(city_name=row[5]))
            available_inventories.append(_Inv(r))

    return render(request, 'ecommerce/test_drive.html', {
        'customer': customer,
        'bookings': bookings,
        'stores': stores,
        'selected_inventory': selected_inventory,
        'available_inventories': available_inventories,
    })


@require_POST
def api_book_test_drive(request):
    """Schedule a pre-purchase test drive."""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required. Please log in.'}, status=401)

    customer = get_customer_from_request(request)
    if not customer:
        return JsonResponse({'success': False, 'error': 'Customer profile not found.'}, status=400)

    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST

    inventory_id = data.get('inventory_id')
    vehicle_id = data.get('vehicle_id')
    store_id = data.get('store_id')

    if inventory_id and (not vehicle_id or not store_id):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT vehicle_id, store_id FROM inventory WHERE inventory_id = %s",
                [inventory_id]
            )
            row = cursor.fetchone()
            if row:
                vehicle_id = row[0]
                store_id = row[1]

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
    """Customer checkout page."""
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to proceed to checkout.")
        return redirect('login')

    customer = get_customer_from_request(request)
    if customer:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT ci.firstname, ci.lastname, ci.customer_status, ci.customer_address,
                       c.city_id, c.city_name, co.country_id, co.country_name
                FROM customer_info ci
                LEFT JOIN city c ON ci.city_id = c.city_id
                LEFT JOIN country co ON ci.country_id = co.country_id
                WHERE ci.customer_id = %s
            """, [customer.customer_id])
            ci_row = cursor.fetchone()
    else:
        ci_row = None

    class _Obj:
        def __init__(self, **kw): self.__dict__.update(kw)
    customer_info = _Obj(
        firstname=ci_row[0], lastname=ci_row[1],
        customer_status=ci_row[2], customer_address=ci_row[3],
        city=_Obj(city_id=ci_row[4], city_name=ci_row[5]),
        country=_Obj(country_id=ci_row[6], country_name=ci_row[7])
    ) if ci_row else None
    
    cart_items, cart_total = CartService.fetch_customer_cart_items(customer) if customer else ([], 0)

    inventory_id = request.GET.get('inventory_id')
    buy_now_item = None
    if inventory_id:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT i.inventory_id, v.vehicle_model, v.mmr, m.make_name, s.store_name
                FROM inventory i
                JOIN vehicle_info v ON i.vehicle_id = v.id
                LEFT JOIN industry_info m ON v.make_id = m.make_id
                JOIN store s ON i.store_id = s.store_id
                WHERE i.inventory_id = %s
            """, [inventory_id])
            b_row = cursor.fetchone()
        if b_row:
            buy_now_item = _Obj(
                inventory_id=b_row[0],
                vehicle=_Obj(vehicle_model=b_row[1], mmr=b_row[2], make=_Obj(make_name=b_row[3])),
                store=_Obj(store_name=b_row[4])
            )


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
    """Submit a new online order."""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required. Please log in.'}, status=401)

    customer = get_customer_from_request(request)
    if not customer:
        return JsonResponse({'success': False, 'error': 'Customer profile not found.'}, status=400)

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
    """View order history strictly for logged in customer."""
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to view your order history.")
        return redirect('login')

    customer = get_customer_from_request(request)
    orders = []
    if customer:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT o.order_id, o.total_amount, o.order_status, o.fulfillment_type,
                       o.created_at, v.vehicle_model, m.make_name, s.store_name
                FROM {order_table} o
                LEFT JOIN inventory i ON o.inventory_id = i.inventory_id
                LEFT JOIN vehicle_info v ON i.vehicle_id = v.id
                LEFT JOIN industry_info m ON v.make_id = m.make_id
                LEFT JOIN store s ON o.store_id = s.store_id
                WHERE o.customer_id = %s
                ORDER BY o.order_id DESC
            """.format(order_table=ORDER_TABLE), [customer.customer_id])
            order_rows = cursor.fetchall()

        class _Obj:
            def __init__(self, **kw): self.__dict__.update(kw)
        STATUS_MAP = {1: 'Needs Approval', 2: 'Approved', 3: 'Partially Paid', 4: 'Paid', 5: 'Fulfilled', 6: 'Rejected', 7: 'Cancelled'}
        for r in order_rows:
            orders.append(_Obj(
                order_id=r[0], total_amount=r[1],
                order_status=r[2], get_order_status_display=lambda s=r[2]: STATUS_MAP.get(s, str(s)),
                fulfillment_type=r[3], created_at=r[4],
                inventory=_Obj(vehicle=_Obj(vehicle_model=r[5], make=_Obj(make_name=r[6]))),
                store=_Obj(store_name=r[7])
            ))
    return render(request, 'ecommerce/customer_orders.html', {
        'customer': customer,
        'orders': orders
    })


# ==============================================================================
# 6. CUSTOMER PROFILE VIEWS & APIS
# ==============================================================================

def customer_profile_view(request):
    """Customer profile management page."""
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to view your customer profile.")
        return redirect('login')

    customer = get_customer_from_request(request)

    class _Obj:
        def __init__(self, **kw): self.__dict__.update(kw)

    customer_info = None
    orders_count = 0
    wishlist_count = 0
    test_drives_count = 0
    cities = []
    countries = []

    if customer:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT ci.firstname, ci.lastname, ci.customer_status, ci.customer_address,
                       c.city_id, c.city_name, co.country_id, co.country_name
                FROM customer_info ci
                LEFT JOIN city c ON ci.city_id = c.city_id
                LEFT JOIN country co ON ci.country_id = co.country_id
                WHERE ci.customer_id = %s
            """, [customer.customer_id])
            ci_row = cursor.fetchone()
            customer_info = _Obj(
                firstname=ci_row[0], lastname=ci_row[1],
                customer_status=ci_row[2], customer_address=ci_row[3],
                city=_Obj(city_id=ci_row[4], city_name=ci_row[5]),
                country=_Obj(country_id=ci_row[6], country_name=ci_row[7])
            ) if ci_row else None

            cursor.execute(f"SELECT COUNT(*) FROM {ORDER_TABLE} WHERE customer_id = %s", [customer.customer_id])
            orders_count = cursor.fetchone()[0]

            cursor.execute(f"SELECT COUNT(*) FROM {WISHLIST_TABLE} WHERE customer_id = %s", [customer.customer_id])
            wishlist_count = cursor.fetchone()[0]

            cursor.execute(f"SELECT COUNT(*) FROM {TEST_DRIVE_TABLE} WHERE customer_id = %s", [customer.customer_id])
            test_drives_count = cursor.fetchone()[0]

            cursor.execute("SELECT city_id, city_name FROM city ORDER BY city_name")
            cities = [_Obj(city_id=r[0], city_name=r[1]) for r in cursor.fetchall()]

            cursor.execute("SELECT country_id, country_name FROM country ORDER BY country_name")
            countries = [_Obj(country_id=r[0], country_name=r[1]) for r in cursor.fetchall()]

    return render(request, 'ecommerce/profile.html', {
        'customer': customer,
        'customer_info': customer_info,
        'orders_count': orders_count,
        'wishlist_count': wishlist_count,
        'test_drives_count': test_drives_count,
        'cities': cities,
        'countries': countries,
    })


@require_POST
def api_update_customer_profile(request):
    """API endpoint to update customer profile info."""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required. Please log in.'}, status=401)

    customer = get_customer_from_request(request)
    if not customer:
        return JsonResponse({'success': False, 'error': 'Customer profile not found.'}, status=400)

    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST

    phone = data.get('phone')
    firstname = data.get('firstname')
    lastname = data.get('lastname')
    customer_address = data.get('customer_address')
    city_id = data.get('city_id')
    country_id = data.get('country_id')

    try:
        with connection.cursor() as cursor:
            if phone is not None:
                cursor.execute(
                    "UPDATE customer SET phone = %s WHERE customer_id = %s",
                    [phone, customer.customer_id]
                )

            # Check if customer_info record exists
            cursor.execute(
                "SELECT customer_id FROM customer_info WHERE customer_id = %s",
                [customer.customer_id]
            )
            existing_info = cursor.fetchone()

            if existing_info:
                # Update existing record
                updates = []
                params = []
                if firstname: updates.append("firstname = %s"); params.append(firstname)
                if lastname: updates.append("lastname = %s"); params.append(lastname)
                if customer_address: updates.append("customer_address = %s"); params.append(customer_address)
                if city_id: updates.append("city_id = %s"); params.append(city_id)
                if country_id: updates.append("country_id = %s"); params.append(country_id)
                if updates:
                    params.append(customer.customer_id)
                    cursor.execute(
                        f"UPDATE customer_info SET {', '.join(updates)} WHERE customer_id = %s",
                        params
                    )
            else:
                # Insert new record
                cursor.execute("""
                    INSERT INTO customer_info
                        (customer_id, firstname, lastname, customer_status, customer_address, city_id, country_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, [
                    customer.customer_id,
                    firstname or request.user.first_name or 'Customer',
                    lastname or request.user.last_name or str(customer.customer_id),
                    'Active',
                    customer_address or 'Registered Address',
                    city_id or 1,
                    country_id or 1
                ])

        return JsonResponse({'success': True, 'message': 'Profile updated successfully!'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
