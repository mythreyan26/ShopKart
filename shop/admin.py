from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Category, Product, ProductColor, ProductColorImage, ProductImage, Review, Wishlist, Cart, Address, Order, OrderItem, Coupon


# ==============================================================================
# Helper Styling Functions for Admin Badges & Previews
# ==============================================================================

def badge_pill(text, bg_color="#f1f5f9", text_color="#334155", border_color="#cbd5e1", icon=""):
    icon_html = f"<i class='{icon}' style='margin-right: 4px;'></i>" if icon else ""
    return format_html(
        '<span style="display: inline-flex; align-items: center; padding: 2px 8px; border-radius: 9999px; '
        'font-size: 11px; font-weight: 600; background-color: {}; color: {}; border: 1px solid {}; white-space: nowrap;">'
        '{}{}</span>',
        bg_color, text_color, border_color, mark_safe(icon_html), text
    )


def color_swatch_pill(name, hex_code):
    if not hex_code:
        hex_code = "#cbd5e1"
    return format_html(
        '<span style="display: inline-flex; align-items: center; gap: 5px; padding: 2px 8px; border-radius: 9999px; '
        'font-size: 11px; font-weight: 600; background-color: #f8fafc; color: #1e293b; border: 1px solid #e2e8f0; white-space: nowrap;">'
        '<span style="width: 10px; height: 10px; border-radius: 50%; background-color: {}; border: 1px solid rgba(0,0,0,0.15); display: inline-block;"></span>'
        '{}</span>',
        hex_code, name or 'Default'
    )


# ==============================================================================
# Inlines
# ==============================================================================

class ProductColorImageInline(admin.TabularInline):
    model = ProductColorImage
    extra = 1
    readonly_fields = ('image_preview',)
    fields = ('image', 'image_preview')

    def image_preview(self, obj):
        if obj and obj.image:
            return format_html(
                '<img src="{}" style="height: 50px; width: 50px; object-fit: cover; border-radius: 6px; border: 1px solid #cbd5e1;" />',
                obj.image.url
            )
        return mark_safe('<span style="color: #94a3b8; font-size: 12px;">No image uploaded</span>')
    image_preview.short_description = "Preview"


class ProductColorInline(admin.StackedInline):
    model = ProductColor
    extra = 0
    fields = (('name', 'color_code', 'is_default'), ('image', 'price', 'original_price', 'quantity'))
    show_change_link = True


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ('image_preview',)
    fields = ('image', 'image_preview')

    def image_preview(self, obj):
        if obj and obj.image:
            return format_html(
                '<img src="{}" style="height: 50px; width: 50px; object-fit: cover; border-radius: 6px; border: 1px solid #cbd5e1;" />',
                obj.image.url
            )
        return mark_safe('<span style="color: #94a3b8; font-size: 12px;">No image uploaded</span>')
    image_preview.short_description = "Preview"


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'color_badge', 'price', 'quantity', 'total_price')
    fields = ('product_name', 'color_badge', 'price', 'quantity', 'total_price')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def color_badge(self, obj):
        if obj.color_name:
            return color_swatch_pill(obj.color_name, obj.color_code)
        return mark_safe("<span style='color: #94a3b8; font-size: 11px;'>-</span>")
    color_badge.short_description = "Color Variant"


