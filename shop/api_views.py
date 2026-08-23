import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Q, Avg
from django.shortcuts import get_object_or_404

from .models import Category, Product, ProductColor, ProductImage, ProductColorImage, Cart, Wishlist, Address, Order, OrderItem, Review, Coupon
from .views import FREE_DELIVERY_THRESHOLD, DELIVERY_FEE


def _serialize_category(cat, include_children=True):
    data = {
        'id': cat.id,
        'name': cat.name,
        'slug': cat.slug,
        'description': cat.description,
        'image': cat.image.url if cat.image else None,
        'parent_id': cat.parent_id,
    }
    if include_children:
        data['subcategories'] = [
            _serialize_category(sub, include_children=False)
            for sub in cat.subcategories.filter(status=0)
        ]
    return data


def _serialize_product(p, full_details=False):
    cslug = p.category.slug if p.category else (p.categories.first().slug if p.categories.exists() else 'all')
    cname = p.category.name if p.category else (p.categories.first().name if p.categories.exists() else 'General')
    
    data = {
        'id': p.id,
        'name': p.name,
        'slug': p.slug,
        'brand': p.brand,
        'vendor': p.vendor,
        'category_name': cname,
        'category_slug': cslug,
        'product_image': p.product_image.url if p.product_image else None,
        'original_price': p.original_price,
        'selling_price': p.selling_price,
        'discount_percent': p.discount_percent,
        'quantity': p.quantity,
        'in_stock': p.in_stock,
        'trending': p.trending,
        'featured': p.featured,
        'is_bestseller': p.is_bestseller,
        'free_delivery': p.free_delivery,
        'avg_rating': p.avg_rating,
        'review_count': p.review_count,
        'created_at': p.created_at.isoformat() if p.created_at else None,
    }

    if full_details:
        data['description'] = p.description
        data['highlights'] = p.highlight_list

        # Color variants
        colors_list = []
        for c in p.colors.all():
            g_urls = [c.image.url] if c.image else []
            for g in c.images.all():
                if g.image and g.image.url not in g_urls:
                    g_urls.append(g.image.url)
            if len(g_urls) <= 1:
                for pg in p.gallery.all():
                    if pg.image and pg.image.url not in g_urls:
                        g_urls.append(pg.image.url)
            
            colors_list.append({
                'id': c.id,
                'name': c.name,
                'color_code': c.color_code,
                'image': c.image.url if c.image else (p.product_image.url if p.product_image else None),
                'price': c.effective_price,
                'original_price': c.effective_original_price,
                'discount_percent': c.discount_percent,
                'quantity': c.quantity,
                'in_stock': c.in_stock,
                'is_default': c.is_default,
                'gallery': g_urls,
            })
        data['colors'] = colors_list

        # Product gallery
        data['gallery'] = [g.image.url for g in p.gallery.all() if g.image]

        # Recent reviews
        data['reviews'] = [
            {
                'id': r.id,
                'username': r.user.username,
                'rating': r.rating,
                'title': r.title,
                'comment': r.comment,
                'created_at': r.created_at.strftime("%b %d, %Y") if r.created_at else None
            }
            for r in p.reviews.all()[:15]
        ]

    return data


# ==============================================================================
# Auth APIs
# ==============================================================================

