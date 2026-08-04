from django.urls import path
from . import views

app_name = 'ecommerce'

urlpatterns = [
    # Core E-Commerce Page Routes
    path('catalog/', views.catalog_view, name='catalog'),
    path('vehicle/<int:inventory_id>/', views.vehicle_detail_view, name='vehicle_detail'),
    path('compare/', views.compare_view, name='compare'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('cart/', views.cart_view, name='cart'),
    path('test-drive/', views.test_drive_view, name='test_drive'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('orders/', views.customer_orders_view, name='customer_orders'),
    path('profile/', views.customer_profile_view, name='customer_profile'),
    path('messages/', views.customer_messages_view, name='customer_messages'),

    # JSON API Endpoints
    path('api/catalog/', views.api_catalog_vehicles, name='api_catalog_vehicles'),
    path('api/bodies/', views.api_vehicle_bodies, name='api_vehicle_bodies'),
    path('api/conditions/', views.api_vehicle_conditions, name='api_vehicle_conditions'),
    path('api/models/', views.api_vehicle_models, name='api_vehicle_models'),
    path('api/trims/', views.api_vehicle_trims, name='api_vehicle_trims'),
    path('api/messages/send/', views.api_send_customer_message, name='api_send_customer_message'),
    path('api/messages/superuser/', views.api_send_superuser_message, name='api_send_superuser_message'),
    path('api/wishlist/toggle/', views.api_toggle_wishlist, name='api_toggle_wishlist'),
    path('api/cart/add/', views.api_add_to_cart, name='api_add_to_cart'),
    path('api/cart/remove/', views.api_remove_from_cart, name='api_remove_from_cart'),
    path('api/test-drive/book/', views.api_book_test_drive, name='api_book_test_drive'),
    path('api/order/submit/', views.api_submit_order, name='api_submit_order'),
    path('api/profile/update/', views.api_update_customer_profile, name='api_update_customer_profile'),
]
