from django import forms
from django.contrib import admin, messages
from django.urls import path, reverse
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count, F, Q, FloatField, Avg
from django.db.models.functions import Coalesce
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Category, Product, ProductColor, ProductColorImage, ProductImage, Review, Wishlist, Cart, Address, Order, OrderItem, Coupon, ContactMessage


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


ORDER_STATUS_STYLES = {
    'placed': {
        'label': 'Order Placed',
        'bg': '#eff6ff',
        'text': '#1d4ed8',
        'border': '#bfdbfe',
        'icon': 'fas fa-clock',
    },
    'confirmed': {
        'label': 'Confirmed & Packed',
        'bg': '#eef2ff',
        'text': '#4338ca',
        'border': '#c7d2fe',
        'icon': 'fas fa-box',
    },
    'shipped': {
        'label': 'Shipped',
        'bg': '#f5f3ff',
        'text': '#6d28d9',
        'border': '#ddd6fe',
        'icon': 'fas fa-truck-moving',
    },
    'out_for_delivery': {
        'label': 'Out for Delivery',
        'bg': '#fffbeb',
        'text': '#b45309',
        'border': '#fde68a',
        'icon': 'fas fa-shipping-fast',
    },
    'delivered': {
        'label': 'Delivered',
        'bg': '#f0fdf4',
        'text': '#15803d',
        'border': '#bbf7d0',
        'icon': 'fas fa-check-circle',
    },
    'cancelled': {
        'label': 'Cancelled',
        'bg': '#fef2f2',
        'text': '#b91c1c',
        'border': '#fecaca',
        'icon': 'fas fa-times-circle',
    },
}


def get_order_payment_status(order):
    if order.status == 'cancelled':
        if order.payment_method in ['card', 'upi']:
            return ('Refund Due / Cancelled', '#fef2f2', '#b91c1c', '#fecaca', 'fas fa-undo')
        return ('Cancelled (No Charge)', '#f8fafc', '#64748b', '#e2e8f0', 'fas fa-ban')
    if order.payment_method == 'cod':
        if order.status == 'delivered':
            return ('Paid (Cash Collected)', '#f0fdf4', '#15803d', '#bbf7d0', 'fas fa-money-bill-wave')
        return ('Pending on Delivery', '#fffbeb', '#b45309', '#fde68a', 'fas fa-hourglass-half')
    return ('Paid Online (Settled)', '#f0fdf4', '#15803d', '#bbf7d0', 'fas fa-shield-alt')



# ==============================================================================
# Inlines
# ==============================================================================

class ProductColorImageInline(admin.TabularInline):
    model = ProductColorImage
    extra = 1
    template = 'admin/shop/productcolor/color_images_inline.html'
    fields = ('image',)

    def image_preview(self, obj):
        if obj and obj.image:
            return format_html(
                '<img src="{}" style="height: 50px; width: 50px; object-fit: contain; border-radius: 8px; border: 1px solid #cbd5e1; background: #ffffff; padding: 2px;" />',
                obj.image.url
            )
        return mark_safe('<span style="color: #94a3b8; font-size: 12px;">No image uploaded</span>')
    image_preview.short_description = "Preview"


class ProductColorForm(forms.ModelForm):
    color_picker = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'type': 'color',
            'style': 'width: 44px; height: 38px; padding: 2px; border-radius: 8px; border: 1px solid #cbd5e1; cursor: pointer; vertical-align: middle; box-shadow: 0 1px 2px rgba(0,0,0,0.05);',
            'title': 'Click to open visual color palette',
            'oninput': "let parent = this.closest('.inline-related, fieldset, tr, .form-row, .card-body'); if(parent) { let input = parent.querySelector('input[name$=\\'color_code\\']'); if(input) input.value = this.value; }",
            'onchange': "let parent = this.closest('.inline-related, fieldset, tr, .form-row, .card-body'); if(parent) { let input = parent.querySelector('input[name$=\\'color_code\\']'); if(input) input.value = this.value; }"
        }),
        label="Color Picker"
    )

    class Meta:
        model = ProductColor
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.color_code:
            self.fields['color_picker'].initial = self.instance.color_code

    def clean(self):
        cleaned_data = super().clean()
        picker = cleaned_data.get('color_picker')
        code = cleaned_data.get('color_code')
        if not code and picker:
            cleaned_data['color_code'] = picker
        return cleaned_data

    def clean_color_code(self):
        code = self.cleaned_data.get('color_code', '').strip()
        if code and not code.startswith('#'):
            code = f"#{code}"
        return code


class ProductColorInline(admin.StackedInline):
    model = ProductColor
    form = ProductColorForm
    extra = 1
    classes = ['collapse-open']
    verbose_name = "Color Variant"
    verbose_name_plural = "🎨 Color Variants & Pricing"
    fields = (
        ('name', 'color_code', 'color_picker', 'color_swatch_display', 'is_default'),
        ('image', 'image_thumbnail', 'color_gallery_display'),
        ('price', 'original_price', 'quantity'),
    )
    readonly_fields = ('color_swatch_display', 'image_thumbnail', 'color_gallery_display')
    show_change_link = True

    def color_gallery_display(self, obj):
        if obj and obj.pk:
            images = obj.images.all()
            if images.exists():
                thumbs = "".join([
                    f'<img src="{img.image.url}" style="height: 38px; width: 38px; object-fit: contain; border-radius: 6px; border: 1px solid #cbd5e1; background: #ffffff; margin-right: 5px; padding: 2px;" />'
                    for img in images[:4]
                ])
                more = f"<span style='font-size: 11px; color: #64748b;'>+{images.count()-4} more</span>" if images.count() > 4 else ""
                link = f'<a href="/admin/shop/productcolor/{obj.id}/change/" style="font-size: 12px; font-weight: 700; color: #ff6000; text-decoration: none; margin-left: 8px;">Edit {images.count()} photos ➔</a>'
                return format_html('<div style="display: flex; align-items: center; margin-top: 4px;">{}{}{}</div>', mark_safe(thumbs), mark_safe(more), mark_safe(link))
            return format_html(
                '<a href="/admin/shop/productcolor/{}/change/" style="font-size: 12px; color: #64748b; text-decoration: none; display: inline-flex; align-items: center; gap: 4px; margin-top: 6px;">'
                '<i class="fas fa-camera"></i> Add extra photos</a>',
                obj.id
            )
        return mark_safe('<span style="color: #94a3b8; font-size: 11px; margin-top: 6px; display: inline-block;">Save variant first</span>')
    color_gallery_display.short_description = "Color Gallery Angles"

    def color_swatch_display(self, obj):
        if obj and obj.color_code:
            return format_html(
                '<div style="display: inline-flex; align-items: center; gap: 8px; margin-top: 4px; padding: 3px 8px; border-radius: 8px; background: #f8fafc; border: 1px solid #e2e8f0;">'
                '<span style="width: 20px; height: 20px; border-radius: 50%; background-color: {}; '
                'border: 1px solid rgba(0,0,0,0.2); box-shadow: 0 1px 2px rgba(0,0,0,0.1); display: inline-block;"></span>'
                '<code style="font-weight: 700; color: #1e293b; font-size: 12px;">{}</code>'
                '</div>',
                obj.color_code, obj.color_code
            )
        return mark_safe('<span style="color: #94a3b8; font-size: 12px; margin-top: 6px; display: inline-block;">Save to preview swatch</span>')
    color_swatch_display.short_description = "Live Swatch"

    def image_thumbnail(self, obj):
        if obj and obj.image:
            return format_html(
                '<div style="margin-top: 4px;">'
                '<img src="{}" style="height: 54px; width: 54px; object-fit: contain; border-radius: 8px; '
                'border: 1px solid #cbd5e1; background: #ffffff; padding: 2px; box-shadow: 0 1px 3px rgba(0,0,0,0.08);" />'
                '</div>',
                obj.image.url
            )
        return mark_safe('<span style="color: #94a3b8; font-size: 12px; margin-top: 6px; display: inline-block;">No photo uploaded</span>')
    image_thumbnail.short_description = "Variant Preview"


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    template = 'admin/shop/product/gallery_grid_inline.html'
    extra = 0
    verbose_name = "Gallery Image"
    verbose_name_plural = "📸 Upload Product Images (Gallery Grid)"
    fields = ('image',)


class ProductReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    verbose_name = "Review"
    verbose_name_plural = "⭐ Customer Reviews & Moderation"
    fields = ('user', 'rating_stars', 'headline_snippet', 'comment_snippet', 'is_verified_purchase', 'created_at')
    readonly_fields = ('user', 'rating_stars', 'headline_snippet', 'comment_snippet', 'is_verified_purchase', 'created_at')
    can_delete = True
    show_change_link = True

    def is_verified_purchase(self, obj):
        if obj and obj.user and obj.product:
            from .models import OrderItem
            bought = OrderItem.objects.filter(order__user=obj.user, product_name=obj.product.name).exists()
            if bought:
                return mark_safe('<span style="color: #16a34a; font-weight: 600; font-size: 11px;"><i class="fas fa-check-circle"></i> Verified Buyer</span>')
            return mark_safe('<span style="color: #94a3b8; font-size: 11px;">Reviewer</span>')
        return "-"
    is_verified_purchase.short_description = "Buyer Status"

    def rating_stars(self, obj):
        stars = "★" * int(obj.rating) + "☆" * (5 - int(obj.rating))
        color = "#16a34a" if obj.rating >= 4 else ("#d97706" if obj.rating == 3 else "#dc2626")
        return format_html(
            '<span style="color: {}; font-weight: 800; font-size: 13px;">{} ({}★)</span>',
            color, stars, obj.rating
        )
    rating_stars.short_description = "Rating"

    def headline_snippet(self, obj):
        return obj.title or "-"
    headline_snippet.short_description = "Headline"

    def comment_snippet(self, obj):
        if obj.comment and len(obj.comment) > 60:
            return f"{obj.comment[:60]}..."
        return obj.comment or "-"
    comment_snippet.short_description = "Comment"

    def has_add_permission(self, request, obj=None):
        return False


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    verbose_name = "Ordered Item"
    verbose_name_plural = "🛍️ Purchased Items & Variants"
    readonly_fields = ('product_thumbnail', 'product_name', 'color_badge', 'price_display', 'quantity', 'total_display')
    fields = ('product_thumbnail', 'product_name', 'color_badge', 'price_display', 'quantity', 'total_display')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def product_thumbnail(self, obj):
        if obj and obj.product and obj.product.product_image:
            return format_html(
                '<img src="{}" style="height: 38px; width: 38px; object-fit: contain; border-radius: 8px; border: 1px solid #cbd5e1; background: #ffffff; padding: 2px;" />',
                obj.product.product_image.url
            )
        return mark_safe('<div style="width: 38px; height: 38px; border-radius: 8px; background: #f1f5f9; display: inline-flex; align-items: center; justify-content: center; color: #94a3b8;"><i class="fas fa-box"></i></div>')
    product_thumbnail.short_description = "Item"

    def color_badge(self, obj):
        if obj.color_name:
            return color_swatch_pill(obj.color_name, obj.color_code)
        return mark_safe("<span style='color: #94a3b8; font-size: 11px;'>-</span>")
    color_badge.short_description = "Color Variant"

    def price_display(self, obj):
        return f"₹{int(obj.price):,}"
    price_display.short_description = "Unit Price"

    def total_display(self, obj):
        return format_html('<span style="font-weight: 700; color: #0f172a;">₹{}</span>', f"{int(obj.total_price):,}")
    total_display.short_description = "Line Total"


# ==============================================================================
# ModelAdmins
# ==============================================================================

