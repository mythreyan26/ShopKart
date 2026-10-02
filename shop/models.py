from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.urls import reverse
import datetime
import os


def getFileName(instance, filename):
    now_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    new_filename = "%s_%s" % (now_time, filename)
    return os.path.join('uploads/', new_filename)


class Category(models.Model):
    name = models.CharField(max_length=150, unique=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories'
    )
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    image = models.ImageField(upload_to=getFileName, null=True, blank=True)
    description = models.TextField(max_length=500, blank=True)
    status = models.BooleanField(default=False, help_text="0-show, 1-hidden")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# Backwards-compatible alias (old code referenced "Catagory")
Catagory = Category


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='primary_products', null=True, blank=True, help_text="Primary category")
    categories = models.ManyToManyField(Category, blank=True, related_name='products', help_text="Select one or more subcategories/categories where this product should appear")
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    brand = models.CharField(max_length=100, blank=True, default="ShopKart")
    vendor = models.CharField(max_length=150, blank=True, default="ShopKart")
    product_image = models.ImageField(upload_to=getFileName, null=True, blank=True)
    quantity = models.IntegerField(default=0)
    original_price = models.FloatField()
    selling_price = models.FloatField()
    description = models.TextField(max_length=2000, blank=True)
    highlights = models.TextField(max_length=1000, blank=True, help_text="One point per line")
    status = models.BooleanField(default=False, help_text="0-show, 1-hidden")
    trending = models.BooleanField(default=False)
    featured = models.BooleanField(default=False)
    is_bestseller = models.BooleanField(default=False)
    free_delivery = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        cslug = self.category.slug if self.category else (self.categories.first().slug if self.categories.exists() else 'all')
        return reverse('product_details', args=[cslug, self.slug])

    @property
    def discount_percent(self):
        if self.original_price and self.original_price > self.selling_price:
            return round((self.original_price - self.selling_price) / self.original_price * 100)
        return 0

    @property
    def avg_rating(self):
        agg = self.reviews.aggregate(models.Avg('rating'))['rating__avg']
        return round(agg, 1) if agg else 0

    @property
    def review_count(self):
        return self.reviews.count()

    @property
    def highlight_list(self):
        return [h.strip() for h in self.highlights.splitlines() if h.strip()]

    @property
    def in_stock(self):
        return self.quantity > 0


class ProductColor(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='colors')
    name = models.CharField(max_length=50, help_text="e.g. Lavender, Space Black, Ocean Blue, Sage Green")
    color_code = models.CharField(max_length=20, default="#000000", help_text="Hex color code e.g. #D8B4E2")
    image = models.ImageField(upload_to=getFileName, help_text="Main thumbnail/front image for this color")
    price = models.FloatField(null=True, blank=True, help_text="Optional custom price for this color. Leave empty to use product selling price.")
    original_price = models.FloatField(null=True, blank=True, help_text="Optional custom original price for this color.")
    quantity = models.IntegerField(default=10, help_text="Stock quantity available for this color")
    is_default = models.BooleanField(default=False, help_text="Is this the default selected color?")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_default', 'id']

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    @property
    def effective_price(self):
        return self.price if self.price is not None else self.product.selling_price

    @property
    def effective_original_price(self):
        return self.original_price if self.original_price is not None else self.product.original_price

    @property
    def discount_percent(self):
        orig = self.effective_original_price
        sell = self.effective_price
        if orig and orig > sell:
            return round((orig - sell) / orig * 100)
        return 0

    @property
    def in_stock(self):
        return self.quantity > 0