# ==============================================================================
# ModelAdmins
# ==============================================================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('image_thumbnail', 'name', 'parent_badge', 'products_count', 'status_badge', 'created_at')
    list_display_links = ('image_thumbnail', 'name')
    list_filter = ('parent', 'status')
    search_fields = ('name', 'slug', 'description', 'parent__name')
    prepopulated_fields = {'slug': ('name',)}
    list_per_page = 20
    date_hierarchy = 'created_at'

    def image_thumbnail(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height: 38px; width: 38px; object-fit: cover; border-radius: 8px; '
                'border: 1px solid #cbd5e1; background: #ffffff; box-shadow: 0 1px 2px rgba(0,0,0,0.05);" />',
                obj.image.url
            )
        return mark_safe('<div style="height: 38px; width: 38px; border-radius: 8px; background: #f1f5f9; '
                         'display: flex; align-items: center; justify-content: center; font-size: 16px;">📁</div>')
    image_thumbnail.short_description = "Image"

    def parent_badge(self, obj):
        if obj.parent:
            return badge_pill(obj.parent.name, bg_color="#eff6ff", text_color="#1d4ed8", border_color="#bfdbfe", icon="fas fa-folder")
        return badge_pill("Root Category", bg_color="#f8fafc", text_color="#64748b", border_color="#e2e8f0")
    parent_badge.short_description = "Parent Category"

    def products_count(self, obj):
        count = obj.products.count() + obj.primary_products.count()
        return badge_pill(f"{count} items", bg_color="#f0fdf4", text_color="#15803d", border_color="#bbf7d0", icon="fas fa-box")
    products_count.short_description = "Products"

    def status_badge(self, obj):
        if not obj.status:
            return badge_pill("Active", bg_color="#ecfdf5", text_color="#047857", border_color="#a7f3d0", icon="fas fa-check-circle")
        return badge_pill("Hidden", bg_color="#fef2f2", text_color="#b91c1c", border_color="#fecaca", icon="fas fa-eye-slash")
    status_badge.short_description = "Status"


