import json
from django.db import connection

from django.shortcuts import render, redirect

from django.utils import timezone

def safe_format_time(dt):
    if not dt:
        return "12:00 AM"
    try:
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt)
        return timezone.localtime(dt).strftime('%I:%M %p')
    except Exception:
        return dt.strftime('%I:%M %p')


from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib import messages
from django.core.files.storage import default_storage
from project1.workspaces import get_workspace_for_user, is_customer_workspace_user

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
    VehicleDetailService, _resolve_vehicle_image_url,
    WishlistModelSerializer, CartItemModelSerializer, TestDriveBookingModelSerializer,
    OrderModelSerializer, PaymentTransactionModelSerializer
)


def _get_request_payload(request):
    """Safely extract payload dictionary from DRF request.data, JSON body, or POST/GET parameters."""
    if hasattr(request, 'data') and request.data is not None:
        if isinstance(request.data, dict):
            return request.data
        elif hasattr(request.data, 'dict'):
            return request.data.dict()
    try:
        if hasattr(request, 'body') and request.body:
            return json.loads(request.body)
    except Exception:
        pass
    if hasattr(request, 'POST') and request.POST:
        return request.POST
    return getattr(request, 'GET', {})


def get_customer_from_request(request):
    if not (hasattr(request, 'user') and request.user.is_authenticated):
        return None

    with connection.cursor() as cursor:
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

        cursor.execute("SELECT customer_id, email, phone FROM customer ORDER BY customer_id ASC LIMIT 1")
        row = cursor.fetchone()
        if row:
            from car_sales.models import Customer as CustomerModel
            cust = CustomerModel()
            cust.customer_id = row[0]
            cust.email = row[1]
            cust.phone = row[2]
            return cust

    return None


def _require_customer_workspace(request, json_mode=False):
    if not is_customer_workspace_user(request.user):
        if json_mode:
            return JsonResponse({'success': False, 'error': 'Permission denied. This action is restricted to the customer workspace.'}, status=403)
        messages.error(request, "Permission denied. This page is restricted to the customer workspace.")
        return redirect('dashboard' if get_workspace_for_user(request.user) == 'car_sales' else 'home')
    return None




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


@api_view(['GET'])
def api_catalog_vehicles(request):
    """JSON API for searching and filtering inventory vehicles."""
    filter_kwargs = {
        'make_id': request.GET.get('make_id'),
        'brand': request.GET.get('brand') or request.GET.get('make'),
        'store_id': request.GET.get('store_id'),
        'search_q': request.GET.get('q'),
        'min_price': request.GET.get('min_price'),
        'max_price': request.GET.get('max_price'),
        'min_miles': request.GET.get('min_miles'),
        'max_miles': request.GET.get('max_miles'),
        'body': request.GET.get('body'),
        'condition': request.GET.get('condition'),
        'transmission': request.GET.get('transmission'),
        'color': request.GET.get('color'),
        'interior': request.GET.get('interior'),
        'state': request.GET.get('state'),
        'trim': request.GET.get('trim'),
        'sort': request.GET.get('sort'),
        'page': request.GET.get('page', 1),
        'page_size': request.GET.get('page_size', 24)
    }

    count_only = str(request.GET.get('count_only', '')).lower() in ['1', 'true', 'yes']
    if count_only:
        count = CatalogService.fetch_catalog_count(**filter_kwargs)
        return JsonResponse({'success': True, 'count': count})

    vehicles, total_count, total_pages, current_page, available_filters = CatalogService.fetch_catalog_vehicles(**filter_kwargs)

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


@api_view(['GET'])
def api_vehicle_bodies(request):
    """JSON API for fetching vehicle body types serialized from database via serializers.py."""
    bodies = VehicleBodyService.fetch_vehicle_bodies()
    return JsonResponse({'success': True, 'count': len(bodies), 'bodies': bodies})


