import datetime
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Sum, Q, Count, F
from .models import Cart, Wishlist, Category, Product, Order, OrderItem, Review, Coupon, ContactMessage


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
    if request.path.startswith('/admin/login') or not (request.path.startswith('/admin') or request.path.startswith('/panel')):
        return {}

    # Real Revenue & Orders metrics
    non_cancelled_orders = Order.objects.exclude(status='cancelled')
    total_revenue = non_cancelled_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0.0
    active_orders_count = non_cancelled_orders.count()
    total_orders_count = Order.objects.count()

    orders_placed_count = Order.objects.filter(status='placed').count()
    orders_confirmed_count = Order.objects.filter(status='confirmed').count()
    orders_shipped_count = Order.objects.filter(status='shipped').count()
    orders_delivered_count = Order.objects.filter(status='delivered').count()
    orders_cancelled_count = Order.objects.filter(status='cancelled').count()

    # Average Order Value (AOV)
    avg_order_value = round(total_revenue / active_orders_count, 2) if active_orders_count > 0 else 0.0
    total_revenue_display = f"₹{int(total_revenue):,}"
    avg_order_value_display = f"₹{int(avg_order_value):,}"

    # Real 7-Day Revenue & Orders Trend
    today = timezone.now().date()
    seven_days_ago = today - datetime.timedelta(days=6)
    daily_sales = []
    daily_revenue_list = []

    for i in range(7):
        day_date = seven_days_ago + datetime.timedelta(days=i)
        day_orders = Order.objects.filter(created_at__date=day_date).exclude(status='cancelled')
        day_rev = float(day_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0.0)
        daily_revenue_list.append(day_rev)
        daily_sales.append({
            'date': day_date.strftime('%b %d'),
            'day': day_date.strftime('%a'),
            'revenue': day_rev,
            'revenue_display': f"₹{int(day_rev):,}" if day_rev > 0 else "₹0",
            'orders_count': day_orders.count(),
        })

    max_revenue = max(daily_revenue_list) if daily_revenue_list and max(daily_revenue_list) > 0 else 100.0
    for day in daily_sales:
        day['height_percent'] = max(int((day['revenue'] / max_revenue) * 100), 8) if day['revenue'] > 0 else 4

    # Catalog & Inventory
    active_products_count = Product.objects.filter(status=False).count()
    total_categories_count = Category.objects.count()
    low_stock_products = Product.objects.filter(quantity__lte=5, status=False)[:6]
    low_stock_products_count = Product.objects.filter(quantity__lte=5, status=False).count()
    out_of_stock_count = Product.objects.filter(quantity=0, status=False).count()

    # Top Selling Products (Real Data)
    top_selling_products = list(
        OrderItem.objects.values('product_name').annotate(
            total_qty=Sum('quantity')
        ).order_by('-total_qty')[:5]
    )

    # Customers & Social Proof
    total_customers_count = User.objects.filter(is_staff=False).count() or User.objects.count()
    total_reviews_count = Review.objects.count()
    active_coupons_count = Coupon.objects.filter(active=True).count()
    unresolved_tickets_count = ContactMessage.objects.filter(is_resolved=False).count()

    # Recent Data
    recent_orders = Order.objects.select_related('user', 'address').prefetch_related('items').order_by('-created_at')[:8]
    featured_products = Product.objects.filter(Q(trending=True) | Q(featured=True), status=False)[:6]

    return {
        'admin_kpi': {
            'total_revenue': total_revenue,
            'total_revenue_display': total_revenue_display,
            'avg_order_value': avg_order_value,
            'avg_order_value_display': avg_order_value_display,
            'active_orders_count': active_orders_count,
            'total_orders_count': total_orders_count,
            'orders_placed_count': orders_placed_count,
            'orders_confirmed_count': orders_confirmed_count,
            'orders_shipped_count': orders_shipped_count,
            'orders_delivered_count': orders_delivered_count,
            'orders_cancelled_count': orders_cancelled_count,
            'active_products_count': active_products_count,
            'total_categories_count': total_categories_count,
            'low_stock_products': low_stock_products,
            'low_stock_products_count': low_stock_products_count,
            'out_of_stock_count': out_of_stock_count,
            'top_selling_products': top_selling_products,
            'total_customers_count': total_customers_count,
            'total_reviews_count': total_reviews_count,
            'active_coupons_count': active_coupons_count,
            'unresolved_tickets_count': unresolved_tickets_count,
            'daily_sales': daily_sales,
            'max_revenue': max_revenue,
            'recent_orders': recent_orders,
            'featured_products': featured_products,
        }
    }