from django import forms


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'categories': forms.SelectMultiple(attrs={
                'class': 'select2 form-control',
                'data-placeholder': 'Click to search and select subcategories...',
                'style': 'width: 100%; min-height: 44px;'
            }),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Full product description...'}),
            'highlights': forms.Textarea(attrs={'rows': 3, 'placeholder': 'One feature or spec per line...'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        categories = cleaned_data.get('categories')
        category = cleaned_data.get('category')
        if categories and not category:
            cleaned_data['category'] = categories.first()
        return cleaned_data


@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    list_display = ('color_preview', 'color_badge', 'product_link', 'price_display', 'quantity', 'is_default', 'gallery_count')
    list_display_links = ('color_preview', 'color_badge')
    list_filter = ('product__category', 'is_default')
    search_fields = ('name', 'product__name', 'color_code')
    inlines = [ProductColorImageInline]
    list_editable = ('quantity', 'is_default')
    list_per_page = 25

    def color_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height: 38px; width: 38px; object-fit: contain; border-radius: 8px; '
                'border: 1px solid #cbd5e1; background: #ffffff; padding: 2px;" />',
                obj.image.url
            )
        return mark_safe('<div style="height: 38px; width: 38px; border-radius: 8px; background: #f1f5f9; display: flex; align-items: center; justify-content: center; font-size: 16px;">🎨</div>')
    color_preview.short_description = "Image"

    def color_badge(self, obj):
        return color_swatch_pill(obj.name, obj.color_code)
    color_badge.short_description = "Color"

    def product_link(self, obj):
        return format_html(
            '<a href="/admin/shop/product/{}/change/" style="font-weight: 600; color: #0284c7;">{}</a>',
            obj.product.id, obj.product.name
        )
    product_link.short_description = "Product"

    def price_display(self, obj):
        if obj.price is not None:
            return format_html('<span style="font-weight: 700; color: #0f172a;">₹{}</span>', f"{int(obj.price):,}")
        return format_html('<span style="color: #94a3b8; font-size: 12px;">₹{} (Default)</span>', f"{int(obj.product.selling_price):,}")
    price_display.short_description = "Price"

    def gallery_count(self, obj):
        count = obj.images.count()
        return badge_pill(f"{count} photos", bg_color="#f0f9ff", text_color="#0369a1", border_color="#bae6fd", icon="fas fa-camera")
    gallery_count.short_description = "Gallery"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ('product_preview', 'product_info', 'display_categories_badges', 'display_colors_badges', 'selling_price', 'quantity', 'status', 'trending', 'featured')
    list_display_links = ('product_preview', 'product_info')
    list_editable = ('selling_price', 'quantity', 'status', 'trending', 'featured')
    list_filter = ('category', 'trending', 'featured', 'is_bestseller', 'status', 'created_at')
    search_fields = ('name', 'brand', 'vendor', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductColorInline, ProductImageInline]
    list_per_page = 20
    date_hierarchy = 'created_at'
    actions = ['make_published', 'make_hidden', 'mark_trending', 'mark_featured']

    fieldsets = (
        ('Basic Information', {
            'fields': (('name', 'slug'), ('brand', 'vendor'))
        }),
        ('Categories & Subcategories', {
            'fields': ('categories', 'category'),
            'description': 'Select all subcategories where this product should appear. (Primary category is set automatically if left blank).'
        }),
        ('Pricing & Inventory', {
            'fields': (('original_price', 'selling_price'), ('quantity', 'free_delivery'))
        }),
        ('Description & Specifications', {
            'fields': ('description', 'highlights')
        }),
        ('Main Product Image & Visibility', {
            'fields': ('product_image', ('status', 'trending', 'featured', 'is_bestseller'))
        }),
    )

    def product_preview(self, obj):
        if obj.product_image:
            return format_html(
                '<img src="{}" style="height: 42px; width: 42px; object-fit: contain; border-radius: 8px; '
                'border: 1px solid #e2e8f0; background: #ffffff; padding: 2px; box-shadow: 0 1px 3px rgba(0,0,0,0.06);" />',
                obj.product_image.url
            )
        return mark_safe('<div style="height: 42px; width: 42px; border-radius: 8px; background: #f8fafc; '
                         'border: 1px solid #e2e8f0; display: flex; align-items: center; justify-content: center; font-size: 18px;">📦</div>')
    product_preview.short_description = "Image"

    def product_info(self, obj):
        brand_html = f"<span style='font-size: 11px; font-weight: 600; color: #94a3b8; text-transform: uppercase;'>{obj.brand}</span>" if obj.brand else ""
        return format_html(
            '<div>'
            '<div style="font-weight: 600; font-size: 13px; color: #0f172a;">{}</div>'
            '{}'
            '</div>',
            obj.name, mark_safe(brand_html)
        )
    product_info.short_description = "Product Name"

    def display_categories_badges(self, obj):
        cats = obj.categories.all()
        if cats.exists():
            badges = "".join([f"<span style='display: inline-block; margin: 1px 3px 1px 0; padding: 2px 6px; border-radius: 4px; font-size: 10.5px; font-weight: 600; background: #f1f5f9; color: #475569; border: 1px solid #e2e8f0;'>{c.name}</span>" for c in cats])
            return mark_safe(badges)
        if obj.category:
            return mark_safe(f"<span style='display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 10.5px; font-weight: 600; background: #f1f5f9; color: #475569; border: 1px solid #e2e8f0;'>{obj.category.name}</span>")
        return mark_safe("<span style='color: #cbd5e1;'>-</span>")
    display_categories_badges.short_description = "Subcategories"

    def display_colors_badges(self, obj):
        colors = obj.colors.all()
        if colors.exists():
            dots = "".join([
                f"<span title='{c.name}' style='display: inline-block; width: 14px; height: 14px; border-radius: 50%; background-color: {c.color_code or '#ccc'}; border: 1px solid rgba(0,0,0,0.2); margin-right: 3px; vertical-align: middle;'></span>"
                for c in colors[:5]
            ])
            extra = f"<span style='font-size: 10px; color: #64748b;'>+{colors.count()-5}</span>" if colors.count() > 5 else ""
            return mark_safe(f"<div style='display: flex; align-items: center;'>{dots}{extra} <span style='font-size: 11px; color: #475569; margin-left: 4px;'>({colors.count()})</span></div>")
        return mark_safe("<span style='color: #cbd5e1; font-size: 12px;'>Standard</span>")
    display_colors_badges.short_description = "Colors"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not obj.category and obj.categories.exists():
            obj.category = obj.categories.first()
            obj.save()

    @admin.action(description="Publish selected products")
    def make_published(self, request, queryset):
        queryset.update(status=False)

    @admin.action(description="Hide selected products")
    def make_hidden(self, request, queryset):
        queryset.update(status=True)

    @admin.action(description="Mark selected as Trending")
    def mark_trending(self, request, queryset):
        queryset.update(trending=True)

    @admin.action(description="Mark selected as Featured")
    def mark_featured(self, request, queryset):
        queryset.update(featured=True)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id_badge', 'customer_info', 'total_badge', 'items_count_badge', 'status', 'payment_badge', 'created_at')
    list_display_links = ('order_id_badge', 'customer_info')
    list_editable = ('status',)
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('id', 'user__username', 'user__email', 'address__full_name', 'address__phone')
    inlines = [OrderItemInline]
    list_per_page = 20
    date_hierarchy = 'created_at'
    actions = ['mark_as_shipped', 'mark_as_delivered', 'mark_as_cancelled']

    def order_id_badge(self, obj):
        return format_html(
            '<span style="font-family: monospace; font-size: 13px; font-weight: 700; color: #ff6000; background: #fff7ed; padding: 3px 8px; border-radius: 6px; border: 1px solid #ffedd5;">'
            '#{}</span>',
            obj.id
        )
    order_id_badge.short_description = "Order ID"

    def customer_info(self, obj):
        full_name = obj.address.full_name if obj.address else obj.user.get_full_name()
        name_html = f"<div style='font-size: 11px; color: #64748b;'>{full_name}</div>" if full_name else ""
        return format_html(
            '<div>'
            '<span style="font-weight: 600; color: #0f172a; font-size: 13px;">{}</span>'
            '{}'
            '</div>',
            obj.user.username, mark_safe(name_html)
        )
    customer_info.short_description = "Customer"

    def total_badge(self, obj):
        return format_html(
            '<span style="font-weight: 800; font-size: 13px; color: #0f172a;">₹{}</span>',
            f"{int(obj.total_amount):,}"
        )
    total_badge.short_description = "Total Amount"

    def items_count_badge(self, obj):
        count = obj.items.count()
        return badge_pill(f"{count} items", bg_color="#f8fafc", text_color="#334155", border_color="#e2e8f0", icon="fas fa-shopping-bag")
    items_count_badge.short_description = "Items"

    def payment_badge(self, obj):
        method_map = {
            'cod': ('Cash on Delivery', '#f8fafc', '#334155', 'fas fa-money-bill-wave'),
            'card': ('Credit/Debit Card', '#eff6ff', '#2563eb', 'fas fa-credit-card'),
            'upi': ('UPI Payment', '#faf5ff', '#7c3aed', 'fas fa-mobile-alt'),
        }
        name, bg, text, icon = method_map.get(obj.payment_method, (obj.payment_method.upper(), '#f8fafc', '#334155', ''))
        return badge_pill(name, bg_color=bg, text_color=text, border_color="#e2e8f0", icon=icon)
    payment_badge.short_description = "Payment"

    @admin.action(description="Mark selected orders as Shipped")
    def mark_as_shipped(self, request, queryset):
        queryset.update(status='shipped')

    @admin.action(description="Mark selected orders as Delivered")
    def mark_as_delivered(self, request, queryset):
        queryset.update(status='delivered')

    @admin.action(description="Mark selected orders as Cancelled")
    def mark_as_cancelled(self, request, queryset):
        queryset.update(status='cancelled')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order_link', 'product_name', 'color_badge', 'quantity', 'price_display', 'total_display')
    list_filter = ('order__status', 'order__created_at')
    search_fields = ('product_name', 'color_name', 'order__id')

    def order_link(self, obj):
        return format_html(
            '<a href="/admin/shop/order/{}/change/" style="font-weight: 700; color: #ff6000;">Order #{}</a>',
            obj.order.id, obj.order.id
        )
    order_link.short_description = "Order"

    def color_badge(self, obj):
        if obj.color_name:
            return color_swatch_pill(obj.color_name, obj.color_code)
        return mark_safe("<span style='color: #94a3b8; font-size: 11px;'>-</span>")
    color_badge.short_description = "Color"

    def price_display(self, obj):
        return f"₹{int(obj.price):,}"
    price_display.short_description = "Unit Price"

    def total_display(self, obj):
        return format_html('<span style="font-weight: 700; color: #0f172a;">₹{}</span>', f"{int(obj.total_price):,}")
    total_display.short_description = "Total"


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'star_rating_badge', 'comment_snippet', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__name', 'user__username', 'title', 'comment')
    date_hierarchy = 'created_at'

    def star_rating_badge(self, obj):
        stars = "★" * obj.rating + "☆" * (5 - obj.rating)
        color = "#16a34a" if obj.rating >= 4 else ("#d97706" if obj.rating == 3 else "#dc2626")
        return format_html(
            '<span style="font-weight: 700; color: {}; font-size: 13px;">{} ({}★)</span>',
            color, stars, obj.rating
        )
    star_rating_badge.short_description = "Rating"

    def comment_snippet(self, obj):
        text = obj.title or obj.comment
        if text and len(text) > 50:
            return f"{text[:50]}..."
        return text or "-"
    comment_snippet.short_description = "Review Summary"


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'phone', 'location_summary', 'default_badge', 'created_at')
    search_fields = ('full_name', 'phone', 'city', 'pincode', 'user__username')
    list_filter = ('is_default', 'state')

    def location_summary(self, obj):
        return f"{obj.city}, {obj.state} - {obj.pincode}"
    location_summary.short_description = "Location"

    def default_badge(self, obj):
        if obj.is_default:
            return badge_pill("Default Address", bg_color="#ecfdf5", text_color="#047857", border_color="#a7f3d0", icon="fas fa-star")
        return mark_safe("<span style='color: #cbd5e1;'>-</span>")
    default_badge.short_description = "Default"


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'color_badge', 'product_qty', 'unit_price_display', 'total_price_display', 'created_at')
    search_fields = ('user__username', 'product__name', 'color__name')
    list_filter = ('created_at',)

    def color_badge(self, obj):
        if obj.color:
            return color_swatch_pill(obj.color.name, obj.color.color_code)
        return mark_safe("<span style='color: #94a3b8; font-size: 11px;'>Standard</span>")
    color_badge.short_description = "Color"

    def unit_price_display(self, obj):
        return f"₹{int(obj.unit_price):,}"
    unit_price_display.short_description = "Unit Price"

    def total_price_display(self, obj):
        return format_html('<span style="font-weight: 700; color: #0f172a;">₹{}</span>', f"{int(obj.total_price):,}")
    total_price_display.short_description = "Total"


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    search_fields = ('user__username', 'product__name')
    list_filter = ('created_at',)


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_display', 'discount_type', 'min_order_amount', 'max_discount', 'active_badge', 'created_at')
    search_fields = ('code', 'description')
    list_filter = ('active', 'discount_type', 'created_at')

    def discount_display(self, obj):
        suffix = '%' if obj.discount_type == 'percentage' else '₹'
        return format_html('<span style="font-weight: 700; color: #ea580c;">{}{}&nbsp;OFF</span>', obj.discount_value, suffix)
    discount_display.short_description = "Discount"

    def active_badge(self, obj):
        if obj.active:
            return badge_pill("Active", bg_color="#ecfdf5", text_color="#047857", border_color="#a7f3d0", icon="fas fa-check-circle")
        return badge_pill("Disabled", bg_color="#fef2f2", text_color="#dc2626", border_color="#fecaca", icon="fas fa-times-circle")
    active_badge.short_description = "Status"


