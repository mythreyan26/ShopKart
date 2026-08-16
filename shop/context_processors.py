from .models import Cart, Wishlist, Category


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
