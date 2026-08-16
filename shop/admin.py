from django.contrib import admin
from .models import Category, Product, ProductImage, Review, Wishlist, Cart, Address, Order, OrderItem

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name','parent' ,'slug', 'status', 'created_at')
    list_filter = ('parent', 'status')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category','selling_price', 'original_price', 'quantity', 'trending', 'featured', 'status')
    list_filter = ('category', 'trending', 'featured', 'is_bestseller', 'status')
    search_fields = ('name', 'brand')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'payment_method', 'total_amount', 'created_at')
    list_filter = ('status', 'payment_method')


admin.site.register(Wishlist)
admin.site.register(Cart)
admin.site.register(Address)
admin.site.register(OrderItem)
