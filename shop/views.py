import json
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Avg
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import Category, Product, ProductColor, ProductColorImage, Cart, Wishlist, Review, Address, Order, OrderItem, Coupon
from .form import CustomUserForm, AddressForm, ReviewForm

FREE_DELIVERY_THRESHOLD = 499
DELIVERY_FEE = 40


# ---------- Storefront ----------

def home(request):
    trending = Product.objects.filter(status=0, trending=1)[:8]
    featured = Product.objects.filter(status=0, featured=1)[:8]
    bestsellers = Product.objects.filter(status=0, is_bestseller=1)[:8]
    categories = Category.objects.filter(status=0, parent__isnull=True)[:8]
    return render(request, "shop/index.html", {
        "products": trending,
        "featured": featured,
        "bestsellers": bestsellers,
        "categories": categories,
    })


def search(request):
    query = request.GET.get('q', '').strip()
    results = Product.objects.filter(status=0)
    if query:
        results = results.filter(
            Q(name__icontains=query) | Q(description__icontains=query) |
            Q(brand__icontains=query) | Q(category__name__icontains=query)
        )
    return render(request, "shop/search.html", {"products": results, "query": query})


def search_autocomplete(request):
    query = request.GET.get('q', '').strip()
    if not query or len(query) < 2:
        return JsonResponse({'results': []})

    products = Product.objects.filter(
        Q(name__icontains=query) | Q(brand__icontains=query) | Q(category__name__icontains=query),
        status=0
    )[:6]

    results = []
    for p in products:
        cslug = p.category.slug if p.category else (p.categories.first().slug if p.categories.exists() else 'all')
        results.append({
            'id': p.id,
            'name': p.name,
            'brand': p.brand,
            'price': int(p.selling_price),
            'original_price': int(p.original_price) if p.original_price else None,
            'discount': p.discount_percent,
            'image': p.product_image.url if p.product_image else '',
            'url': reverse('product_details', args=[cslug, p.slug]),
            'rating': p.avg_rating,
        })
    return JsonResponse({'results': results})


def collections(request):
    categories = Category.objects.filter(
        status=0,
        parent__isnull=True
    )
    return render(
        request,
        "shop/collections.html",
        {"catagory": categories}
    )

def category_detail(request, slug):
    category = Category.objects.filter(slug=slug, status=0).first() or Category.objects.filter(name=slug, status=0).first()
    if not category:
        messages.warning(request, "No such category found!")
        return redirect('collections')

    subcategories = category.subcategories.filter(status=0)

    # If this category has subcategories, display ONLY subcategories
    if subcategories.exists():
        return render(request, "shop/category_detail.html", {
            "category": category,
            "subcategories": subcategories,
        })

    # If it is a leaf subcategory, display its products
    return collectionsview(request, slug)


def collectionsview(request, name):
    category = Category.objects.filter(slug=name, status=0).first() or Category.objects.filter(name=name, status=0).first()
    if not category:
        messages.warning(request, "No such category found!")
        return redirect('collections')

    subcategories = category.subcategories.filter(status=0)

    # If category has subcategories and no filter query params, display ONLY subcategories
    if subcategories.exists() and not request.GET.get('min_price') and not request.GET.get('max_price') and not request.GET.get('sort'):
        return render(request, "shop/category_detail.html", {
            "category": category,
            "subcategories": subcategories,
        })

    subcat_ids = list(subcategories.values_list('id', flat=True))
    all_cat_ids = [category.id] + subcat_ids

    products = Product.objects.filter(
        Q(category_id__in=all_cat_ids) | Q(categories__id__in=all_cat_ids),
        status=0
    ).distinct()

    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(selling_price__gte=min_price)
    if max_price:
        products = products.filter(selling_price__lte=max_price)

    sort = request.GET.get('sort', '')
    if sort == 'price_low':
        products = products.order_by('selling_price')
    elif sort == 'price_high':
        products = products.order_by('-selling_price')
    elif sort == 'newest':
        products = products.order_by('-created_at')

    # Sibling subcategories if this is a subcategory
    sibling_subcategories = []
    if category.parent:
        sibling_subcategories = category.parent.subcategories.filter(status=0)

    return render(request, "shop/products/index.html", {
        "products": products,
        "category": category,
        "category_name": category.name,
        "subcategories": subcategories,
        "sibling_subcategories": sibling_subcategories,
        "sort": sort,
    })


