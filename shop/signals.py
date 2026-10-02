from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import (
    Product, ProductColor, ProductColorImage, ProductImage,
    Category, Order, Coupon, Review
)
from .live_sync import record_change


@receiver(post_save, sender=Product)
def on_product_save(sender, instance, created, **kwargs):
    cslug = instance.category.slug if instance.category else (instance.categories.first().slug if instance.categories.exists() else 'all')
    record_change(
        entity_type="product",
        entity_id=instance.id,
        action="created" if created else "updated",
        details={
            "id": instance.id,
            "name": instance.name,
            "slug": instance.slug,
            "brand": instance.brand,
            "selling_price": instance.selling_price,
            "original_price": instance.original_price,
            "discount_percent": instance.discount_percent,
            "quantity": instance.quantity,
            "in_stock": instance.in_stock,
            "status": instance.status,
            "trending": instance.trending,
            "featured": instance.featured,
            "category_slug": cslug,
            "image_url": instance.product_image.url if instance.product_image else "",
        }
    )


@receiver(post_delete, sender=Product)
def on_product_delete(sender, instance, **kwargs):
    record_change(
        entity_type="product",
        entity_id=instance.id,
        action="deleted",
        details={"id": instance.id, "slug": instance.slug, "name": instance.name}
    )


@receiver(post_save, sender=ProductColor)
def on_product_color_save(sender, instance, created, **kwargs):
    prod = instance.product
    record_change(
        entity_type="product",
        entity_id=prod.id,
        action="color_updated",
        details={
            "id": prod.id,
            "slug": prod.slug,
            "color_id": instance.id,
            "color_name": instance.name,
            "price": instance.effective_price,
            "original_price": instance.effective_original_price,
            "quantity": instance.quantity,
            "in_stock": instance.in_stock,
            "is_default": instance.is_default,
        }
    )


@receiver(post_delete, sender=ProductColor)
def on_product_color_delete(sender, instance, **kwargs):
    record_change(
        entity_type="product",
        entity_id=instance.product_id,
        action="color_deleted",
        details={"id": instance.product_id, "color_id": instance.id}
    )


@receiver(post_save, sender=Category)
def on_category_save(sender, instance, created, **kwargs):
    record_change(
        entity_type="category",
        entity_id=instance.id,
        action="created" if created else "updated",
        details={"id": instance.id, "name": instance.name, "slug": instance.slug, "status": instance.status}
    )


@receiver(post_delete, sender=Category)
def on_category_delete(sender, instance, **kwargs):
    record_change(
        entity_type="category",
        entity_id=instance.id,
        action="deleted",
        details={"id": instance.id, "slug": instance.slug, "name": instance.name}
    )


@receiver(post_save, sender=Order)
def on_order_save(sender, instance, created, **kwargs):
    record_change(
        entity_type="order",
        entity_id=instance.id,
        action="created" if created else "status_updated",
        details={
            "id": instance.id,
            "user_id": instance.user_id,
            "status": instance.status,
            "status_display": instance.get_status_display(),
            "total_amount": instance.total_amount,
            "coupon_code": instance.coupon_code,
        }
    )


@receiver(post_save, sender=Coupon)
def on_coupon_save(sender, instance, created, **kwargs):
    record_change(
        entity_type="coupon",
        entity_id=instance.id,
        action="created" if created else "updated",
        details={"id": instance.id, "code": instance.code, "active": instance.active}
    )


@receiver(post_delete, sender=Coupon)
def on_coupon_delete(sender, instance, **kwargs):
    record_change(
        entity_type="coupon",
        entity_id=instance.id,
        action="deleted",
        details={"id": instance.id, "code": instance.code}
    )


@receiver(post_save, sender=Review)
def on_review_save(sender, instance, created, **kwargs):
    record_change(
        entity_type="review",
        entity_id=instance.id,
        action="created" if created else "updated",
        details={"product_id": instance.product_id, "rating": instance.rating}
    )