class ProductColorImage(models.Model):
    color = models.ForeignKey(ProductColor, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=getFileName, help_text="Additional angle/gallery photo for this color")

    def __str__(self):
        return f"Gallery image for {self.color}"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='gallery')
    image = models.ImageField(upload_to=getFileName)

    def __str__(self):
        return f"Image for {self.product.name}"


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(default=5)
    title = models.CharField(max_length=150, blank=True)
    comment = models.TextField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('product', 'user')

    def __str__(self):
        return f"{self.product.name} - {self.rating} stars by {self.user.username}"


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    color = models.ForeignKey(ProductColor, on_delete=models.SET_NULL, null=True, blank=True, related_name='cart_items')
    product_qty = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product', 'color')

    @property
    def unit_price(self):
        if self.color and self.color.price is not None:
            return self.color.price
        return self.product.selling_price

    @property
    def total_price(self):
        return round(self.unit_price * self.product_qty, 2)

    def __str__(self):
        color_str = f" ({self.color.name})" if self.color else ""
        return f"{self.user.username} - {self.product.name}{color_str} x{self.product_qty}"


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=15)
    address_line = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Address"
        verbose_name_plural = "Addresses"

    def __str__(self):
        return f"{self.full_name}, {self.city} - {self.pincode}"


class Coupon(models.Model):
    DISCOUNT_TYPES = [
        ('percentage', 'Percentage (%)'),
        ('fixed', 'Fixed Amount (₹)'),
    ]
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, default='percentage')
    discount_value = models.FloatField(help_text="Discount percentage (e.g. 10) or fixed amount in INR (e.g. 100)")
    min_order_amount = models.FloatField(default=0, help_text="Minimum order subtotal to apply this coupon")
    max_discount = models.FloatField(null=True, blank=True, help_text="Maximum discount cap for percentage coupons")
    description = models.CharField(max_length=255, blank=True, help_text="e.g. 10% OFF on all orders")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        suffix = '%' if self.discount_type == 'percentage' else '₹'
        return f"{self.code} ({self.discount_value}{suffix} OFF)"

    def calculate_discount(self, subtotal):
        if not self.active or subtotal < self.min_order_amount:
            return 0
        if self.discount_type == 'percentage':
            disc = (subtotal * self.discount_value) / 100.0
            if self.max_discount:
                disc = min(disc, self.max_discount)
            return round(disc, 2)
        else:
            return round(min(self.discount_value, subtotal), 2)


class Order(models.Model):
    STATUS_CHOICES = [
        ('placed', 'Order Placed'),
        ('confirmed', 'Confirmed & Packed'),
        ('shipped', 'Shipped'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    PAYMENT_CHOICES = [
        ('cod', 'Cash on Delivery'),
        ('card', 'Credit / Debit Card'),
        ('upi', 'UPI'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default='cod')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='placed')
    subtotal = models.FloatField(default=0)
    coupon_code = models.CharField(max_length=50, blank=True, default='')
    discount_amount = models.FloatField(default=0)
    delivery_fee = models.FloatField(default=0)
    total_amount = models.FloatField(default=0)
    cancellation_reason = models.TextField(blank=True, default='')
    cancelled_at = models.DateTimeField(null=True, blank=True)
    tracking_number = models.CharField(max_length=60, blank=True, default='')
    estimated_delivery = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        updates = []
        if not self.tracking_number:
            self.tracking_number = f"SK-TRK-{self.id:06d}"
            updates.append('tracking_number')
        if not self.estimated_delivery:
            self.estimated_delivery = datetime.date.today() + datetime.timedelta(days=4)
            updates.append('estimated_delivery')
        if updates:
            super().save(update_fields=updates)

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=150)
    color_name = models.CharField(max_length=50, blank=True, default='')
    color_code = models.CharField(max_length=20, blank=True, default='')
    quantity = models.IntegerField(default=1)
    price = models.FloatField(default=0)

    @property
    def total_price(self):
        return round(self.price * self.quantity, 2)

    def __str__(self):
        color_str = f" [{self.color_name}]" if self.color_name else ""
        return f"{self.product_name}{color_str} x{self.quantity}"


class ContactMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='contact_messages')
    name = models.CharField(max_length=150)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Message from {self.name} - {self.subject}"