def product_details(request, cname, pname):
    # Check if the URL is actually a subcategory like /collections/electronics/mobiles
    subcat_check = Category.objects.filter(Q(slug=pname) | Q(name=pname), status=0).first()
    if subcat_check:
        return collectionsview(request, pname)

    category = Category.objects.filter(slug=cname, status=0).first() or Category.objects.filter(name=cname, status=0).first()
    
    product = Product.objects.filter(slug=pname, status=0).first() or Product.objects.filter(name=pname, status=0).first()
    if not product:
        messages.error(request, "No such product found")
        return redirect('collections')

    if not category:
        category = product.category or product.categories.first()

    related = Product.objects.filter(
        Q(category=category) | Q(categories=category),
        status=0
    ).exclude(pk=product.pk).distinct()[:4]
    reviews = product.reviews.all()[:20]
    in_wishlist = False
    already_reviewed = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()
        already_reviewed = Review.objects.filter(user=request.user, product=product).exists()

    if request.method == 'POST' and request.user.is_authenticated:
        form = ReviewForm(request.POST)
        if form.is_valid() and not already_reviewed:
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, "Thanks! Your review has been posted.")
            return redirect('product_details', cname, pname)
    else:
        form = ReviewForm()

    # Preload and serialize colors & their gallery images
    colors_qs = list(product.colors.prefetch_related('images').all())
    colors_data = []
    default_color = None

    for c in colors_qs:
        gallery_urls = []
        if c.image:
            gallery_urls.append(c.image.url)
        for g_img in c.images.all():
            if g_img.image and g_img.image.url not in gallery_urls:
                gallery_urls.append(g_img.image.url)

        # If this color only has its main image, also include product gallery
        if len(gallery_urls) <= 1:
            for pg in product.gallery.all():
                if pg.image and pg.image.url not in gallery_urls:
                    gallery_urls.append(pg.image.url)

        c_item = {
            'id': c.id,
            'name': c.name,
            'color_code': c.color_code,
            'image_url': c.image.url if c.image else (product.product_image.url if product.product_image else ''),
            'price': c.effective_price,
            'original_price': c.effective_original_price,
            'discount_percent': c.discount_percent,
            'in_stock': c.in_stock,
            'quantity': c.quantity,
            'is_default': c.is_default,
            'gallery': gallery_urls,
        }
        colors_data.append(c_item)
        if c.is_default and not default_color:
            default_color = c_item

    if colors_data and not default_color:
        default_color = colors_data[0]

    return render(request, "shop/products/product_details.html", {
        "products": product,
        "product": product,
        "related": related,
        "reviews": reviews,
        "in_wishlist": in_wishlist,
        "already_reviewed": already_reviewed,
        "review_form": form,
        "colors": colors_qs,
        "colors_json": json.dumps(colors_data),
        "default_color": default_color,
    })



# ---------- Auth ----------

def logout_page(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, "Logged out successfully")
    return redirect("/")


def login_page(request):
    if request.user.is_authenticated:
        return redirect("/")
    if request.method == 'POST':
        name = request.POST.get('username')
        pwd = request.POST.get('password')
        user = authenticate(request, username=name, password=pwd)
        if user is not None:
            login(request, user)
            messages.success(request, "Logged in successfully")
            return redirect(request.GET.get('next') or "/")
        messages.error(request, "Invalid username or password")
        return redirect("/login")
    return render(request, "shop/login.html")


def register(request):
    form = CustomUserForm()
    if request.method == 'POST':
        form = CustomUserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registration successful, you can log in now!")
            return redirect('login')
    return render(request, "shop/register.html", {'form': form})


# ---------- Cart & Coupons ----------

def _calculate_cart_totals(user, session):
    items = Cart.objects.filter(user=user).select_related('product', 'color')
    subtotal = sum(item.total_price for item in items)

    coupon_code = session.get('coupon_code')
    coupon = None
    discount_amount = 0

    if coupon_code and subtotal > 0:
        coupon = Coupon.objects.filter(code__iexact=coupon_code, active=True).first()
        if coupon and subtotal >= coupon.min_order_amount:
            discount_amount = coupon.calculate_discount(subtotal)
        else:
            if 'coupon_code' in session:
                del session['coupon_code']
                session.modified = True
            coupon = None

    subtotal_after_discount = max(0, subtotal - discount_amount)
    delivery_fee = 0 if subtotal >= FREE_DELIVERY_THRESHOLD or subtotal == 0 else DELIVERY_FEE
    grand_total = subtotal_after_discount + delivery_fee

    return {
        'items': items,
        'subtotal': subtotal,
        'coupon': coupon,
        'discount_amount': discount_amount,
        'subtotal_after_discount': subtotal_after_discount,
        'delivery_fee': delivery_fee,
        'total': grand_total,
    }


