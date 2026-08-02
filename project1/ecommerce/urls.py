from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'ecommerce'

urlpatterns = [
    # Top-Level Clean E-Commerce Routes
    path('catalog/', views.catalog_view, name='catalog'),
    path('category/', views.catalog_view, name='category'),
    path('api/catalog/', views.api_catalog_vehicles, name='api_catalog_vehicles'),

    path('api/bodies/', views.api_vehicle_bodies, name='api_vehicle_bodies'),
    path('api/conditions/', views.api_vehicle_conditions, name='api_vehicle_conditions'),
    path('api/models/', views.api_vehicle_models, name='api_vehicle_models'),

    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('api/wishlist/toggle/', views.api_toggle_wishlist, name='api_toggle_wishlist'),

    path('cart/', views.cart_view, name='cart'),
    path('api/cart/add/', views.api_add_to_cart, name='api_add_to_cart'),
    path('api/cart/remove/', views.api_remove_from_cart, name='api_remove_from_cart'),

    path('test-drive/', views.test_drive_view, name='test_drive'),
    path('api/test-drive/book/', views.api_book_test_drive, name='api_book_test_drive'),

    path('checkout/', views.checkout_view, name='checkout'),
    path('api/order/submit/', views.api_submit_order, name='api_submit_order'),
    path('orders/', views.customer_orders_view, name='customer_orders'),

    # Customer Profile Routes
    path('profile/', views.customer_profile_view, name='customer_profile'),
    path('api/profile/update/', views.api_update_customer_profile, name='api_update_customer_profile'),

    # Redirect legacy /ecommerce/... paths to new clean URLs
    path('ecommerce/catalog/', RedirectView.as_view(url='/catalog/', permanent=True)),
    path('ecommerce/cart/', RedirectView.as_view(url='/cart/', permanent=True)),
    path('ecommerce/wishlist/', RedirectView.as_view(url='/wishlist/', permanent=True)),
    path('ecommerce/checkout/', RedirectView.as_view(url='/checkout/', permanent=True)),
    path('ecommerce/orders/', RedirectView.as_view(url='/orders/', permanent=True)),
    path('ecommerce/test-drive/', RedirectView.as_view(url='/test-drive/', permanent=True)),
    path('ecommerce/profile/', RedirectView.as_view(url='/profile/', permanent=True)),
]
