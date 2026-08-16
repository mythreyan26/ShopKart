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
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
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
        return reverse('product_details', args=[self.category.slug, self.slug])

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
    product_qty = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    @property
    def total_price(self):
        return round(self.product.selling_price * self.product_qty, 2)

    def __str__(self):
        return f"{self.user.username} - {self.product.name} x{self.product_qty}"


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

    def __str__(self):
        return f"{self.full_name}, {self.city} - {self.pincode}"


class Order(models.Model):
    STATUS_CHOICES = [
        ('placed', 'Order Placed'),
        ('shipped', 'Shipped'),
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
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='placed')
    subtotal = models.FloatField(default=0)
    delivery_fee = models.FloatField(default=0)
    total_amount = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=150)
    quantity = models.IntegerField(default=1)
    price = models.FloatField(default=0)

    @property
    def total_price(self):
        return round(self.price * self.quantity, 2)

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"