@login_required
def cart_view(request):
    cart_data = _calculate_cart_totals(request.user, request.session)
    available_coupons = Coupon.objects.filter(active=True)[:4]
    
    return render(request, "shop/cart.html", {
        "items": cart_data['items'],
        "subtotal": cart_data['subtotal'],
        "coupon": cart_data['coupon'],
        "discount_amount": cart_data['discount_amount'],
        "subtotal_after_discount": cart_data['subtotal_after_discount'],
        "delivery_fee": cart_data['delivery_fee'],
        "total": cart_data['total'],
        "free_delivery_threshold": FREE_DELIVERY_THRESHOLD,
        "available_coupons": available_coupons,
    })


@login_required
@require_POST
def apply_coupon(request):
    code = request.POST.get('coupon_code', '').strip().upper()
    if not code:
        messages.error(request, "Please enter a coupon code.")
        return redirect(request.META.get('HTTP_REFERER', 'cart'))

    coupon = Coupon.objects.filter(code__iexact=code, active=True).first()
    if not coupon:
        messages.error(request, f"Coupon code '{code}' is invalid or expired.")
        return redirect(request.META.get('HTTP_REFERER', 'cart'))

    items = Cart.objects.filter(user=request.user)
    subtotal = sum(item.total_price for item in items)

    if subtotal < coupon.min_order_amount:
        messages.warning(request, f"Coupon '{coupon.code}' requires a minimum order of ₹{int(coupon.min_order_amount)}.")
        return redirect(request.META.get('HTTP_REFERER', 'cart'))

    discount = coupon.calculate_discount(subtotal)
    request.session['coupon_code'] = coupon.code
    request.session.modified = True
    messages.success(request, f"Coupon '{coupon.code}' applied! You saved ₹{int(discount)}.")
    return redirect(request.META.get('HTTP_REFERER', 'cart'))


@login_required
def remove_coupon(request):
    if 'coupon_code' in request.session:
        del request.session['coupon_code']
        request.session.modified = True
        messages.info(request, "Coupon removed.")
    return redirect(request.META.get('HTTP_REFERER', 'cart'))


@login_required
@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id, status=0)
    color_id = request.POST.get('color_id')
    color = None
    if color_id:
        color = ProductColor.objects.filter(pk=color_id, product=product).first()
    if not color and product.colors.exists():
        color = product.colors.filter(is_default=True).first() or product.colors.first()

    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        product=product,
        color=color,
        defaults={'product_qty': 1}
    )
    if not created:
        cart_item.product_qty += 1
        cart_item.save()

    color_str = f" ({color.name})" if color else ""
    messages.success(request, f"Added '{product.name}{color_str}' to your cart")
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
@require_POST
def update_cart(request, item_id):
    item = get_object_or_404(Cart, pk=item_id, user=request.user)
    action = request.POST.get('action')
    if action == 'increase':
        item.product_qty += 1
        item.save()
    elif action == 'decrease':
        item.product_qty -= 1
        if item.product_qty <= 0:
            item.delete()
        else:
            item.save()
    return redirect('cart')


@login_required
def remove_from_cart(request, item_id):
    Cart.objects.filter(pk=item_id, user=request.user).delete()
    messages.success(request, "Item removed from cart")
    return redirect('cart')


# ---------- Wishlist ----------

@login_required
def wishlist_view(request):
    items = Wishlist.objects.filter(user=request.user).select_related('product')
    return render(request, "shop/wishlist.html", {"items": items})


@login_required
@require_POST
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    obj, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if not created:
        obj.delete()
        messages.info(request, "Removed from wishlist")
    else:
        messages.success(request, "Added to wishlist")
    return redirect(request.META.get('HTTP_REFERER', 'home'))


# ---------- Checkout & Orders ----------

