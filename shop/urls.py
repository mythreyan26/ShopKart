from django.urls import path
from . import views
from . import admin_views

urlpatterns = [
    path('', views.home, name="home"),
    path('search', views.search, name="search"),
    path('search/autocomplete', views.search_autocomplete, name="search_autocomplete"),

    path('register', views.register, name="register"),
    path('login', views.login_page, name="login"),
    path('logout', views.logout_page, name="logout"),
    path('profile', views.profile_view, name="profile"),
    path('profile/update', views.update_profile, name="update_profile"),
    path('profile/change-password', views.change_password, name="change_password"),

    path('collections', views.collections, name="collections"),
    path('collections/<str:name>', views.collectionsview, name="collections_view"),
    path('collections/<str:cname>/<str:pname>', views.product_details, name="product_details"),

    path('cart', views.cart_view, name="cart"),
    path('cart/add/<int:product_id>', views.add_to_cart, name="add_to_cart"),
    path('cart/update/<int:item_id>', views.update_cart, name="update_cart"),
    path('cart/remove/<int:item_id>', views.remove_from_cart, name="remove_from_cart"),
    path('cart/clear', views.clear_cart, name="clear_cart"),
    path('cart/move-to-wishlist/<int:item_id>', views.move_to_wishlist, name="move_to_wishlist"),
    path('coupon/apply', views.apply_coupon, name="apply_coupon"),
    path('coupon/remove', views.remove_coupon, name="remove_coupon"),

    path('wishlist', views.wishlist_view, name="wishlist"),
    path('wishlist/toggle/<int:product_id>', views.toggle_wishlist, name="toggle_wishlist"),
    path('wishlist/move-to-cart/<int:product_id>', views.move_to_cart, name="move_to_cart"),

    path('checkout', views.checkout, name="checkout"),
    path('checkout/add-address', views.add_address, name="add_address"),
    path('address/edit/<int:address_id>', views.edit_address, name="edit_address"),
    path('address/delete/<int:address_id>', views.delete_address, name="delete_address"),
    path('address/default/<int:address_id>', views.set_default_address, name="set_default_address"),

    path('order/success/<int:order_id>', views.order_success, name="order_success"),
    path('orders', views.my_orders, name="my_orders"),
    path('orders/<int:order_id>', views.order_detail, name="order_detail"),
    path('orders/<int:order_id>/cancel', views.cancel_order, name="cancel_order"),
    path('orders/item/<int:item_id>/cancel', views.cancel_order_item, name="cancel_order_item"),
    path('orders/<int:order_id>/reorder', views.reorder, name="reorder"),
    path('orders/<int:order_id>/invoice', views.invoice_view, name="invoice"),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),

    # Info & Legal pages
    path('about', views.about_us, name="about"),
    path('contact', views.contact_us, name="contact"),
    path('faq', views.faq, name="faq"),
    path('returns-policy', views.returns_policy, name="returns_policy"),
    path('terms', views.terms_of_service, name="terms"),
    path('privacy', views.privacy_policy, name="privacy"),

    # ==============================================================================
    # Custom SaaS Admin Portal (Matching Reference Design)
    # ==============================================================================
    path('panel/', admin_views.admin_dashboard_redirect, name="admin_panel_root"),
    path('panel/orders/', admin_views.admin_orders, name="admin_orders"),
    path('panel/orders/<int:order_id>/status/', admin_views.admin_order_update_status, name="admin_order_update_status"),
    path('panel/products/', admin_views.admin_products, name="admin_products"),
    path('panel/products/create/', admin_views.admin_product_create, name="admin_product_create"),
    path('panel/products/<int:product_id>/edit/', admin_views.admin_product_edit, name="admin_product_edit"),
    path('panel/products/<int:product_id>/delete/', admin_views.admin_product_delete, name="admin_product_delete"),
    path('panel/products/<int:product_id>/variant/add/', admin_views.admin_variant_add, name="admin_variant_add"),
    path('panel/categories/', admin_views.admin_categories, name="admin_categories"),
    path('panel/users/', admin_views.admin_users, name="admin_users"),
    path('panel/support/', admin_views.admin_support, name="admin_support"),
    path('panel/support/<int:message_id>/toggle/', admin_views.admin_support_toggle, name="admin_support_toggle"),
]
