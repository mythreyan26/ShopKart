"""
URL configuration for ms_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import os
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.http import FileResponse
from django.views.generic import TemplateView


def service_worker_view(request):
    sw_path = os.path.join(settings.BASE_DIR, 'static', 'sw.js')
    response = FileResponse(open(sw_path, 'rb'), content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response


def manifest_view(request):
    manifest_path = os.path.join(settings.BASE_DIR, 'static', 'manifest.json')
    response = FileResponse(open(manifest_path, 'rb'), content_type='application/manifest+json')
    response['Cache-Control'] = 'public, max-age=86400'
    return response


from shop.admin_views import admin_analytics_view, admin_inventory_view


urlpatterns = [
    path('admin/analytics/', admin_analytics_view, name='admin_analytics'),
    path('admin/reports/', admin_analytics_view, name='admin_reports'),
    path('admin/inventory/', admin_inventory_view, name='admin_inventory'),
    path('admin/', admin.site.urls),
    path('api/', include('shop.api_urls')),
    path('sw.js', service_worker_view, name='pwa_sw'),
    path('manifest.json', manifest_view, name='pwa_manifest'),
    path('offline/', TemplateView.as_view(template_name='shop/offline.html'), name='pwa_offline'),
    path('', include('shop.urls')),
]

# Serve media files (images, uploaded product graphics) in production and development
urlpatterns += [
    re_path(r'^images/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)