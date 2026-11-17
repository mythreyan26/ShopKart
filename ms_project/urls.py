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


from shop import admin_views
from shop.admin_views import admin_analytics_view, admin_inventory_view


urlpatterns = [
    # Admin Panel (Updated to match Miguel Studio reference image)
    path('admin/analytics/', admin_analytics_view, name='admin_analytics'),
    path('admin/reports/', admin_analytics_view, name='admin_reports'),
    path('admin/inventory/', admin_inventory_view, name='admin_inventory'),

    # Products & Categories
    path('admin/products/', admin_views.admin_products, name="admin_products"),
    path('admin/shop/product/', admin_views.admin_products),
    path('admin/products/create/', admin_views.admin_product_create, name="admin_product_create"),
    path('admin/shop/product/add/', admin_views.admin_product_create),
    path('admin/products/<int:product_id>/edit/', admin_views.admin_product_edit, name="admin_product_edit"),
    path('admin/products/<int:product_id>/delete/', admin_views.admin_product_delete, name="admin_product_delete"),
    path('admin/products/<int:product_id>/variant/add/', admin_views.admin_variant_add, name="admin_variant_add"),
    path('admin/categories/', admin_views.admin_categories, name="admin_categories"),
    path('admin/shop/category/', admin_views.admin_categories),
    path('admin/shop/category/add/', admin_views.admin_categories),

    # Product Colors (Overriding old Django admin /admin/shop/productcolor/)
    path('admin/product-colors/', admin_views.admin_product_colors, name="admin_product_colors"),
    path('admin/shop/productcolor/', admin_views.admin_product_colors),
    path('admin/product-colors/create/', admin_views.admin_product_color_create, name="admin_product_color_create"),
    path('admin/shop/productcolor/add/', admin_views.admin_product_color_create),
    path('admin/product-colors/<int:color_id>/delete/', admin_views.admin_product_color_delete, name="admin_product_color_delete"),

    # Orders & Order Items
    path('admin/orders/', admin_views.admin_orders, name="admin_orders"),
    path('admin/shop/order/', admin_views.admin_orders),
    path('admin/order-items/', admin_views.admin_order_items, name="admin_order_items"),
    path('admin/shop/orderitem/', admin_views.admin_order_items),
    path('admin/shop/orderitem/add/', admin_views.admin_order_items),

    # Coupons (Overriding old Django admin /admin/shop/coupon/)
    path('admin/coupons/', admin_views.admin_coupons, name="admin_coupons"),
    path('admin/shop/coupon/', admin_views.admin_coupons),
    path('admin/coupons/create/', admin_views.admin_coupon_create, name="admin_coupon_create"),
    path('admin/shop/coupon/add/', admin_views.admin_coupon_create),
    path('admin/coupons/<int:coupon_id>/toggle/', admin_views.admin_coupon_toggle, name="admin_coupon_toggle"),
    path('admin/coupons/<int:coupon_id>/delete/', admin_views.admin_coupon_delete, name="admin_coupon_delete"),

    # Reviews (Overriding old Django admin /admin/shop/review/)
    path('admin/reviews/', admin_views.admin_reviews, name="admin_reviews"),
    path('admin/shop/review/', admin_views.admin_reviews),
    path('admin/shop/review/add/', admin_views.admin_reviews),
    path('admin/reviews/<int:review_id>/delete/', admin_views.admin_review_delete, name="admin_review_delete"),

    # Addresses (Overriding old Django admin /admin/shop/address/)
    path('admin/addresses/', admin_views.admin_addresses, name="admin_addresses"),
    path('admin/shop/address/', admin_views.admin_addresses),
    path('admin/shop/address/add/', admin_views.admin_addresses),

    # Carts (Overriding old Django admin /admin/shop/cart/)
    path('admin/carts/', admin_views.admin_carts, name="admin_carts"),
    path('admin/shop/cart/', admin_views.admin_carts),
    path('admin/carts/<int:cart_id>/delete/', admin_views.admin_cart_delete, name="admin_cart_delete"),

    # Wishlists (Overriding old Django admin /admin/shop/wishlist/)
    path('admin/wishlists/', admin_views.admin_wishlists, name="admin_wishlists"),
    path('admin/shop/wishlist/', admin_views.admin_wishlists),

    # Users, Support, Orders
    path('admin/users/', admin_views.admin_users, name="admin_users"),
    path('admin/auth/user/', admin_views.admin_users),
    path('admin/auth/group/', admin_views.admin_users),
    path('admin/support/', admin_views.admin_support, name="admin_support"),
    path('admin/shop/contactmessage/', admin_views.admin_support),
    path('admin/support/<int:message_id>/toggle/', admin_views.admin_support_toggle, name="admin_support_toggle"),
    path('admin/orders/<int:order_id>/status/', admin_views.admin_order_update_status, name="admin_order_update_status"),
    path('admin/dashboard/', admin_views.admin_orders, name="admin_dashboard"),
    path('admin/', admin_views.admin_orders, name="admin_orders"),

    # Django built-in admin site for models and auth (/admin/login/, /admin/logout/, /admin/shop/order/, etc.)
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
