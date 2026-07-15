from django.urls import path, include
from .views import *

urlpatterns = [
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    path('', index_view, name='home'),
    path('dashboard/', home_view, name='dashboard'),
    path('employees/', employee_view, name='employee'),
    path('countries/', country_view, name='country'),
    path('cities/', city_view, name='city'),
    path('stores/', store_view, name='store'),
    path('emproles/', role_view, name='emprole'),
    path('statuses/', status_view, name='status'),
    path('industry/', industry_view, name='industry'),
    path('vehicles/', vehicle_view, name='vehicle'),
    path('customers/', customer_view, name='customer'),
    path('sales/', selling_view, name='selling'),
    path('budgets/', budget_view, name='budget'),
    path('admin-panel/', admin_panel_view, name='admin_panel'),
    path('api/employee_sales/', employee_sales_api, name='employee_sales_api'),
    path('api/store_sales/', store_sales_api, name='store_sales_api'),
    path('api/store_vehicle_sales/', store_vehicle_sales_api, name='store_vehicle_sales_api'),
    path('api/customer_vehicle_sales/', customer_vehicle_sales_api, name='customer_vehicle_sales_api'),
    path('api/customer_store_spending/', customer_store_spending_api, name='customer_store_spending_api'),
    path('api-page/employee-sales/', employee_sales_page_view, name='employee_sales_page_view'),
    path('api-page/store-sales/', store_sales_page_view, name='store_sales_page_view'),
    path('api-page/store-vehicle-sales/', store_vehicle_sales_page_view, name='store_vehicle_sales_page_view'),
    path('api-page/customer-vehicle-sales/', customer_vehicle_sales_page_view, name='customer_vehicle_sales_page_view'),
    path('api-page/customer-store-spending/', customer_store_spending_page_view, name='customer_store_spending_page_view'),
    path('api/budget-vs-sales/', budget_vs_sales_api, name='budget_vs_sales_api'),
    path('api-page/budget-vs-sales/', budget_vs_sales_page_view, name='budget_vs_sales_page_view'),
    path('api/inventory/', inventory_api, name='inventory_api'),
    path('api/inventory/<int:pk>/', inventory_api, name='inventory_api_detail'),
    path('api-page/inventory/', inventory_api_page_view, name='inventory_api_page_view'),
    path('api/budgets/stats/', budget_stats_api, name='budget_stats_api'),

    # Invoice URLs
    path('invoices/', invoice_view, name='invoice'),
    path('api/invoices/', invoice_api, name='invoice_api'),
    path('api/invoices/<int:pk>/', invoice_api, name='invoice_api_detail'),
    path('invoices/<int:invoice_id>/pdf/', download_invoice_pdf, name='download_invoice_pdf'),
]

# Dynamically register the 10 CRUD API endpoints to avoid boilerplate code
api_routes = [
    ('countries', country_api, 'country_api'),
    ('cities', city_api, 'city_api'),
    ('stores', store_api, 'store_api'),
    ('emproles', role_api, 'role_api'),
    ('statuses', status_api, 'status_api'),
    ('industry', industry_api, 'industry_api'),
    ('vehicles', vehicle_api, 'vehicle_api'),
    ('customers', customer_api, 'customer_api'),
    ('sales', sales_api, 'sales_api'),
    ('budgets', budget_api, 'budget_api'),
    ('employees', employee_api, 'employee_api'),
]

for route, view_func, name in api_routes:
    urlpatterns.extend([
        path(f'api/{route}/', view_func, name=name),
        path(f'api/{route}/<int:pk>/', view_func, name=f'{name}_detail'),
    ])