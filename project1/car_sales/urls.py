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
]