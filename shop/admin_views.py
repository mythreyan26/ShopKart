import json
import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Sum, Q, Count, F
from django.utils import timezone
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import admin

from .models import (
    Order, OrderItem, Product, ProductColor, ProductColorImage,
    ProductImage, Category, ContactMessage, Review, Coupon
)

staff_required = user_passes_test(lambda u: u.is_authenticated and u.is_staff, login_url='/admin/login/')


@staff_required
def admin_dashboard_redirect(request):
    return redirect('/admin/')


# ==============================================================================
# 1. Orders & Revenue Dashboard (Redirected to Django Admin)
# ==============================================================================

@staff_required
def admin_orders(request):
    return redirect('/admin/shop/order/')


@staff_required
@require_POST
def admin_order_update_status(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    new_status = request.POST.get('status')
    valid_statuses = [choice[0] for choice in Order.STATUS_CHOICES]

    if new_status in valid_statuses:
        old_status = order.status
        order.status = new_status
        if new_status == 'cancelled' and old_status != 'cancelled':
            order.cancelled_at = timezone.now()
            order.cancellation_reason = request.POST.get('cancellation_reason', 'Cancelled by Admin')
            # Restore stock
            for item in order.items.all():
                if item.product:
                    item.product.quantity += item.quantity
                    item.product.save(update_fields=['quantity'])
                    if item.color_name:
                        c_var = item.product.colors.filter(name=item.color_name).first()
                        if c_var:
                            c_var.quantity += item.quantity
                            c_var.save(update_fields=['quantity'])
        order.save()
        messages.success(request, f"Order status updated to '{order.get_status_display()}'.")
    else:
        messages.error(request, "Invalid order status selected.")

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or '/admin/shop/order/'
    return redirect(next_url)


# ==============================================================================
# 2. Products Catalog & Create/Edit Studio (Image 2 & 3 Replicas)
# ==============================================================================

@staff_required
def admin_products(request):
    search_query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '')
    
    products_qs = Product.objects.all().select_related('category').prefetch_related('colors', 'gallery').order_by('-created_at')

    if search_query:
        products_qs = products_qs.filter(
            Q(name__icontains=search_query) |
            Q(brand__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )

    if category_id:
        products_qs = products_qs.filter(category_id=category_id)

    paginator = Paginator(products_qs, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.filter(status=0)

    return render(request, 'shop/admin/products.html', {
        'products': page_obj,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_id,
        'active_menu': 'products',
        'active_submenu': 'products',
        'page_title': 'Products',
    })


@staff_required
def admin_product_create(request):
    parent_categories = Category.objects.filter(parent__isnull=True, status=0)
    sub_categories = Category.objects.filter(parent__isnull=False, status=0)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        category_id = request.POST.get('category') or request.POST.get('sub_category')
        brand = request.POST.get('brand', '').strip() or "ShopKart"
        selling_price = float(request.POST.get('selling_price') or 0.0)
        original_price = float(request.POST.get('original_price') or (selling_price * 1.15 if selling_price else 0.0))
        quantity = int(request.POST.get('quantity') or 0)
        sku = request.POST.get('sku', '').strip()
        product_image = request.FILES.get('product_image')

        if not name:
            messages.error(request, "Product title is required.")
            return redirect('admin_product_create')

        base_slug = slugify(name) or "product"
        slug = base_slug
        counter = 1
        while Product.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        category = Category.objects.filter(pk=category_id).first() if category_id else parent_categories.first()

        product = Product.objects.create(
            name=name,
            slug=slug,
            category=category,
            brand=brand,
            vendor=sku or brand,
            description=description,
            highlights=description[:500] if description else "",
            selling_price=selling_price,
            original_price=original_price,
            quantity=quantity,
            product_image=product_image,
            status=0,
        )

        gallery_images = request.FILES.getlist('gallery_images')
        for img in gallery_images:
            ProductImage.objects.create(product=product, image=img)

        variants_json = request.POST.get('variants_data')
        if variants_json:
            try:
                variants_list = json.loads(variants_json)
                for var_data in variants_list:
                    var_name = (var_data.get('name') or var_data.get('size') or 'Standard').strip()
                    var_color = (var_data.get('color_code') or '#000000').strip()
                    var_qty = int(var_data.get('quantity') or 0)
                    var_price = float(var_data.get('price') or selling_price)
                    ProductColor.objects.create(
                        product=product,
                        name=var_name,
                        color_code=var_color,
                        quantity=var_qty,
                        price=var_price
                    )
            except Exception:
                pass

        messages.success(request, f"Product '{product.name}' created successfully!")
        return redirect('admin_products')

    return render(request, 'shop/admin/product_form.html', {
        'parent_categories': parent_categories,
        'sub_categories': sub_categories,
        'product': None,
        'is_edit': False,
        'active_menu': 'products',
        'active_submenu': 'products',
        'page_title': 'Create Product',
    })


@staff_required
def admin_product_edit(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    parent_categories = Category.objects.filter(parent__isnull=True, status=0)
    sub_categories = Category.objects.filter(parent__isnull=False, status=0)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        category_id = request.POST.get('category') or request.POST.get('sub_category')
        brand = request.POST.get('brand', '').strip()
        selling_price = float(request.POST.get('selling_price') or 0.0)
        original_price = float(request.POST.get('original_price') or selling_price)
        quantity = int(request.POST.get('quantity') or 0)
        sku = request.POST.get('sku', '').strip()
        product_image = request.FILES.get('product_image')

        if name:
            product.name = name
        if description:
            product.description = description
            if not product.highlights:
                product.highlights = description[:500]
        if category_id:
            category = Category.objects.filter(pk=category_id).first()
            if category:
                product.category = category
        if brand:
            product.brand = brand
        if sku:
            product.vendor = sku
        product.selling_price = selling_price
        product.original_price = original_price
        product.quantity = quantity
        if product_image:
            product.product_image = product_image
        product.save()

        gallery_images = request.FILES.getlist('gallery_images')
        for img in gallery_images:
            ProductImage.objects.create(product=product, image=img)

        variants_json = request.POST.get('variants_data')
        if variants_json:
            try:
                variants_list = json.loads(variants_json)
                for var_data in variants_list:
                    var_id = var_data.get('id')
                    var_name = (var_data.get('name') or var_data.get('size') or 'Standard').strip()
                    var_color = (var_data.get('color_code') or '#000000').strip()
                    var_qty = int(var_data.get('quantity') or 0)
                    var_price = float(var_data.get('price') or selling_price)
                    if var_id:
                        ProductColor.objects.filter(pk=var_id, product=product).update(
                            name=var_name,
                            color_code=var_color,
                            quantity=var_qty,
                            price=var_price
                        )
                    else:
                        ProductColor.objects.create(
                            product=product,
                            name=var_name,
                            color_code=var_color,
                            quantity=var_qty,
                            price=var_price
                        )
            except Exception:
                pass

        messages.success(request, f"Product '{product.name}' updated successfully!")
        return redirect('admin_products')

    return render(request, 'shop/admin/product_form.html', {
        'parent_categories': parent_categories,
        'sub_categories': sub_categories,
        'product': product,
        'is_edit': True,
        'active_menu': 'products',
        'active_submenu': 'products',
        'page_title': f'Edit Product: {product.name}',
    })


@staff_required
@require_POST
def admin_product_delete(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    name = product.name
    product.delete()
    messages.success(request, f"Product '{name}' has been deleted.")
    return redirect('admin_products')


@staff_required
@require_POST
def admin_variant_add(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    size_or_name = (request.POST.get('size') or request.POST.get('name') or 'Standard').strip()
    color_code = (request.POST.get('color_code') or '#2563eb').strip()
    quantity = int(request.POST.get('quantity') or 10)
    price = float(request.POST.get('price') or product.selling_price)
    image = request.FILES.get('variant_image')

    variant = ProductColor.objects.create(
        product=product,
        name=size_or_name,
        color_code=color_code,
        quantity=quantity,
        price=price
    )
    if image:
        ProductColorImage.objects.create(color=variant, image=image)

    messages.success(request, f"Variation '{size_or_name}' added successfully!")
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or f'/panel/products/{product.id}/edit/'
    return redirect(next_url)


# ==============================================================================
# 3. Categories, Users & Customer Support
# ==============================================================================

@staff_required
def admin_categories(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        parent_id = request.POST.get('parent_id')
        description = request.POST.get('description', '').strip()
        image = request.FILES.get('image')

        if name:
            slug = slugify(name)
            parent = Category.objects.filter(pk=parent_id).first() if parent_id else None
            Category.objects.create(
                name=name,
                slug=slug,
                parent=parent,
                description=description,
                image=image,
                status=0
            )
            messages.success(request, f"Category '{name}' created successfully!")
            return redirect('admin_categories')

    categories = Category.objects.filter(parent__isnull=True).prefetch_related('subcategories').annotate(prod_count=Count('products'))
    return render(request, 'shop/admin/categories.html', {
        'categories': categories,
        'active_menu': 'products',
        'active_submenu': 'categories',
        'page_title': 'Categories',
    })


@staff_required
def admin_users(request):
    users_qs = User.objects.all().annotate(order_count=Count('orders')).order_by('-date_joined')
    paginator = Paginator(users_qs, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'shop/admin/users.html', {
        'users_list': page_obj,
        'active_menu': 'users',
        'page_title': 'Users & Customers',
    })


@staff_required
def admin_support(request):
    messages_qs = ContactMessage.objects.all().order_by('-created_at')
    return render(request, 'shop/admin/support.html', {
        'support_messages': messages_qs,
        'active_menu': 'customer_support',
        'page_title': 'Customer Support Inquiries',
    })


@staff_required
@require_POST
def admin_support_toggle(request, message_id):
    msg = get_object_or_404(ContactMessage, pk=message_id)
    msg.is_resolved = not msg.is_resolved
    msg.save()
    status_label = "resolved" if msg.is_resolved else "open"
    messages.success(request, f"Inquiry marked as {status_label}.")
    return redirect('admin_support')


# ==============================================================================
# Executive E-Commerce Analytics & Centralized Inventory Control
# ==============================================================================

@staff_member_required
def admin_analytics_view(request):
    """
    Executive Analytics, Sales & Financial Telemetry Studio.
    """
    context = admin.site.each_context(request)
    context['title'] = "E-Commerce Analytics & Financial Intelligence Reports"
    context['subtitle'] = "Executive Performance Telemetry"

    # Orders & Revenue Telemetry
    all_orders = Order.objects.all()
    non_cancelled = all_orders.exclude(status='cancelled')
    total_orders = all_orders.count()
    gross_revenue = all_orders.aggregate(s=Sum('total_amount'))['s'] or 0.0
    net_revenue = non_cancelled.aggregate(s=Sum('total_amount'))['s'] or 0.0
    total_discounts = all_orders.aggregate(s=Sum('discount_amount'))['s'] or 0.0
    active_count = non_cancelled.count()
    aov = (net_revenue / active_count) if active_count > 0 else 0.0

    # Payment Methods Telemetry
    cod_orders = non_cancelled.filter(payment_method='cod')
    cod_revenue = cod_orders.aggregate(s=Sum('total_amount'))['s'] or 0.0
    cod_count = cod_orders.count()
    cod_percent = int((cod_revenue / net_revenue) * 100) if net_revenue > 0 else 0

    upi_orders = all_orders.filter(payment_method__in=['upi', 'card'])
    upi_revenue = upi_orders.aggregate(s=Sum('total_amount'))['s'] or 0.0
    upi_count = upi_orders.count()
    upi_percent = 100 - cod_percent if net_revenue > 0 else 0

    # 7-Day Velocity Telemetry
    today = timezone.now().date()
    daily_sales = []
    daily_revs = []
    for i in range(7):
        day_date = today - datetime.timedelta(days=6 - i)
        day_orders = Order.objects.filter(created_at__date=day_date).exclude(status='cancelled')
        rev = float(day_orders.aggregate(s=Sum('total_amount'))['s'] or 0.0)
        daily_revs.append(rev)
        daily_sales.append({
            'date': day_date.strftime('%b %d'),
            'day': day_date.strftime('%a'),
            'revenue': rev,
            'orders_count': day_orders.count(),
        })
    max_rev = max(daily_revs) if daily_revs and max(daily_revs) > 0 else 100.0
    for day in daily_sales:
        day['height_percent'] = max(int((day['revenue'] / max_rev) * 100), 8) if day['revenue'] > 0 else 4

    # Top Velocity Products
    top_products_data = list(
        OrderItem.objects.values('product_name').annotate(
            total_qty=Sum('quantity'),
            total_revenue=Sum(F('quantity') * F('price'))
        ).order_by('-total_qty')[:5]
    )

    # Categories & Inventory Distribution
    categories = Category.objects.all()
    category_list = []
    for c in categories:
        prods = c.products.all()
        stock = sum(p.quantity for p in prods)
        val = sum(p.quantity * p.selling_price for p in prods)
        if prods.count() > 0 or stock > 0:
            category_list.append({
                'id': c.id,
                'name': c.name,
                'product_count': prods.count(),
                'stock_units': stock,
                'valuation': val,
            })
    category_list.sort(key=lambda x: x['valuation'], reverse=True)

    # Inventory Valuation
    all_products = Product.objects.all()
    total_inventory_units = sum(p.quantity for p in all_products)
    total_valuation = sum(p.quantity * p.selling_price for p in all_products)
    if total_valuation >= 10000000:
        inventory_valuation_display = f"{total_valuation / 10000000:.2f} Cr"
    elif total_valuation >= 100000:
        inventory_valuation_display = f"{total_valuation / 100000:.2f} Lakh"
    else:
        inventory_valuation_display = f"{int(total_valuation):,}"

    # Customer Cohorts
    all_users = User.objects.all()
    total_customers = all_users.count()
    paying_customers = User.objects.filter(orders__status__in=['placed', 'confirmed', 'shipped', 'delivered']).distinct().count()
    prospects_count = total_customers - paying_customers
    vip_count = 0
    for u in all_users:
        spend = u.orders.exclude(status='cancelled').aggregate(s=Sum('total_amount'))['s'] or 0.0
        if spend >= 25000:
            vip_count += 1

    # Marketing Coupons Telemetry
    active_coupons = Coupon.objects.filter(active=True).count()
    coupon_orders = Order.objects.exclude(coupon_code__isnull=True).exclude(coupon_code='')
    coupon_redemptions = coupon_orders.count()
    top_code = coupon_orders.values('coupon_code').annotate(cnt=Count('id')).order_by('-cnt').first()
    top_coupon_code = top_code['coupon_code'] if top_code else "None"

    context['analytics'] = {
        'net_revenue': net_revenue,
        'gross_revenue': gross_revenue,
        'total_orders': total_orders,
        'aov': aov,
        'total_discounts': total_discounts,
        'inventory_valuation_display': inventory_valuation_display,
        'total_inventory_units': total_inventory_units,
        'total_customers': total_customers,
        'paying_customers': paying_customers,
        'prospects_count': prospects_count,
        'vip_count': vip_count,
        'cod_revenue': cod_revenue,
        'cod_orders': cod_count,
        'cod_percent': cod_percent,
        'upi_revenue': upi_revenue,
        'upi_orders': upi_count,
        'upi_percent': upi_percent,
        'daily_sales': daily_sales,
        'top_products': top_products_data,
        'top_categories': category_list[:8],
        'unresolved_tickets': ContactMessage.objects.filter(is_resolved=False).count(),
        'active_coupons': active_coupons,
        'coupon_redemptions': coupon_redemptions,
        'top_coupon_code': top_coupon_code,
        'total_reviews': Review.objects.count(),
    }
    return render(request, 'admin/analytics.html', context)


@staff_member_required
def admin_inventory_view(request):
    """
    Centralized Warehouse Inventory & Stock Control Studio.
    """
    context = admin.site.each_context(request)
    context['title'] = "Warehouse & Inventory Management Studio"
    context['subtitle'] = "Real-Time Physical Stock Control"

    filter_param = request.GET.get('filter', '')
    products_qs = Product.objects.select_related('category').order_by('quantity', 'name')

    total_units = sum(p.quantity for p in Product.objects.all())
    total_valuation = sum(p.quantity * p.selling_price for p in Product.objects.all())
    low_stock_count = Product.objects.filter(quantity__lte=5).count()
    out_of_stock_count = Product.objects.filter(quantity=0).count()
    total_products = Product.objects.count()

    if filter_param == 'low':
        products_qs = products_qs.filter(quantity__lte=5)
    elif filter_param == 'healthy':
        products_qs = products_qs.filter(quantity__gt=5)
    elif filter_param == 'out':
        products_qs = products_qs.filter(quantity=0)

    # Attach valuation dynamically
    product_list = []
    for p in products_qs:
        p.valuation = p.quantity * p.selling_price
        product_list.append(p)

    if total_valuation >= 10000000:
        valuation_display = f"{total_valuation / 10000000:.2f} Cr"
    elif total_valuation >= 100000:
        valuation_display = f"{total_valuation / 100000:.2f} Lakh"
    else:
        valuation_display = f"{int(total_valuation):,}"

    context['inventory_data'] = {
        'products': product_list,
        'total_units': total_units,
        'total_products': total_products,
        'total_valuation_display': valuation_display,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
    }
    return render(request, 'admin/inventory.html', context)

