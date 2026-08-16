from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.views.decorators.http import require_POST

from .models import Category, Product, Cart, Wishlist, Review, Address, Order, OrderItem
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
    category = get_object_or_404(Category, slug=slug)

    subcategories = category.subcategories.filter(status=0)

    return render(
        request,
        "shop/category_detail.html",
        {
            "category": category,
            "subcategories": subcategories,
        }
    )

def collectionsview(request, name):
    category = Category.objects.filter(slug=name, status=0).first() or Category.objects.filter(name=name, status=0).first()
    if not category:
        messages.warning(request, "No such category found!")
        return redirect('collections')

    subcategories = category.subcategories.filter(status=0)
    subcat_ids = list(subcategories.values_list('id', flat=True))

    products = Product.objects.filter(Q(category=category) | Q(category_id__in=subcat_ids), status=0)

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
        category = product.category

    related = Product.objects.filter(category=product.category, status=0).exclude(pk=product.pk)[:4]
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

    return render(request, "shop/products/product_details.html", {
        "products": product,
        "product": product,
        "related": related,
        "reviews": reviews,
        "in_wishlist": in_wishlist,
        "already_reviewed": already_reviewed,
        "review_form": form,
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


# ---------- Cart ----------

@login_required
def cart_view(request):
    items = Cart.objects.filter(user=request.user).select_related('product')
    subtotal = sum(item.total_price for item in items)
    delivery_fee = 0 if subtotal >= FREE_DELIVERY_THRESHOLD or subtotal == 0 else DELIVERY_FEE
    total = subtotal + delivery_fee
    return render(request, "shop/cart.html", {
        "items": items,
        "subtotal": subtotal,
        "delivery_fee": delivery_fee,
        "total": total,
        "free_delivery_threshold": FREE_DELIVERY_THRESHOLD,
    })


@login_required
@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id, status=0)
    cart_item, created = Cart.objects.get_or_create(user=request.user, product=product, defaults={'product_qty': 1})
    if not created:
        cart_item.product_qty += 1
        cart_item.save()
    messages.success(request, f"Added '{product.name}' to your cart")
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


# ---------- Checkout / Orders ----------

@login_required
def checkout(request):
    items = Cart.objects.filter(user=request.user).select_related('product')
    if not items.exists():
        messages.warning(request, "Your cart is empty")
        return redirect('cart')

    addresses = Address.objects.filter(user=request.user)
    subtotal = sum(item.total_price for item in items)
    delivery_fee = 0 if subtotal >= FREE_DELIVERY_THRESHOLD else DELIVERY_FEE
    total = subtotal + delivery_fee

    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        payment_method = request.POST.get('payment_method', 'cod')
        address = Address.objects.filter(pk=address_id, user=request.user).first()
        if not address:
            messages.error(request, "Please select a delivery address")
            return redirect('checkout')

        order = Order.objects.create(
            user=request.user, address=address, payment_method=payment_method,
            subtotal=subtotal, delivery_fee=delivery_fee, total_amount=total,
        )
        for item in items:
            OrderItem.objects.create(
                order=order, product=item.product, product_name=item.product.name,
                quantity=item.product_qty, price=item.product.selling_price,
            )
        items.delete()
        messages.success(request, "Your order has been placed!")
        return redirect('order_success', order_id=order.id)

    return render(request, "shop/checkout.html", {
        "items": items, "addresses": addresses, "subtotal": subtotal,
        "delivery_fee": delivery_fee, "total": total, "address_form": AddressForm(),
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