@csrf_exempt
@require_http_methods(["POST"])
def api_auth_register(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return JsonResponse({'success': False, 'error': 'Username and password are required.'}, status=400)

    if User.objects.filter(username=username).exists():
        return JsonResponse({'success': False, 'error': 'Username already taken.'}, status=400)

    user = User.objects.create_user(username=username, email=email, password=password)
    login(request, user)
    return JsonResponse({
        'success': True,
        'message': 'Account created successfully!',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_auth_login(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return JsonResponse({
            'success': True,
            'message': 'Logged in successfully!',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        })
    return JsonResponse({'success': False, 'error': 'Invalid username or password.'}, status=401)


@csrf_exempt
@require_http_methods(["POST", "GET"])
def api_auth_logout(request):
    if request.user.is_authenticated:
        logout(request)
    return JsonResponse({'success': True, 'message': 'Logged out successfully.'})


def api_auth_user(request):
    if not request.user.is_authenticated:
        return JsonResponse({'authenticated': False, 'user': None})
    
    cart_count = sum(Cart.objects.filter(user=request.user).values_list('product_qty', flat=True)) or 0
    wishlist_count = Wishlist.objects.filter(user=request.user).count()
    orders_count = Order.objects.filter(user=request.user).count()
    addresses_count = Address.objects.filter(user=request.user).count()

    return JsonResponse({
        'authenticated': True,
        'user': {
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'cart_count': cart_count,
            'wishlist_count': wishlist_count,
            'orders_count': orders_count,
            'addresses_count': addresses_count,
        }
    })


# ==============================================================================
# Catalog APIs
# ==============================================================================

def api_categories_list(request):
    top_categories = Category.objects.filter(status=0, parent__isnull=True).prefetch_related('subcategories')
    return JsonResponse({
        'success': True,
        'categories': [_serialize_category(cat, include_children=True) for cat in top_categories]
    })


def api_category_detail(request, slug):
    cat = Category.objects.filter(slug=slug, status=0).first() or Category.objects.filter(name=slug, status=0).first()
    if not cat:
        return JsonResponse({'success': False, 'error': 'Category not found.'}, status=404)

    subcats = cat.subcategories.filter(status=0)
    subcat_ids = list(subcats.values_list('id', flat=True))
    all_cat_ids = [cat.id] + subcat_ids

    products_qs = Product.objects.filter(
        Q(category_id__in=all_cat_ids) | Q(categories__id__in=all_cat_ids),
        status=0
    ).distinct()

    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products_qs = products_qs.filter(selling_price__gte=min_price)
    if max_price:
        products_qs = products_qs.filter(selling_price__lte=max_price)

    sort = request.GET.get('sort', '')
    if sort == 'price_low':
        products_qs = products_qs.order_by('selling_price')
    elif sort == 'price_high':
        products_qs = products_qs.order_by('-selling_price')
    elif sort == 'newest':
        products_qs = products_qs.order_by('-created_at')

    return JsonResponse({
        'success': True,
        'category': _serialize_category(cat, include_children=True),
        'subcategories': [_serialize_category(s, include_children=False) for s in subcats],
        'products': [_serialize_product(p) for p in products_qs]
    })


def api_products_list(request):
    qs = Product.objects.filter(status=0)

    if request.GET.get('trending') == '1':
        qs = qs.filter(trending=True)
    if request.GET.get('featured') == '1':
        qs = qs.filter(featured=True)
    if request.GET.get('bestseller') == '1':
        qs = qs.filter(is_bestseller=True)

    category_slug = request.GET.get('category')
    if category_slug:
        qs = qs.filter(Q(category__slug=category_slug) | Q(categories__slug=category_slug)).distinct()

    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        qs = qs.filter(selling_price__gte=min_price)
    if max_price:
        qs = qs.filter(selling_price__lte=max_price)

    sort = request.GET.get('sort')
    if sort == 'price_low':
        qs = qs.order_by('selling_price')
    elif sort == 'price_high':
        qs = qs.order_by('-selling_price')
    elif sort == 'newest':
        qs = qs.order_by('-created_at')

    limit = request.GET.get('limit')
    if limit and limit.isdigit():
        qs = qs[:int(limit)]

    return JsonResponse({
        'success': True,
        'count': len(qs) if isinstance(qs, list) else qs.count(),
        'products': [_serialize_product(p) for p in qs]
    })


def api_product_detail(request, slug):
    p = Product.objects.filter(slug=slug, status=0).first() or (Product.objects.filter(pk=slug, status=0).first() if slug.isdigit() else None)
    if not p:
        return JsonResponse({'success': False, 'error': 'Product not found.'}, status=404)

    related = Product.objects.filter(
        Q(category=p.category) | Q(categories=p.category),
        status=0
    ).exclude(pk=p.pk).distinct()[:6]

    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(user=request.user, product=p).exists()

    return JsonResponse({
        'success': True,
        'product': _serialize_product(p, full_details=True),
        'in_wishlist': in_wishlist,
        'related_products': [_serialize_product(r) for r in related]
    })


def api_search(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'success': True, 'count': 0, 'products': []})

    results = Product.objects.filter(
        Q(name__icontains=query) | Q(description__icontains=query) |
        Q(brand__icontains=query) | Q(category__name__icontains=query),
        status=0
    ).distinct()

    return JsonResponse({
        'success': True,
        'query': query,
        'count': results.count(),
        'products': [_serialize_product(p) for p in results[:30]]
    })


# ==============================================================================
# Cart APIs
# ==============================================================================

def _get_cart_payload(user):
    items = Cart.objects.filter(user=user).select_related('product', 'color')
    items_data = []
    subtotal = 0

    for item in items:
        unit_price = item.unit_price
        total_price = item.total_price
        subtotal += total_price
        color_img = item.color.image.url if item.color and item.color.image else None
        prod_img = item.product.product_image.url if item.product.product_image else None

        items_data.append({
            'id': item.id,
            'product_id': item.product.id,
            'product_name': item.product.name,
            'product_slug': item.product.slug,
            'image': color_img or prod_img,
            'color_id': item.color.id if item.color else None,
            'color_name': item.color.name if item.color else None,
            'color_code': item.color.color_code if item.color else None,
            'quantity': item.product_qty,
            'unit_price': unit_price,
            'total_price': total_price,
            'stock': item.color.quantity if item.color else item.product.quantity,
        })

    delivery_fee = 0 if subtotal >= FREE_DELIVERY_THRESHOLD or subtotal == 0 else DELIVERY_FEE
    grand_total = subtotal + delivery_fee

    return {
        'items': items_data,
        'total_items_count': sum(i['quantity'] for i in items_data),
        'subtotal': round(subtotal, 2),
        'delivery_fee': delivery_fee,
        'free_delivery_threshold': FREE_DELIVERY_THRESHOLD,
        'amount_needed_for_free_delivery': max(0, FREE_DELIVERY_THRESHOLD - subtotal) if subtotal > 0 else FREE_DELIVERY_THRESHOLD,
        'grand_total': round(grand_total, 2),
    }


def api_cart_list(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Login required.'}, status=401)

    return JsonResponse({
        'success': True,
        'cart': _get_cart_payload(request.user)
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_cart_add(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Login required.'}, status=401)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    product_id = data.get('product_id')
    color_id = data.get('color_id')
    qty = int(data.get('quantity', 1))

    if not product_id:
        return JsonResponse({'success': False, 'error': 'Product ID is required.'}, status=400)

    product = get_object_or_404(Product, pk=product_id, status=0)
    color = None
    if color_id:
        color = ProductColor.objects.filter(pk=color_id, product=product).first()
    if not color and product.colors.exists():
        color = product.colors.filter(is_default=True).first() or product.colors.first()

    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        product=product,
        color=color,
        defaults={'product_qty': qty}
    )
    if not created:
        cart_item.product_qty += qty
        cart_item.save()

    return JsonResponse({
        'success': True,
        'message': f"Added '{product.name}' to cart.",
        'cart': _get_cart_payload(request.user)
    })


@csrf_exempt
@require_http_methods(["POST", "PUT"])
def api_cart_update(request, item_id):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Login required.'}, status=401)

    item = get_object_or_404(Cart, pk=item_id, user=request.user)
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    action = data.get('action')
    quantity = data.get('quantity')

    if action == 'increase':
        item.product_qty += 1
        item.save()
    elif action == 'decrease':
        item.product_qty -= 1
        if item.product_qty <= 0:
            item.delete()
        else:
            item.save()
    elif quantity is not None:
        new_qty = int(quantity)
        if new_qty <= 0:
            item.delete()
        else:
            item.product_qty = new_qty
            item.save()

    return JsonResponse({
        'success': True,
        'message': 'Cart updated.',
        'cart': _get_cart_payload(request.user)
    })


@csrf_exempt
@require_http_methods(["POST", "DELETE"])
def api_cart_remove(request, item_id):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Login required.'}, status=401)

    Cart.objects.filter(pk=item_id, user=request.user).delete()
    return JsonResponse({
        'success': True,
        'message': 'Item removed from cart.',
        'cart': _get_cart_payload(request.user)
    })


# ==============================================================================
# Wishlist APIs
# ==============================================================================

def api_wishlist_list(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Login required.'}, status=401)

    items = Wishlist.objects.filter(user=request.user).select_related('product')
    return JsonResponse({
        'success': True,
        'count': items.count(),
        'items': [
            {
                'id': w.id,
                'product': _serialize_product(w.product),
                'created_at': w.created_at.isoformat()
            }
            for w in items
        ]
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_wishlist_toggle(request, product_id):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Login required.'}, status=401)

    product = get_object_or_404(Product, pk=product_id)
    obj, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    
    if not created:
        obj.delete()
        in_wishlist = False
        message = f"Removed '{product.name}' from wishlist."
    else:
        in_wishlist = True
        message = f"Added '{product.name}' to wishlist."

    count = Wishlist.objects.filter(user=request.user).count()

    return JsonResponse({
        'success': True,
        'in_wishlist': in_wishlist,
        'wishlist_count': count,
        'message': message
    })


# ==============================================================================
# Address APIs
# ==============================================================================

def api_address_list(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Login required.'}, status=401)

    addresses = Address.objects.filter(user=request.user).order_by('-is_default', '-created_at')
    return JsonResponse({
        'success': True,
        'addresses': [
            {
                'id': a.id,
                'full_name': a.full_name,
                'phone': a.phone,
                'address_line': a.address_line,
                'city': a.city,
                'state': a.state,
                'pincode': a.pincode,
                'is_default': a.is_default,
            }
            for a in addresses
        ]
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_address_create(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Login required.'}, status=401)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    full_name = data.get('full_name', '').strip()
    phone = data.get('phone', '').strip()
    address_line = data.get('address_line', '').strip()
    city = data.get('city', '').strip()
    state = data.get('state', '').strip()
    pincode = data.get('pincode', '').strip()
    is_default = bool(data.get('is_default', False))

    if not all([full_name, phone, address_line, city, state, pincode]):
        return JsonResponse({'success': False, 'error': 'All address fields are required.'}, status=400)

    if is_default:
        Address.objects.filter(user=request.user).update(is_default=False)

    address = Address.objects.create(
        user=request.user,
        full_name=full_name,
        phone=phone,
        address_line=address_line,
        city=city,
        state=state,
        pincode=pincode,
        is_default=is_default or not Address.objects.filter(user=request.user).exists()
    )

    return JsonResponse({
        'success': True,
        'message': 'Address saved successfully!',
        'address': {
            'id': address.id,
            'full_name': address.full_name,
            'phone': address.phone,
            'address_line': address.address_line,
            'city': address.city,
            'state': address.state,
            'pincode': address.pincode,
            'is_default': address.is_default,
        }
    })


# ==============================================================================
# Orders & Checkout APIs
# ==============================================================================

@csrf_exempt
@require_http_methods(["POST"])
def api_order_create(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Login required.'}, status=401)

    items = Cart.objects.filter(user=request.user).select_related('product', 'color')
    if not items.exists():
        return JsonResponse({'success': False, 'error': 'Your cart is empty.'}, status=400)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    address_id = data.get('address_id')
    payment_method = data.get('payment_method', 'cod')

    address = Address.objects.filter(pk=address_id, user=request.user).first()
    if not address:
        # Fallback to default address if none provided
        address = Address.objects.filter(user=request.user, is_default=True).first() or Address.objects.filter(user=request.user).first()
        if not address:
            return JsonResponse({'success': False, 'error': 'Please select or add a delivery address.'}, status=400)

    subtotal = sum(item.total_price for item in items)
    delivery_fee = 0 if subtotal >= FREE_DELIVERY_THRESHOLD else DELIVERY_FEE
    total = subtotal + delivery_fee

    order = Order.objects.create(
        user=request.user,
        address=address,
        payment_method=payment_method,
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        total_amount=total,
    )

    for item in items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            product_name=item.product.name,
            color_name=item.color.name if item.color else '',
            color_code=item.color.color_code if item.color else '',
            quantity=item.product_qty,
            price=item.unit_price,
        )

    # Empty cart
    items.delete()

    return JsonResponse({
        'success': True,
        'message': 'Order placed successfully!',
        'order_id': order.id,
        'order': {
            'id': order.id,
            'total_amount': order.total_amount,
            'payment_method': order.payment_method,
            'status': order.status,
            'created_at': order.created_at.strftime("%b %d, %Y, %I:%M %p")
        }
    })


def api_orders_list(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Login required.'}, status=401)

    orders = Order.objects.filter(user=request.user).prefetch_related('items').order_by('-created_at')
    orders_data = []

    for o in orders:
        orders_data.append({
            'id': o.id,
            'status': o.status,
            'status_display': o.get_status_display(),
            'payment_method': o.get_payment_method_display(),
            'subtotal': o.subtotal,
            'delivery_fee': o.delivery_fee,
            'total_amount': o.total_amount,
            'created_at': o.created_at.strftime("%b %d, %Y, %I:%M %p"),
            'items_count': o.items.count(),
            'items': [
                {
                    'id': it.id,
                    'product_name': it.product_name,
                    'color_name': it.color_name,
                    'color_code': it.color_code,
                    'quantity': it.quantity,
                    'price': it.price,
                    'total_price': it.total_price,
                }
                for it in o.items.all()
            ]
        })

    return JsonResponse({
        'success': True,
        'count': len(orders_data),
        'orders': orders_data
    })


def api_order_detail(request, order_id):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Login required.'}, status=401)

    order = get_object_or_404(Order, pk=order_id, user=request.user)

    return JsonResponse({
        'success': True,
        'order': {
            'id': order.id,
            'status': order.status,
            'status_display': order.get_status_display(),
            'payment_method': order.get_payment_method_display(),
            'subtotal': order.subtotal,
            'delivery_fee': order.delivery_fee,
            'total_amount': order.total_amount,
            'created_at': order.created_at.strftime("%b %d, %Y, %I:%M %p"),
            'address': {
                'full_name': order.address.full_name if order.address else 'N/A',
                'phone': order.address.phone if order.address else 'N/A',
                'address_line': order.address.address_line if order.address else 'N/A',
                'city': order.address.city if order.address else 'N/A',
                'state': order.address.state if order.address else 'N/A',
                'pincode': order.address.pincode if order.address else 'N/A',
            },
            'items': [
                {
                    'id': it.id,
                    'product_name': it.product_name,
                    'color_name': it.color_name,
                    'color_code': it.color_code,
                    'quantity': it.quantity,
                    'price': it.price,
                    'total_price': it.total_price,
                }
                for it in order.items.all()
            ]
        }
    })


# ==============================================================================
# Coupon APIs
# ==============================================================================

def api_coupon_list(request):
    coupons = Coupon.objects.filter(active=True)
    return JsonResponse({
        'success': True,
        'coupons': [
            {
                'id': c.id,
                'code': c.code,
                'discount_type': c.discount_type,
                'discount_value': c.discount_value,
                'min_order_amount': c.min_order_amount,
                'max_discount': c.max_discount,
                'description': c.description,
            }
            for c in coupons
        ]
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_coupon_apply(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Login required.'}, status=401)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    code = data.get('coupon_code', '').strip().upper()
    if not code:
        return JsonResponse({'success': False, 'error': 'Coupon code is required.'}, status=400)

    coupon = Coupon.objects.filter(code__iexact=code, active=True).first()
    if not coupon:
        return JsonResponse({'success': False, 'error': f"Coupon '{code}' is invalid or expired."}, status=400)

    items = Cart.objects.filter(user=request.user)
    subtotal = sum(item.total_price for item in items)

    if subtotal < coupon.min_order_amount:
        return JsonResponse({
            'success': False,
            'error': f"Coupon requires a minimum order subtotal of ₹{int(coupon.min_order_amount)}."
        }, status=400)

    discount = coupon.calculate_discount(subtotal)
    request.session['coupon_code'] = coupon.code
    request.session.modified = True

    return JsonResponse({
        'success': True,
        'message': f"Coupon '{coupon.code}' applied successfully!",
        'coupon': {
            'code': coupon.code,
            'discount_amount': discount,
            'description': coupon.description
        },
        'cart': _get_cart_payload(request.user)
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_coupon_remove(request):
    if 'coupon_code' in request.session:
        del request.session['coupon_code']
        request.session.modified = True

    return JsonResponse({
        'success': True,
        'message': 'Coupon removed.',
        'cart': _get_cart_payload(request.user) if request.user.is_authenticated else None
    })


def api_search_autocomplete(request):
    query = request.GET.get('q', '').strip()
    if not query or len(query) < 2:
        return JsonResponse({'results': []})

    products = Product.objects.filter(
        Q(name__icontains=query) | Q(brand__icontains=query) | Q(category__name__icontains=query),
        status=0
    )[:6]

    results = []
    for p in products:
        results.append({
            'id': p.id,
            'name': p.name,
            'slug': p.slug,
            'brand': p.brand,
            'price': p.selling_price,
            'image': p.product_image.url if p.product_image else '',
            'rating': p.avg_rating,
        })
    return JsonResponse({'results': results})


@csrf_exempt
@require_http_methods(["POST"])
def api_profile_update(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Login required.'}, status=401)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    email = data.get('email', '').strip()

    user = request.user
    if first_name is not None:
        user.first_name = first_name
    if last_name is not None:
        user.last_name = last_name
    if email:
        user.email = email
    user.save()

    return JsonResponse({
        'success': True,
        'message': 'Profile updated successfully!',
        'user': {
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email
        }
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_review_create(request, product_id):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Login required.'}, status=401)

    product = get_object_or_404(Product, pk=product_id)
    if Review.objects.filter(user=request.user, product=product).exists():
        return JsonResponse({'success': False, 'error': 'You have already reviewed this product.'}, status=400)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    rating = int(data.get('rating', 5))
    title = data.get('title', '').strip()
    comment = data.get('comment', '').strip()

    review = Review.objects.create(
        user=request.user,
        product=product,
        rating=rating,
        title=title,
        comment=comment
    )

    return JsonResponse({
        'success': True,
        'message': 'Review submitted successfully!',
        'review': {
            'id': review.id,
            'username': request.user.username,
            'rating': review.rating,
            'title': review.title,
            'comment': review.comment,
            'created_at': review.created_at.strftime("%b %d, %Y")
        }
    })

