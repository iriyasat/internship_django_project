from django.contrib.admin import AdminSite
from project1.workspaces import is_car_sales_admin_user, is_ecommerce_admin_user

class CarSalesAdminSite(AdminSite):
    site_header = "Car Sales Dealership Administration"
    site_title = "Car Sales Admin"
    index_title = "Dealership Management Dashboard"

    def has_permission(self, request):
        return request.user.is_active and is_car_sales_admin_user(request.user)

class EcommerceAdminSite(AdminSite):
    site_header = "E-Commerce Platform Administration"
    site_title = "E-Commerce Admin"
    index_title = "E-Commerce Platform Management"

    def has_permission(self, request):
        return request.user.is_active and is_ecommerce_admin_user(request.user)

car_sales_admin_site = CarSalesAdminSite(name='car_sales_admin')
ecommerce_admin_site = EcommerceAdminSite(name='ecommerce_admin')
