from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('search', views.search, name="search"),

    path('register', views.register, name="register"),
    path('login', views.login_page, name="login"),
    path('logout', views.logout_page, name="logout"),

    path('collections', views.collections, name="collections"),
    path('collections/<str:name>', views.collectionsview, name="collections_view"),
    path('collections/<str:cname>/<str:pname>', views.product_details, name="product_details"),

    path('cart', views.cart_view, name="cart"),
    path('cart/add/<int:product_id>', views.add_to_cart, name="add_to_cart"),
    path('cart/update/<int:item_id>', views.update_cart, name="update_cart"),
    path('cart/remove/<int:item_id>', views.remove_from_cart, name="remove_from_cart"),

    path('wishlist', views.wishlist_view, name="wishlist"),
    path('wishlist/toggle/<int:product_id>', views.toggle_wishlist, name="toggle_wishlist"),

    path('checkout', views.checkout, name="checkout"),
    path('checkout/add-address', views.add_address, name="add_address"),
    path('order/success/<int:order_id>', views.order_success, name="order_success"),
    path('orders', views.my_orders, name="my_orders"),
    path('orders/<int:order_id>', views.order_detail, name="order_detail"),
    path('category/<slug:slug>/',views.category_detail,name='category_detail')
]
