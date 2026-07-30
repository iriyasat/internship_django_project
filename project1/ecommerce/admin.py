from django.contrib import admin
from project1.admin_sites import ecommerce_admin_site
from .models import Wishlist, Cart, CartItem, TestDriveBooking, Order, PaymentTransaction


# Register in custom EcommerceAdminSite
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('customer', 'vehicle', 'created_at')
    search_fields = ('customer__email', 'vehicle__vehicle_model', 'vehicle__vin')
    list_select_related = ('customer', 'vehicle')


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


class CartAdmin(admin.ModelAdmin):
    list_display = ('customer', 'created_at', 'updated_at')
    search_fields = ('customer__email',)
    inlines = [CartItemInline]


class TestDriveBookingAdmin(admin.ModelAdmin):
    list_display = ('booking_id', 'customer', 'vehicle', 'store', 'assigned_employee', 'booking_date', 'booking_time', 'status')
    list_filter = ('status', 'booking_date', 'store')
    search_fields = ('customer__email', 'vehicle__vehicle_model', 'vehicle__vin', 'assigned_employee__first_name')
    list_select_related = ('customer', 'vehicle', 'store', 'assigned_employee')


class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_id', 'customer', 'inventory', 'store', 
        'assigned_employee', 'order_status', 'payment_preference', 
        'fulfillment_type', 'total_amount', 'reviewed_at', 'created_at'
    )
    list_filter = ('order_status', 'payment_preference', 'fulfillment_type', 'store')
    search_fields = ('order_id', 'customer__email', 'inventory__vehicle__vin', 'assigned_employee__first_name')
    list_select_related = ('customer', 'inventory', 'store', 'assigned_employee', 'invoice')


class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'order', 'invoice', 'customer', 'payment_method', 'payment_type', 'amount', 'recorded_by_employee', 'status', 'created_at')
    list_filter = ('status', 'payment_method', 'payment_type')
    search_fields = ('gateway_transaction_id', 'order__order_id', 'customer__email', 'invoice__invoice_id')
    list_select_related = ('order', 'invoice', 'customer', 'recorded_by_employee')


# Register to both default admin.site and dedicated ecommerce_admin_site
admin.site.register(Wishlist, WishlistAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(TestDriveBooking, TestDriveBookingAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(PaymentTransaction, PaymentTransactionAdmin)

ecommerce_admin_site.register(Wishlist, WishlistAdmin)
ecommerce_admin_site.register(Cart, CartAdmin)
ecommerce_admin_site.register(TestDriveBooking, TestDriveBookingAdmin)
ecommerce_admin_site.register(Order, OrderAdmin)
ecommerce_admin_site.register(PaymentTransaction, PaymentTransactionAdmin)