@login_required
def checkout(request):
    cart_data = _calculate_cart_totals(request.user, request.session)
    items = cart_data['items']

    if not items.exists():
        messages.warning(request, "Your cart is empty. Please add items to place an order.")
        return redirect('cart')

    addresses = Address.objects.filter(user=request.user)
    subtotal = cart_data['subtotal']
    discount_amount = cart_data['discount_amount']
    coupon = cart_data['coupon']
    delivery_fee = cart_data['delivery_fee']
    total = cart_data['total']

    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        payment_method = request.POST.get('payment_method', 'cod')

        address = None
        if address_id:
            address = Address.objects.filter(pk=address_id, user=request.user).first()

        # If no address selected, check if user filled in the new address form directly on checkout
        if not address:
            full_name = request.POST.get('full_name', '').strip()
            phone = request.POST.get('phone', '').strip()
            address_line = request.POST.get('address_line', '').strip()
            city = request.POST.get('city', '').strip()
            state = request.POST.get('state', '').strip()
            pincode = request.POST.get('pincode', '').strip()

            if full_name and phone and address_line and city and pincode:
                is_def = not addresses.exists() or bool(request.POST.get('is_default'))
                if is_def:
                    Address.objects.filter(user=request.user).update(is_default=False)
                address = Address.objects.create(
                    user=request.user,
                    full_name=full_name,
                    phone=phone,
                    address_line=address_line,
                    city=city,
                    state=state,
                    pincode=pincode,
                    is_default=is_def
                )

        # Fallback to default or first address if available
        if not address and addresses.exists():
            address = addresses.filter(is_default=True).first() or addresses.first()

        if not address:
            messages.error(request, "Please enter your delivery address to place your order.")
            return redirect('checkout')

        order = Order.objects.create(
            user=request.user,
            address=address,
            payment_method=payment_method,
            subtotal=subtotal,
            coupon_code=coupon.code if coupon else '',
            discount_amount=discount_amount,
            delivery_fee=delivery_fee,
            total_amount=total,
            status='placed'
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
        
        # Clear cart and session coupon
        items.delete()
        if 'coupon_code' in request.session:
            del request.session['coupon_code']
            request.session.modified = True

        messages.success(request, f"Order #{order.id} placed successfully!")
        return redirect('order_success', order_id=order.id)

    return render(request, "shop/checkout.html", {
        "items": items,
        "addresses": addresses,
        "subtotal": subtotal,
        "coupon": coupon,
        "discount_amount": discount_amount,
        "delivery_fee": delivery_fee,
        "total": total,
        "address_form": AddressForm(),
    })


@login_required
@require_POST
def add_address(request):
    form = AddressForm(request.POST)
    if form.is_valid():
        address = form.save(commit=False)
        address.user = request.user
        if address.is_default:
            Address.objects.filter(user=request.user).update(is_default=False)
        address.save()
        messages.success(request, "Address saved")
    else:
        messages.error(request, "Please fill all address fields correctly")
    return redirect(request.META.get('HTTP_REFERER', 'checkout'))


@login_required
def delete_address(request, address_id):
    Address.objects.filter(pk=address_id, user=request.user).delete()
    messages.success(request, "Address deleted successfully")
    return redirect(request.META.get('HTTP_REFERER', 'profile'))


@login_required
def set_default_address(request, address_id):
    Address.objects.filter(user=request.user).update(is_default=False)
    Address.objects.filter(pk=address_id, user=request.user).update(is_default=True)
    messages.success(request, "Default delivery address updated.")
    return redirect(request.META.get('HTTP_REFERER', 'profile'))


@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    return render(request, "shop/order_success.html", {"order": order})


@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items')
    return render(request, "shop/orders.html", {"orders": orders})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    return render(request, "shop/order_detail.html", {"order": order})


@login_required
def invoice_view(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    return render(request, "shop/invoice.html", {"order": order})


# ---------- User Profile Hub ----------

@login_required
def profile_view(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items')
    addresses = Address.objects.filter(user=request.user).order_by('-is_default', '-created_at')
    wishlist_count = Wishlist.objects.filter(user=request.user).count()
    total_spent = sum(o.total_amount for o in orders.exclude(status='cancelled'))

    return render(request, "shop/profile.html", {
        "orders": orders,
        "addresses": addresses,
        "wishlist_count": wishlist_count,
        "total_spent": total_spent,
        "address_form": AddressForm(),
    })


@login_required
@require_POST
def update_profile(request):
    first_name = request.POST.get('first_name', '').strip()
    last_name = request.POST.get('last_name', '').strip()
    email = request.POST.get('email', '').strip()

    user = request.user
    user.first_name = first_name
    user.last_name = last_name
    if email:
        user.email = email
    user.save()
    messages.success(request, "Profile updated successfully!")
    return redirect('profile')

