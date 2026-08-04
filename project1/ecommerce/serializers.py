import json
import uuid
from datetime import datetime, date, time
from django.db import transaction, models, connections, connection
from django.utils import timezone
from rest_framework import serializers

from car_sales.models import (
    Customer, CustomerInfo, Inventory, VehicleInfo, Store, 
    Employee, SellingInfo, Invoice, IndustryInfo
)
from .models import Wishlist, Cart, CartItem, TestDriveBooking, Order, PaymentTransaction
from .db import (
    WISHLIST_TABLE,
    CART_TABLE,
    CART_ITEM_TABLE,
    TEST_DRIVE_TABLE,
    CART_PK_COLUMN,
    CART_ITEM_CART_COLUMN,
)


def _slugify_make(value):
    return ''.join(ch for ch in str(value or '').lower() if ch.isalnum())


def _resolve_vehicle_image_url(make_name, vehicle_model=None):
    """Resolve a local vehicle image from static/cars, falling back to the brand logo."""
    from pathlib import Path
    from django.conf import settings

    image_dir = Path(settings.BASE_DIR) / 'static' / 'cars'
    make_slug = _slugify_make(make_name)
    model_slug = _slugify_make(vehicle_model)
    logo_alias = 'mercedes' if 'mercedes' in make_slug else ('landrover' if 'landrover' in make_slug else make_slug)

    for stem in filter(None, (
        f"{make_slug}-{model_slug}" if make_slug and model_slug else None,
        model_slug or None,
        make_slug or None,
        f"{logo_alias}-{model_slug}" if logo_alias and model_slug and logo_alias != make_slug else None,
        logo_alias or None,
    )):
        for ext in ('.webp', '.png', '.jpg', '.jpeg'):
            candidate = image_dir / f"{stem}{ext}"
            if candidate.exists():
                return f"/static/cars/{candidate.name}"

    return f"/static/logos/{logo_alias}.png"


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


class VehicleBodySerializer(serializers.Serializer):
    name = serializers.CharField()
    display_name = serializers.CharField()
    count = serializers.IntegerField(default=0)
    url = serializers.CharField()
    svg = serializers.CharField()
    image_url = serializers.CharField(required=False, allow_blank=True)


