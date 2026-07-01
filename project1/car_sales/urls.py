from django.urls import path, include
from .views import *

urlpatterns = [
    path('', home_view, name='home'),
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
    path('reports/employee/', employee_report_view, name='employee_report'),
    path('reports/vehicle/', vehicle_report_view, name='vehicle_report'),
    path('reports/sales/', sales_report_view, name='sales_report'),
    path('admin-panel/', admin_panel_view, name='admin_panel'),
    path('admin-panel/crud/<str:model_name>/<str:action>/', admin_crud_view, name='admin_crud'),
    path('admin-panel/crud/<str:model_name>/<str:action>/<int:pk>/', admin_crud_view, name='admin_crud_pk'),
    path('api/employee_sales/', employee_sales_api, name='employee_sales_api'),
    path('api/store_sales/', store_sales_api, name='store_sales_api'),
    path('api-page/employee-sales/', employee_sales_page_view, name='employee_sales_page_view'),
    path('api-page/store-sales/', store_sales_page_view, name='store_sales_page_view'),
]