@api_view(['GET'])
def api_vehicle_conditions(request):
    """JSON API for fetching vehicle condition tabs (All Car, New Car, Used Car) serialized from database via serializers.py."""
    active_condition = request.GET.get('condition', 'all')
    tabs = VehicleConditionService.fetch_condition_tabs(active_condition=active_condition)
    return JsonResponse({'success': True, 'count': len(tabs), 'conditions': tabs})


@api_view(['GET'])
def api_vehicle_models(request):
    """JSON API for fetching distinct vehicle models for a selected brand/make via serializers.py."""
    brand = request.GET.get('brand') or request.GET.get('make')
    make_id = request.GET.get('make_id')
    models_list = CatalogService.fetch_vehicle_models(brand=brand, make_id=make_id)
    return JsonResponse({'success': True, 'count': len(models_list), 'models': models_list})


@api_view(['GET'])
def api_vehicle_trims(request):
    """JSON API for fetching distinct vehicle trims for a selected brand/model via serializers.py."""
    brand = request.GET.get('brand') or request.GET.get('make')
    model = request.GET.get('model') or request.GET.get('q')
    trims_list = CatalogService.fetch_vehicle_trims(brand=brand, model=model)
    return JsonResponse({'success': True, 'count': len(trims_list), 'trims': trims_list})



def compare_view(request):
    """Compare up to 4 vehicles side-by-side using raw SQL."""
    customer = get_customer_from_request(request)
    if customer:
        wishlist_count, cart_count = fetch_customer_nav_counts(customer.customer_id)
    else:
        wishlist_count = 0
        cart_count = 0

    raw_ids = []
    ids_csv = (request.GET.get('ids') or '').strip()
    if ids_csv:
        raw_ids.extend(ids_csv.split(','))
    raw_ids.extend(request.GET.getlist('inventory_id'))

    seen = set()
    selected_ids = []
    for item in raw_ids:
        try:
            inv_id = int(str(item).strip())
        except (TypeError, ValueError):
            continue
        if inv_id > 0 and inv_id not in seen:
            seen.add(inv_id)
            selected_ids.append(inv_id)
        if len(selected_ids) == 4:
            break

    compare_vehicles = []
    if selected_ids:
        placeholders = ", ".join(["%s"] * len(selected_ids))
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    i.inventory_id, i.status,
                    v.id AS vehicle_id, v.vehicle_model, v.trim, v.body, v.transmission,
                    v.color, v.interior, v.state, v.condition, v.odometer, v.mmr, v.vin,
                    m.make_name,
                    s.store_name, c.city_name, co.country_name
                FROM inventory i
                JOIN vehicle_info v ON i.vehicle_id = v.id
                LEFT JOIN industry_info m ON v.make_id = m.make_id
                JOIN store s ON i.store_id = s.store_id
                JOIN city c ON s.city_id = c.city_id
                JOIN country co ON s.country_id = co.country_id
                WHERE i.inventory_id IN ({placeholders})
                """,
                selected_ids,
            )
            rows = cursor.fetchall()

        row_map = {}
        for row in rows:
            (
                inventory_id,
                status_code,
                vehicle_id,
                model,
                trim,
                body,
                transmission,
                color,
                interior,
                state,
                condition,
                odometer,
                price,
                vin,
                make_name,
                store_name,
                city_name,
                country_name,
            ) = row
            make_slug = str(make_name or '').lower().replace(' ', '').replace('-', '')
            logo_alias = 'mercedes' if 'mercedes' in make_slug else ('landrover' if 'landrover' in make_slug else make_slug)
            row_map[inventory_id] = {
                'inventory_id': inventory_id,
                'vehicle_id': vehicle_id,
                'make': make_name or 'Vehicle',
                'model': model or '',
                'trim': trim or '',
                'body': body or '',
                'transmission': transmission or '',
                'color': color or '',
                'interior': interior or '',
                'state': state or '',
                'condition': condition,
                'odometer': odometer,
                'price': price,
                'vin': vin or '',
                'status_code': status_code,
                'store_name': store_name or '',
                'city': city_name or '',
                'country': country_name or '',
                'image_url': _resolve_vehicle_image_url(make_name, model),
            }

        compare_vehicles = [row_map[i] for i in selected_ids if i in row_map]

    return render(
        request,
        'ecommerce/compare.html',
        {
            'customer': customer,
            'wishlist_count': wishlist_count,
            'cart_count': cart_count,
            'compare_vehicles': compare_vehicles,
            'selected_ids': selected_ids,
            'max_compare': 4,
        },
    )





def wishlist_view(request):
    """Customer wishlist page."""
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to access your saved wishlist.")
        return redirect('login')
    gate = _require_customer_workspace(request)
    if gate:
        return gate

    customer = get_customer_from_request(request)
    wishlist_items = WishlistService.fetch_customer_wishlist(customer) if customer else []
    wishlist_count, cart_count = fetch_customer_nav_counts(customer.customer_id) if customer else (0, 0)
    return render(request, 'ecommerce/wishlist.html', {
        'customer': customer,
        'wishlist_items': wishlist_items,
        'wishlist_count': wishlist_count,
        'cart_count': cart_count,
    })


@api_view(['POST', 'DELETE'])
def api_toggle_wishlist(request):
    """Add, remove, or toggle a vehicle in customer's wishlist."""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required. Please log in.'}, status=401)

    customer = get_customer_from_request(request)
    if not customer:
        return JsonResponse({'success': False, 'error': 'Customer account profile not found.'}, status=400)

    payload = _get_request_payload(request)
    target_id = payload.get('vehicle_id') or payload.get('inventory_id') or payload.get('id')

    if not target_id:
        return JsonResponse({'success': False, 'error': 'vehicle_id required'}, status=400)

    vehicle_id = None
    with connection.cursor() as cursor:
        cursor.execute("SELECT id FROM vehicle_info WHERE id = %s LIMIT 1", [target_id])
        v_row = cursor.fetchone()
        if v_row:
            vehicle_id = v_row[0]
        else:
            cursor.execute("SELECT vehicle_id FROM inventory WHERE inventory_id = %s LIMIT 1", [target_id])
            inv_row = cursor.fetchone()
            if inv_row and inv_row[0]:
                vehicle_id = inv_row[0]
            else:
                vehicle_id = target_id

    action = 'delete' if (request.method == 'DELETE' or request.path.endswith('/remove/') or payload.get('action') in ('delete', 'remove')) else None

    try:
        res = WishlistService.toggle_wishlist(customer, vehicle_id, action=action)
        return JsonResponse({'success': True, **res})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)



