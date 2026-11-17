import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal

from shop.models import (
    Category, Product, ProductColor, Cart, Wishlist,
    Address, Order, OrderItem, Review, Coupon, ContactMessage
)


class AccountAndAuthTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='johndoe',
            email='john@example.com',
            password='OldPassword@123',
            first_name='John',
            last_name='Doe'
        )

    def test_profile_view_and_update(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)

        update_response = self.client.post(reverse('update_profile'), {
            'first_name': 'Johnny',
            'last_name': 'Walker',
            'email': 'johnny@example.com'
        }, follow=True)
        self.assertEqual(update_response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Johnny')
        self.assertEqual(self.user.email, 'johnny@example.com')

    def test_change_password_success(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('change_password'), {
            'old_password': 'OldPassword@123',
            'new_password': 'NewStrongPass#2026',
            'confirm_password': 'NewStrongPass#2026'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewStrongPass#2026'))

    def test_change_password_wrong_old(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('change_password'), {
            'old_password': 'WrongPassword123',
            'new_password': 'NewStrongPass#2026',
            'confirm_password': 'NewStrongPass#2026'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password('NewStrongPass#2026'))

    def test_address_management_and_edit(self):
        self.client.force_login(self.user)
        addr = Address.objects.create(
            user=self.user,
            full_name='John Doe',
            phone='9876543210',
            address_line='123 Tech Park',
            city='Bengaluru',
            state='Karnataka',
            pincode='560001',
            is_default=True
        )

        # GET edit address
        resp = self.client.get(reverse('edit_address', kwargs={'address_id': addr.id}))
        self.assertEqual(resp.status_code, 200)

        # POST edit address
        post_resp = self.client.post(reverse('edit_address', kwargs={'address_id': addr.id}), {
            'full_name': 'Johnathan Doe',
            'phone': '9876543210',
            'address_line': '456 Innovation Hub',
            'city': 'Bengaluru',
            'state': 'Karnataka',
            'pincode': '560002',
            'is_default': '1'
        }, follow=True)
        self.assertEqual(post_resp.status_code, 200)
        addr.refresh_from_db()
        self.assertEqual(addr.full_name, 'Johnathan Doe')
        self.assertEqual(addr.address_line, '456 Innovation Hub')


class CatalogAndDiscoveryTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(
            name='Audio',
            slug='audio',
            description='Audio devices'
        )
        self.p1 = Product.objects.create(
            category=self.category,
            name='Sony WH-1000XM5',
            slug='sony-wh-1000xm5',
            brand='Sony',
            original_price=29990,
            selling_price=24990,
            quantity=10,
            status=0
        )
        self.p2 = Product.objects.create(
            category=self.category,
            name='Bose QC45',
            slug='bose-qc45',
            brand='Bose',
            original_price=26990,
            selling_price=22990,
            quantity=0,
            status=0
        )

    def test_collections_brand_and_stock_filtering(self):
        # All in Audio
        resp = self.client.get(reverse('collections_view', kwargs={'name': 'audio'}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Sony WH-1000XM5')
        self.assertContains(resp, 'Bose QC45')

        # Filter by brand Sony
        resp_sony = self.client.get(reverse('collections_view', kwargs={'name': 'audio'}) + '?brand=Sony')
        self.assertContains(resp_sony, 'Sony WH-1000XM5')
        self.assertNotContains(resp_sony, 'Bose QC45')

        # Filter in_stock=1
        resp_stock = self.client.get(reverse('collections_view', kwargs={'name': 'audio'}) + '?in_stock=1')
        self.assertContains(resp_stock, 'Sony WH-1000XM5')
        self.assertNotContains(resp_stock, 'Bose QC45')

    def test_product_detail_and_reviews_breakdown(self):
        user1 = User.objects.create_user(username='reviewer1', password='pass')
        user2 = User.objects.create_user(username='reviewer2', password='pass')
        Review.objects.create(user=user1, product=self.p1, rating=5, comment='Superb sound')
        Review.objects.create(user=user2, product=self.p1, rating=4, comment='Good battery')

        resp = self.client.get(reverse('product_details', kwargs={'cname': 'audio', 'pname': 'sony-wh-1000xm5'}))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('rating_breakdown', resp.context)
        self.assertIn('recommend_pct', resp.context)
        breakdown = {item['star']: item for item in resp.context['rating_breakdown']}
        self.assertEqual(breakdown[5]['count'], 1)
        self.assertEqual(breakdown[5]['pct'], 50)
        self.assertEqual(breakdown[4]['count'], 1)
        self.assertEqual(breakdown[4]['pct'], 50)
        self.assertEqual(resp.context['recommend_pct'], 100)


class CartWishlistAndOrderLifecycleTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='shopper', password='ShopperPass123')
        self.category = Category.objects.create(name='Laptops', slug='laptops')
        self.product = Product.objects.create(
            category=self.category,
            name='MacBook Pro M3',
            slug='macbook-pro-m3',
            brand='Apple',
            original_price=169900,
            selling_price=159900,
            quantity=5,
            status=0
        )
        self.color = ProductColor.objects.create(
            product=self.product,
            name='Space Black',
            color_code='#1c1b22',
            price=159900,
            quantity=5
        )
        self.address = Address.objects.create(
            user=self.user,
            full_name='Jane Buyer',
            phone='9123456780',
            address_line='Suite 10, Brigade Road',
            city='Bengaluru',
            state='Karnataka',
            pincode='560025',
            is_default=True
        )

    def test_cart_operations_and_move_to_wishlist(self):
        self.client.force_login(self.user)
        # Add to cart
        self.client.post(reverse('add_to_cart', kwargs={'product_id': self.product.id}), {'color_id': self.color.id})
        cart_item = Cart.objects.get(user=self.user, product=self.product)
        self.assertEqual(cart_item.product_qty, 1)

        # Move to wishlist
        resp = self.client.post(reverse('move_to_wishlist', kwargs={'item_id': cart_item.id}), follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Cart.objects.filter(user=self.user, product=self.product).exists())
        self.assertTrue(Wishlist.objects.filter(user=self.user, product=self.product).exists())

        # Move back to cart
        resp2 = self.client.post(reverse('move_to_cart', kwargs={'product_id': self.product.id}), follow=True)
        self.assertEqual(resp2.status_code, 200)
        self.assertTrue(Cart.objects.filter(user=self.user, product=self.product).exists())
        self.assertFalse(Wishlist.objects.filter(user=self.user, product=self.product).exists())

        # Clear cart
        resp3 = self.client.post(reverse('clear_cart'), follow=True)
        self.assertEqual(resp3.status_code, 200)
        self.assertEqual(Cart.objects.filter(user=self.user).count(), 0)

    def test_order_placement_cancellation_and_reorder(self):
        self.client.force_login(self.user)
        Cart.objects.create(
            user=self.user,
            product=self.product,
            color=self.color,
            product_qty=2
        )

        # Checkout
        checkout_resp = self.client.post(reverse('checkout'), {
            'address_id': self.address.id,
            'payment_method': 'card'
        }, follow=True)
        self.assertEqual(checkout_resp.status_code, 200)

        order = Order.objects.filter(user=self.user).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.status, 'placed')
        self.assertTrue(order.tracking_number.startswith('SK-TRK-'))
        self.assertIsNotNone(order.estimated_delivery)

        # Cancel order
        cancel_resp = self.client.post(reverse('cancel_order', kwargs={'order_id': order.id}), {
            'cancellation_reason': 'Ordered by mistake'
        }, follow=True)
        self.assertEqual(cancel_resp.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, 'cancelled')
        self.assertEqual(order.cancellation_reason, 'Ordered by mistake')
        self.assertIsNotNone(order.cancelled_at)

        # Verify stock restoration
        self.product.refresh_from_db()
        self.color.refresh_from_db()
        self.assertEqual(self.product.quantity, 7)  # 5 + 2 restored
        self.assertEqual(self.color.quantity, 7)    # 5 + 2 restored

        # Re-order ("Buy Again")
        reorder_resp = self.client.post(reverse('reorder', kwargs={'order_id': order.id}), follow=True)
        self.assertEqual(reorder_resp.status_code, 200)
        cart_items = Cart.objects.filter(user=self.user)
        self.assertEqual(cart_items.count(), 1)
        self.assertEqual(cart_items.first().product_qty, 2)


class SupportAndInfoPagesTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_informational_pages_render(self):
        pages = ['about', 'faq', 'returns_policy', 'terms', 'privacy']
        for page_name in pages:
            resp = self.client.get(reverse(page_name))
            self.assertEqual(resp.status_code, 200, f"Page {page_name} failed to render")

    def test_contact_us_form_submission(self):
        resp = self.client.get(reverse('contact'))
        self.assertEqual(resp.status_code, 200)

        post_resp = self.client.post(reverse('contact'), {
            'name': 'Sarah Connor',
            'email': 'sarah@resistance.org',
            'subject': 'Bulk Order Inquiry',
            'message': 'Looking to purchase 50 laptops for our enterprise.'
        }, follow=True)
        self.assertEqual(post_resp.status_code, 200)

        msg = ContactMessage.objects.filter(email='sarah@resistance.org').first()
        self.assertIsNotNone(msg)
        self.assertEqual(msg.name, 'Sarah Connor')
        self.assertEqual(msg.subject, 'Bulk Order Inquiry')
        self.assertFalse(msg.is_resolved)


class RestApiSuiteTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='api_user',
            email='api@shopkart.com',
            password='ApiPassword123'
        )
        self.category = Category.objects.create(name='Wearables', slug='wearables')
        self.product = Product.objects.create(
            category=self.category,
            name='Galaxy Watch 6',
            slug='galaxy-watch-6',
            brand='Samsung',
            original_price=29999,
            selling_price=24999,
            quantity=15,
            status=0
        )

    def test_api_password_change(self):
        self.client.force_login(self.user)
        resp = self.client.post(
            reverse('api_password_change'),
            data=json.dumps({
                'old_password': 'ApiPassword123',
                'new_password1': 'BrandNewApiPass@99',
                'new_password2': 'BrandNewApiPass@99'
            }),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('success'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('BrandNewApiPass@99'))

    def test_api_address_crud(self):
        self.client.force_login(self.user)
        # Create
        create_resp = self.client.post(
            reverse('api_address_create'),
            data=json.dumps({
                'full_name': 'API Tester',
                'phone': '9876500000',
                'address_line': 'Plot 42, Cyber Gateway',
                'city': 'Hyderabad',
                'state': 'Telangana',
                'pincode': '500081',
                'is_default': True
            }),
            content_type='application/json'
        )
        self.assertEqual(create_resp.status_code, 200)
        addr_id = create_resp.json()['address']['id']

        # Update
        update_resp = self.client.post(
            reverse('api_address_update', kwargs={'address_id': addr_id}),
            data=json.dumps({
                'full_name': 'API Tester Modified',
                'phone': '9876500000',
                'address_line': 'Plot 42, Cyber Gateway, 3rd Floor',
                'city': 'Hyderabad',
                'state': 'Telangana',
                'pincode': '500081',
                'is_default': True
            }),
            content_type='application/json'
        )
        self.assertEqual(update_resp.status_code, 200)
        self.assertEqual(update_resp.json()['address']['full_name'], 'API Tester Modified')

        # Delete
        del_resp = self.client.post(
            reverse('api_address_delete', kwargs={'address_id': addr_id})
        )
        self.assertEqual(del_resp.status_code, 200)
        self.assertFalse(Address.objects.filter(pk=addr_id).exists())

    def test_api_contact_submission(self):
        resp = self.client.post(
            reverse('api_contact_submit'),
            data=json.dumps({
                'name': 'API Inquirer',
                'email': 'inquirer@example.com',
                'subject': 'API Support Question',
                'message': 'Does the API support webhooks?'
            }),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('success'))
        self.assertTrue(ContactMessage.objects.filter(email='inquirer@example.com').exists())

    def test_api_cart_clear_and_moves(self):
        self.client.force_login(self.user)
        item = Cart.objects.create(user=self.user, product=self.product, product_qty=1)

        # Move to wishlist API
        resp = self.client.post(reverse('api_cart_move_to_wishlist', kwargs={'item_id': item.id}))
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Cart.objects.filter(pk=item.id).exists())
        self.assertTrue(Wishlist.objects.filter(user=self.user, product=self.product).exists())

        # Move back to cart API
        resp2 = self.client.post(reverse('api_wishlist_move_to_cart', kwargs={'product_id': self.product.id}))
        self.assertEqual(resp2.status_code, 200)
        self.assertTrue(Cart.objects.filter(user=self.user, product=self.product).exists())

        # Clear cart API
        resp3 = self.client.post(reverse('api_cart_clear'))
        self.assertEqual(resp3.status_code, 200)
        self.assertEqual(Cart.objects.filter(user=self.user).count(), 0)


class AdminPanelLoginTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='admin_runner',
            email='admin@shopkart.com',
            password='AdminPassword#123'
        )
        self.customer = User.objects.create_user(
            username='regular_customer',
            email='customer@shopkart.com',
            password='CustomerPassword#123'
        )

    def test_admin_login_page_renders_redesigned_ui(self):
        res = self.client.get('/admin/login/?next=/admin/')
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')
        self.assertIn('ShopKart', content)
        self.assertIn('Executive Command Center', content)
        self.assertIn('admin-login-form', content)
        self.assertIn('csrfmiddlewaretoken', content)
        self.assertIn('Sign In to Console', content)

    def test_admin_login_failed_authentication(self):
        res = self.client.post('/admin/login/', {
            'username': 'admin_runner',
            'password': 'WrongPassword#999',
            'next': '/admin/'
        })
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')
        self.assertTrue('Authentication Failed' in content or 'error' in content.lower())

    def test_admin_login_successful_authentication(self):
        res = self.client.post('/admin/login/', {
            'username': 'admin_runner',
            'password': 'AdminPassword#123',
            'next': '/admin/'
        }, follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.request['PATH_INFO'], '/admin/')

    def test_staff_can_view_customer_orders_and_invoices(self):
        # Create an order placed by regular customer
        order = Order.objects.create(
            user=self.customer,
            total_amount=1200,
            status='placed'
        )
        # Login as admin
        self.client.force_login(self.admin_user)
        # Verify admin can view customer order detail and invoice without 404
        res_detail = self.client.get(reverse('order_detail', kwargs={'order_id': order.id}))
        self.assertEqual(res_detail.status_code, 200)

        res_inv = self.client.get(reverse('invoice', kwargs={'order_id': order.id}))
        self.assertEqual(res_inv.status_code, 200)


class GeminiAITestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_ai_empty_prompt_rejected(self):
        res = self.client.post(reverse('api_ai_chat'), json.dumps({'prompt': ''}), content_type='application/json')
        self.assertEqual(res.status_code, 400)
        data = res.json()
        self.assertFalse(data['success'])

    def test_ai_storefront_empty_prompt_rejected(self):
        res = self.client.post(reverse('ai_chat'), json.dumps({'prompt': ''}), content_type='application/json')
        self.assertEqual(res.status_code, 400)
        data = res.json()
        self.assertFalse(data['success'])

