from django.contrib.admin import AdminSite

class CarSalesAdminSite(AdminSite):
    site_header = "Car Sales Dealership Administration"
    site_title = "Car Sales Admin"
    index_title = "Dealership Management Dashboard"

    def has_permission(self, request):
        if not (request.user.is_active and request.user.is_staff):
            return False
        username = getattr(request.user, 'username', '')
        return username == 'admin' or username.startswith('car_sales_') or request.user.is_superuser

class EcommerceAdminSite(AdminSite):
    site_header = "E-Commerce Platform Administration"
    site_title = "E-Commerce Admin"
    index_title = "E-Commerce Platform Management"

    def has_permission(self, request):
        if not (request.user.is_active and request.user.is_staff):
            return False
        username = getattr(request.user, 'username', '')
        return username == 'ihriyasat' or username.startswith('ecomm_') or request.user.is_superuser

car_sales_admin_site = CarSalesAdminSite(name='car_sales_admin')
ecommerce_admin_site = EcommerceAdminSite(name='ecommerce_admin')
