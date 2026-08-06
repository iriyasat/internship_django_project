"""
URL configuration for project1 project.
"""
from django.contrib import admin
from django.urls import path, include 
from django.http import JsonResponse
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from project1.admin_sites import car_sales_admin_site, ecommerce_admin_site

def chrome_devtools_json(request):
    return JsonResponse({})

urlpatterns = [
    path('favicon.ico', RedirectView.as_view(url='/static/assets/img/favicon.png', permanent=True)),
    path('django-admin/login/', RedirectView.as_view(url='/login/', query_string=True)),
    path('django-admin/logout/', RedirectView.as_view(url='/logout/', query_string=True)),
    
    # Dual Superadmin Portals
    path('admin/car-sales/', car_sales_admin_site.urls),
    path('admin/ecommerce/', ecommerce_admin_site.urls),
    path('django-admin/', admin.site.urls),
    
    path('.well-known/appspecific/com.chrome.devtools.json', chrome_devtools_json),
    path('', include('ecommerce.urls')),
    path('', include('car_sales.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