class StockStatusFilter(admin.SimpleListFilter):
    title = 'Inventory Health'
    parameter_name = 'stock_status'

    def lookups(self, request, model_admin):
        return (
            ('in_stock', '✓ Healthy Stock (> 10 units)'),
            ('low_stock', '⚠ Low Stock (1 - 10 units)'),
            ('out_of_stock', '✗ Out of Stock (0 units)'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'in_stock':
            return queryset.filter(quantity__gt=10)
        if self.value() == 'low_stock':
            return queryset.filter(quantity__gt=0, quantity__lte=10)
        if self.value() == 'out_of_stock':
            return queryset.filter(quantity__lte=0)
        return queryset


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    change_list_template = 'admin/shop/category/change_list.html'
    list_display = ('image_thumbnail', 'name', 'parent_badge', 'products_count', 'inventory_units_count', 'status_badge', 'quick_actions', 'created_at')
    list_display_links = ('image_thumbnail', 'name')
    list_filter = ('parent', 'status', 'created_at')
    search_fields = ('name', 'slug', 'description', 'parent__name')
    prepopulated_fields = {'slug': ('name',)}
    list_per_page = 25
    date_hierarchy = 'created_at'

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        total_categories = Category.objects.count()
        root_categories = Category.objects.filter(parent__isnull=True).count()
        subcategories = Category.objects.filter(parent__isnull=False).count()
        active_categories = Category.objects.filter(status=False).count()
        total_units = Product.objects.aggregate(s=Sum('quantity'))['s'] or 0
        extra_context['category_stats'] = {
            'total_categories': total_categories,
            'root_categories': root_categories,
            'subcategories': subcategories,
            'active_categories': active_categories,
            'total_units': total_units,
        }
        return super().changelist_view(request, extra_context=extra_context)

    fieldsets = (
        ('📁 Category Identity', {
            'fields': (('name', 'slug'), 'parent')
        }),
        ('🖼️ Visuals & Description', {
            'fields': ('image', 'description')
        }),
        ('⚙️ Visibility Settings', {
            'fields': ('status',)
        }),
    )

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
        return badge_pill(f"{count} products", bg_color="#f0fdf4", text_color="#15803d", border_color="#bbf7d0", icon="fas fa-box")
    products_count.short_description = "Products"

    def inventory_units_count(self, obj):
        total_qty = (obj.products.aggregate(s=Sum('quantity'))['s'] or 0) + (obj.primary_products.aggregate(s=Sum('quantity'))['s'] or 0)
        return format_html('<span style="font-weight: 700; color: #0f172a; font-size: 12.5px;">{} units</span>', f"{total_qty:,}")
    inventory_units_count.short_description = "Stock Units"

    def status_badge(self, obj):
        if not obj.status:
            return badge_pill("Active", bg_color="#ecfdf5", text_color="#047857", border_color="#a7f3d0", icon="fas fa-check-circle")
        return badge_pill("Hidden", bg_color="#fef2f2", text_color="#b91c1c", border_color="#fecaca", icon="fas fa-eye-slash")
    status_badge.short_description = "Status"

    def quick_actions(self, obj):
        return format_html(
            '<a href="/collections/{}" target="_blank" class="btn-studio-action" title="View Category on Storefront" style="padding: 4px 8px; border-radius: 6px; background: #f1f5f9; color: #334155; border: 1px solid #cbd5e1; font-size: 11px; font-weight: 600; text-decoration: none; display: inline-flex; align-items: center; gap: 4px;">'
            '<i class="fas fa-external-link-alt"></i> Storefront</a>',
            obj.name
        )
    quick_actions.short_description = "Actions"



from django import forms


class AdminThumbnailDropzoneWidget(forms.ClearableFileInput):
    template_name = 'admin/shop/product/thumbnail_dropzone_widget.html'

    def render(self, name, value, attrs=None, renderer=None):
        from django.template.loader import render_to_string
        context = self.get_context(name, value, attrs)
        return mark_safe(render_to_string(self.template_name, context))


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'product_image': AdminThumbnailDropzoneWidget(),
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
    change_list_template = 'admin/shop/productcolor/change_list.html'
    form = ProductColorForm
    list_display = ('color_preview', 'color_badge', 'product_link', 'price_display', 'quantity', 'stock_status_badge', 'is_default', 'gallery_count', 'quick_actions')
    list_display_links = ('color_preview', 'color_badge')
    list_filter = ('product__category', 'is_default')
    search_fields = ('name', 'product__name', 'color_code')
    inlines = [ProductColorImageInline]
    list_editable = ('quantity', 'is_default')
    list_per_page = 25

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        total_variants = ProductColor.objects.count()
        default_variants = ProductColor.objects.filter(is_default=True).count()
        total_units = ProductColor.objects.aggregate(s=Sum('quantity'))['s'] or 0
        low_stock_count = ProductColor.objects.filter(quantity__lte=10).count()
        extra_context['variant_stats'] = {
            'total_variants': total_variants,
            'default_variants': default_variants,
            'total_units': total_units,
            'low_stock_count': low_stock_count,
        }
        return super().changelist_view(request, extra_context=extra_context)

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        if object_id:
            pc = ProductColor.objects.filter(pk=object_id).select_related('product').first()
            if pc and pc.product:
                extra_context['sibling_colors'] = pc.product.colors.exclude(pk=pc.pk).prefetch_related('images')
        return super().changeform_view(request, object_id, form_url, extra_context=extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/add-image/',
                self.admin_site.admin_view(self.ajax_add_image),
                name='shop_productcolor_add_image'
            ),
            path(
                '<path:object_id>/delete-image/<int:image_id>/',
                self.admin_site.admin_view(self.ajax_delete_image),
                name='shop_productcolor_delete_image'
            ),
            path(
                '<path:object_id>/replace-image/<int:image_id>/',
                self.admin_site.admin_view(self.ajax_replace_image),
                name='shop_productcolor_replace_image'
            ),
        ]
        return custom_urls + urls

    def ajax_add_image(self, request, object_id):
        if request.method == 'POST' and request.FILES.get('image'):
            pc = get_object_or_404(ProductColor, pk=object_id)
            img = ProductColorImage.objects.create(color=pc, image=request.FILES['image'])
            return JsonResponse({'status': 'ok', 'id': img.id, 'url': img.image.url})
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

    def ajax_delete_image(self, request, object_id, image_id):
        if request.method == 'POST':
            pc = get_object_or_404(ProductColor, pk=object_id)
            img = get_object_or_404(ProductColorImage, pk=image_id, color=pc)
            img.delete()
            return JsonResponse({'status': 'ok'})
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

    def ajax_replace_image(self, request, object_id, image_id):
        if request.method == 'POST' and request.FILES.get('image'):
            pc = get_object_or_404(ProductColor, pk=object_id)
            img = get_object_or_404(ProductColorImage, pk=image_id, color=pc)
            img.image = request.FILES['image']
            img.save(update_fields=['image'])
            return JsonResponse({'status': 'ok', 'url': img.image.url})
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

    fieldsets = (
        ('🎨 Variant Details', {
            'fields': ('product', ('name', 'color_code', 'color_picker'), 'image', 'is_default')
        }),
        ('💰 Pricing & Stock', {
            'fields': (('price', 'original_price'), 'quantity')
        }),
    )

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
            '<a href="/admin/shop/product/{}/change/" style="font-weight: 700; color: #0284c7; text-decoration: none;">{}</a>',
            obj.product.id, obj.product.name
        )
    product_link.short_description = "Parent Product"

    def price_display(self, obj):
        if obj.price is not None:
            return format_html('<span style="font-weight: 700; color: #0f172a;">₹{}</span>', f"{int(obj.price):,}")
        return format_html('<span style="color: #94a3b8; font-size: 12px;">₹{} (Default)</span>', f"{int(obj.product.selling_price):,}")
    price_display.short_description = "Variant Price"

    def stock_status_badge(self, obj):
        if obj.quantity > 10:
            return badge_pill(f"{obj.quantity} in stock", bg_color="#f0fdf4", text_color="#15803d", border_color="#bbf7d0", icon="fas fa-check")
        elif obj.quantity > 0:
            return badge_pill(f"{obj.quantity} Low", bg_color="#fffbeb", text_color="#b45309", border_color="#fde68a", icon="fas fa-exclamation-triangle")
        return badge_pill("Out of Stock", bg_color="#fef2f2", text_color="#dc2626", border_color="#fecaca", icon="fas fa-times-circle")
    stock_status_badge.short_description = "Stock Health"

    def gallery_count(self, obj):
        count = obj.images.count()
        return badge_pill(f"{count} photos", bg_color="#f0f9ff", text_color="#0369a1", border_color="#bae6fd", icon="fas fa-camera")
    gallery_count.short_description = "Photos"

    def quick_actions(self, obj):
        return format_html(
            '<a href="/admin/shop/product/{}/change/" class="btn-studio-action" title="Edit Parent Product" style="padding: 4px 8px; border-radius: 6px; background: #0f172a; color: #fff; font-size: 11px; font-weight: 700; text-decoration: none; display: inline-flex; align-items: center; gap: 4px;">'
            '<i class="fas fa-box-open"></i> Product</a>',
            obj.product.id
        )
    quick_actions.short_description = "Actions"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = (
        'sku_and_preview',
        'product_info',
        'category_hierarchy',
        'selling_price',
        'pricing_display',
        'quantity',
        'stock_status_badge',
        'colors_preview',
        'trending',
        'featured',
        'is_bestseller',
        'status_badge',
        'quick_actions'
    )
    list_display_links = ('sku_and_preview', 'product_info')
    list_editable = ('quantity', 'selling_price', 'trending', 'featured', 'is_bestseller')
    list_filter = (StockStatusFilter, 'category', 'trending', 'featured', 'is_bestseller', 'free_delivery', 'status', 'created_at')
    search_fields = ('name', 'brand', 'vendor', 'slug', 'id', 'category__name', 'categories__name')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductColorInline, ProductReviewInline]
    list_per_page = 25
    date_hierarchy = 'created_at'
    change_list_template = 'admin/shop/product/change_list.html'
    change_form_template = 'admin/shop/product/change_form.html'
    actions = [
        'make_published',
        'make_hidden',
        'mark_trending',
        'unmark_trending',
        'mark_featured',
        'unmark_featured',
        'mark_bestseller',
        'unmark_bestseller',
        'enable_free_delivery',
        'disable_free_delivery',
        'restock_quick_add_10',
        'restock_quick_add_25'
    ]

    fieldsets = (
        ('📦 Basic Product Information', {
            'fields': (('name', 'slug'), ('brand', 'vendor'))
        }),
        ('📁 Categories & Taxonomy', {
            'fields': ('categories', 'category'),
            'description': 'Select all subcategories where this product should appear. (Primary category is set automatically if left blank).'
        }),
        ('💰 Pricing, Inventory & Shipping', {
            'fields': (('original_price', 'selling_price'), ('quantity', 'free_delivery'))
        }),
        ('📝 Description & Feature Highlights', {
            'fields': ('description', 'highlights')
        }),
        ('🖼️ Main Product Image & Merchandising Flags', {
            'fields': ('product_image', ('status', 'trending', 'featured', 'is_bestseller'))
        }),
    )

    def sku_and_preview(self, obj):
        sku_str = f"#SK-PRD-{obj.id:04d}"
        if obj.product_image:
            thumb = f'<img src="{obj.product_image.url}" style="height: 42px; width: 42px; object-fit: contain; border-radius: 8px; border: 1px solid #e2e8f0; background: #ffffff; padding: 2px; box-shadow: 0 1px 3px rgba(0,0,0,0.06);" />'
        else:
            thumb = '<div style="height: 42px; width: 42px; border-radius: 8px; background: #f8fafc; border: 1px solid #e2e8f0; display: flex; align-items: center; justify-content: center; font-size: 18px; color: #94a3b8;"><i class="fas fa-box"></i></div>'

        return format_html(
            '<div style="display: flex; align-items: center; gap: 8px;">'
            '{}'
            '<div>'
            '<span style="font-family: monospace; font-size: 11px; font-weight: 800; color: #0284c7; background: #f0f9ff; border: 1px solid #bae6fd; padding: 2px 6px; border-radius: 5px; display: inline-block;">{}</span>'
            '</div>'
            '</div>',
            mark_safe(thumb),
            sku_str
        )
    sku_and_preview.short_description = "SKU & Image"

    def product_info(self, obj):
        brand_badge = f"<span style='font-size: 10px; font-weight: 700; color: #475569; background: #f1f5f9; padding: 1px 5px; border-radius: 4px; border: 1px solid #e2e8f0; text-transform: uppercase;'>{obj.brand}</span>" if obj.brand else ""
        vendor_str = f"<span style='font-size: 11px; color: #64748b; margin-left: 4px;'>via {obj.vendor}</span>" if obj.vendor else ""
        return format_html(
            '<div>'
            '<div style="font-weight: 700; font-size: 13px; color: #0f172a; line-height: 1.25; margin-bottom: 2px;">{}</div>'
            '<div style="display: flex; align-items: center; gap: 4px;">{}{}</div>'
            '</div>',
            obj.name,
            mark_safe(brand_badge),
            mark_safe(vendor_str)
        )
    product_info.short_description = "Product Name"

    def category_hierarchy(self, obj):
        cats = list(obj.categories.all())
        if cats:
            badges = "".join([f"<span style='display: inline-block; margin: 1px 3px 1px 0; padding: 2px 6px; border-radius: 4px; font-size: 10.5px; font-weight: 600; background: #f1f5f9; color: #475569; border: 1px solid #e2e8f0;'>{c.name}</span>" for c in cats[:2]])
            more = f"<span style='font-size: 10px; color: #64748b;'>+{len(cats)-2}</span>" if len(cats) > 2 else ""
            return mark_safe(f"{badges}{more}")
        if obj.category:
            return format_html('<span style="display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 10.5px; font-weight: 600; background: #f1f5f9; color: #475569; border: 1px solid #e2e8f0;">{}</span>', obj.category.name)
        return mark_safe("<span style='color: #cbd5e1;'>-</span>")
    category_hierarchy.short_description = "Category"

    def pricing_display(self, obj):
        if obj.original_price and obj.original_price > obj.selling_price:
            discount_pct = int(round((obj.original_price - obj.selling_price) / obj.original_price * 100))
            discount_badge = f"<span style='font-size: 10px; font-weight: 700; color: #15803d; background: #f0fdf4; border: 1px solid #bbf7d0; padding: 1px 4px; border-radius: 3px; margin-left: 3px;'>-{discount_pct}%</span>"
            mrp_str = f"<div style='font-size: 11px; color: #94a3b8; text-decoration: line-through;'>MRP ₹{int(obj.original_price):,} {discount_badge}</div>"
        else:
            mrp_str = "<div style='font-size: 10.5px; color: #94a3b8;'>Standard MRP</div>"
        return format_html(
            '<div>'
            '{}'
            '</div>',
            mark_safe(mrp_str)
        )
    pricing_display.short_description = "MSRP & Discount"

    def stock_status_badge(self, obj):
        if obj.quantity > 10:
            return badge_pill(f"Healthy", bg_color="#f0fdf4", text_color="#15803d", border_color="#bbf7d0", icon="fas fa-check-circle")
        elif obj.quantity > 0:
            return badge_pill(f"Low Stock", bg_color="#fffbeb", text_color="#b45309", border_color="#fde68a", icon="fas fa-exclamation-triangle")
        return badge_pill("Out of Stock", bg_color="#fef2f2", text_color="#dc2626", border_color="#fecaca", icon="fas fa-times-circle")
    stock_status_badge.short_description = "Stock Health"

    def colors_preview(self, obj):
        colors = obj.colors.all()
        if colors.exists():
            dots = "".join([
                f"<span title='{c.name}' style='display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: {c.color_code or '#cbd5e1'}; border: 1px solid rgba(0,0,0,0.2); margin-right: 2px; vertical-align: middle;'></span>"
                for c in colors[:4]
            ])
            extra = f"<span style='font-size: 10px; color: #64748b;'>+{colors.count()-4}</span>" if colors.count() > 4 else ""
            return mark_safe(f"<div style='display: flex; align-items: center;'>{dots}{extra} <span style='font-size: 11px; color: #475569; margin-left: 3px;'>({colors.count()})</span></div>")
        return mark_safe("<span style='color: #94a3b8; font-size: 11px;'>Standard</span>")
    colors_preview.short_description = "Variants"

    def status_badge(self, obj):
        if not obj.status:
            return badge_pill("Active", bg_color="#ecfdf5", text_color="#047857", border_color="#a7f3d0", icon="fas fa-globe")
        return badge_pill("Hidden", bg_color="#f8fafc", text_color="#64748b", border_color="#e2e8f0", icon="fas fa-eye-slash")
    status_badge.short_description = "Visibility"

    def quick_actions(self, obj):
        storefront_link = ""
        if obj.category:
            url = f"/collections/{obj.category.name}/{obj.name}"
            storefront_link = f'<a href="{url}" target="_blank" class="btn-studio-action" title="View on Customer Storefront" style="padding: 4px 7px; border-radius: 6px; background: #f1f5f9; color: #334155; border: 1px solid #cbd5e1; font-size: 11px; font-weight: 600; text-decoration: none; display: inline-flex; align-items: center;"><i class="fas fa-external-link-alt"></i></a>'

        return format_html(
            '<div style="display: inline-flex; align-items: center; gap: 4px;">'
            '<a href="/admin/shop/product/{}/change/" class="btn-studio-action" title="Edit Product in Studio" style="padding: 4px 8px; border-radius: 6px; background: #0f172a; color: #fff; font-size: 11px; font-weight: 700; text-decoration: none; display: inline-flex; align-items: center; gap: 4px;">'
            '<i class="fas fa-edit"></i> Edit</a>'
            '{}'
            '</div>',
            obj.id,
            mark_safe(storefront_link)
        )
    quick_actions.short_description = "Actions"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not obj.category and obj.categories.exists():
            obj.category = obj.categories.first()
            obj.save()

    # Bulk Actions
    @admin.action(description="🌐 Publish selected products (Make Active)")
    def make_published(self, request, queryset):
        updated = queryset.update(status=False)
        self.message_user(request, f"Successfully published {updated} product(s) to storefront.", level=messages.SUCCESS)

    @admin.action(description="👁️ Hide selected products (Make Draft/Hidden)")
    def make_hidden(self, request, queryset):
        updated = queryset.update(status=True)
        self.message_user(request, f"Successfully hidden {updated} product(s) from storefront.", level=messages.SUCCESS)

    @admin.action(description="🔥 Mark selected as Trending")
    def mark_trending(self, request, queryset):
        updated = queryset.update(trending=True)
        self.message_user(request, f"Marked {updated} product(s) as Trending.", level=messages.SUCCESS)

    @admin.action(description="Remove selected from Trending")
    def unmark_trending(self, request, queryset):
        updated = queryset.update(trending=False)
        self.message_user(request, f"Removed {updated} product(s) from Trending.", level=messages.SUCCESS)

    @admin.action(description="⭐ Mark selected as Featured")
    def mark_featured(self, request, queryset):
        updated = queryset.update(featured=True)
        self.message_user(request, f"Marked {updated} product(s) as Featured.", level=messages.SUCCESS)

    @admin.action(description="Remove selected from Featured")
    def unmark_featured(self, request, queryset):
        updated = queryset.update(featured=False)
        self.message_user(request, f"Removed {updated} product(s) from Featured.", level=messages.SUCCESS)

    @admin.action(description="🏆 Mark selected as Bestseller")
    def mark_bestseller(self, request, queryset):
        updated = queryset.update(is_bestseller=True)
        self.message_user(request, f"Marked {updated} product(s) as Bestsellers.", level=messages.SUCCESS)

    @admin.action(description="Remove selected from Bestseller")
    def unmark_bestseller(self, request, queryset):
        updated = queryset.update(is_bestseller=False)
        self.message_user(request, f"Removed {updated} product(s) from Bestsellers.", level=messages.SUCCESS)

    @admin.action(description="🚚 Enable Free Delivery for selected")
    def enable_free_delivery(self, request, queryset):
        updated = queryset.update(free_delivery=True)
        self.message_user(request, f"Enabled Free Delivery for {updated} product(s).", level=messages.SUCCESS)

    @admin.action(description="Disable Free Delivery for selected")
    def disable_free_delivery(self, request, queryset):
        updated = queryset.update(free_delivery=False)
        self.message_user(request, f"Disabled Free Delivery for {updated} product(s).", level=messages.SUCCESS)

    @admin.action(description="⚡ Quick Replenish: Add +10 units stock to selected")
    def restock_quick_add_10(self, request, queryset):
        for p in queryset:
            p.quantity += 10
            p.save(update_fields=['quantity'])
        self.message_user(request, f"Successfully added +10 units to {queryset.count()} product(s).", level=messages.SUCCESS)

    @admin.action(description="⚡ Quick Replenish: Add +25 units stock to selected")
    def restock_quick_add_25(self, request, queryset):
        for p in queryset:
            p.quantity += 25
            p.save(update_fields=['quantity'])
        self.message_user(request, f"Successfully added +25 units to {queryset.count()} product(s).", level=messages.SUCCESS)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/quick-stock/<int:add_units>/',
                self.admin_site.admin_view(self.quick_stock_view),
                name='shop_product_quick_stock'
            ),
            path(
                '<path:object_id>/quick-toggle/<str:field_name>/',
                self.admin_site.admin_view(self.quick_toggle_view),
                name='shop_product_quick_toggle'
            ),
        ]
        return custom_urls + urls

    def quick_stock_view(self, request, object_id, add_units):
        if request.method != 'POST':
            messages.error(request, "Invalid request method.")
            return redirect(f'/admin/shop/product/{object_id}/change/')

        product = get_object_or_404(Product, pk=object_id)
        if not self.has_change_permission(request, product):
            messages.error(request, "Permission denied.")
            return redirect(f'/admin/shop/product/{object_id}/change/')

        product.quantity += add_units
        product.save(update_fields=['quantity'])
        messages.success(request, f"Warehouse stock replenished: Added +{add_units} units to '{product.name}'. New stock: {product.quantity} units.")
        referer = request.META.get('HTTP_REFERER')
        if referer:
            return HttpResponseRedirect(referer)
        return redirect(f'/admin/shop/product/{object_id}/change/')

    def quick_toggle_view(self, request, object_id, field_name):
        if request.method != 'POST':
            messages.error(request, "Invalid request method.")
            return redirect(f'/admin/shop/product/{object_id}/change/')

        product = get_object_or_404(Product, pk=object_id)
        if not self.has_change_permission(request, product):
            messages.error(request, "Permission denied.")
            return redirect(f'/admin/shop/product/{object_id}/change/')

        if field_name not in ['status', 'trending', 'featured', 'is_bestseller', 'free_delivery']:
            messages.error(request, "Invalid field toggle.")
            return redirect(f'/admin/shop/product/{object_id}/change/')

        current_val = getattr(product, field_name)
        setattr(product, field_name, not current_val)
        product.save(update_fields=[field_name])
        new_status_str = "Enabled" if getattr(product, field_name) else "Disabled"
        if field_name == 'status':
            new_status_str = "Hidden / Draft" if product.status else "Published Live on Storefront"
        messages.success(request, f"Updated {field_name.replace('_', ' ').title()}: {new_status_str}.")
        referer = request.META.get('HTTP_REFERER')
        if referer:
            return HttpResponseRedirect(referer)
        return redirect(f'/admin/shop/product/{object_id}/change/')

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        products_qs = Product.objects.all()
        total_p = products_qs.count()
        total_units = products_qs.aggregate(s=Sum('quantity'))['s'] or 0
        total_val = products_qs.aggregate(v=Sum(F('quantity') * F('selling_price')))['v'] or 0
        low_stock = products_qs.filter(quantity__gt=0, quantity__lte=10).count()
        out_of_stock = products_qs.filter(quantity__lte=0).count()
        active_p = products_qs.filter(status=False).count()
        hidden_p = products_qs.filter(status=True).count()
        trending_p = products_qs.filter(trending=True).count()
        featured_p = products_qs.filter(featured=True).count()
        bestseller_p = products_qs.filter(is_bestseller=True).count()

        extra_context['product_stats'] = {
            'total_products': total_p,
            'total_units': total_units,
            'total_valuation': total_val,
            'low_stock_count': low_stock,
            'out_of_stock_count': out_of_stock,
            'active_count': active_p,
            'hidden_count': hidden_p,
            'trending_count': trending_p,
            'featured_count': featured_p,
            'bestseller_count': bestseller_p,
            'categories_count': Category.objects.count(),
            'variants_count': ProductColor.objects.count(),
        }
        return super().changelist_view(request, extra_context=extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        try:
            product = Product.objects.select_related('category').get(pk=object_id)
            stock_val = product.quantity * product.selling_price
            discount_pct = 0
            if product.original_price and product.original_price > product.selling_price:
                discount_pct = int(round((product.original_price - product.selling_price) / product.original_price * 100))

            from .models import OrderItem
            lifetime_sold = OrderItem.objects.filter(product=product).aggregate(s=Sum('quantity'))['s'] or 0

            storefront_url = ""
            if product.category:
                storefront_url = f"/collections/{product.category.name}/{product.name}"

            extra_context['product_studio_data'] = {
                'product': product,
                'stock_valuation': stock_val,
                'discount_pct': discount_pct,
                'lifetime_sales': lifetime_sold,
                'storefront_url': storefront_url,
            }
        except Exception:
            pass

        return super().change_view(request, object_id, form_url=form_url, extra_context=extra_context)



@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_id_badge',
        'customer_info',
        'items_preview',
        'total_badge',
        'payment_status_badge',
        'order_status_badge',
        'fulfillment_badge',
        'created_at_display',
        'quick_actions'
    )
    list_display_links = ('order_id_badge', 'customer_info')
    list_filter = ('status', 'payment_method', 'created_at', 'estimated_delivery')
    search_fields = (
        'id', 'tracking_number', 'user__username', 'user__email',
        'address__full_name', 'address__phone', 'address__city',
        'coupon_code', 'items__product_name'
    )
    inlines = [OrderItemInline]
    list_per_page = 25
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    change_form_template = 'admin/shop/order/change_form.html'
    change_list_template = 'admin/shop/order/change_list.html'
    actions = [
        'mark_as_confirmed',
        'mark_as_shipped',
        'mark_as_out_for_delivery',
        'mark_as_delivered',
        'mark_as_cancelled_restock'
    ]
    readonly_fields = ('created_at', 'subtotal', 'discount_amount', 'delivery_fee', 'total_amount', 'cancelled_at')

    fieldsets = (
        ('📦 Order Overview & Fulfillment Status', {
            'fields': (('status', 'payment_method'), ('tracking_number', 'estimated_delivery'), 'created_at')
        }),
        ('👤 Customer & Shipping Address', {
            'fields': ('user', 'address')
        }),
        ('💳 Financial Summary & Promo', {
            'fields': (('subtotal', 'coupon_code'), ('discount_amount', 'delivery_fee'), 'total_amount')
        }),
        ('🚫 Cancellation Details', {
            'fields': (('cancellation_reason', 'cancelled_at'),),
            'classes': ('collapse',),
        }),
    )

    def order_id_badge(self, obj):
        tracking = f"<div style='font-family: monospace; font-size: 10px; color: #64748b; margin-top: 2px;'><i class='fas fa-barcode' style='margin-right: 2px;'></i>{obj.tracking_number}</div>" if obj.tracking_number else ""
        order_code = f"#SK-ORD-{obj.id:05d}"
        return format_html(
            '<div style="line-height: 1.3;">'
            '<span style="font-family: monospace; font-size: 12.5px; font-weight: 800; color: #ff6000; background: #fff7ed; padding: 3px 8px; border-radius: 6px; border: 1px solid #fed7aa; display: inline-block;">'
            '{}</span>'
            '{}'
            '</div>',
            order_code,
            mark_safe(tracking)
        )
    order_id_badge.short_description = "Order ID"

    def customer_info(self, obj):
        full_name = obj.address.full_name if obj.address and obj.address.full_name else (obj.user.get_full_name() or obj.user.username)
        phone = obj.address.phone if obj.address and obj.address.phone else ""
        initial = (full_name[0] if full_name else obj.user.username[0]).upper()
        phone_html = f"<div style='font-size: 11px; color: #64748b;'><i class='fas fa-phone-alt' style='font-size: 9px; margin-right: 4px;'></i>{phone}</div>" if phone else ""
        return format_html(
            '<div style="display: flex; align-items: center; gap: 8px;">'
            '<div style="width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(135deg, #1e293b, #334155); color: #ffffff; font-weight: 700; font-size: 12px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">'
            '{}'
            '</div>'
            '<div>'
            '<div style="font-weight: 700; font-size: 12.5px; color: #0f172a; line-height: 1.2;">{}</div>'
            '<div style="font-size: 11px; color: #475569;">@{}</div>'
            '{}'
            '</div>'
            '</div>',
            initial,
            full_name,
            obj.user.username,
            mark_safe(phone_html)
        )
    customer_info.short_description = "Customer"

    def items_preview(self, obj):
        items = list(obj.items.select_related('product').all())
        count = len(items)
        if not count:
            return mark_safe("<span style='color: #94a3b8; font-size: 11px;'>No items</span>")
        first = items[0]
        p_name = first.product_name
        if len(p_name) > 22:
            p_name = p_name[:22] + "..."
        
        img_url = ""
        if first.product and first.product.product_image:
            img_url = first.product.product_image.url

        thumb_html = f'<img src="{img_url}" style="width: 28px; height: 28px; object-fit: contain; border-radius: 6px; border: 1px solid #cbd5e1; background: #fff; padding: 1px; margin-right: 6px; vertical-align: middle;" />' if img_url else '<span style="display: inline-flex; width: 28px; height: 28px; border-radius: 6px; background: #f1f5f9; align-items: center; justify-content: center; margin-right: 6px; font-size: 11px; color: #64748b;"><i class="fas fa-box"></i></span>'
        more_text = f" <span style='font-size: 10px; font-weight: 700; color: #ff6000; background: #fff7ed; padding: 1px 5px; border-radius: 9999px; margin-left: 3px;'>+{count-1}</span>" if count > 1 else ""
        color_snippet = f" <span style='font-size: 10.5px; color: #64748b;'>({first.color_name})</span>" if first.color_name else ""

        return format_html(
            '<div style="display: flex; align-items: center;">'
            '{}'
            '<div>'
            '<div style="font-weight: 600; font-size: 12px; color: #1e293b; line-height: 1.2;">{}{}{}</div>'
            '<div style="font-size: 10.5px; color: #64748b; margin-top: 1px;">{} item{} total &middot; x{}</div>'
            '</div>'
            '</div>',
            mark_safe(thumb_html),
            p_name,
            mark_safe(color_snippet),
            mark_safe(more_text),
            count,
            "s" if count != 1 else "",
            first.quantity
        )
    items_preview.short_description = "Ordered Items"

    def total_badge(self, obj):
        coupon_html = ""
        if obj.discount_amount and obj.discount_amount > 0:
            code_str = f" [{obj.coupon_code}]" if obj.coupon_code else ""
            coupon_html = f"<div style='font-size: 10px; font-weight: 600; color: #16a34a;'><i class='fas fa-tag'></i> -₹{int(obj.discount_amount):,}{code_str}</div>"
        return format_html(
            '<div>'
            '<div style="font-weight: 800; font-size: 13.5px; color: #0f172a; letter-spacing: -0.01em;">₹{}</div>'
            '{}'
            '</div>',
            f"{int(obj.total_amount):,}",
            mark_safe(coupon_html)
        )
    total_badge.short_description = "Total Amount"

    def payment_status_badge(self, obj):
        label, bg, text, border, icon = get_order_payment_status(obj)
        method_labels = {'cod': 'COD', 'card': 'Card', 'upi': 'UPI'}
        method_str = method_labels.get(obj.payment_method, obj.payment_method.upper())
        return format_html(
            '<div>'
            '<div style="margin-bottom: 3px;">{}</div>'
            '<span style="font-size: 10px; font-weight: 700; color: #475569; background: #f1f5f9; padding: 1px 6px; border-radius: 4px; border: 1px solid #e2e8f0;">'
            '<i class="fas fa-wallet" style="font-size: 9px; margin-right: 3px;"></i>{}'
            '</span>'
            '</div>',
            badge_pill(label, bg_color=bg, text_color=text, border_color=border, icon=icon),
            method_str
        )
    payment_status_badge.short_description = "Payment Status"

    def order_status_badge(self, obj):
        cfg = ORDER_STATUS_STYLES.get(obj.status, {
            'label': obj.get_status_display(),
            'bg': '#f1f5f9',
            'text': '#334155',
            'border': '#cbd5e1',
            'icon': 'fas fa-circle',
        })
        return badge_pill(cfg['label'], bg_color=cfg['bg'], text_color=cfg['text'], border_color=cfg['border'], icon=cfg['icon'])
    order_status_badge.short_description = "Order Status"

    def fulfillment_badge(self, obj):
        eta_str = ""
        if obj.status == 'delivered':
            eta_str = "<div style='font-size: 10.5px; font-weight: 600; color: #16a34a;'><i class='fas fa-check-circle'></i> Delivered</div>"
        elif obj.status == 'cancelled':
            eta_str = "<div style='font-size: 10.5px; font-weight: 600; color: #dc2626;'><i class='fas fa-ban'></i> Cancelled</div>"
        elif obj.estimated_delivery:
            eta_str = f"<div style='font-size: 10.5px; color: #64748b;'><i class='far fa-calendar-check' style='margin-right: 3px;'></i>ETA: {obj.estimated_delivery.strftime('%b %d')}</div>"

        return format_html(
            '<div>'
            '<span style="font-family: monospace; font-size: 11px; font-weight: 700; color: #334155; background: #f8fafc; border: 1px solid #cbd5e1; padding: 2px 6px; border-radius: 4px;">'
            '{}</span>'
            '{}'
            '</div>',
            obj.tracking_number or "Pending",
            mark_safe(eta_str)
        )
    fulfillment_badge.short_description = "Fulfillment"

    def created_at_display(self, obj):
        return format_html(
            '<div style="line-height: 1.25;">'
            '<div style="font-weight: 600; font-size: 11.5px; color: #1e293b;">{}</div>'
            '<div style="font-size: 10.5px; color: #64748b;">{}</div>'
            '</div>',
            obj.created_at.strftime("%d %b %Y"),
            obj.created_at.strftime("%I:%M %p")
        )
    created_at_display.short_description = "Date"

    def quick_actions(self, obj):
        return format_html(
            '<div style="display: inline-flex; align-items: center; gap: 4px;">'
            '<a href="/admin/shop/order/{}/change/" class="btn-studio-action" title="Open Fulfillment Studio" style="padding: 4px 8px; border-radius: 6px; background: #0f172a; color: #fff; font-size: 11px; font-weight: 700; text-decoration: none; display: inline-flex; align-items: center; gap: 4px;">'
            '<i class="fas fa-sliders-h"></i> Studio</a>'
            '<a href="/orders/{}/invoice" target="_blank" class="btn-studio-action" title="Print Invoice / Packing Slip" style="padding: 4px 7px; border-radius: 6px; background: #f1f5f9; color: #334155; border: 1px solid #cbd5e1; font-size: 11px; font-weight: 600; text-decoration: none; display: inline-flex; align-items: center;">'
            '<i class="fas fa-print"></i></a>'
            '<a href="/orders/{}" target="_blank" class="btn-studio-action" title="View Customer Storefront Page" style="padding: 4px 7px; border-radius: 6px; background: #f1f5f9; color: #334155; border: 1px solid #cbd5e1; font-size: 11px; font-weight: 600; text-decoration: none; display: inline-flex; align-items: center;">'
            '<i class="fas fa-external-link-alt"></i></a>'
            '</div>',
            obj.id, obj.id, obj.id
        )
    quick_actions.short_description = "Actions"

    # Bulk Operations
    @admin.action(description="📦 Mark selected orders as Confirmed & Packed")
    def mark_as_confirmed(self, request, queryset):
        updated = queryset.update(status='confirmed')
        self.message_user(request, f"Successfully updated {updated} order(s) to Confirmed & Packed.", level=messages.SUCCESS)

    @admin.action(description="🚚 Mark selected orders as Shipped")
    def mark_as_shipped(self, request, queryset):
        updated = queryset.update(status='shipped')
        self.message_user(request, f"Successfully updated {updated} order(s) to Shipped.", level=messages.SUCCESS)

    @admin.action(description="⚡ Mark selected orders as Out for Delivery")
    def mark_as_out_for_delivery(self, request, queryset):
        updated = queryset.update(status='out_for_delivery')
        self.message_user(request, f"Successfully updated {updated} order(s) to Out for Delivery.", level=messages.SUCCESS)

    @admin.action(description="✅ Mark selected orders as Delivered")
    def mark_as_delivered(self, request, queryset):
        updated = queryset.update(status='delivered')
        self.message_user(request, f"Successfully updated {updated} order(s) to Delivered.", level=messages.SUCCESS)

    @admin.action(description="🚫 Cancel selected orders & restore inventory")
    def mark_as_cancelled_restock(self, request, queryset):
        cancelled_count = 0
        restocked_items_count = 0
        for order in queryset:
            if order.status != 'cancelled':
                order.status = 'cancelled'
                order.cancelled_at = timezone.now()
                order.cancellation_reason = "Bulk cancelled by administrator in order operations studio"
                order.save()
                for item in order.items.all():
                    if item.product:
                        item.product.quantity = item.product.quantity + item.quantity
                        item.product.save(update_fields=['quantity'])
                        if item.color_name:
                            c_var = item.product.colors.filter(name=item.color_name).first()
                            if c_var:
                                c_var.quantity = c_var.quantity + item.quantity
                                c_var.save(update_fields=['quantity'])
                        restocked_items_count += item.quantity
                cancelled_count += 1
        self.message_user(
            request,
            f"Successfully cancelled {cancelled_count} order(s) and restored {restocked_items_count} item(s) to warehouse inventory.",
            level=messages.SUCCESS
        )

    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            old_status = form.initial.get('status')
            new_status = form.cleaned_data.get('status')
            if new_status == 'cancelled' and old_status != 'cancelled':
                if not obj.cancelled_at:
                    obj.cancelled_at = timezone.now()
                if not obj.cancellation_reason:
                    obj.cancellation_reason = "Cancelled by Administrator"
                restocked = 0
                for item in obj.items.all():
                    if item.product:
                        item.product.quantity = item.product.quantity + item.quantity
                        item.product.save(update_fields=['quantity'])
                        if item.color_name:
                            c_var = item.product.colors.filter(name=item.color_name).first()
                            if c_var:
                                c_var.quantity = c_var.quantity + item.quantity
                                c_var.save(update_fields=['quantity'])
                        restocked += item.quantity
                self.message_user(
                    request,
                    f"Order #{obj.id} marked as Cancelled. {restocked} item(s) safely returned to warehouse stock.",
                    level=messages.SUCCESS
                )
        super().save_model(request, obj, form, change)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/quick-status/<str:new_status>/',
                self.admin_site.admin_view(self.quick_status_view),
                name='shop_order_quick_status'
            ),
        ]
        return custom_urls + urls

    def quick_status_view(self, request, object_id, new_status):
        if request.method != 'POST':
            messages.error(request, "Invalid request method.")
            return redirect(f'/admin/shop/order/{object_id}/change/')

        order = get_object_or_404(Order, pk=object_id)
        if not self.has_change_permission(request, order):
            messages.error(request, "You do not have permission to modify this order.")
            return redirect(f'/admin/shop/order/{object_id}/change/')

        valid_statuses = dict(Order.STATUS_CHOICES)
        if new_status not in valid_statuses:
            messages.error(request, f"Invalid status '{new_status}'.")
            return redirect(f'/admin/shop/order/{object_id}/change/')

        old_status = order.status
        if old_status == new_status:
            messages.info(request, f"Order #{order.id} is already in '{valid_statuses[new_status]}' state.")
            return redirect(f'/admin/shop/order/{object_id}/change/')

        if new_status == 'cancelled' and old_status != 'cancelled':
            order.status = 'cancelled'
            order.cancelled_at = timezone.now()
            order.cancellation_reason = request.POST.get('cancellation_reason', 'Cancelled via Order Fulfillment Studio by Administrator')
            order.save()
            restocked = 0
            for item in order.items.all():
                if item.product:
                    item.product.quantity = item.product.quantity + item.quantity
                    item.product.save(update_fields=['quantity'])
                    if item.color_name:
                        c_var = item.product.colors.filter(name=item.color_name).first()
                        if c_var:
                            c_var.quantity = c_var.quantity + item.quantity
                            c_var.save(update_fields=['quantity'])
                    restocked += item.quantity
            messages.success(request, f"Order #{order.id} has been Cancelled. {restocked} item(s) safely returned to warehouse inventory.")
        else:
            order.status = new_status
            order.save()
            messages.success(request, f"Order #{order.id} status successfully transitioned to '{valid_statuses[new_status]}'.")

        return redirect(f'/admin/shop/order/{object_id}/change/')

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        orders_qs = Order.objects.all()
        total_orders = orders_qs.count()
        total_rev = orders_qs.exclude(status='cancelled').aggregate(s=Sum('total_amount'))['s'] or 0
        counts = dict(orders_qs.values_list('status').annotate(c=Count('id')))

        placed_c = counts.get('placed', 0)
        confirmed_c = counts.get('confirmed', 0)
        shipped_c = counts.get('shipped', 0)
        out_c = counts.get('out_for_delivery', 0)
        delivered_c = counts.get('delivered', 0)
        cancelled_c = counts.get('cancelled', 0)

        extra_context['order_stats'] = {
            'total_orders': total_orders,
            'total_revenue': total_rev,
            'placed': placed_c,
            'confirmed': confirmed_c,
            'shipped': shipped_c,
            'out_for_delivery': out_c,
            'delivered': delivered_c,
            'cancelled': cancelled_c,
            'processing': placed_c + confirmed_c,
            'in_transit': shipped_c + out_c,
        }
        return super().changelist_view(request, extra_context=extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        try:
            order = Order.objects.select_related('user', 'address').prefetch_related('items__product__colors').get(pk=object_id)
            enriched_items = []
            for it in order.items.all():
                img_url = ""
                color_variant = None
                if it.product:
                    if it.color_name:
                        color_variant = it.product.colors.filter(name=it.color_name).first()
                    if color_variant and color_variant.image:
                        img_url = color_variant.image.url
                    elif it.product.product_image:
                        img_url = it.product.product_image.url

                stock_qty = 0
                if color_variant:
                    stock_qty = color_variant.quantity
                elif it.product:
                    stock_qty = it.product.quantity

                enriched_items.append({
                    'item': it,
                    'product': it.product,
                    'image_url': img_url,
                    'color_name': it.color_name,
                    'color_code': it.color_code or (color_variant.color_code if color_variant else '#cbd5e1'),
                    'unit_price': it.price,
                    'quantity': it.quantity,
                    'total_price': it.total_price,
                    'stock_qty': stock_qty,
                    'is_low_stock': stock_qty <= 5,
                })

            step_sequence = [
                ('placed', 'Order Placed', 'fas fa-clipboard-check', 'Order received & logged'),
                ('confirmed', 'Confirmed & Packed', 'fas fa-box-open', 'Inventory allocated & packed'),
                ('shipped', 'Shipped', 'fas fa-truck-moving', 'Handed over to carrier'),
                ('out_for_delivery', 'Out for Delivery', 'fas fa-shipping-fast', 'Local courier out for delivery'),
                ('delivered', 'Delivered', 'fas fa-check-circle', 'Delivered to customer'),
            ]

            status_indices = {s[0]: i for i, s in enumerate(step_sequence)}
            current_idx = status_indices.get(order.status, -1)

            stepper = []
            for i, (slug, label, icon, desc) in enumerate(step_sequence):
                if order.status == 'cancelled':
                    is_done = False
                    is_active = False
                else:
                    is_done = (i < current_idx)
                    is_active = (i == current_idx)
                stepper.append({
                    'slug': slug,
                    'label': label,
                    'icon': icon,
                    'desc': desc,
                    'is_done': is_done,
                    'is_active': is_active,
                })

            pay_label, pay_bg, pay_text, pay_border, pay_icon = get_order_payment_status(order)

            extra_context['studio_data'] = {
                'order': order,
                'items': enriched_items,
                'items_count': len(enriched_items),
                'stepper': stepper,
                'is_cancelled': (order.status == 'cancelled'),
                'payment': {
                    'method_display': order.get_payment_method_display(),
                    'status_label': pay_label,
                    'bg': pay_bg,
                    'text': pay_text,
                    'border': pay_border,
                    'icon': pay_icon,
                },
                'can_confirm': order.status == 'placed',
                'can_ship': order.status in ['placed', 'confirmed'],
                'can_out_delivery': order.status == 'shipped',
                'can_deliver': order.status in ['shipped', 'out_for_delivery'],
                'can_cancel': order.status != 'cancelled',
            }
        except Exception:
            pass

        return super().change_view(request, object_id, form_url=form_url, extra_context=extra_context)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order_link', 'product_thumbnail', 'product_name', 'color_badge', 'quantity', 'price_display', 'total_display')
    list_filter = ('order__status', 'order__created_at')
    search_fields = ('product_name', 'color_name', 'order__id', 'order__tracking_number')

    def order_link(self, obj):
        order_code = f"#SK-ORD-{obj.order.id:05d}"
        return format_html(
            '<a href="/admin/shop/order/{}/change/" style="font-weight: 700; color: #ff6000; text-decoration: none;">'
            '<span style="font-family: monospace; background: #fff7ed; padding: 2px 7px; border-radius: 6px; border: 1px solid #fed7aa;">{}</span></a>',
            obj.order.id, order_code
        )
    order_link.short_description = "Order"

    def product_thumbnail(self, obj):
        if obj and obj.product and obj.product.product_image:
            return format_html(
                '<img src="{}" style="height: 36px; width: 36px; object-fit: contain; border-radius: 6px; border: 1px solid #cbd5e1; background: #ffffff; padding: 2px;" />',
                obj.product.product_image.url
            )
        return mark_safe('<div style="width: 36px; height: 36px; border-radius: 6px; background: #f1f5f9; display: inline-flex; align-items: center; justify-content: center; color: #94a3b8;"><i class="fas fa-box"></i></div>')
    product_thumbnail.short_description = "Photo"

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
    change_list_template = 'admin/shop/review/change_list.html'

    list_display = ('product_preview', 'user_link', 'star_rating_badge', 'comment_snippet', 'quick_actions', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__name', 'user__username', 'title', 'comment')
    date_hierarchy = 'created_at'
    list_per_page = 25

    def product_preview(self, obj):
        img_html = ''
        if obj.product.product_image:
            img_html = f'<img src="{obj.product.product_image.url}" style="width: 32px; height: 32px; object-fit: contain; border-radius: 6px; border: 1px solid #cbd5e1; background: #fff;" />'
        return format_html(
            '<div style="display: flex; align-items: center; gap: 8px;">'
            '{}'
            '<div>'
            '<a href="/admin/shop/product/{}/change/" style="font-weight: 700; color: #0284c7; text-decoration: none;">{}</a>'
            '<div style="font-size: 11px; color: #64748b;">{}</div>'
            '</div>'
            '</div>',
            mark_safe(img_html), obj.product.id, obj.product.name, obj.product.category.name if obj.product.category else 'Uncategorized'
        )
    product_preview.short_description = "Product"

    def user_link(self, obj):
        return format_html(
            '<a href="/admin/auth/user/{}/change/" style="font-weight: 700; color: #0f172a; text-decoration: none; display: inline-flex; align-items: center; gap: 4px;">'
            '<i class="fas fa-user-circle" style="color: #64748b;"></i>{}</a>',
            obj.user.id, obj.user.username
        )
    user_link.short_description = "Customer"

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

    def quick_actions(self, obj):
        return format_html(
            '<div style="display: inline-flex; align-items: center; gap: 4px;">'
            '<a href="/admin/shop/product/{}/change/" class="btn-studio-action" style="padding: 4px 7px; border-radius: 6px; background: #f8fafc; color: #334155; border: 1px solid #cbd5e1; font-size: 11px; text-decoration: none;" title="Edit Product"><i class="fas fa-box-open"></i></a>'
            '<a href="/admin/auth/user/{}/change/" class="btn-studio-action" style="padding: 4px 7px; border-radius: 6px; background: #0f172a; color: #ffffff; font-size: 11px; text-decoration: none;" title="Customer CRM"><i class="fas fa-id-card"></i> CRM</a>'
            '</div>',
            obj.product.id, obj.user.id
        )
    quick_actions.short_description = "Actions"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        total_reviews = Review.objects.count()
        avg_rating = Review.objects.aggregate(a=Avg('rating'))['a'] or 0.0
        five_star_count = Review.objects.filter(rating=5).count()
        four_star_count = Review.objects.filter(rating=4).count()
        critical_count = Review.objects.filter(rating__lte=2).count()
        reviewed_products_count = Review.objects.values('product').distinct().count()

        extra_context['review_stats'] = {
            'total_reviews': total_reviews,
            'avg_rating': avg_rating,
            'five_star_count': five_star_count,
            'four_star_count': four_star_count,
            'critical_count': critical_count,
            'reviewed_products_count': reviewed_products_count,
        }
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    change_list_template = 'admin/shop/address/change_list.html'
    list_display = ('full_name', 'user_link', 'phone_display', 'location_summary', 'default_badge', 'quick_actions', 'created_at')
    search_fields = ('full_name', 'phone', 'city', 'pincode', 'user__username', 'user__email')
    list_filter = ('is_default', 'state')

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        total_addresses = Address.objects.count()
        default_addresses = Address.objects.filter(is_default=True).count()
        unique_cities = Address.objects.values('city').distinct().count()
        customer_count = Address.objects.values('user').distinct().count()
        extra_context['address_stats'] = {
            'total_addresses': total_addresses,
            'default_addresses': default_addresses,
            'unique_cities': unique_cities,
            'customer_count': customer_count,
        }
        return super().changelist_view(request, extra_context=extra_context)

    def user_link(self, obj):
        return format_html(
            '<a href="/admin/auth/user/{}/change/" style="font-weight: 700; color: #0284c7; text-decoration: none;">'
            '<i class="fas fa-user-circle" style="margin-right: 4px;"></i>{}</a>',
            obj.user.id, obj.user.username
        )
    user_link.short_description = "Customer"

    def phone_display(self, obj):
        if obj.phone:
            return format_html(
                '<a href="tel:{}" style="color: #0f172a; text-decoration: none; font-weight: 600;">'
                '<i class="fas fa-phone-alt" style="color: #10b981; font-size: 10px; margin-right: 4px;"></i>{}</a>',
                obj.phone, obj.phone
            )
        return mark_safe("<span style='color: #94a3b8;'>-</span>")
    phone_display.short_description = "Phone"

    def location_summary(self, obj):
        return f"{obj.city}, {obj.state} - {obj.pincode}"
    location_summary.short_description = "Location"

    def default_badge(self, obj):
        if obj.is_default:
            return badge_pill("Default Address", bg_color="#ecfdf5", text_color="#047857", border_color="#a7f3d0", icon="fas fa-star")
        return mark_safe("<span style='color: #cbd5e1;'>-</span>")
    default_badge.short_description = "Default"

    def quick_actions(self, obj):
        whatsapp = f'<a href="https://wa.me/{obj.phone}" target="_blank" class="btn-studio-action" title="WhatsApp" style="padding: 4px 7px; border-radius: 6px; background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; font-size: 11px; text-decoration: none;"><i class="fab fa-whatsapp"></i></a>' if obj.phone else ''
        return format_html(
            '<div style="display: inline-flex; align-items: center; gap: 4px;">'
            '<a href="/admin/auth/user/{}/change/" class="btn-studio-action" title="Customer CRM" style="padding: 4px 8px; border-radius: 6px; background: #0f172a; color: #ffffff; font-size: 11px; font-weight: 700; text-decoration: none; display: inline-flex; align-items: center; gap: 4px;">'
            '<i class="fas fa-id-card"></i> CRM</a>'
            '{}'
            '</div>',
            obj.user.id, mark_safe(whatsapp)
        )
    quick_actions.short_description = "Actions"


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user_link', 'product', 'color_badge', 'product_qty', 'unit_price_display', 'total_price_display', 'created_at')
    search_fields = ('user__username', 'product__name', 'color__name')
    list_filter = ('created_at',)

    def user_link(self, obj):
        return format_html(
            '<a href="/admin/auth/user/{}/change/" style="font-weight: 700; color: #0284c7; text-decoration: none;">'
            '<i class="fas fa-user-circle" style="margin-right: 4px;"></i>{}</a>',
            obj.user.id, obj.user.username
        )
    user_link.short_description = "Customer"

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
    list_display = ('user_link', 'product', 'created_at')
    search_fields = ('user__username', 'product__name')
    list_filter = ('created_at',)

    def user_link(self, obj):
        return format_html(
            '<a href="/admin/auth/user/{}/change/" style="font-weight: 700; color: #0284c7; text-decoration: none;">'
            '<i class="fas fa-user-circle" style="margin-right: 4px;"></i>{}</a>',
            obj.user.id, obj.user.username
        )
    user_link.short_description = "Customer"


AVATAR_PALETTES = [
    ('#eff6ff', '#1d4ed8'), # Blue
    ('#f0fdf4', '#15803d'), # Green
    ('#faf5ff', '#7c3aed'), # Purple
    ('#fff7ed', '#c2410c'), # Orange
    ('#fdf2f8', '#be185d'), # Pink
    ('#ecfeff', '#0e7490'), # Cyan
]


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    change_list_template = 'admin/shop/coupon/change_list.html'
    change_form_template = 'admin/shop/coupon/change_form.html'

    list_display = ('voucher_code_badge', 'discount_badge', 'eligibility_terms', 'redemption_analytics', 'active_badge', 'quick_actions', 'created_at')
    search_fields = ('code', 'description')
    list_filter = ('active', 'discount_type', 'created_at')
    date_hierarchy = 'created_at'
    list_per_page = 25

    fieldsets = (
        ('🎟️ Coupon Voucher Code', {
            'fields': ('code', 'description')
        }),
        ('💰 Discount Configuration', {
            'fields': (('discount_type', 'discount_value'), ('min_order_amount', 'max_discount'))
        }),
        ('⚙️ Activation Status', {
            'fields': ('active',)
        }),
    )

    def voucher_code_badge(self, obj):
        desc = f'<div style="font-size: 11px; color: #64748b; margin-top: 3px;">{obj.description}</div>' if obj.description else ''
        return format_html(
            '<div>'
            '<div style="display: inline-flex; align-items: center; gap: 6px;">'
            '<a href="/admin/shop/coupon/{}/change/" style="font-family: monospace; font-size: 13px; font-weight: 800; background: #fff7ed; color: #ea580c; border: 1px solid #fed7aa; padding: 2px 9px; border-radius: 6px; letter-spacing: 0.05em; text-decoration: none;">'
            '<i class="fas fa-tag" style="margin-right: 4px; font-size: 11px;"></i>{}</a>'
            '</div>'
            '{}'
            '</div>',
            obj.id, obj.code, mark_safe(desc)
        )
    voucher_code_badge.short_description = "Coupon Code"

    def discount_badge(self, obj):
        if obj.discount_type == 'percentage':
            val_str = f"{int(obj.discount_value) if obj.discount_value == int(obj.discount_value) else obj.discount_value}% OFF"
            return badge_pill(val_str, bg_color="#eff6ff", text_color="#1d4ed8", border_color="#bfdbfe", icon="fas fa-percent")
        else:
            val_str = f"₹{int(obj.discount_value):,} OFF"
            return badge_pill(val_str, bg_color="#f0fdf4", text_color="#15803d", border_color="#bbf7d0", icon="fas fa-rupee-sign")
    discount_badge.short_description = "Discount Benefit"

    def eligibility_terms(self, obj):
        min_spend = f"Min Spend: ₹{int(obj.min_order_amount):,}"
        cap = f"Cap: ₹{int(obj.max_discount):,}" if obj.max_discount else "No Cap"
        return format_html(
            '<div style="font-size: 12px; color: #334155; font-weight: 600;">'
            '<div>{}</div>'
            '<div style="font-size: 11px; color: #64748b; font-weight: 400; margin-top: 1px;">{}</div>'
            '</div>',
            min_spend, cap
        )
    eligibility_terms.short_description = "Rules & Criteria"

    def redemption_analytics(self, obj):
        orders = Order.objects.filter(coupon_code=obj.code)
        count = orders.count()
        savings = orders.aggregate(s=Sum('discount_amount'))['s'] or 0.0
        if count > 0:
            return format_html(
                '<div style="font-size: 12px;">'
                '<a href="/admin/shop/order/?coupon_code__exact={}" style="font-weight: 700; color: #2563eb; text-decoration: none;">'
                '<i class="fas fa-receipt" style="margin-right: 3px;"></i>{} checkouts</a>'
                '<div style="font-size: 11px; color: #16a34a; font-weight: 600; margin-top: 1px;">₹{} saved</div>'
                '</div>',
                obj.code, count, f"{int(savings):,}"
            )
        return mark_safe('<span style="color: #94a3b8; font-size: 11px;">0 redemptions</span>')
    redemption_analytics.short_description = "Redemptions & Impact"

    def active_badge(self, obj):
        if obj.active:
            return badge_pill("Active Promotion", bg_color="#ecfdf5", text_color="#047857", border_color="#a7f3d0", icon="fas fa-check-circle")
        return badge_pill("Disabled", bg_color="#fef2f2", text_color="#dc2626", border_color="#fecaca", icon="fas fa-ban")
    active_badge.short_description = "Status"

    def quick_actions(self, obj):
        toggle_title = "Deactivate Promo" if obj.active else "Activate Promo"
        toggle_icon = "fa-ban" if obj.active else "fa-check"
        toggle_style = "background: #fef2f2; color: #dc2626; border: 1px solid #fecaca;" if obj.active else "background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0;"
        return format_html(
            '<div style="display: inline-flex; align-items: center; gap: 5px;">'
            '<a href="/admin/shop/coupon/{}/change/" class="btn-studio-action" style="padding: 4px 8px; border-radius: 6px; background: #0f172a; color: #ffffff; font-size: 11px; font-weight: 700; text-decoration: none; display: inline-flex; align-items: center; gap: 4px;" title="Open Voucher Studio">'
            '<i class="fas fa-sliders-h"></i> Studio</a>'
            '<a href="/admin/shop/coupon/{}/toggle-active/" class="btn-studio-action" style="padding: 4px 7px; border-radius: 6px; font-size: 11px; font-weight: 700; text-decoration: none; display: inline-flex; align-items: center; gap: 3px; {}" title="{}">'
            '<i class="fas {}"></i></a>'
            '</div>',
            obj.id, obj.id, mark_safe(toggle_style), toggle_title, mark_safe(toggle_icon)
        )
    quick_actions.short_description = "Actions"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:coupon_id>/toggle-active/',
                self.admin_site.admin_view(self.toggle_active_view),
                name='shop_coupon_toggle_active'
            ),
        ]
        return custom_urls + urls

    def toggle_active_view(self, request, coupon_id):
        coupon = get_object_or_404(Coupon, pk=coupon_id)
        if not self.has_change_permission(request, coupon):
            messages.error(request, "Permission denied.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER') or reverse('admin:shop_coupon_changelist'))
        coupon.active = not coupon.active
        coupon.save(update_fields=['active'])
        status_label = "activated" if coupon.active else "disabled"
        messages.success(request, f"Coupon voucher '{coupon.code}' successfully {status_label}.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER') or reverse('admin:shop_coupon_changelist'))

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        total_coupons = Coupon.objects.count()
        active_coupons = Coupon.objects.filter(active=True).count()

        coupon_orders = Order.objects.exclude(coupon_code__isnull=True).exclude(coupon_code='')
        total_redemptions = coupon_orders.count()
        total_discount_granted = coupon_orders.aggregate(s=Sum('discount_amount'))['s'] or 0.0
        aov_savings = (total_discount_granted / total_redemptions) if total_redemptions > 0 else 0.0

        top_code_data = coupon_orders.values('coupon_code').annotate(
            cnt=Count('id'),
            sav=Sum('discount_amount')
        ).order_by('-cnt').first()

        top_coupon = None
        top_coupon_orders = 0
        top_coupon_savings = 0.0
        if top_code_data:
            top_coupon = Coupon.objects.filter(code=top_code_data['coupon_code']).first()
            top_coupon_orders = top_code_data['cnt']
            top_coupon_savings = top_code_data['sav'] or 0.0

        extra_context['marketing_stats'] = {
            'total_coupons': total_coupons,
            'active_coupons': active_coupons,
            'total_redemptions': total_redemptions,
            'total_discount_granted': total_discount_granted,
            'aov_savings': aov_savings,
            'top_coupon': top_coupon,
            'top_coupon_orders': top_coupon_orders,
            'top_coupon_savings': top_coupon_savings,
        }
        return super().changelist_view(request, extra_context=extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        coupon = self.get_object(request, object_id)
        if coupon:
            orders = Order.objects.filter(coupon_code=coupon.code).select_related('user').order_by('-created_at')[:20]
            redemptions_count = Order.objects.filter(coupon_code=coupon.code).count()
            total_savings = Order.objects.filter(coupon_code=coupon.code).aggregate(s=Sum('discount_amount'))['s'] or 0.0
            total_sales_volume = Order.objects.filter(coupon_code=coupon.code).aggregate(s=Sum('total_amount'))['s'] or 0.0

            extra_context['coupon_studio_data'] = {
                'orders': orders,
                'redemptions_count': redemptions_count,
                'total_savings': total_savings,
                'total_sales_volume': total_sales_volume,
            }
        return super().change_view(request, object_id, form_url, extra_context=extra_context)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    change_list_template = 'admin/shop/contactmessage/change_list.html'

    list_display = ('sender_info', 'customer_link', 'subject_and_preview', 'resolved_badge', 'quick_actions', 'created_at')
    list_filter = ('is_resolved', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 25
    actions = ['mark_as_resolved', 'mark_as_unresolved']

    def sender_info(self, obj):
        initials = ''.join([part[0].upper() for part in obj.name.strip().split()[:2]]) if obj.name else "U"
        bg, text = AVATAR_PALETTES[obj.id % len(AVATAR_PALETTES)]
        return format_html(
            '<div style="display: flex; align-items: center; gap: 8px;">'
            '<div style="width: 32px; height: 32px; border-radius: 50%; background: {}; color: {}; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 11px; flex-shrink: 0; border: 1px solid rgba(0,0,0,0.06);">'
            '{}</div>'
            '<div>'
            '<div style="font-weight: 700; color: #0f172a; font-size: 13px;">{}</div>'
            '<a href="mailto:{}" style="color: #64748b; font-size: 11px; text-decoration: none;">{}</a>'
            '</div>'
            '</div>',
            bg, text, initials, obj.name, obj.email, obj.email
        )
    sender_info.short_description = "Sender"

    def customer_link(self, obj):
        if obj.user:
            return format_html(
                '<a href="/admin/auth/user/{}/change/" style="font-weight: 700; color: #0284c7; text-decoration: none; display: inline-flex; align-items: center; gap: 5px;">'
                '<i class="fas fa-user-circle"></i>@{}</a>',
                obj.user.id, obj.user.username
            )
        return mark_safe(
            '<span style="color: #64748b; font-size: 11px; background: #f8fafc; border: 1px solid #e2e8f0; padding: 2px 7px; border-radius: 9999px; font-weight: 600;">'
            '<i class="fas fa-user-clock" style="margin-right: 3px;"></i>Guest Visitor</span>'
        )
    customer_link.short_description = "Account"

    def subject_and_preview(self, obj):
        preview = obj.message[:70] + ('...' if len(obj.message) > 70 else '')
        return format_html(
            '<div style="max-width: 380px;">'
            '<div style="font-weight: 700; color: #0f172a; font-size: 12.5px; margin-bottom: 2px;">{}</div>'
            '<div style="font-size: 11.5px; color: #64748b; line-height: 1.35;">{}</div>'
            '</div>',
            obj.subject, preview
        )
    subject_and_preview.short_description = "Subject & Message"

    def resolved_badge(self, obj):
        if obj.is_resolved:
            return badge_pill("Resolved", bg_color="#ecfdf5", text_color="#047857", border_color="#a7f3d0", icon="fas fa-check-circle")
        return badge_pill("Pending Action", bg_color="#fffbeb", text_color="#d97706", border_color="#fde68a", icon="fas fa-clock")
    resolved_badge.short_description = "Status"

    def quick_actions(self, obj):
        crm_btn = f'<a href="/admin/auth/user/{obj.user.id}/change/" class="btn-studio-action" style="padding: 4px 7px; border-radius: 6px; background: #0f172a; color: #ffffff; font-size: 11px; text-decoration: none;" title="Customer CRM Profile"><i class="fas fa-id-card"></i> CRM</a>' if obj.user else ''
        toggle_title = "Mark as Pending" if obj.is_resolved else "Mark as Resolved"
        toggle_icon = "fa-undo" if obj.is_resolved else "fa-check"
        toggle_style = "background: #f8fafc; color: #64748b; border: 1px solid #cbd5e1;" if obj.is_resolved else "background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0;"
        return format_html(
            '<div style="display: inline-flex; align-items: center; gap: 4px;">'
            '<a href="mailto:{}?subject=Re: {}" class="btn-studio-action" style="padding: 4px 8px; border-radius: 6px; background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; font-size: 11px; font-weight: 700; text-decoration: none; display: inline-flex; align-items: center; gap: 4px;" title="Direct Email Reply">'
            '<i class="fas fa-reply"></i> Reply</a>'
            '<a href="/admin/shop/contactmessage/{}/toggle-resolved/" class="btn-studio-action" style="padding: 4px 7px; border-radius: 6px; font-size: 11px; font-weight: 700; text-decoration: none; display: inline-flex; align-items: center; gap: 3px; {}" title="{}">'
            '<i class="fas {}"></i></a>'
            '{}'
            '</div>',
            obj.email, obj.subject, obj.id, mark_safe(toggle_style), toggle_title, mark_safe(toggle_icon), mark_safe(crm_btn)
        )
    quick_actions.short_description = "Actions"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:message_id>/toggle-resolved/',
                self.admin_site.admin_view(self.toggle_resolved_view),
                name='shop_contactmessage_toggle_resolved'
            ),
        ]
        return custom_urls + urls

    def toggle_resolved_view(self, request, message_id):
        msg = get_object_or_404(ContactMessage, pk=message_id)
        if not self.has_change_permission(request, msg):
            messages.error(request, "Permission denied.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER') or reverse('admin:shop_contactmessage_changelist'))
        msg.is_resolved = not msg.is_resolved
        msg.save(update_fields=['is_resolved'])
        status_label = "marked as Resolved" if msg.is_resolved else "marked as Pending"
        messages.success(request, f"Customer inquiry from '{msg.name}' successfully {status_label}.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER') or reverse('admin:shop_contactmessage_changelist'))

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        total_messages = ContactMessage.objects.count()
        pending_count = ContactMessage.objects.filter(is_resolved=False).count()
        resolved_count = ContactMessage.objects.filter(is_resolved=True).count()
        registered_user_count = ContactMessage.objects.filter(user__isnull=False).count()
        guest_count = ContactMessage.objects.filter(user__isnull=True).count()

        extra_context['inquiry_stats'] = {
            'total_messages': total_messages,
            'pending_count': pending_count,
            'resolved_count': resolved_count,
            'registered_user_count': registered_user_count,
            'guest_count': guest_count,
        }
        return super().changelist_view(request, extra_context=extra_context)

    @admin.action(description="Mark selected inquiries as Resolved")
    def mark_as_resolved(self, request, queryset):
        queryset.update(is_resolved=True)

    @admin.action(description="Mark selected inquiries as Unresolved")
    def mark_as_unresolved(self, request, queryset):
        queryset.update(is_resolved=False)


# ==============================================================================
# Customer CRM Intelligence & Management Hub
# ==============================================================================

def get_customer_phone(user):
    addr = user.addresses.filter(is_default=True).first() or user.addresses.first()
    if addr and addr.phone:
        return addr.phone
    order = user.orders.filter(address__isnull=False).first()
    if order and order.address and order.address.phone:
        return order.address.phone
    return None

def get_customer_location(user):
    addr = user.addresses.filter(is_default=True).first() or user.addresses.first()
    if addr:
        return f"{addr.city}, {addr.state}"
    order = user.orders.filter(address__isnull=False).first()
    if order and order.address:
        return f"{order.address.city}, {order.address.state}"
    return None


class CustomerTypeFilter(admin.SimpleListFilter):
    title = 'Customer Segmentation'
    parameter_name = 'customer_type'

    def lookups(self, request, model_admin):
        return (
            ('buyer', '🛍️ Active Buyers (1+ Orders)'),
            ('repeat', '🔁 Repeat Buyers (2+ Orders)'),
            ('vip', '👑 VIP Spenders (>₹25,000)'),
            ('prospect', '🌱 Prospects (0 Orders)'),
            ('staff', '🛡️ Store Staff / Admin'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'buyer':
            return queryset.filter(orders__isnull=False).distinct()
        elif self.value() == 'repeat':
            return queryset.annotate(order_cnt=Count('orders')).filter(order_cnt__gt=1)
        elif self.value() == 'vip':
            return queryset.annotate(
                spend=Coalesce(Sum('orders__total_amount', filter=~Q(orders__status='cancelled')), 0.0, output_field=FloatField())
            ).filter(spend__gte=25000)
        elif self.value() == 'prospect':
            return queryset.filter(orders__isnull=True)
        elif self.value() == 'staff':
            return queryset.filter(is_staff=True)
        return queryset


class CustomerSpendingFilter(admin.SimpleListFilter):
    title = 'Spending Tier'
    parameter_name = 'spending_tier'

    def lookups(self, request, model_admin):
        return (
            ('tier_high', 'Tier 1: High (> ₹25,000)'),
            ('tier_med', 'Tier 2: Medium (₹5,000 - ₹25,000)'),
            ('tier_low', 'Tier 3: Entry (< ₹5,000)'),
            ('tier_zero', 'Tier 0: No Spending (₹0)'),
        )

    def queryset(self, request, queryset):
        annotated = queryset.annotate(
            spend=Coalesce(Sum('orders__total_amount', filter=~Q(orders__status='cancelled')), 0.0, output_field=FloatField())
        )
        if self.value() == 'tier_high':
            return annotated.filter(spend__gt=25000)
        elif self.value() == 'tier_med':
            return annotated.filter(spend__gte=5000, spend__lte=25000)
        elif self.value() == 'tier_low':
            return annotated.filter(spend__gt=0, spend__lt=5000)
        elif self.value() == 'tier_zero':
            return annotated.filter(spend=0)
        return queryset


class CustomerAddressInline(admin.TabularInline):
    model = Address
    extra = 0
    fields = ('full_name', 'phone', 'address_line', 'city', 'state', 'pincode', 'is_default')
    classes = ['collapse']


class CustomerReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    readonly_fields = ('product', 'rating', 'title', 'comment', 'created_at')
    can_delete = True
    classes = ['collapse']


class CustomerCRMAdmin(BaseUserAdmin):
    change_list_template = 'admin/auth/user/change_list.html'
    change_form_template = 'admin/auth/user/change_form.html'

    inlines = [CustomerAddressInline, CustomerReviewInline]

    list_display = (
        'customer_avatar_identity',
        'contact_details',
        'role_status_badge',
        'orders_count_badge',
        'lifetime_spend_badge',
        'aov_badge',
        'last_order_info',
        'date_joined_formatted',
        'quick_crm_actions',
    )
    list_display_links = ('customer_avatar_identity',)
    list_filter = (
        'is_active',
        'is_staff',
        'is_superuser',
        CustomerTypeFilter,
        CustomerSpendingFilter,
        'date_joined',
    )
    search_fields = ('username', 'first_name', 'last_name', 'email', 'addresses__phone', 'addresses__city')
    ordering = ('-date_joined',)
    list_per_page = 20

    actions = ['activate_customers', 'deactivate_customers']

    def customer_avatar_identity(self, obj):
        name = obj.get_full_name() or obj.username
        initial = (obj.first_name[0] if obj.first_name else obj.username[0]).upper()
        bg, fg = AVATAR_PALETTES[obj.id % len(AVATAR_PALETTES)]
        return format_html(
            '<div style="display: flex; align-items: center; gap: 10px;">'
            '<div style="width: 36px; height: 36px; border-radius: 50%; background: {}; color: {}; font-weight: 800; font-size: 14px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid rgba(0,0,0,0.06);">{}</div>'
            '<div>'
            '<div style="font-weight: 700; color: #0f172a; font-size: 13px; line-height: 1.2;">{}</div>'
            '<div style="font-size: 11px; color: #64748b; font-family: monospace;">@{} &middot; <span style="color: #94a3b8;">#SK-CST-{}</span></div>'
            '</div>'
            '</div>',
            bg, fg, initial, name, obj.username, f"{obj.id:04d}"
        )
    customer_avatar_identity.short_description = "Customer Identity"

    def contact_details(self, obj):
        phone = get_customer_phone(obj)
        location = get_customer_location(obj)
        email = obj.email or "No email"

        phone_html = f'<a href="tel:{phone}" style="color: #0f172a; text-decoration: none; font-weight: 600;"><i class="fas fa-phone-alt" style="color: #10b981; font-size: 10px; margin-right: 4px;"></i>{phone}</a>' if phone else '<span style="color: #94a3b8; font-size: 11px;">No phone</span>'

        loc_html = f'<div style="font-size: 11px; color: #64748b; margin-top: 2px;"><i class="fas fa-map-marker-alt" style="color: #f59e0b; font-size: 10px; margin-right: 4px;"></i>{location}</div>' if location else ''

        email_html = f'<div style="font-size: 11px; color: #0284c7;"><a href="mailto:{obj.email}" style="color: #0284c7; text-decoration: none;">{email}</a></div>' if obj.email else '<div style="font-size: 11px; color: #94a3b8;">No email registered</div>'

        return format_html(
            '<div>{}{}{}</div>',
            mark_safe(phone_html),
            mark_safe(loc_html),
            mark_safe(email_html)
        )
    contact_details.short_description = "Contact & Location"

    def role_status_badge(self, obj):
        badges = []
        if obj.is_superuser:
            badges.append(badge_pill("Super Admin", bg_color="#fef2f2", text_color="#dc2626", border_color="#fecaca", icon="fas fa-shield-alt"))
        elif obj.is_staff:
            badges.append(badge_pill("Staff", bg_color="#eff6ff", text_color="#2563eb", border_color="#bfdbfe", icon="fas fa-user-shield"))

        total_spent = obj.orders.exclude(status='cancelled').aggregate(s=Sum('total_amount'))['s'] or 0.0

        if total_spent >= 25000:
            badges.append(badge_pill("VIP Spender", bg_color="#faf5ff", text_color="#7c3aed", border_color="#ddd6fe", icon="fas fa-crown"))
        elif obj.orders.exists():
            badges.append(badge_pill("Buyer", bg_color="#f0fdf4", text_color="#15803d", border_color="#bbf7d0", icon="fas fa-shopping-bag"))
        else:
            badges.append(badge_pill("Prospect", bg_color="#f8fafc", text_color="#64748b", border_color="#e2e8f0", icon="fas fa-seedling"))

        if not obj.is_active:
            badges.append(badge_pill("Suspended", bg_color="#fef2f2", text_color="#991b1b", border_color="#fecaca", icon="fas fa-ban"))

        return mark_safe("<div style='display: flex; flex-direction: column; gap: 4px; align-items: flex-start;'>" + "".join(badges) + "</div>")
    role_status_badge.short_description = "Customer Tier"

    def orders_count_badge(self, obj):
        cnt = obj.orders.count()
        if cnt > 0:
            return format_html(
                '<a href="/admin/shop/order/?user__id__exact={}" title="Filter orders by {}" '
                'style="display: inline-flex; align-items: center; gap: 5px; background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; padding: 3px 9px; border-radius: 9999px; font-weight: 700; font-size: 11.5px; text-decoration: none;">'
                '<i class="fas fa-shopping-bag"></i> {} orders</a>',
                obj.id, obj.username, cnt
            )
        return mark_safe('<span style="color: #94a3b8; font-size: 11.5px; font-weight: 500;">0 orders</span>')
    orders_count_badge.short_description = "Orders"

    def lifetime_spend_badge(self, obj):
        spent = obj.orders.exclude(status='cancelled').aggregate(s=Sum('total_amount'))['s'] or 0.0
        if spent > 0:
            return format_html(
                '<span style="font-weight: 800; color: #0f172a; font-size: 13px;">₹{}</span>',
                f"{int(spent):,}"
            )
        return mark_safe('<span style="color: #94a3b8; font-size: 12px;">₹0</span>')
    lifetime_spend_badge.short_description = "Lifetime Spend"

    def aov_badge(self, obj):
        orders = obj.orders.exclude(status='cancelled')
        count = orders.count()
        if count > 0:
            spent = orders.aggregate(s=Sum('total_amount'))['s'] or 0.0
            aov = spent / count
            return format_html(
                '<span style="font-weight: 600; color: #475569; font-size: 12px;">₹{}</span>',
                f"{int(aov):,}"
            )
        return mark_safe('<span style="color: #cbd5e1; font-size: 11px;">-</span>')
    aov_badge.short_description = "AOV"

    def last_order_info(self, obj):
        latest = obj.orders.first()
        if latest:
            return format_html(
                '<div>'
                '<a href="/admin/shop/order/{}/change/" style="font-weight: 700; color: #0284c7; text-decoration: none; font-size: 11.5px;">#SK-ORD-{}</a>'
                '<div style="font-size: 11px; color: #64748b;">{}</div>'
                '</div>',
                latest.id, f"{latest.id:06d}", latest.created_at.strftime("%b %d, %Y")
            )
        return mark_safe('<span style="color: #94a3b8; font-size: 11px;">No orders</span>')
    last_order_info.short_description = "Recent Order"

    def date_joined_formatted(self, obj):
        return format_html(
            '<span style="font-size: 11.5px; color: #475569; font-weight: 500;">{}</span>',
            obj.date_joined.strftime("%b %d, %Y")
        )
    date_joined_formatted.short_description = "Joined"

    def quick_crm_actions(self, obj):
        phone = get_customer_phone(obj)
        phone_btn = f'<a href="https://wa.me/{phone}" target="_blank" class="btn-studio-action" title="WhatsApp Customer" style="padding: 4px 7px; border-radius: 6px; background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; font-size: 11px; text-decoration: none;"><i class="fab fa-whatsapp"></i></a>' if phone else ''
        email_btn = f'<a href="mailto:{obj.email}" class="btn-studio-action" title="Send Email" style="padding: 4px 7px; border-radius: 6px; background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; font-size: 11px; text-decoration: none;"><i class="fas fa-envelope"></i></a>' if obj.email else ''

        return format_html(
            '<div style="display: inline-flex; align-items: center; gap: 4px;">'
            '<a href="/admin/auth/user/{}/change/" class="btn-studio-action" title="Customer 360 CRM Profile" style="padding: 4px 8px; border-radius: 6px; background: #0f172a; color: #ffffff; font-size: 11px; font-weight: 700; text-decoration: none; display: inline-flex; align-items: center; gap: 4px;">'
            '<i class="fas fa-id-card"></i> CRM</a>'
            '<a href="/admin/shop/order/?user__id__exact={}" class="btn-studio-action" title="View Orders" style="padding: 4px 7px; border-radius: 6px; background: #f8fafc; color: #334155; border: 1px solid #cbd5e1; font-size: 11px; text-decoration: none;">'
            '<i class="fas fa-shopping-bag"></i></a>'
            '{}{}'
            '</div>',
            obj.id, obj.id, mark_safe(email_btn), mark_safe(phone_btn)
        )
    quick_crm_actions.short_description = "Actions"

    @admin.action(description="Activate selected customer accounts")
    def activate_customers(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Successfully activated {updated} customer accounts.", messages.SUCCESS)

    @admin.action(description="Deactivate / Suspend selected customer accounts")
    def deactivate_customers(self, request, queryset):
        if queryset.filter(id=request.user.id).exists():
            self.message_user(request, "Safety alert: You cannot deactivate your own administrative account.", messages.ERROR)
            queryset = queryset.exclude(id=request.user.id)
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Successfully suspended {updated} customer accounts.", messages.WARNING)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:user_id>/toggle-active/', self.admin_site.admin_view(self.toggle_active_view), name='auth_user_toggle_active'),
        ]
        return custom_urls + urls

    def toggle_active_view(self, request, user_id):
        if request.method != 'POST':
            messages.error(request, "Invalid request method.")
            return HttpResponseRedirect(reverse('admin:auth_user_change', args=[user_id]))
        if user_id == request.user.id:
            messages.error(request, "Safety alert: You cannot toggle active status on your own logged-in account.")
            return HttpResponseRedirect(reverse('admin:auth_user_change', args=[user_id]))
        user = get_object_or_404(User, pk=user_id)
        user.is_active = not user.is_active
        user.save(update_fields=['is_active'])
        action = "activated" if user.is_active else "suspended"
        messages.success(request, f"Customer account @{user.username} successfully {action}.")
        return HttpResponseRedirect(reverse('admin:auth_user_change', args=[user_id]))

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        total_users = User.objects.count()
        active_buyers = User.objects.filter(orders__isnull=False).distinct().count()
        repeat_buyers = User.objects.annotate(order_cnt=Count('orders')).filter(order_cnt__gt=1).count()
        prospect_count = total_users - active_buyers
        staff_count = User.objects.filter(is_staff=True).count()
        active_count = User.objects.filter(is_active=True).count()

        non_cancelled_orders = Order.objects.exclude(status='cancelled')
        total_clv = non_cancelled_orders.aggregate(s=Sum('total_amount'))['s'] or 0.0
        nc_count = non_cancelled_orders.count()
        aov = (total_clv / nc_count) if nc_count > 0 else 0.0

        top_customer = User.objects.annotate(
            spend=Coalesce(Sum('orders__total_amount', filter=~Q(orders__status='cancelled')), 0.0, output_field=FloatField())
        ).order_by('-spend').first()

        extra_context['customer_stats'] = {
            'total_users': total_users,
            'active_buyers': active_buyers,
            'repeat_buyers': repeat_buyers,
            'prospect_count': prospect_count,
            'staff_count': staff_count,
            'active_count': active_count,
            'total_clv': total_clv,
            'aov': aov,
            'top_customer': top_customer,
        }
        return super().changelist_view(request, extra_context=extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        try:
            user_obj = User.objects.get(pk=object_id)
            orders_qs = user_obj.orders.all()
            total_orders = orders_qs.count()
            non_cancelled = orders_qs.exclude(status='cancelled')
            delivered_orders = orders_qs.filter(status='delivered').count()
            active_orders = orders_qs.filter(status__in=['placed', 'confirmed', 'shipped', 'out_for_delivery']).count()
            cancelled_orders = orders_qs.filter(status='cancelled').count()

            lifetime_spend = non_cancelled.aggregate(s=Sum('total_amount'))['s'] or 0.0
            nc_count = non_cancelled.count()
            aov = (lifetime_spend / nc_count) if nc_count > 0 else 0.0

            phone = get_customer_phone(user_obj)
            location = get_customer_location(user_obj)

            addresses = list(user_obj.addresses.all())
            reviews = list(Review.objects.filter(user=user_obj).select_related('product'))
            wishlist_items = list(user_obj.wishlist_items.all().select_related('product'))
            cart_items = list(Cart.objects.filter(user=user_obj).select_related('product', 'color'))
            recent_orders = list(orders_qs.prefetch_related('items__product')[:8])

            if user_obj.is_superuser:
                tier_label = "Super Administrator"
                tier_badge_bg = "#fef2f2"
                tier_badge_color = "#dc2626"
                tier_icon = "fas fa-shield-alt"
            elif user_obj.is_staff:
                tier_label = "Store Staff / Team"
                tier_badge_bg = "#eff6ff"
                tier_badge_color = "#2563eb"
                tier_icon = "fas fa-user-shield"
            elif lifetime_spend >= 25000:
                tier_label = "👑 VIP Elite Customer"
                tier_badge_bg = "#faf5ff"
                tier_badge_color = "#7c3aed"
                tier_icon = "fas fa-crown"
            elif total_orders > 0:
                tier_label = "🛍️ Active Customer"
                tier_badge_bg = "#f0fdf4"
                tier_badge_color = "#15803d"
                tier_icon = "fas fa-shopping-bag"
            else:
                tier_label = "🌱 Prospect / Registered"
                tier_badge_bg = "#f8fafc"
                tier_badge_color = "#64748b"
                tier_icon = "fas fa-seedling"

            extra_context['crm_profile'] = {
                'phone': phone,
                'location': location,
                'total_orders': total_orders,
                'delivered_orders': delivered_orders,
                'active_orders': active_orders,
                'cancelled_orders': cancelled_orders,
                'lifetime_spend': lifetime_spend,
                'aov': aov,
                'recent_orders': recent_orders,
                'addresses': addresses,
                'reviews': reviews,
                'wishlist_items': wishlist_items,
                'cart_items': cart_items,
                'tier_label': tier_label,
                'tier_badge_bg': tier_badge_bg,
                'tier_badge_color': tier_badge_color,
                'tier_icon': tier_icon,
            }
        except Exception as e:
            extra_context['crm_profile_error'] = str(e)

        return super().change_view(request, object_id, form_url, extra_context=extra_context)


# Re-register User with CustomerCRMAdmin
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

admin.site.register(User, CustomerCRMAdmin)