class VehicleBodyService:
    BODY_SVG_MAP = {
        'electric': '<svg width="41" height="40" viewBox="0 0 41 40" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M6.95237 27.1027C8.73393 27.1027 10.1782 25.6585 10.1782 23.8769C10.1782 22.0954 8.73393 20.6511 6.95237 20.6511C5.17081 20.6511 3.72656 22.0954 3.72656 23.8769C3.72656 25.6585 5.17081 27.1027 6.95237 27.1027Z" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M30.175 27.1027C31.9566 27.1027 33.4008 25.6585 33.4008 23.8769C33.4008 22.0954 31.9566 20.6511 30.175 20.6511C28.3935 20.6511 26.9492 22.0954 26.9492 23.8769C26.9492 25.6585 28.3935 27.1027 30.175 27.1027Z" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M26.95 24.5222H10.1758" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M33.4032 24.5217H37.9194L39.8548 23.2314L39.2097 22.5862V20.6508L40.5 20.0056L40.2419 19.8766C37.0161 17.812 32.629 16.7798 28.8871 16.7798C28.8871 16.7798 28.2419 15.8766 26.9516 14.9734C25.6613 14.0701 23.7258 13.0379 21.1452 12.9088C16.1129 12.6508 6.30645 16.7798 6.30645 16.7798H1.79032C1.01613 16.7798 0.5 17.425 0.5 18.0701V23.2314L3.72581 23.8766" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M35.3398 19.3621L37.2753 20.0072" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M11.4699 18.7155L6.30859 16.78" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M14.6914 20.0072L21.7882 21.8137C22.1753 21.9427 22.5624 21.8137 22.8204 21.5556L25.5301 19.3621" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M28.8881 16.78H20.501C17.5333 16.78 14.5655 16.1348 11.7268 14.9735L11.4688 14.8445" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M0.5 20.6511H1.01612C2.17741 20.6511 3.33871 19.8769 3.72581 18.7156H0.5" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path></svg>',
        'sedan': '<svg width="41" height="18" viewBox="0 0 41 18" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M8.88597 17.2766C10.6675 17.2766 12.1118 15.8323 12.1118 14.0508C12.1118 12.2692 10.6675 10.825 8.88597 10.825C7.1044 10.825 5.66016 12.2692 5.66016 14.0508C5.66016 15.8323 7.1044 17.2766 8.88597 17.2766Z" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M31.468 17.2766C33.2496 17.2766 34.6938 15.8323 34.6938 14.0508C34.6938 12.2692 33.2496 10.825 31.468 10.825C29.6864 10.825 28.2422 12.2692 28.2422 14.0508C28.2422 15.8323 29.6864 17.2766 31.468 17.2766Z" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M12.1133 14.0494H28.2424" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M34.6936 14.0484H40.5001V9.53228C37.5324 7.46776 34.0485 6.30647 30.4356 6.30647H29.5323L25.7904 1.53226C25.2743 0.887097 24.5001 0.5 23.7259 0.5H10.6936C10.4355 0.5 10.0484 0.629034 9.79034 0.758066L5.6613 4.37098H3.08065C2.30646 4.37098 1.79033 4.88711 1.79033 5.6613V9.53228L0.5 10.8226V12.7581L5.6613 14.0484" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M14.6927 8.23975H13.4023" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M21.1458 8.23975H19.8555" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M29.5313 6.30647H12.1119L9.53125 5.01614V3.72582L13.4022 0.5" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M1.78906 9.53134H3.07939C3.85358 9.53134 4.36971 9.01521 4.36971 8.24101C4.36971 7.46681 3.85358 6.95068 3.07939 6.95068H1.78906" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M36.6289 7.59521V9.5307C36.6289 10.3049 37.145 10.821 37.9192 10.821H40.4999" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M17.9219 0.5V6.30647" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path></svg>',
        'suv': '<svg width="41" height="40" viewBox="0 0 41 40" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M29.6618 25.8069H11.9844" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M35.8548 25.8068H37.2742L40.5 24.5165V19.3552L30.1774 16.7746L26.5645 13.1617C25.5323 12.1294 24.2419 11.6133 22.9516 11.6133H7.59677C4.75806 12.9036 2.30644 15.0972 1.01612 18.0649L0.5 19.3552V23.8713L5.01613 25.8068H5.79033" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M40.4992 20.6455H37.2734L37.9186 23.2262H40.4992" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M0.5 19.3552H3.72581L3.20969 20.7746C2.82259 21.8068 1.66129 22.581 0.5 22.581" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M10.8228 11.6133L8.24219 15.4842L9.53251 16.7746H30.1777" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M8.88987 28.3874C10.6714 28.3874 12.1157 26.9432 12.1157 25.1616C12.1157 23.38 10.6714 21.9358 8.88987 21.9358C7.10831 21.9358 5.66406 23.38 5.66406 25.1616C5.66406 26.9432 7.10831 28.3874 8.88987 28.3874Z" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M32.7571 28.3874C34.5386 28.3874 35.9829 26.9432 35.9829 25.1616C35.9829 23.38 34.5386 21.9358 32.7571 21.9358C30.9755 21.9358 29.5312 23.38 29.5312 25.1616C29.5312 26.9432 30.9755 28.3874 32.7571 28.3874Z" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M7.59551 11.6133L4.36971 16.7746H1.78906" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M19.2109 16.7746V11.6133" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M12.1106 19.3552H10.8203" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M19.8555 19.3552H21.791" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path></svg>',
        'pickup truck': '<svg width="41" height="18" viewBox="0 0 41 18" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M10.8235 17.2742C12.605 17.2742 14.0493 15.8299 14.0493 14.0484C14.0493 12.2668 12.605 10.8226 10.8235 10.8226C9.0419 10.8226 7.59766 12.2668 7.59766 14.0484C7.59766 15.8299 9.0419 17.2742 10.8235 17.2742Z" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M33.4016 17.2742C35.1832 17.2742 36.6274 15.8299 36.6274 14.0484C36.6274 12.2668 35.1832 10.8226 33.4016 10.8226C31.62 10.8226 30.1758 12.2668 30.1758 14.0484C30.1758 15.8299 31.62 17.2742 33.4016 17.2742Z" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M7.59677 14.0484H1.79032L0.5 12.7581V5.66129H13.4032V0.5H24.1129C24.7581 0.5 25.2742 0.758057 25.6613 1.01612L31.4677 5.66129L39.3387 6.82257C39.9839 6.9516 40.5 7.46773 40.5 8.1129V12.7581C40.5 13.5323 39.9839 14.0484 39.2097 14.0484H36.629" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M30.1759 14.0484H14.0469" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M21.1445 0.5V5.66129" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M22.4349 8.24194H21.1445" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M0.5 7.5968H4.37097L3.46774 9.01616C3.20968 9.27423 2.95161 9.53229 2.56452 9.53229H0.629033" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M40.4986 10.1774H37.918V8.24194H40.4986" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path></svg>',
        'truck': '<svg width="41" height="18" viewBox="0 0 41 18" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M10.8235 17.2742C12.605 17.2742 14.0493 15.8299 14.0493 14.0484C14.0493 12.2668 12.605 10.8226 10.8235 10.8226C9.0419 10.8226 7.59766 12.2668 7.59766 14.0484C7.59766 15.8299 9.0419 17.2742 10.8235 17.2742Z" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M33.4016 17.2742C35.1832 17.2742 36.6274 15.8299 36.6274 14.0484C36.6274 12.2668 35.1832 10.8226 33.4016 10.8226C31.62 10.8226 30.1758 12.2668 30.1758 14.0484C30.1758 15.8299 31.62 17.2742 33.4016 17.2742Z" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M7.59677 14.0484H1.79032L0.5 12.7581V5.66129H13.4032V0.5H24.1129C24.7581 0.5 25.2742 0.758057 25.6613 1.01612L31.4677 5.66129L39.3387 6.82257C39.9839 6.9516 40.5 7.46773 40.5 8.1129V12.7581C40.5 13.5323 39.9839 14.0484 39.2097 14.0484H36.629" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M30.1759 14.0484H14.0469" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M21.1445 0.5V5.66129" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M22.4349 8.24194H21.1445" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M0.5 7.5968H4.37097L3.46774 9.01616C3.20968 9.27423 2.95161 9.53229 2.56452 9.53229H0.629033" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M40.4986 10.1774H37.918V8.24194H40.4986" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path></svg>',
        'luxury': '<svg width="41" height="16" viewBox="0 0 41 16" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M29.832 11.8333H11.832" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M36.4999 11.8333H40.4999V8.49999V7.83332C40.4999 7.83332 40.6333 5.16666 28.5 4.49999C27.1666 3.16666 25.7 2.23333 24.1 1.56667C22.5 0.900003 20.6333 0.5 18.9 0.5H15.7C15.5666 0.5 15.4333 0.5 15.3 0.5C14.2333 0.5 13.3 0.766668 12.2333 1.03333L9.83332 1.7L7.16666 2.5H1.83333L1.16667 4.49999V6.49999L0.5 7.83332L1.16667 11.1666L5.16666 11.7" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M8.5013 15.1667C10.3422 15.1667 11.8346 13.6743 11.8346 11.8333C11.8346 9.99238 10.3422 8.5 8.5013 8.5C6.66035 8.5 5.16797 9.99238 5.16797 11.8333C5.16797 13.6743 6.66035 15.1667 8.5013 15.1667Z" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M33.1654 15.1667C35.0063 15.1667 36.4987 13.6743 36.4987 11.8333C36.4987 9.99238 35.0063 8.5 33.1654 8.5C31.3244 8.5 29.832 9.99238 29.832 11.8333C29.832 13.6743 31.3244 15.1667 33.1654 15.1667Z" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M1.16797 4.5H4.5013L3.16797 6.5H1.16797" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M9.83203 1.83331L10.632 2.89998C11.432 3.96665 12.632 4.49998 13.832 4.49998H28.4987" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M17.8333 6.5H16.5" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M28.4987 7.83331L27.5653 9.29998C27.2987 9.69997 26.8987 9.83331 26.4987 9.83331H17.832" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M15.168 0.5V4.49999" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M36.5 5.83331L37.0333 6.89998C37.5667 7.83331 38.5 8.49998 39.5667 8.49998H40.5" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path></svg>',
        'hatchback': '<svg width="41" height="40" viewBox="0 0 41 40" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M7.5969 27.2678C9.37846 27.2678 10.8227 25.8235 10.8227 24.042C10.8227 22.2604 9.37846 20.8162 7.5969 20.8162C5.81534 20.8162 4.37109 22.2604 4.37109 24.042C4.37109 25.8235 5.81534 27.2678 7.5969 27.2678Z" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M16.6289 11.1387V15.0096" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M30.8241 16.3L10.8241 15.6548L6.95312 14.3645L9.53377 11.1387" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M4.37097 24.0424L0.5 23.3972V20.1714L1.79032 18.8811L1.14516 16.9456L5.66129 11.7843L4.37097 11.1392L14.5645 10.7521C20.5 10.494 26.3065 12.5585 30.8226 16.3005C30.8226 16.3005 37.0161 16.9456 40.5 19.5263V24.6876H35.3387" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M32.1125 27.2678C33.8941 27.2678 35.3383 25.8235 35.3383 24.042C35.3383 22.2604 33.8941 20.8162 32.1125 20.8162C30.331 20.8162 28.8867 22.2604 28.8867 24.042C28.8867 25.8235 30.331 27.2678 32.1125 27.2678Z" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M2.43422 15.6548L5.66003 16.9451C4.88584 18.1064 3.46648 18.8806 2.04712 18.8806H1.78906" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M40.4972 21.4614C38.8198 21.0743 37.1424 20.3001 35.8521 19.2679L35.3359 18.8808L38.3037 18.2356" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M12.1106 18.2356H10.8203" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M19.8567 18.2356H18.5664" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M10.8203 24.042H28.8848" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path></svg>',
        'crossover': '<svg width="41" height="40" viewBox="0 0 41 40" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M9.53049 26.0959C11.3121 26.0959 12.7563 24.6517 12.7563 22.8701C12.7563 21.0885 11.3121 19.6443 9.53049 19.6443C7.74893 19.6443 6.30469 21.0885 6.30469 22.8701C6.30469 24.6517 7.74893 26.0959 9.53049 26.0959Z" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M32.7571 26.0959C34.5386 26.0959 35.9829 24.6517 35.9829 22.8701C35.9829 21.0885 34.5386 19.6443 32.7571 19.6443C30.9755 19.6443 29.5312 23.38 29.5312 25.1616C29.5312 26.9432 30.9755 28.3874 32.7571 28.3874Z" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M6.30645 22.8701L0.5 21.5798V18.354L1.79032 17.7088L0.5 15.7733C0.5 15.7733 5.91935 11.9023 12.1129 11.9023C17.0161 11.9023 21.7903 11.9023 23.5968 11.9023C24.1129 11.9023 24.629 12.0314 25.0161 12.2894L30.1774 15.7733C30.1774 15.7733 36.5 16.1604 40.5 17.0636L39.8548 18.354L40.5 19.6443V22.2249L35.9839 22.8701" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M12.7578 22.8701H29.532" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M30.1777 15.7733H10.8228L8.24219 15.1282C9.14541 13.8378 10.3067 12.9346 11.7261 12.2894L12.7583 11.9023" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M13.4023 17.7087H14.6927" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M21.1445 17.7087H22.4349" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M1.79032 17.7087H4.37097L3.72581 15.7732H0.5" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M37.9219 18.354H39.8574" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M18.5664 15.7733V11.9023" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path></svg>',
        'convertible': '<svg width="41" height="40" viewBox="0 0 41 40" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M29.8359 22.9993H11.8359" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M9.83332 13.666H1.83333L1.16667 15.666V17.666L0.5 18.9993L1.16667 22.3327L5.16666 22.866" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M36.5026 22.9993H40.5026V19.666V18.9993C40.5026 18.9993 40.6359 16.3327 28.5026 15.666C27.1693 14.3327 23.8359 11.666 23.8359 11.666" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M8.49739 26.3327C10.3383 26.3327 11.8307 24.8403 11.8307 22.9993C11.8307 21.1584 10.3383 19.666 8.49739 19.666C6.65644 19.666 5.16406 21.1584 5.16406 22.9993C5.16406 24.8403 6.65644 26.3327 8.49739 26.3327Z" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M33.1693 26.3327C35.0102 26.3327 36.5026 24.8403 36.5026 22.9993C36.5026 21.1584 35.0102 19.666 33.1693 19.666C31.3283 19.666 29.8359 21.1584 29.8359 22.9993C29.8359 24.8403 31.3283 26.3327 33.1693 26.3327Z" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M1.16406 15.666H4.49739L4.09739 16.466C3.56405 17.5327 2.36406 18.066 1.16406 17.666" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M9.83594 13.666C10.6359 14.7327 11.9693 15.666 13.1693 15.666H28.5026" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M17.8333 17.666H16.5" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M36.5 16.9993L37.0333 18.0659C37.5667 18.9993 38.5 19.6659 39.5667 19.6659H40.5" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M17.8359 13.666V15.666" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M27.8359 20.9993H17.8359" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path></svg>',
        'coupe': '<svg width="41" height="40" viewBox="0 0 41 40" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M9.875 25.937C11.6009 25.937 13 24.5379 13 22.812C13 21.0861 11.6009 19.687 9.875 19.687C8.14911 19.687 6.75 21.0861 6.75 22.812C6.75 24.5379 8.14911 25.937 9.875 25.937Z" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M34 23.9375L40.5 22.8125V20.3125L39.75 19.5625C38.75 18.5625 37.75 17.9375 36.5 17.4375C35.625 17.1875 34.875 16.9375 33.875 16.8125L29.125 16.4375H28.625H23.625H16.75L15.5 12.0625C6.125 12.8125 0.5 17.6875 0.5 17.6875V22.0625L6.75 23.3125" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M28.25 24.062L12.875 23.437" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M18.625 18.437H16.75" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M22.375 12.812L28.625 16.562" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M36.4995 17.563C36.1245 18.063 36.6245 19.188 37.6245 20.063C38.6245 20.938 39.8745 21.313 40.3745 20.813C40.4995 20.688 40.4995 20.563 40.4995 20.438" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M0.5 17.812H3.625V15.937" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M13.625 14.687L14.25 16.562H23.625" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M31.125 25.937C32.8509 25.937 34.25 24.5379 34.25 22.812C34.25 21.0861 32.8509 19.687 31.125 19.687C29.3991 19.687 28 21.0861 28 22.812C28 24.5379 29.3991 25.937 31.125 25.937Z" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path></svg>',
        'minivan': '<svg width="41" height="18" viewBox="0 0 41 18" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M8.88 17.27C10.66 17.27 12.11 15.83 12.11 14.05C12.11 12.27 10.66 10.82 8.88 10.82C7.1 10.82 5.66 12.27 5.66 14.05C5.66 15.83 7.1 17.27 8.88 17.27Z" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M31.47 17.27C33.25 17.27 34.69 15.83 34.69 14.05C34.69 12.27 33.25 10.82 31.47 10.82C29.69 10.82 28.24 12.27 28.24 14.05C28.24 15.83 29.69 17.27 31.47 17.27Z" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M12.11 14.05H28.24" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M34.69 14.05H40.5V6.5C37.53 3.5 33.05 2.5 28.44 2.5H10.69C7.43 2.5 4.66 4.37 3.08 7.5L0.5 10.5V13.5L5.66 14.05" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path></svg>',
        'van': '<svg width="41" height="18" viewBox="0 0 41 18" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M8.88 17.27C10.66 17.27 12.11 15.83 12.11 14.05C12.11 12.27 10.66 10.82 8.88 10.82C7.1 10.82 5.66 12.27 5.66 14.05C5.66 15.83 7.1 17.27 8.88 17.27Z" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M31.47 17.27C33.25 17.27 34.69 15.83 34.69 14.05C34.69 12.27 33.25 10.82 31.47 10.82C29.69 10.82 28.24 12.27 28.24 14.05C28.24 15.83 29.69 17.27 31.47 17.27Z" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M12.11 14.05H28.24" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M34.69 14.05H40.5V6.5C37.53 3.5 33.05 2.5 28.44 2.5H10.69C7.43 2.5 4.66 4.37 3.08 7.5L0.5 10.5V13.5L5.66 14.05" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path></svg>',
        'wagon': '<svg width="41" height="18" viewBox="0 0 41 18" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M8.88 17.27C10.66 17.27 12.11 15.83 12.11 14.05C12.11 12.27 10.66 10.82 8.88 10.82C7.1 10.82 5.66 12.27 5.66 14.05C5.66 15.83 7.1 17.27 8.88 17.27Z" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M31.47 17.27C33.25 17.27 34.69 15.83 34.69 14.05C34.69 12.27 33.25 10.82 31.47 10.82C29.69 10.82 28.24 12.27 28.24 14.05C28.24 15.83 29.69 17.27 31.47 17.27Z" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M12.11 14.05H28.24" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path><path d="M34.69 14.05H40.5V8.5C37.53 6.5 34.05 5.5 30.44 5.5H12.69C9.43 5.5 6.66 7.37 5.08 9.5L1.5 12.5V14L5.66 14.05" stroke="white" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"></path></svg>',
    }

    @classmethod
    def get_svg_for_body(cls, body_name):
        b_lower = body_name.lower()
        if 'electric' in b_lower:
            return cls.BODY_SVG_MAP['electric']
        elif 'sedan' in b_lower:
            return cls.BODY_SVG_MAP['sedan']
        elif 'suv' in b_lower:
            return cls.BODY_SVG_MAP['suv']
        elif 'cab' in b_lower or 'truck' in b_lower or 'xtracab' in b_lower or 'crew' in b_lower:
            return cls.BODY_SVG_MAP['pickup truck']
        elif 'luxury' in b_lower:
            return cls.BODY_SVG_MAP['luxury']
        elif 'hatchback' in b_lower:
            return cls.BODY_SVG_MAP['hatchback']
        elif 'crossover' in b_lower:
            return cls.BODY_SVG_MAP['crossover']
        elif 'convertible' in b_lower:
            return cls.BODY_SVG_MAP['convertible']
        elif 'coupe' in b_lower or 'koup' in b_lower:
            return cls.BODY_SVG_MAP['coupe']
        elif 'van' in b_lower or 'minivan' in b_lower:
            return cls.BODY_SVG_MAP['minivan']
        elif 'wagon' in b_lower:
            return cls.BODY_SVG_MAP['wagon']
        return cls.BODY_SVG_MAP['sedan']

    @staticmethod
    def _get_car_image_urls():
        from pathlib import Path
        from django.conf import settings

        image_dir = Path(settings.BASE_DIR) / 'static' / 'cars'
        urls = []
        for pattern in ('*.jpg', '*.jpeg', '*.png', '*.webp'):
            urls.extend(f"/static/cars/{path.name}" for path in image_dir.glob(pattern))
        return urls

    @staticmethod
    def _resolve_body_image_url(body_name):
        """Pick a representative inventory vehicle image for a body type."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT m.make_name, v.vehicle_model
                FROM inventory i
                JOIN vehicle_info v ON i.vehicle_id = v.id
                LEFT JOIN industry_info m ON v.make_id = m.make_id
                WHERE i.status IN (2, 4) AND v.body IS NOT NULL AND LOWER(v.body) = LOWER(%s)
                ORDER BY i.inventory_id DESC
                LIMIT 1
            """, [body_name])
            row = cursor.fetchone()

        if row:
            make_name, vehicle_model = row
            return _resolve_vehicle_image_url(make_name, vehicle_model)
        return ''

    @classmethod
    def fetch_vehicle_bodies(cls):
        # RAW SQL Execution
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT v.body, COUNT(i.inventory_id) as count
                FROM inventory i
                JOIN vehicle_info v ON i.vehicle_id = v.id
                WHERE i.status IN (2, 4)
                  AND v.body IS NOT NULL
                  AND v.body != ''
                GROUP BY v.body
                ORDER BY count DESC
            """)
            db_bodies = [{'body': row[0], 'count': row[1]} for row in cursor.fetchall()]

        body_list = []
        seen = set()

        for item in db_bodies:
            raw_body = item['body'].strip()
            count = item['count']
            display_name = 'SUV' if raw_body.lower() == 'suv' else raw_body.title()
            
            if display_name not in seen:
                seen.add(display_name)
                body_list.append({
                    'name': display_name,
                    'display_name': display_name,
                    'count': count,
                    'url': f"/catalog/?body={display_name}",
                    'svg': cls.get_svg_for_body(display_name),
                    'image_url': cls._resolve_body_image_url(raw_body),
                })

        serializer = VehicleBodySerializer(body_list, many=True)
        return serializer.data


class VehicleConditionSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    count = serializers.IntegerField(default=0)
    url = serializers.CharField()
    is_active = serializers.BooleanField(default=False)


class VehicleConditionService:
    NEW_CAR_MAX_ODOMETER = 100

    @classmethod
    def fetch_condition_tabs(cls, active_condition='all'):
        # RAW SQL Execution
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM inventory WHERE status IN (2, 4)")
            all_count = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*)
                FROM inventory i
                JOIN vehicle_info v ON i.vehicle_id = v.id
                WHERE i.status IN (2, 4) AND v.odometer <= %s
            """, [cls.NEW_CAR_MAX_ODOMETER])
            new_count = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*)
                FROM inventory i
                JOIN vehicle_info v ON i.vehicle_id = v.id
                WHERE i.status IN (2, 4) AND v.odometer > %s
            """, [cls.NEW_CAR_MAX_ODOMETER])
            used_count = cursor.fetchone()[0]

        act = str(active_condition or 'all').lower()

        tabs = [
            {
                'id': 'all',
                'name': 'All Car',
                'count': all_count,
                'url': '/catalog/?condition=all',
                'is_active': act in ['all', '']
            },
            {
                'id': 'new',
                'name': 'New Car',
                'count': new_count,
                'url': '/catalog/?condition=new',
                'is_active': act == 'new'
            },
            {
                'id': 'used',
                'name': 'Used Car',
                'count': used_count,
                'url': '/catalog/?condition=used',
                'is_active': act in ['used', 'pre-owned']
            }
        ]

        serializer = VehicleConditionSerializer(tabs, many=True)
        return serializer.data


# ------------------------------------------------------------------------------
# Encapsulated Business Query & Transaction Services (RAW SQL)
# ------------------------------------------------------------------------------

class CatalogService:
    @staticmethod
    def _build_catalog_filters(make_id=None, brand=None, store_id=None, search_q=None, min_price=None, max_price=None, min_miles=None, max_miles=None, body=None, condition=None, transmission=None, color=None, interior=None, state=None, trim=None, **kwargs):
        params = []
        where_clauses = ["i.status IN (2, 4)"]

        if make_id and str(make_id).isdigit():
            where_clauses.append("v.make_id = %s")
            params.append(int(make_id))
        elif brand and str(brand).lower() not in ['all', '']:
            where_clauses.append("LOWER(m.make_name) LIKE %s")
            params.append(f"%{brand.lower()}%")
        elif make_id and not str(make_id).isdigit() and str(make_id).lower() not in ['all', '']:
            where_clauses.append("LOWER(m.make_name) LIKE %s")
            params.append(f"%{make_id.lower()}%")

        if store_id:
            where_clauses.append("i.store_id = %s")
            params.append(store_id)

        if body:
            b_lower = body.lower()
            if b_lower in ['pickup truck', 'truck']:
                where_clauses.append("(LOWER(v.body) LIKE %s OR LOWER(v.body) LIKE %s OR LOWER(v.body) LIKE %s)")
                params.extend(['%cab%', '%truck%', '%xtracab%'])
            elif b_lower in ['minivan', 'van']:
                where_clauses.append("(LOWER(v.body) LIKE %s OR LOWER(v.body) LIKE %s)")
                params.extend(['%van%', '%minivan%'])
            elif b_lower == 'coupe':
                where_clauses.append("(LOWER(v.body) LIKE %s OR LOWER(v.body) LIKE %s)")
                params.extend(['%coupe%', '%koup%'])
            else:
                where_clauses.append("LOWER(v.body) LIKE %s")
                params.append(f"%{b_lower}%")

        if condition and str(condition).lower() not in ['all', 'condition', '']:
            c_lower = str(condition).lower()
            if c_lower == 'new':
                where_clauses.append("v.odometer <= 100")
            elif c_lower in ['used', 'pre-owned']:
                where_clauses.append("v.odometer > 100")
            elif c_lower in ['excellent', '40-50']:
                where_clauses.append("v.condition >= 40")
            elif c_lower in ['very_good', '30-39']:
                where_clauses.append("v.condition BETWEEN 30 AND 39")
            elif c_lower in ['good', '20-29']:
                where_clauses.append("v.condition BETWEEN 20 AND 29")
            elif c_lower in ['fair', '1-19']:
                where_clauses.append("v.condition BETWEEN 1 AND 19")
            elif c_lower.isdigit():
                where_clauses.append("v.condition = %s")
                params.append(int(c_lower))

        if transmission and str(transmission).lower() not in ['all', '']:
            t_lower = str(transmission).lower()
            if 'auto' in t_lower:
                where_clauses.append("LOWER(v.transmission) LIKE %s")
                params.append('%auto%')
            elif 'man' in t_lower:
                where_clauses.append("LOWER(v.transmission) LIKE %s")
                params.append('%manual%')
            else:
                where_clauses.append("LOWER(v.transmission) LIKE %s")
                params.append(f"%{t_lower}%")

        if color and str(color).lower() not in ['all', 'color', '']:
            where_clauses.append("LOWER(v.color) LIKE %s")
            params.append(f"%{color.lower()}%")

        if interior and str(interior).lower() not in ['all', 'interior', '']:
            where_clauses.append("LOWER(v.interior) LIKE %s")
            params.append(f"%{interior.lower()}%")

        if state and str(state).lower() not in ['all', 'state', '']:
            where_clauses.append("LOWER(v.state) = %s")
            params.append(state.lower())

        if trim and str(trim).lower() not in ['all', 'trim', '']:
            where_clauses.append("LOWER(v.trim) LIKE %s")
            params.append(f"%{trim.lower()}%")

        if search_q:
            where_clauses.append("(LOWER(v.vehicle_model) LIKE %s OR LOWER(m.make_name) LIKE %s OR LOWER(v.vin) LIKE %s)")
            q_like = f"%{search_q.lower()}%"
            params.extend([q_like, q_like, q_like])

        if min_price:
            try:
                where_clauses.append("v.mmr >= %s")
                params.append(int(min_price))
            except (ValueError, TypeError):
                pass
        if max_price:
            try:
                where_clauses.append("v.mmr <= %s")
                params.append(int(max_price))
            except (ValueError, TypeError):
                pass

        if min_miles:
            try:
                where_clauses.append("v.odometer >= %s")
                params.append(int(min_miles))
            except (ValueError, TypeError):
                pass
        if max_miles:
            try:
                where_clauses.append("v.odometer <= %s")
                params.append(int(max_miles))
            except (ValueError, TypeError):
                pass

        return where_clauses, params

    @classmethod
    def fetch_catalog_count(cls, **filters):
        where_clauses, params = cls._build_catalog_filters(**filters)
        where_sql = " WHERE " + " AND ".join(where_clauses)
        count_sql = f"""
            SELECT COUNT(*)
            FROM inventory i
            JOIN vehicle_info v ON i.vehicle_id = v.id
            LEFT JOIN industry_info m ON v.make_id = m.make_id
            JOIN store s ON i.store_id = s.store_id
            JOIN city c ON s.city_id = c.city_id
            JOIN country co ON s.country_id = co.country_id
            {where_sql}
        """

        with connection.cursor() as cursor:
            cursor.execute(count_sql, params)
            return cursor.fetchone()[0]

    @classmethod
    def fetch_catalog_vehicles(cls, make_id=None, brand=None, store_id=None, search_q=None, min_price=None, max_price=None, min_miles=None, max_miles=None, body=None, condition=None, transmission=None, color=None, interior=None, state=None, trim=None, sort=None, page=1, page_size=24, limit=None, **kwargs):
        where_clauses, params = cls._build_catalog_filters(
            make_id=make_id, brand=brand, store_id=store_id, search_q=search_q,
            min_price=min_price, max_price=max_price, min_miles=min_miles,
            max_miles=max_miles, body=body, condition=condition,
            transmission=transmission, color=color, interior=interior,
            state=state, trim=trim
        )
        where_sql = " WHERE " + " AND ".join(where_clauses)

        # Count total query
        count_sql = f"""
            SELECT COUNT(*)
            FROM inventory i
            JOIN vehicle_info v ON i.vehicle_id = v.id
            LEFT JOIN industry_info m ON v.make_id = m.make_id
            JOIN store s ON i.store_id = s.store_id
            JOIN city c ON s.city_id = c.city_id
            JOIN country co ON s.country_id = co.country_id
            {where_sql}
        """

        # Sorting logic
        sort_order = "i.inventory_id DESC"
        if sort == 'lowest-price':
            sort_order = "v.mmr ASC"
        elif sort == 'highest-price':
            sort_order = "v.mmr DESC"
        elif sort == 'lowest-mileage':
            sort_order = "v.odometer ASC"
        elif sort == 'highest-mileage':
            sort_order = "v.odometer DESC"

        try:
            page = int(page) if page else 1
        except (ValueError, TypeError):
            page = 1

        try:
            page_size = int(page_size) if page_size else (limit or 24)
        except (ValueError, TypeError):
            page_size = 24

        offset = (page - 1) * page_size

        select_sql = f"""
            SELECT i.inventory_id, i.vehicle_id, i.store_id, i.status,
                   v.vehicle_model, v.trim, v.body, v.transmission, v.color, v.interior, v.state, v.condition, v.odometer, v.mmr, v.vin,
                   m.make_name, s.store_name, c.city_name, co.country_name
            FROM inventory i
            JOIN vehicle_info v ON i.vehicle_id = v.id
            LEFT JOIN industry_info m ON v.make_id = m.make_id
            JOIN store s ON i.store_id = s.store_id
            JOIN city c ON s.city_id = c.city_id
            JOIN country co ON s.country_id = co.country_id
            {where_sql}
            ORDER BY {sort_order}
            LIMIT %s OFFSET %s
        """

        with connection.cursor() as cursor:
            cursor.execute(count_sql, params)
            total_count = cursor.fetchone()[0]

            cursor.execute(select_sql, params + [page_size, offset])
            rows = cursor.fetchall()

            # Price Stats SQL
            cursor.execute(f"SELECT MIN(v.mmr), MAX(v.mmr) FROM inventory i JOIN vehicle_info v ON i.vehicle_id = v.id LEFT JOIN industry_info m ON v.make_id = m.make_id {where_sql}", params)
            p_stats = cursor.fetchone()
            min_p = p_stats[0] or 0
            max_p = p_stats[1] or 182000

        status_map = {1: 'Available', 4: 'Pre-Order', 2: 'Sold', 3: 'Reserved'}
        vehicles = []
        for r in rows:
            inv_id, v_id, s_id, st_code, v_model, v_trim, v_body, v_trans, v_color, v_int, v_state, v_cond, v_odo, v_mmr, v_vin, m_name, s_name, c_name, co_name = r

            
            # Resolve image URL
            img_url = _resolve_vehicle_image_url(m_name, v_model)

            vehicles.append({
                'inventory_id': inv_id,
                'vehicle_id': v_id,
                'make': m_name or 'Vehicle',
                'model': v_model or '',
                'trim': v_trim or '',
                'body': v_body or '',
                'transmission': v_trans or '',
                'color': v_color or '',
                'condition': v_cond or '',
                'odometer': v_odo or '',
                'price': v_mmr or 0,
                'vin': v_vin or '',
                'status': status_map.get(st_code, 'Available'),
                'status_code': st_code,
                'store_id': s_id,
                'store_name': s_name,
                'city': c_name,
                'country': co_name,
                'image_url': img_url,
            })

        available_filters = {
            'min_price': min_p,
            'max_price': max_p,
            'conditions': {
                'all': total_count,
            }
        }

        import math
        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1
        return vehicles, total_count, total_pages, page, available_filters

    @staticmethod
    def fetch_catalog_meta(active_condition='all'):
        """Fetch catalog metadata (makes, stores, transmissions, colors, condition counts, max price) using Raw SQL."""
        with connection.cursor() as cursor:
            cursor.execute("SELECT make_id, make_name FROM industry_info ORDER BY make_name")
            makes = [{'id': row[0], 'make_name': row[1]} for row in cursor.fetchall()]

            cursor.execute("""
                SELECT s.store_id, s.store_name, c.city_name, co.country_name
                FROM store s
                JOIN city c ON s.city_id = c.city_id
                JOIN country co ON s.country_id = co.country_id
                ORDER BY s.store_name
            """)
            stores = [{'store_id': r[0], 'store_name': r[1], 'city': {'city_name': r[2]}, 'country': {'country_name': r[3]}} for r in cursor.fetchall()]

            cursor.execute("SELECT DISTINCT transmission FROM vehicle_info WHERE transmission IS NOT NULL AND transmission != '' ORDER BY transmission")
            transmissions = [r[0] for r in cursor.fetchall()]

            cursor.execute("SELECT DISTINCT color FROM vehicle_info WHERE color IS NOT NULL AND color != '' ORDER BY color")
            colors = [r[0] for r in cursor.fetchall()]

            cursor.execute("SELECT COUNT(*) FROM inventory WHERE status IN (2, 4)")
            cnt_all = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM inventory i JOIN vehicle_info v ON i.vehicle_id = v.id WHERE i.status IN (2, 4) AND v.condition >= 40")
            cnt_excellent = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM inventory i JOIN vehicle_info v ON i.vehicle_id = v.id WHERE i.status IN (2, 4) AND v.condition BETWEEN 30 AND 39")
            cnt_very_good = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM inventory i JOIN vehicle_info v ON i.vehicle_id = v.id WHERE i.status IN (2, 4) AND v.condition BETWEEN 20 AND 29")
            cnt_good = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM inventory i JOIN vehicle_info v ON i.vehicle_id = v.id WHERE i.status IN (2, 4) AND v.condition BETWEEN 1 AND 19")
            cnt_fair = cursor.fetchone()[0]

            cursor.execute("SELECT MAX(v.mmr) FROM inventory i JOIN vehicle_info v ON i.vehicle_id = v.id WHERE i.status IN (2, 4)")
            max_p = cursor.fetchone()[0] or 182000

        vehicle_bodies = VehicleBodyService.fetch_vehicle_bodies()
        condition_tabs = VehicleConditionService.fetch_condition_tabs(active_condition=active_condition)

        return {
            'makes': makes,
            'stores': stores,
            'transmissions': transmissions,
            'colors': colors,
            'vehicle_bodies': vehicle_bodies,
            'condition_tabs': condition_tabs,
            'condition_counts': {
                'all': cnt_all,
                'excellent': cnt_excellent,
                'very_good': cnt_very_good,
                'good': cnt_good,
                'fair': cnt_fair,
            },
            'max_price_db': max_p,
            'fuel_types': ['Gasoline', 'Diesel', 'Hybrid', 'Electric', 'Flex Fuel'],
        }

    @staticmethod
    def fetch_vehicle_models(brand=None, make_id=None):
        """Fetch distinct vehicle models for a brand or make_id using Raw SQL."""
        where_clauses = ["vehicle_model IS NOT NULL", "vehicle_model != ''"]
        params = []

        if make_id and str(make_id).isdigit():
            where_clauses.append("make_id = %s")
            params.append(int(make_id))
        elif brand and str(brand).lower() not in ['all', '']:
            where_clauses.append("make_id IN (SELECT make_id FROM industry_info WHERE LOWER(make_name) LIKE %s)")
            params.append(f"%{brand.lower()}%")

        where_sql = " WHERE " + " AND ".join(where_clauses)
        query = f"SELECT DISTINCT vehicle_model FROM vehicle_info {where_sql} ORDER BY vehicle_model LIMIT 50"

        with connection.cursor() as cursor:
            cursor.execute(query, params)
            return [row[0] for row in cursor.fetchall()]

    @staticmethod
    def fetch_vehicle_trims(brand=None, model=None):
        """Fetch distinct vehicle trims for a brand or model using Raw SQL."""
        where_clauses = ["trim IS NOT NULL", "trim != ''"]
        params = []

        if brand and str(brand).lower() not in ['all', '']:
            where_clauses.append("make_id IN (SELECT make_id FROM industry_info WHERE LOWER(make_name) LIKE %s)")
            params.append(f"%{brand.lower()}%")
        if model and str(model).lower() not in ['all', '']:
            where_clauses.append("LOWER(vehicle_model) LIKE %s")
            params.append(f"%{model.lower()}%")

        where_sql = " WHERE " + " AND ".join(where_clauses)
        query = f"SELECT DISTINCT trim FROM vehicle_info {where_sql} ORDER BY trim LIMIT 50"

        with connection.cursor() as cursor:
            cursor.execute(query, params)
            return [row[0] for row in cursor.fetchall()]


class VehicleDetailService:
    @staticmethod
    def fetch_detail_data(inventory_id):
        """Fetch full vehicle detail using Raw SQL only — no ORM."""
        import re
        from django.http import Http404

        PNG_ALIASES = {'mercedesbenz': 'mercedes', 'landrover': 'landrover'}

        with connection.cursor() as cursor:
            # Main inventory + vehicle + store detail
            cursor.execute("""
                SELECT
                    i.inventory_id, i.vehicle_id, i.store_id, i.status,
                    v.vehicle_model, v.trim, v.body, v.transmission, v.color, v.interior,
                    v.state, v.condition, v.odometer, v.mmr, v.vin, v.make_id,
                    m.make_name,
                    s.store_id, s.store_name,
                    ci.city_name, co.country_name,
                    e.employee_id,
                    e.first_name AS emp_firstname, e.last_name AS emp_lastname,
                    e.employee_role AS emp_position
                FROM inventory i
                JOIN vehicle_info v ON i.vehicle_id = v.id
                LEFT JOIN industry_info m ON v.make_id = m.make_id
                JOIN store s ON i.store_id = s.store_id
                JOIN city ci ON s.city_id = ci.city_id
                JOIN country co ON s.country_id = co.country_id
                LEFT JOIN employee e ON i.employee_id = e.employee_id
                WHERE i.inventory_id = %s
            """, [inventory_id])
            row = cursor.fetchone()

        if not row:
            raise Http404(f"Inventory {inventory_id} not found")

        (
            inv_id, v_id, store_id, status,
            v_model, v_trim, v_body, v_trans, v_color, v_interior,
            v_state, v_cond, v_odo, v_mmr, v_vin, make_id,
            make_name,
            s_id, s_name, city_name, country_name,
            emp_id, emp_firstname, emp_lastname, emp_position
        ) = row


        brand_slug = re.sub(r'[^a-z0-9]', '', str(make_name or '').lower())
        png_slug = PNG_ALIASES.get(brand_slug, brand_slug)
        brand_logo_url = f"/static/logos/{png_slug}.png"
        vehicle_image_url = _resolve_vehicle_image_url(make_name, v_model)

        # Build mock objects that templates expect
        class _Obj(dict):
            """Dict-like object with attribute access for template compatibility."""
            def __getattr__(self, k):
                try: return self[k]
                except KeyError: return None
            def __setattr__(self, k, v): self[k] = v

        vehicle = _Obj(
            id=v_id, vehicle_id=v_id,
            vehicle_model=v_model, trim=v_trim, body=v_body,
            transmission=v_trans, color=v_color, interior=v_interior,
            state=v_state, condition=v_cond, odometer=v_odo, mmr=v_mmr, vin=v_vin,
            make_id=make_id,
            make=_Obj(make_name=make_name),
            image_url=vehicle_image_url
        )
        store = _Obj(
            store_id=s_id, store_name=s_name,
            city=_Obj(city_name=city_name),
            country=_Obj(country_name=country_name)
        )
        employee = _Obj(
            employee_id=emp_id,
            firstname=emp_firstname, lastname=emp_lastname,
            position=emp_position,
            full_name=f"{emp_firstname or ''} {emp_lastname or ''}".strip() or None
        ) if emp_id else None

        status_map = {1: 'Available', 2: 'Sold', 3: 'Reserved', 4: 'Pre-Order'}
        inventory = _Obj(
            inventory_id=inv_id, vehicle_id=v_id, store_id=store_id,
            status=status, status_display=status_map.get(status, 'Available'),
            vehicle=vehicle, store=store, employee=employee
        )

        # Similar vehicles raw SQL (price-range first, then diversified by brand)
        import random
        target_cards = 16
        base_price = int(v_mmr or 0)
        min_price = max(0, int(base_price * 0.8))
        max_price = int(base_price * 1.2) if base_price else 0
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT i.inventory_id, v.vehicle_model, v.trim, v.mmr, v.odometer, m.make_name, s.store_name, c.city_name
                FROM inventory i
                JOIN vehicle_info v ON i.vehicle_id = v.id
                LEFT JOIN industry_info m ON v.make_id = m.make_id
                JOIN store s ON i.store_id = s.store_id
                JOIN city c ON s.city_id = c.city_id
                WHERE i.status IN (2, 4)
                  AND i.inventory_id != %s
                  AND (
                    (%s > 0 AND v.mmr BETWEEN %s AND %s)
                    OR (%s <= 0)
                  )
                ORDER BY ABS(COALESCE(v.mmr, 0) - %s) ASC, RAND()
                LIMIT 80
            """, [inventory_id, base_price, min_price, max_price, base_price, base_price])
            sim_rows = cursor.fetchall()
            if len(sim_rows) < target_cards:
                existing_ids = [inventory_id] + [row[0] for row in sim_rows]
                placeholders = ', '.join(['%s'] * len(existing_ids))
                topup_limit = max(0, target_cards * 3 - len(sim_rows))
                cursor.execute(f"""
                    SELECT i.inventory_id, v.vehicle_model, v.trim, v.mmr, v.odometer, m.make_name, s.store_name, c.city_name
                    FROM inventory i
                    JOIN vehicle_info v ON i.vehicle_id = v.id
                    LEFT JOIN industry_info m ON v.make_id = m.make_id
                    JOIN store s ON i.store_id = s.store_id
                    JOIN city c ON s.city_id = c.city_id
                    WHERE i.status IN (2, 4)
                      AND i.inventory_id NOT IN ({placeholders})
                    ORDER BY ABS(COALESCE(v.mmr, 0) - %s) ASC, RAND()
                    LIMIT %s
                """, [*existing_ids, base_price, topup_limit])
                sim_rows.extend(cursor.fetchall())

        rows_by_brand = {}
        for row in sim_rows:
            brand_key = str(row[5] or 'unknown').strip().lower()
            rows_by_brand.setdefault(brand_key, []).append(row)

        brand_keys = list(rows_by_brand.keys())
        diversified_rows = []
        while len(diversified_rows) < target_cards and any(rows_by_brand.get(k) for k in brand_keys):
            random.shuffle(brand_keys)
            for brand in brand_keys:
                if rows_by_brand.get(brand):
                    diversified_rows.append(rows_by_brand[brand].pop(0))
                    if len(diversified_rows) >= target_cards:
                        break

        if len(diversified_rows) < target_cards:
            selected_ids = {row[0] for row in diversified_rows}
            for row in sim_rows:
                if row[0] not in selected_ids:
                    diversified_rows.append(row)
                    selected_ids.add(row[0])
                    if len(diversified_rows) >= target_cards:
                        break

        similar_inventory = []
        for r in diversified_rows:
            inv_i, v_mod, v_tr, v_pr, v_odo_sim, m_nm, s_nm, c_nm = r
            similar_inventory.append({
                'inventory_id': inv_i,
                'vehicle': {
                    'vehicle_model': v_mod,
                    'trim': v_tr,
                    'mmr': v_pr,
                    'odometer': v_odo_sim,
                    'make': {'make_name': m_nm},
                    'image_url': _resolve_vehicle_image_url(m_nm, v_mod)
                },
                'store': {'store_name': s_nm, 'city': {'city_name': c_nm}}
            })
        similar_inventory_groups = [similar_inventory[i:i + 4] for i in range(0, len(similar_inventory), 4)]

        return {
            'inventory': inventory,
            'vehicle': vehicle,
            'brand_logo_url': brand_logo_url,
            'similar_inventory': similar_inventory,
            'similar_inventory_groups': similar_inventory_groups,
        }






