from django.contrib.auth.models import User
from django.db.models import Sum, Q
from .models import Cart, Wishlist, Category, Product, Order, Review


def cart_context(request):
    cart_count = 0
    wishlist_count = 0
    wishlist_ids = []
    if request.user.is_authenticated:
        cart_count = sum(Cart.objects.filter(user=request.user).values_list('product_qty', flat=True)) or 0
        wishlist_ids = list(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))
        wishlist_count = len(wishlist_ids)
    nav_categories = Category.objects.filter(
        status=0,
        parent__isnull=True
    ).prefetch_related('subcategories')
    return {
        'cart_count': cart_count,
        'wishlist_count': wishlist_count,
        'wishlist_ids': wishlist_ids,
        'nav_categories': nav_categories,
    }


def admin_dashboard_context(request):
    if not request.path.startswith('/admin'):
        return {}

    total_revenue = Order.objects.exclude(status='cancelled').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    orders_placed_count = Order.objects.filter(status='placed').count()
    orders_shipped_count = Order.objects.filter(status='shipped').count()
    orders_delivered_count = Order.objects.filter(status='delivered').count()
    total_orders_count = Order.objects.count()

    active_products_count = Product.objects.filter(status=False).count()
    total_categories_count = Category.objects.count()
    low_stock_products = Product.objects.filter(quantity__lte=5, status=False)[:6]
    low_stock_products_count = Product.objects.filter(quantity__lte=5, status=False).count()

    total_customers_count = User.objects.filter(is_staff=False).count() or User.objects.count()
    total_reviews_count = Review.objects.count()

    recent_orders = Order.objects.select_related('user', 'address').prefetch_related('items').order_by('-created_at')[:6]
    featured_products = Product.objects.filter(Q(trending=True) | Q(featured=True), status=False)[:6]

    return {
        'admin_kpi': {
            'total_revenue': total_revenue,
            'orders_placed_count': orders_placed_count,
            'orders_shipped_count': orders_shipped_count,
            'orders_delivered_count': orders_delivered_count,
            'total_orders_count': total_orders_count,
            'active_products_count': active_products_count,
            'total_categories_count': total_categories_count,
            'low_stock_products_count': low_stock_products_count,
            'total_customers_count': total_customers_count,
            'total_reviews_count': total_reviews_count,
            'recent_orders': recent_orders,
            'featured_products': featured_products,
            'low_stock_products': low_stock_products,
        }
    }