def cart_view(request):
    """Customer shopping cart page."""
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to view your shopping cart.")
        return redirect('login')
    gate = _require_customer_workspace(request)
    if gate:
        return gate

    customer = get_customer_from_request(request)
    cart_items, total_price = CartService.fetch_customer_cart_items(customer) if customer else ([], 0)
    wishlist_count, cart_count = fetch_customer_nav_counts(customer.customer_id) if customer else (0, 0)
    return render(request, 'ecommerce/cart.html', {
        'customer': customer,
        'cart_items': cart_items,
        'total_price': total_price,
        'wishlist_count': wishlist_count,
        'cart_count': cart_count,
    })


@api_view(['POST'])
def api_add_to_cart(request):
    """Add an inventory item to customer's cart."""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required. Please log in.'}, status=401)

    customer = get_customer_from_request(request)
    if not customer:
        return JsonResponse({'success': False, 'error': 'Customer profile not found.'}, status=400)

    payload = _get_request_payload(request)
    inventory_id = payload.get('inventory_id') or payload.get('vehicle_id') or payload.get('id')

    try:
        res = CartService.add_to_cart(customer, inventory_id)
        return JsonResponse({'success': True, **res})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@api_view(['POST'])
def api_remove_from_cart(request):
    """Remove an item from customer's cart."""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required. Please log in.'}, status=401)

    customer = get_customer_from_request(request)
    if not customer:
        return JsonResponse({'success': False, 'error': 'Customer profile not found.'}, status=400)

    payload = _get_request_payload(request)
    inventory_id = payload.get('inventory_id') or payload.get('vehicle_id') or payload.get('id')

    try:
        res = CartService.remove_from_cart(customer, inventory_id)
        return JsonResponse({'success': True, **res})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)