class WishlistService:
    @staticmethod
    def fetch_customer_wishlist(customer):
        """Fetch all wishlist items for a customer using Raw SQL."""
        if not customer:
            return []
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT w.id, w.vehicle_id, v.vehicle_model, v.mmr, m.make_name, w.created_at
                FROM {wishlist_table} w
                JOIN vehicle_info v ON w.vehicle_id = v.id
                LEFT JOIN industry_info m ON v.make_id = m.make_id
                WHERE w.customer_id = %s
                ORDER BY w.created_at DESC
            """.format(wishlist_table=WISHLIST_TABLE), [customer.customer_id])
            rows = cursor.fetchall()

        class _WishlistItem:
            """Lightweight wishlist item proxy for template compatibility."""
            def __init__(self, row):
                self.id, self.vehicle_id, model, price, make_name, self.created_at = row
                class _Make:
                    def __init__(self, name): self.make_name = name
                class _Vehicle:
                    def __init__(self, vehicle_id, model, price, make_obj):
                        self.id = vehicle_id
                        self.vehicle_model = model
                        self.mmr = price
                        self.make = make_obj
                        self.image_url = _resolve_vehicle_image_url(make_obj.make_name, model)
                self.vehicle = _Vehicle(self.vehicle_id, model, price, _Make(make_name))

        return [_WishlistItem(r) for r in rows]

    @staticmethod
    def toggle_wishlist(customer, vehicle_id):
        """Add or remove a vehicle from the customer wishlist using Raw SQL."""
        if not customer:
            raise ValueError("Authentication required")
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT id FROM {WISHLIST_TABLE} WHERE customer_id = %s AND vehicle_id = %s",
                [customer.customer_id, vehicle_id]
            )
            existing = cursor.fetchone()
            if existing:
                cursor.execute(f"DELETE FROM {WISHLIST_TABLE} WHERE id = %s", [existing[0]])
                added = False
                msg = "Removed from Wishlist"
            else:
                cursor.execute(
                    f"INSERT INTO {WISHLIST_TABLE} (customer_id, vehicle_id, created_at) VALUES (%s, %s, NOW())",
                    [customer.customer_id, vehicle_id]
                )
                added = True
                msg = "Added to Wishlist"
            cursor.execute(
                f"SELECT COUNT(*) FROM {WISHLIST_TABLE} WHERE customer_id = %s",
                [customer.customer_id]
            )
            count = cursor.fetchone()[0]
        return {'added': added, 'message': msg, 'wishlist_count': count}


class CartService:
    @staticmethod
    def fetch_customer_cart_items(customer):
        """Fetch cart items with prices using Raw SQL."""
        if not customer:
            return [], 0
        with connection.cursor() as cursor:
            # Ensure cart exists
            cursor.execute(
                f"SELECT {CART_PK_COLUMN} FROM {CART_TABLE} WHERE customer_id = %s",
                [customer.customer_id]
            )
            cart_row = cursor.fetchone()
            if not cart_row:
                cursor.execute(
                    f"INSERT INTO {CART_TABLE} (customer_id, created_at) VALUES (%s, NOW())",
                    [customer.customer_id]
                )
                cursor.execute(
                    f"SELECT {CART_PK_COLUMN} FROM {CART_TABLE} WHERE customer_id = %s",
                    [customer.customer_id]
                )
                cart_row = cursor.fetchone()
            cart_id = cart_row[0]

            cursor.execute("""
                SELECT ci.id, ci.inventory_id, v.vehicle_model, v.mmr, m.make_name,
                       s.store_name, ci.added_at
                FROM {cart_item_table} ci
                JOIN inventory i ON ci.inventory_id = i.inventory_id
                JOIN vehicle_info v ON i.vehicle_id = v.id
                LEFT JOIN industry_info m ON v.make_id = m.make_id
                JOIN store s ON i.store_id = s.store_id
                WHERE ci.{cart_item_cart_column} = %s
                ORDER BY ci.added_at DESC
            """.format(cart_item_table=CART_ITEM_TABLE, cart_item_cart_column=CART_ITEM_CART_COLUMN), [cart_id])
            rows = cursor.fetchall()

        class _CartItem:
            """Lightweight cart item proxy for template compatibility."""
            def __init__(self, row):
                self.id, self.inventory_id, model, price, make_name, store_name, self.added_at = row
                class _Make:
                    def __init__(self, name): self.make_name = name
                class _Vehicle:
                    def __init__(self, model, price, make_obj):
                        self.vehicle_model = model; self.mmr = price; self.make = make_obj
                        self.image_url = _resolve_vehicle_image_url(make_obj.make_name, model)
                class _Store:
                    def __init__(self, name): self.store_name = name
                class _Inv:
                    def __init__(self, inv_id, veh, store):
                        self.inventory_id = inv_id; self.vehicle = veh; self.store = store
                self.inventory = _Inv(
                    self.inventory_id,
                    _Vehicle(model, price, _Make(make_name)),
                    _Store(store_name)
                )
                self.price = price

        items = [_CartItem(r) for r in rows]
        total_price = sum(item.price for item in items)
        return items, total_price

    @staticmethod
    def add_to_cart(customer, inventory_id):
        """Add inventory item to cart using Raw SQL."""
        if not customer:
            raise ValueError("Authentication required")
        with connection.cursor() as cursor:
            cursor.execute("SELECT status FROM inventory WHERE inventory_id = %s", [inventory_id])
            inv_row = cursor.fetchone()
            if not inv_row:
                raise ValueError("Inventory item not found")
            if inv_row[0] not in [1, 4]:  # 1=Available, 4=Pre-Order
                raise ValueError("Item is no longer available")

            cursor.execute(
                f"SELECT {CART_PK_COLUMN} FROM {CART_TABLE} WHERE customer_id = %s",
                [customer.customer_id]
            )
            cart_row = cursor.fetchone()
            if not cart_row:
                cursor.execute(
                    f"INSERT INTO {CART_TABLE} (customer_id, created_at) VALUES (%s, NOW())",
                    [customer.customer_id]
                )
                cursor.execute(
                    f"SELECT {CART_PK_COLUMN} FROM {CART_TABLE} WHERE customer_id = %s",
                    [customer.customer_id]
                )
                cart_row = cursor.fetchone()
            cart_id = cart_row[0]

            cursor.execute(
                f"SELECT id FROM {CART_ITEM_TABLE} WHERE {CART_ITEM_CART_COLUMN} = %s AND inventory_id = %s",
                [cart_id, inventory_id]
            )
            existing = cursor.fetchone()
            if existing:
                created = False
            else:
                cursor.execute(
                    f"INSERT INTO {CART_ITEM_TABLE} ({CART_ITEM_CART_COLUMN}, inventory_id, added_at) VALUES (%s, %s, NOW())",
                    [cart_id, inventory_id]
                )
                created = True

            cursor.execute(f"SELECT COUNT(*) FROM {CART_ITEM_TABLE} WHERE {CART_ITEM_CART_COLUMN} = %s", [cart_id])
            count = cursor.fetchone()[0]

        return {'created': created, 'message': 'Added to Cart' if created else 'Item already in Cart', 'cart_count': count}

    @staticmethod
    def remove_from_cart(customer, inventory_id):
        """Remove item from cart using Raw SQL."""
        if not customer:
            raise ValueError("Authentication required")
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT {CART_PK_COLUMN} FROM {CART_TABLE} WHERE customer_id = %s",
                [customer.customer_id]
            )
            cart_row = cursor.fetchone()
            if cart_row:
                cart_id = cart_row[0]
                cursor.execute(
                    f"DELETE FROM {CART_ITEM_TABLE} WHERE {CART_ITEM_CART_COLUMN} = %s AND inventory_id = %s",
                    [cart_id, inventory_id]
                )
                cursor.execute(f"SELECT COUNT(*) FROM {CART_ITEM_TABLE} WHERE {CART_ITEM_CART_COLUMN} = %s", [cart_id])
                count = cursor.fetchone()[0]
            else:
                count = 0
        return {'message': 'Item removed from cart', 'cart_count': count}


class TestDriveService:
    @staticmethod
    def fetch_customer_bookings(customer):
        """Fetch all test drive bookings for a customer using Raw SQL."""
        if not customer:
            return []
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    td.booking_id, td.vehicle_id, td.store_id, td.assigned_employee_id,
                    td.booking_date, td.booking_time, td.status, td.notes, td.created_at,
                    v.vehicle_model, m.make_name, s.store_name,
                    e.first_name, e.last_name
                FROM {test_drive_table} td
                JOIN vehicle_info v ON td.vehicle_id = v.id
                LEFT JOIN industry_info m ON v.make_id = m.make_id
                JOIN store s ON td.store_id = s.store_id
                LEFT JOIN employee e ON td.assigned_employee_id = e.employee_id
                WHERE td.customer_id = %s
                ORDER BY td.booking_date DESC
            """.format(test_drive_table=TEST_DRIVE_TABLE), [customer.customer_id])
            rows = cursor.fetchall()


        class _Booking:
            """Lightweight booking proxy for template compatibility."""
            def __init__(self, row):
                (
                    self.booking_id, self.vehicle_id, self.store_id, self.assigned_employee_id,
                    self.booking_date, self.booking_time, self.status, self.notes, self.created_at,
                    model, make_name, store_name, emp_first, emp_last
                ) = row
                class _Make:
                    def __init__(self, n): self.make_name = n
                class _Vehicle:
                    def __init__(self, vid, model, make_obj):
                        self.id = vid; self.vehicle_model = model; self.make = make_obj
                class _Store:
                    def __init__(self, name): self.store_name = name
                class _Emp:
                    def __init__(self, f, l):
                        self.firstname = f; self.lastname = l
                        self.full_name = f"{f or ''} {l or ''}".strip()
                self.vehicle = _Vehicle(self.vehicle_id, model, _Make(make_name))
                self.store = _Store(store_name)
                self.assigned_employee = _Emp(emp_first, emp_last) if self.assigned_employee_id else None
                STATUS_MAP = {1: 'Scheduled', 2: 'Completed', 3: 'Cancelled', 'SCHEDULED': 'Scheduled', 'COMPLETED': 'Completed', 'CANCELLED': 'Cancelled'}
                self.status_display = STATUS_MAP.get(self.status, str(self.status).replace('_', ' ').title())

        return [_Booking(r) for r in rows]

    @staticmethod
    def create_booking(customer, vehicle_id, store_id, booking_date_str, booking_time_str='10:00', notes=''):
        """Create a test drive booking using Raw SQL."""
        if not customer:
            raise ValueError("Authentication required")
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM vehicle_info WHERE id = %s", [vehicle_id])
            if not cursor.fetchone():
                raise ValueError("Vehicle not found")
            cursor.execute("SELECT store_id FROM store WHERE store_id = %s", [store_id])
            if not cursor.fetchone():
                raise ValueError("Store not found")

            cursor.execute("""
                INSERT INTO {test_drive_table}
                    (customer_id, vehicle_id, store_id, booking_date, booking_time, notes, status, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, 'SCHEDULED', NOW(), NOW())
            """.format(test_drive_table=TEST_DRIVE_TABLE), [customer.customer_id, vehicle_id, store_id, booking_date_str, booking_time_str, notes])
            booking_id = cursor.lastrowid

            cursor.execute(
                f"SELECT booking_id, booking_date, booking_time FROM {TEST_DRIVE_TABLE} WHERE booking_id = %s",
                [booking_id]
            )
            row = cursor.fetchone()

        class _Booking:
            def __init__(self, r):
                self.booking_id, self.booking_date, self.booking_time = r
        return _Booking(row)


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
