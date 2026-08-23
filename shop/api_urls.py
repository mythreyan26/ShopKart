from django.urls import path
from . import api_views

urlpatterns = [
    # Auth & Profile
    path('auth/register/', api_views.api_auth_register, name='api_auth_register'),
    path('auth/login/', api_views.api_auth_login, name='api_auth_login'),
    path('auth/logout/', api_views.api_auth_logout, name='api_auth_logout'),
    path('auth/user/', api_views.api_auth_user, name='api_auth_user'),
    path('auth/profile/update/', api_views.api_profile_update, name='api_profile_update'),

    # Catalog & Products
    path('categories/', api_views.api_categories_list, name='api_categories_list'),
    path('categories/<slug:slug>/', api_views.api_category_detail, name='api_category_detail'),
    path('products/', api_views.api_products_list, name='api_products_list'),
    path('products/<str:slug>/', api_views.api_product_detail, name='api_product_detail'),
    path('search/', api_views.api_search, name='api_search'),
    path('search/autocomplete/', api_views.api_search_autocomplete, name='api_search_autocomplete'),

    # Cart
    path('cart/', api_views.api_cart_list, name='api_cart_list'),
    path('cart/add/', api_views.api_cart_add, name='api_cart_add'),
    path('cart/update/<int:item_id>/', api_views.api_cart_update, name='api_cart_update'),
    path('cart/remove/<int:item_id>/', api_views.api_cart_remove, name='api_cart_remove'),

    # Coupons
    path('coupons/', api_views.api_coupon_list, name='api_coupon_list'),
    path('coupons/apply/', api_views.api_coupon_apply, name='api_coupon_apply'),
    path('coupons/remove/', api_views.api_coupon_remove, name='api_coupon_remove'),

    # Wishlist
    path('wishlist/', api_views.api_wishlist_list, name='api_wishlist_list'),
    path('wishlist/toggle/<int:product_id>/', api_views.api_wishlist_toggle, name='api_wishlist_toggle'),

    # Addresses
    path('addresses/', api_views.api_address_list, name='api_address_list'),
    path('addresses/create/', api_views.api_address_create, name='api_address_create'),

    # Orders & Checkout
    path('orders/', api_views.api_orders_list, name='api_orders_list'),
    path('orders/create/', api_views.api_order_create, name='api_order_create'),
    path('orders/<int:order_id>/', api_views.api_order_detail, name='api_order_detail'),

    # Reviews
    path('products/<int:product_id>/reviews/create/', api_views.api_review_create, name='api_review_create'),
]
