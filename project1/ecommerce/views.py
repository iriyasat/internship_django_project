import json
from django.db import transaction
from django.db.models import Max
from django.shortcuts import render, redirect, get_object_or_404

from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.contrib import messages

from car_sales.models import Customer, CustomerInfo, Store, IndustryInfo, Inventory, Employee, City, Country, VehicleInfo
from .models import Order, PaymentTransaction, Wishlist, Cart, TestDriveBooking
from .serializers import (
    CatalogService, WishlistService, CartService, TestDriveService, OrderService,
    VehicleBodyService, VehicleBodySerializer, VehicleConditionService, VehicleConditionSerializer,
    WishlistModelSerializer, CartItemModelSerializer, TestDriveBookingModelSerializer,
    OrderModelSerializer, PaymentTransactionModelSerializer
)


# Strictly secure helper to get current authenticated customer record
def get_customer_from_request(request):
    if hasattr(request, 'user') and request.user.is_authenticated:
        # 1. Check cust_<id> username format
        if request.user.username.startswith('cust_'):
            try:
                c_id = int(request.user.username.split('_')[1])
                cust = Customer.objects.filter(customer_id=c_id).first()
                if cust:
                    return cust
            except Exception:
                pass

        # 2. Check matching email in customer table
        if request.user.email:
            cust = Customer.objects.filter(email=request.user.email).first()
            if cust:
                return cust

        # 3. Safely create dedicated Customer record for this user
        try:
            with transaction.atomic():
                cust = Customer.objects.create(
                    email=request.user.email or f"{request.user.username}@customer.com",
                    password=request.user.password or "securepass",
                    phone="+1-555-0199"
                )
                CustomerInfo.objects.create(
                    customer=cust,
                    firstname=request.user.first_name or "Customer",
                    lastname=request.user.last_name or str(cust.customer_id),
                    customer_status="Active",
                    customer_address="Registered Address",
                    city_id=1,
                    country_id=1
                )
                return cust
        except Exception:
            return Customer.objects.filter(email=request.user.email).first()

    return None


# ==============================================================================
# 1. CATALOG & SEARCH VIEWS / APIS
# ==============================================================================

def catalog_view(request):
    """Customer vehicle catalog page."""
    makes = IndustryInfo.objects.all().order_by('make_name')
    stores = Store.objects.select_related('city', 'country').all().order_by('store_name')
    customer = get_customer_from_request(request)
    wishlist_count = Wishlist.objects.filter(customer=customer).count() if customer else 0
    cart = Cart.objects.filter(customer=customer).first() if customer else None
    cart_count = cart.items.count() if cart else 0
    vehicle_bodies = VehicleBodyService.fetch_vehicle_bodies()
    condition_tabs = VehicleConditionService.fetch_condition_tabs(active_condition=request.GET.get('condition', 'all'))

    transmissions = list(VehicleInfo.objects.exclude(transmission__isnull=True).exclude(transmission='').values_list('transmission', flat=True).distinct().order_by('transmission'))
    colors = list(VehicleInfo.objects.exclude(color__isnull=True).exclude(color='').values_list('color', flat=True).distinct().order_by('color'))
    fuel_types = ['Gasoline', 'Diesel', 'Hybrid', 'Electric', 'Flex Fuel']

    avail_qs = Inventory.objects.filter(status__in=[Inventory.StatusChoices.AVAILABLE, Inventory.StatusChoices.PRE_ORDER])
    condition_counts = {
        'all': avail_qs.count(),
        'excellent': avail_qs.filter(vehicle__condition__gte=40).count(),
        'very_good': avail_qs.filter(vehicle__condition__range=(30, 39)).count(),
        'good': avail_qs.filter(vehicle__condition__range=(20, 29)).count(),
        'fair': avail_qs.filter(vehicle__condition__range=(1, 19)).count(),
    }

    price_stats = avail_qs.aggregate(Max('vehicle__mmr'))
    max_price_db = price_stats['vehicle__mmr__max'] or 182000

    return render(request, 'ecommerce/catalog.html', {
        'customer': customer,
        'makes': makes,
        'stores': stores,
        'wishlist_count': wishlist_count,
        'cart_count': cart_count,
        'vehicle_bodies': vehicle_bodies,
        'condition_tabs': condition_tabs,
        'condition_counts': condition_counts,
        'max_price_db': max_price_db,
        'active_condition': request.GET.get('condition', 'all'),
        'transmissions': transmissions,
        'colors': colors,
        'fuel_types': fuel_types,
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
    """JSON API for fetching distinct vehicle models for a selected brand/make."""
    brand = request.GET.get('brand') or request.GET.get('make')
    make_id = request.GET.get('make_id')

    qs = VehicleInfo.objects.all()
    if make_id and str(make_id).isdigit():
        qs = qs.filter(make_id=make_id)
    elif brand and str(brand).lower() not in ['all', '']:
        qs = qs.filter(make__make_name__icontains=brand)

    models_list = list(
        qs.exclude(vehicle_model__isnull=True)
          .exclude(vehicle_model='')
          .values_list('vehicle_model', flat=True)
          .distinct()
          .order_by('vehicle_model')[:50]
    )

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
    stores = Store.objects.select_related('city', 'country').all()

    return render(request, 'ecommerce/test_drive.html', {
        'customer': customer,
        'bookings': bookings,
        'stores': stores
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
    """Customer checkout page."""
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to proceed to checkout.")
        return redirect('login')

    customer = get_customer_from_request(request)
    customer_info = CustomerInfo.objects.filter(customer=customer).select_related('city', 'country').first() if customer else None
    
    cart_items, cart_total = CartService.fetch_customer_cart_items(customer) if customer else ([], 0)

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
    orders = Order.objects.filter(customer=customer).select_related('inventory__vehicle__make', 'store', 'invoice', 'assigned_employee').order_by('-order_id') if customer else []
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
    customer_info = CustomerInfo.objects.filter(customer=customer).select_related('city', 'country').first() if customer else None
    
    orders_count = Order.objects.filter(customer=customer).count() if customer else 0
    wishlist_count = Wishlist.objects.filter(customer=customer).count() if customer else 0
    test_drives_count = TestDriveBooking.objects.filter(customer=customer).count() if customer else 0

    cities = City.objects.all().order_by('city_name')
    countries = Country.objects.all().order_by('country_name')

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
        with transaction.atomic():
            if phone is not None:
                customer.phone = phone
                customer.save()

            info, _ = CustomerInfo.objects.get_or_create(
                customer=customer,
                defaults={
                    'firstname': firstname or request.user.first_name or "Customer",
                    'lastname': lastname or request.user.last_name or str(customer.customer_id),
                    'customer_status': 'Active',
                    'customer_address': customer_address or 'Registered Address',
                    'city_id': city_id or 1,
                    'country_id': country_id or 1
                }
            )
            if firstname: info.firstname = firstname
            if lastname: info.lastname = lastname
            if customer_address: info.customer_address = customer_address
            if city_id: info.city_id = city_id
            if country_id: info.country_id = country_id
            info.save()

        return JsonResponse({'success': True, 'message': 'Profile updated successfully!'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
