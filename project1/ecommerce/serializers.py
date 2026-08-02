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


class VehicleBodySerializer(serializers.Serializer):
    name = serializers.CharField()
    display_name = serializers.CharField()
    count = serializers.IntegerField(default=0)
    url = serializers.CharField()
    svg = serializers.CharField()


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

    @classmethod
    def fetch_vehicle_bodies(cls):
        db_bodies = (
            VehicleInfo.objects
            .exclude(body__isnull=True)
            .exclude(body='')
            .values('body')
            .annotate(count=models.Count('id'))
            .order_by('-count')
        )

        body_list = []
        seen = set()

        # Featured UI items first
        featured_names = ['Electric', 'Sedan', 'SUV', 'Pickup Truck', 'Access Cab', 'Luxury', 'Hatchback', 'Crossover', 'Convertible', 'Coupe', 'Minivan', 'Wagon']

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
                    'svg': cls.get_svg_for_body(display_name)
                })

        # Ensure featured list items are also included if missing
        for fname in featured_names:
            if fname not in seen:
                seen.add(fname)
                body_list.append({
                    'name': fname,
                    'display_name': fname,
                    'count': 0,
                    'url': f"/catalog/?body={fname}",
                    'svg': cls.get_svg_for_body(fname)
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
        avail_qs = Inventory.objects.select_related('vehicle').filter(
            status__in=[Inventory.StatusChoices.AVAILABLE, Inventory.StatusChoices.PRE_ORDER]
        )

        all_count = avail_qs.count()
        new_count = avail_qs.filter(vehicle__odometer__lte=cls.NEW_CAR_MAX_ODOMETER).count()
        used_count = avail_qs.filter(vehicle__odometer__gt=cls.NEW_CAR_MAX_ODOMETER).count()

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
# Encapsulated Business Query & Transaction Services
# ------------------------------------------------------------------------------

class CatalogService:
    @staticmethod
    def fetch_catalog_vehicles(make_id=None, brand=None, store_id=None, search_q=None, min_price=None, max_price=None, min_miles=None, max_miles=None, body=None, condition=None, transmission=None, color=None, interior=None, state=None, trim=None, limit=60):
        qs = Inventory.objects.select_related('vehicle__make', 'store', 'store__city', 'store__country').filter(
            status__in=[Inventory.StatusChoices.AVAILABLE, Inventory.StatusChoices.PRE_ORDER]
        )

        if make_id and str(make_id).isdigit():
            qs = qs.filter(vehicle__make_id=make_id)
        elif brand and str(brand).lower() not in ['all', '']:
            qs = qs.filter(vehicle__make__make_name__icontains=brand)
        elif make_id and not str(make_id).isdigit() and str(make_id).lower() not in ['all', '']:
            qs = qs.filter(vehicle__make__make_name__icontains=make_id)

        if store_id:
            qs = qs.filter(store_id=store_id)
        if body:
            b_lower = body.lower()
            if b_lower in ['pickup truck', 'truck']:
                qs = qs.filter(
                    models.Q(vehicle__body__icontains='cab') |
                    models.Q(vehicle__body__icontains='truck') |
                    models.Q(vehicle__body__icontains='xtracab')
                )
            elif b_lower in ['minivan', 'van']:
                qs = qs.filter(
                    models.Q(vehicle__body__icontains='van') |
                    models.Q(vehicle__body__icontains='minivan')
                )
            elif b_lower == 'coupe':
                qs = qs.filter(
                    models.Q(vehicle__body__icontains='coupe') |
                    models.Q(vehicle__body__icontains='koup')
                )
            else:
                qs = qs.filter(vehicle__body__icontains=body)
        if condition and str(condition).lower() not in ['all', 'condition', '']:
            c_lower = str(condition).lower()
            if c_lower == 'new':
                qs = qs.filter(vehicle__odometer__lte=VehicleConditionService.NEW_CAR_MAX_ODOMETER)
            elif c_lower in ['used', 'pre-owned']:
                qs = qs.filter(vehicle__odometer__gt=VehicleConditionService.NEW_CAR_MAX_ODOMETER)
            elif c_lower in ['excellent', '40-50']:
                qs = qs.filter(vehicle__condition__gte=40)
            elif c_lower in ['very_good', '30-39']:
                qs = qs.filter(vehicle__condition__range=(30, 39))
            elif c_lower in ['good', '20-29']:
                qs = qs.filter(vehicle__condition__range=(20, 29))
            elif c_lower in ['fair', '1-19']:
                qs = qs.filter(vehicle__condition__range=(1, 19))
            elif c_lower.isdigit():
                qs = qs.filter(vehicle__condition=int(c_lower))
        if transmission and str(transmission).lower() not in ['all', '']:
            t_lower = str(transmission).lower()
            if 'auto' in t_lower:
                qs = qs.filter(vehicle__transmission__icontains='auto')
            elif 'man' in t_lower:
                qs = qs.filter(vehicle__transmission__icontains='manual')
            else:
                qs = qs.filter(vehicle__transmission__icontains=transmission)
        if color and str(color).lower() not in ['all', 'color', '']:
            qs = qs.filter(vehicle__color__icontains=color)
        if interior and str(interior).lower() not in ['all', 'interior', '']:
            qs = qs.filter(vehicle__interior__icontains=interior)
        if state and str(state).lower() not in ['all', 'state', '']:
            qs = qs.filter(vehicle__state__iexact=state)
        if trim and str(trim).lower() not in ['all', 'trim', '']:
            qs = qs.filter(vehicle__trim__icontains=trim)
        if search_q:
            qs = qs.filter(
                models.Q(vehicle__vehicle_model__icontains=search_q) |
                models.Q(vehicle__make__make_name__icontains=search_q) |
                models.Q(vehicle__vin__icontains=search_q)
            )
        if min_price:
            try:
                qs = qs.filter(vehicle__mmr__gte=int(min_price))
            except (ValueError, TypeError):
                pass
        if max_price:
            try:
                qs = qs.filter(vehicle__mmr__lte=int(max_price))
            except (ValueError, TypeError):
                pass
        if min_miles:
            try:
                qs = qs.filter(vehicle__odometer__gte=int(min_miles))
            except (ValueError, TypeError):
                pass
        if max_miles:
            try:
                qs = qs.filter(vehicle__odometer__lte=int(max_miles))
            except (ValueError, TypeError):
                pass

        total_count = qs.count()
        sliced_qs = qs.order_by('-inventory_id')[:limit]

        vehicles = []
        for item in sliced_qs:
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
                'image_url': v.image_url,
            })
        return vehicles, total_count


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
