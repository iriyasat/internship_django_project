from django.urls import path
from . import views

app_name = 'ecommerce'

urlpatterns = [
    # Customer Catalog & Filtering
    path('catalog/', views.catalog_view, name='catalog'),
    path('api/catalog/', views.api_catalog_vehicles, name='api_catalog_vehicles'),

    # Customer Wishlist
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('api/wishlist/toggle/', views.api_toggle_wishlist, name='api_toggle_wishlist'),

    # Customer Shopping Cart
    path('cart/', views.cart_view, name='cart'),
    path('api/cart/add/', views.api_add_to_cart, name='api_add_to_cart'),
    path('api/cart/remove/', views.api_remove_from_cart, name='api_remove_from_cart'),

    # Test Drive Scheduling
    path('test-drive/', views.test_drive_view, name='test_drive'),
    path('api/test-drive/book/', views.api_book_test_drive, name='api_book_test_drive'),

    # Checkout & Customer Orders
    path('checkout/', views.checkout_view, name='checkout'),
    path('api/order/submit/', views.api_submit_order, name='api_submit_order'),
    path('orders/', views.customer_orders_view, name='customer_orders'),

    # Store Staff Dashboard & Workflow APIs
    path('staff/dashboard/', views.store_staff_dashboard_view, name='staff_dashboard'),
    path('api/staff/review-order/', views.api_review_order, name='api_review_order'),
    path('api/staff/record-payment/', views.api_record_payment, name='api_record_payment'),
    path('api/staff/fulfill-order/', views.api_fulfill_order, name='api_fulfill_order'),
]