def test_drive_view(request):
    """Test drive booking page and user's scheduled test drives."""
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to schedule or view your test drive bookings.")
        return redirect('login')
    gate = _require_customer_workspace(request)
    if gate:
        return gate

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


@api_view(['POST'])
def api_book_test_drive(request):
    """Schedule a pre-purchase test drive."""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required. Please log in.'}, status=401)
    gate = _require_customer_workspace(request, json_mode=True)
    if gate:
        return gate

    customer = get_customer_from_request(request)
    if not customer:
        return JsonResponse({'success': False, 'error': 'Customer profile not found.'}, status=400)

    data = _get_request_payload(request)

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




def checkout_view(request):
    """Customer checkout page."""
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to proceed to checkout.")
        return redirect('login')
    gate = _require_customer_workspace(request)
    if gate:
        return gate

    customer = get_customer_from_request(request)
    if customer:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT ci.firstname, ci.lastname, ci.customer_status, ci.customer_address, ci.profile_picture,
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
    profile_picture = ci_row[4] if ci_row and ci_row[4] else None
    profile_picture_url = f"/media/{profile_picture}" if profile_picture else None
    customer_info = _Obj(
        firstname=ci_row[0], lastname=ci_row[1],
        customer_status=ci_row[2], customer_address=ci_row[3],
        profile_picture=profile_picture,
        profile_picture_url=profile_picture_url,
        city=_Obj(city_id=ci_row[5], city_name=ci_row[6]) if ci_row and ci_row[5] else None,
        country=_Obj(country_id=ci_row[7], country_name=ci_row[8]) if ci_row and ci_row[7] else None
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
            make_name = b_row[3] or 'Vehicle'
            model_name = b_row[1] or ''
            buy_now_item = _Obj(
                inventory_id=b_row[0],
                vehicle=_Obj(
                    vehicle_model=model_name,
                    mmr=b_row[2],
                    make=_Obj(make_name=make_name),
                    image_url=_resolve_vehicle_image_url(make_name, model_name)
                ),
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


@api_view(['POST'])
def api_submit_order(request):
    """Submit a new online order."""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required. Please log in.'}, status=401)

    customer = get_customer_from_request(request)
    if not customer:
        return JsonResponse({'success': False, 'error': 'Customer profile not found.'}, status=400)

    data = _get_request_payload(request)

    inventory_id = data.get('inventory_id') or data.get('vehicle_id') or data.get('id')
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
    """View order history — redirects to merged profile page orders tab."""
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to view your order history.")
        return redirect('login')
    return redirect('/profile/?tab=orders')



def customer_profile_view(request):
    """Customer profile management & merged order history page."""
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to view your customer profile.")
        return redirect('login')
    gate = _require_customer_workspace(request)
    if gate:
        return gate

    customer = get_customer_from_request(request)

    class _Obj:
        def __init__(self, **kw): self.__dict__.update(kw)

    customer_info = None
    orders_count = 0
    wishlist_count = 0
    test_drives_count = 0
    cities = []
    countries = []
    orders = []

    if customer:
        order_table = connection.ops.quote_name(ORDER_TABLE)
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT ci.firstname, ci.lastname, ci.customer_status, ci.customer_address, ci.profile_picture,
                       c.city_id, c.city_name, co.country_id, co.country_name
                FROM customer_info ci
                LEFT JOIN city c ON ci.city_id = c.city_id
                LEFT JOIN country co ON ci.country_id = co.country_id
                WHERE ci.customer_id = %s
            """, [customer.customer_id])
            ci_row = cursor.fetchone()
            profile_picture = ci_row[4] if ci_row and ci_row[4] else None
            profile_picture_url = f"/media/{profile_picture}" if profile_picture else None
            customer_info = _Obj(
                firstname=ci_row[0] if ci_row else '',
                lastname=ci_row[1] if ci_row else '',
                customer_status=ci_row[2] if ci_row else 'Active',
                customer_address=ci_row[3] if ci_row else '',
                profile_picture=profile_picture,
                profile_picture_url=profile_picture_url,
                city=_Obj(city_id=ci_row[5], city_name=ci_row[6]) if ci_row and ci_row[5] else None,
                country=_Obj(country_id=ci_row[7], country_name=ci_row[8]) if ci_row and ci_row[7] else None
            ) if ci_row else None

            cursor.execute(f"SELECT COUNT(*) FROM {order_table} WHERE customer_id = %s", [customer.customer_id])
            orders_count = cursor.fetchone()[0]

            cursor.execute(f"SELECT COUNT(*) FROM {WISHLIST_TABLE} WHERE customer_id = %s", [customer.customer_id])
            wishlist_count = cursor.fetchone()[0]

            cursor.execute(f"SELECT COUNT(*) FROM {TEST_DRIVE_TABLE} WHERE customer_id = %s", [customer.customer_id])
            test_drives_count = cursor.fetchone()[0]

            cursor.execute("SELECT city_id, city_name FROM city ORDER BY city_name")
            cities = [_Obj(city_id=r[0], city_name=r[1]) for r in cursor.fetchall()]

            cursor.execute("SELECT country_id, country_name FROM country ORDER BY country_name")
            countries = [_Obj(country_id=r[0], country_name=r[1]) for r in cursor.fetchall()]

            cursor.execute("""
                SELECT o.order_id, o.total_amount, o.order_status, o.fulfillment_type,
                       o.created_at, v.vehicle_model, m.make_name, s.store_name,
                       o.payment_preference, e.first_name, e.last_name
                FROM {order_table} o
                LEFT JOIN inventory i ON o.inventory_id = i.inventory_id
                LEFT JOIN vehicle_info v ON i.vehicle_id = v.id
                LEFT JOIN industry_info m ON v.make_id = m.make_id
                LEFT JOIN store s ON o.store_id = s.store_id
                LEFT JOIN employee e ON o.assigned_employee_id = e.employee_id
                WHERE o.customer_id = %s
                ORDER BY o.order_id DESC
            """.format(order_table=order_table), [customer.customer_id])
            order_rows = cursor.fetchall()

            STATUS_MAP = {
                'NEEDS_APPROVAL': 'Needs Approval',
                'APPROVED': 'Approved',
                'PARTIALLY_PAID': 'Partially Paid',
                'PAID': 'Paid',
                'FULFILLED': 'Fulfilled',
                'REJECTED': 'Rejected',
                'CANCELLED': 'Cancelled',
            }
            PAYMENT_MAP = {
                'ONLINE_CARD': 'Online Card (Upfront)',
                'STORE_PAYMENT': 'Pay Upfront at Store (Cash/Card)',
                'CASH_ON_DELIVERY': 'Cash on Delivery (COD)',
                'FINANCING': 'Financing / Bank Transfer',
            }
            for r in order_rows:
                vehicle_model = r[5]
                make_name = r[6]
                orders.append(_Obj(
                    order_id=r[0],
                    total_amount=r[1],
                    order_status=r[2],
                    get_order_status_display=STATUS_MAP.get(r[2], str(r[2])),
                    fulfillment_type=r[3],
                    created_at=r[4],
                    get_payment_preference_display=PAYMENT_MAP.get(r[8], r[8]),
                    assigned_employee=f"{(r[9] or '').strip()} {(r[10] or '').strip()}".strip() or None,
                    invoice=None,
                    inventory=_Obj(vehicle=_Obj(
                        vehicle_model=vehicle_model,
                        make=_Obj(make_name=make_name),
                        image_url=_resolve_vehicle_image_url(make_name, vehicle_model),
                    )),
                    store=_Obj(store_name=r[7]),
                ))

    active_tab = request.GET.get('tab', 'overview')

    return render(request, 'ecommerce/profile.html', {
        'customer': customer,
        'customer_info': customer_info,
        'orders_count': orders_count,
        'wishlist_count': wishlist_count,
        'test_drives_count': test_drives_count,
        'cities': cities,
        'countries': countries,
        'orders': orders,
        'active_tab': active_tab,
    })


@api_view(['POST'])
def api_update_customer_profile(request):
    """API endpoint to update customer profile info."""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required. Please log in.'}, status=401)
    gate = _require_customer_workspace(request, json_mode=True)
    if gate:
        return gate

    customer = get_customer_from_request(request)
    if not customer:
        return JsonResponse({'success': False, 'error': 'Customer profile not found.'}, status=400)

    data = request.POST
    if not data:
        try:
            data = json.loads(request.body)
        except Exception:
            data = {}

    phone = data.get('phone')
    password = (data.get('password') or '').strip()
    confirm_password = (data.get('confirm_password') or '').strip()

    if password or confirm_password:
        if password != confirm_password:
            return JsonResponse({'success': False, 'error': 'New Password and Confirm Password do not match.'}, status=400)
        if len(password) < 6:
            return JsonResponse({'success': False, 'error': 'New Password must be at least 6 characters long.'}, status=400)

    firstname = data.get('firstname')
    lastname = data.get('lastname')
    customer_status = data.get('customer_status')
    customer_address = data.get('customer_address')
    city_id = data.get('city_id')
    country_id = data.get('country_id')
    profile_picture = request.FILES.get('profile_picture')

    profile_picture_path = None
    if profile_picture:
        allowed_types = {'image/png', 'image/jpeg', 'image/jpg', 'image/svg+xml'}
        if profile_picture.content_type not in allowed_types:
            return JsonResponse({'success': False, 'error': 'Invalid image format. Allowed: PNG, JPG, JPEG, SVG.'}, status=400)
        if profile_picture.size > 4 * 1024 * 1024:
            return JsonResponse({'success': False, 'error': 'Image size must be 4 MB or smaller.'}, status=400)
        profile_picture_path = default_storage.save(f"profile_pics/{profile_picture.name}", profile_picture)

    try:
        with connection.cursor() as cursor:
            if phone is not None:
                cursor.execute(
                    "UPDATE customer SET phone = %s WHERE customer_id = %s",
                    [phone, customer.customer_id]
                )

            if password:
                cursor.execute(
                    "UPDATE customer SET password = %s WHERE customer_id = %s",
                    [password, customer.customer_id]
                )
                if hasattr(request, 'user') and request.user.is_authenticated:
                    try:
                        request.user.set_password(password)
                        request.user.save()
                        from django.contrib.auth import update_session_auth_hash
                        update_session_auth_hash(request, request.user)
                    except Exception:
                        pass

            cursor.execute(
                "SELECT customer_id FROM customer_info WHERE customer_id = %s",
                [customer.customer_id]
            )
            existing_info = cursor.fetchone()

            if existing_info:
                updates = []
                params = []
                if firstname: updates.append("firstname = %s"); params.append(firstname)
                if lastname: updates.append("lastname = %s"); params.append(lastname)
                if customer_status: updates.append("customer_status = %s"); params.append(customer_status)
                if customer_address: updates.append("customer_address = %s"); params.append(customer_address)
                if city_id: updates.append("city_id = %s"); params.append(city_id)
                if country_id: updates.append("country_id = %s"); params.append(country_id)
                if profile_picture_path: updates.append("profile_picture = %s"); params.append(profile_picture_path)
                if updates:
                    params.append(customer.customer_id)
                    cursor.execute(
                        f"UPDATE customer_info SET {', '.join(updates)} WHERE customer_id = %s",
                        params
                    )
            else:
                cursor.execute("""
                    INSERT INTO customer_info
                        (customer_id, firstname, lastname, customer_status, customer_address, city_id, country_id, profile_picture)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, [
                    customer.customer_id,
                    firstname or request.user.first_name or 'Customer',
                    lastname or request.user.last_name or str(customer.customer_id),
                    customer_status or 'Active',
                    customer_address or 'Registered Address',
                    city_id or 1,
                    country_id or 1,
                    profile_picture_path
                ])

        return JsonResponse({'success': True, 'message': 'Profile updated successfully!'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@api_view(['POST'])
def api_send_customer_message(request):
    """API endpoint for customers to send messages to a dealership store."""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required. Please log in to send a message.'}, status=401)
    gate = _require_customer_workspace(request, json_mode=True)
    if gate:
        return gate

    customer = get_customer_from_request(request)
    if not customer:
        return JsonResponse({'success': False, 'error': 'Customer profile not found.'}, status=400)

    data = request.POST
    if not data:
        try:
            data = json.loads(request.body)
        except Exception:
            data = {}

    inventory_id = data.get('inventory_id')
    store_id = data.get('store_id')
    message_text = (data.get('message') or data.get('message_text') or '').strip()

    if not message_text:
        return JsonResponse({'success': False, 'error': 'Message content cannot be empty.'}, status=400)

    employee_id = None
    if inventory_id:
        with connection.cursor() as cursor:
            cursor.execute("SELECT store_id, employee_id FROM inventory WHERE inventory_id = %s", [inventory_id])
            inv_row = cursor.fetchone()
            if inv_row:
                store_id = store_id or inv_row[0]
                employee_id = inv_row[1]

    if not store_id:
        return JsonResponse({'success': False, 'error': 'Target store is required.'}, status=400)

    try:
        from car_sales.models import CustomerMessage
        now_time = timezone.localtime(timezone.now()).strftime('%I:%M %p')
        timestamped_line = f"[TIME: {now_time}] {message_text}"

        existing_msg = CustomerMessage.objects.filter(
            customer_id=customer.customer_id,
            store_id=int(store_id)
        ).order_by('message_id').first()

        if existing_msg:
            existing_msg.message = f"{existing_msg.message}\n{timestamped_line}"
            existing_msg.updated_at = timezone.now()
            existing_msg.save()
            msg = existing_msg
        else:
            msg = CustomerMessage.objects.create(
                customer_id=customer.customer_id,
                store_id=int(store_id),
                employee_id=int(employee_id) if employee_id else None,
                message=timestamped_line
            )

        return JsonResponse({
            'success': True,
            'message': 'Your message has been sent successfully!',
            'message_id': msg.message_id
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def customer_messages_view(request):
    """View customer messages grouped into single-record chat threads with precise line timestamps."""
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to view your messages.")
        return redirect('login')
    gate = _require_customer_workspace(request)
    if gate:
        return gate

    customer = get_customer_from_request(request)

    class _Obj:
        def __init__(self, **kw): self.__dict__.update(kw)

    chat_threads = []
    stores = []

    if customer:
        with connection.cursor() as cursor:
            cursor.execute("SELECT store_id, store_name, address FROM store ORDER BY store_name")
            stores = [_Obj(store_id=r[0], store_name=r[1], address=r[2]) for r in cursor.fetchall()]

            cursor.execute("""
                SELECT cm.message_id, cm.message, cm.created_at, cm.updated_at,
                       s.store_id, s.store_name,
                       e.employee_id, e.first_name, e.last_name
                FROM customer_message cm
                JOIN store s ON cm.store_id = s.store_id
                LEFT JOIN employee e ON cm.employee_id = e.employee_id
                WHERE cm.customer_id = %s
                ORDER BY cm.message_id DESC
            """, [customer.customer_id])
            msg_rows = cursor.fetchall()

            for r in msg_rows:
                msg_id = r[0]
                full_raw_text = r[1] or ''
                created_at = r[2]
                updated_at = r[3]
                store_id = r[4]
                store_name = r[5]
                emp_id = r[6]
                emp_fn = (r[7] or '').strip()
                emp_ln = (r[8] or '').strip()
                default_emp_name = f"{emp_fn} {emp_ln}".strip() if (emp_fn or emp_ln) else "Store Staff"

                lines = [line.strip() for line in full_raw_text.split('\n') if line.strip()]
                msg_list = []
                assigned_emp = default_emp_name if emp_id else None
                fallback_time_str = safe_format_time(updated_at or created_at)
                last_msg_time = fallback_time_str

                for line in lines:
                    msg_time = fallback_time_str
                    is_reply = False
                    clean_txt = line
                    sender_label = "You"

                    if line.startswith('[Reply from '):
                        is_reply = True
                        parts = line.split(']: ', 1)
                        header_part = parts[0].replace('[Reply from ', '').strip()
                        clean_txt = parts[1] if len(parts) == 2 else line

                        if '|' in header_part:
                            h_name, h_time = header_part.rsplit('|', 1)
                            assigned_emp = h_name.strip() or (assigned_emp or "Store Staff")
                            msg_time = h_time.strip()
                        else:
                            assigned_emp = header_part or (assigned_emp or "Store Staff")

                        sender_label = assigned_emp
                    elif line.startswith('[TIME: '):
                        is_reply = False
                        parts = line.split('] ', 1)
                        if len(parts) == 2:
                            msg_time = parts[0].replace('[TIME: ', '').strip()
                            clean_txt = parts[1]
                        sender_label = "You"

                    last_msg_text = clean_txt
                    last_msg_time = msg_time
                    msg_list.append(_Obj(
                        message_id=msg_id,
                        message=clean_txt,
                        is_reply=is_reply,
                        sender_name=sender_label,
                        created_at=created_at,
                        msg_time=msg_time
                    ))

                chat_threads.append(_Obj(
                    message_id=msg_id,
                    store_id=store_id,
                    store_name=store_name,
                    assigned_employee=assigned_emp,
                    last_message=last_msg_text,
                    last_time_str=last_msg_time,
                    last_time=updated_at or created_at,
                    messages=msg_list,
                ))

    return render(request, 'ecommerce/messages.html', {
        'customer': customer,
        'chat_threads': chat_threads,
        'stores': stores,
    })


@api_view(['POST'])
def api_send_superuser_message(request):
    """API endpoint to send newsletter/direct messages to Head Office Superusers."""
    data = request.POST
    if not data:
        try:
            data = json.loads(request.body)
        except Exception:
            data = {}

    email = (data.get('email') or data.get('footer-email') or '').strip()
    if not email:
        return JsonResponse({'success': False, 'error': 'Email address is required.'}, status=400)

    customer = get_customer_from_request(request)
    customer_id = customer.customer_id if customer else None

    with connection.cursor() as cursor:
        cursor.execute("SELECT store_id FROM store ORDER BY store_id ASC LIMIT 1")
        store_row = cursor.fetchone()
        main_store_id = store_row[0] if store_row else 1

        if not customer_id:
            cursor.execute("SELECT customer_id FROM customer WHERE email = %s", [email])
            c_row = cursor.fetchone()
            if c_row:
                customer_id = c_row[0]
            else:
                cursor.execute("SELECT customer_id FROM customer ORDER BY customer_id ASC LIMIT 1")
                fallback_c = cursor.fetchone()
                customer_id = fallback_c[0] if fallback_c else 1

    try:
        from car_sales.models import CustomerMessage
        msg = CustomerMessage.objects.create(
            customer_id=customer_id,
            store_id=main_store_id,
            employee_id=None,
            message=f"Newsletter Subscription & Superuser Direct Inquiry from: {email}"
        )
        return JsonResponse({
            'success': True,
            'message': 'Thank you! Your email inquiry has been sent to our Head Office superusers.',
            'message_id': msg.message_id
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
