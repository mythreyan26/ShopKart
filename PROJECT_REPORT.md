# Technical Project Report: ShopKart E-Commerce Platform

---

## Document Overview
- **Project Name:** ShopKart
- **Architecture:** Django Model-View-Template (MVT) with decoupled REST API and Server-Sent Events
- **Backend Stack:** Python 3.12, Django 5.1 / 6.1, SQLite (Development), PostgreSQL (Production)
- **Frontend Stack:** HTML5, Tailwind CSS (CDN), Alpine.js (CDN), Service Worker (PWA)
- **Mobile Client:** React Native (Expo SDK 51)
- **Application Server:** Gunicorn (WSGI) with WhiteNoise static storage
- **Verification Status:** Automated test suite passing (20/20 tests)

---

## 1. System Architecture

ShopKart is structured around Django's Model-View-Template pattern, supplemented by a stateless JSON API layer (`/api/`) and an event-driven live synchronization stream.

### 1.1 Architecture Components

- **Presentation Layer:**
  - Responsive web templates rendered via Django templates, styled with Tailwind CSS utility classes, and made reactive using Alpine.js for client state (dropdowns, modals, tabs, debounced search).
  - Progressive Web App (PWA) layer with service worker caching (`static/sw.js`), web manifest metadata (`static/manifest.json`), and an offline fallback route (`/offline/`).
  - Cross-platform mobile client (`mobile_app/`) built with React Native and Expo, interacting directly with the REST endpoints under `/api/`.

- **Application and Routing Layer:**
  - Standard customer routes handled in `shop/views.py`.
  - JSON REST API routes handled in `shop/api_views.py`.
  - Staff administrative views handled in `shop/admin_views.py` and Django's built-in `admin.site`.

- **Middleware Pipeline:**
  - `DualSessionMiddleware`: Separates administrative sessions (`admin_sessionid`) from storefront sessions (`sessionid`), preventing customer logins from invalidating staff sessions. Verifies `is_staff=True` before synchronizing credentials.
  - `APICORSMiddleware`: Handles preflight `OPTIONS` requests and Cross-Origin Resource Sharing headers for cross-platform API consumers.
  - Standard Django middleware: `SecurityMiddleware`, `WhiteNoiseMiddleware`, `AuthenticationMiddleware`, `MessageMiddleware`, `XFrameOptionsMiddleware`.

- **Data Persistence:**
  - Relational database management via Django ORM. Local development uses SQLite (`db.sqlite3`); production uses PostgreSQL via `dj-database-url` with connection pooling considerations (`conn_max_age=0`, SSL enabled).
  - Media storage for product and category graphics located in `static/uploads/` and `static/images/`.

---

## 2. Data Modeling and Relational Schema

The database schema enforces data integrity through foreign key constraints, cascading policies, and unique constraints.

### 2.1 Core Entities

1. **Category:**
   - Supports hierarchical nesting via a self-referential foreign key (`parent = ForeignKey('self', null=True)`).
   - Generates URL slugs automatically from category names on save.

2. **Product:**
   - Stores master product data: brand, vendor, descriptions, highlights, base pricing, and stock quantity.
   - Computes dynamic discount percentages: `round(((original_price - selling_price) / original_price) * 100)`.
   - Calculates aggregate ratings and verified review counts dynamically.

3. **ProductColor & ProductColorImage:**
   - Enables SKU variant management by colorway.
   - Allows variant-specific pricing, stock quantities, and angle photography.

4. **Cart & Wishlist:**
   - Cart lines store user reference, product reference, variant reference, and quantity.
   - Enforces unique combinations of user, product, and color (`unique_together = ('user', 'product', 'color')`).
   - Supports bi-directional transfer between cart and wishlist.

5. **Coupon:**
   - Supports percentage discounts and fixed cash reductions.
   - Enforces minimum order subtotal requirements and maximum discount caps.

6. **Address:**
   - Stores recipient name, phone, line address, city, state, and postal code.
   - Supports marking a default shipping destination.

7. **Order & OrderItem:**
   - Captures order subtotal, discount, delivery fee, payment method (COD, Card, UPI), and tracking status (Placed, Confirmed, Shipped, Delivered, Cancelled).
   - Generates tracking numbers (`SK-TRK-XXXXXX`) and delivery dates automatically.
   - `OrderItem` preserves price, product name, and colorway at purchase time to maintain historical accuracy regardless of catalog changes.

8. **Review & ContactMessage:**
   - Enforces one review per customer per product (`unique_together = ('product', 'user')`).
   - Contact messages record user support inquiries with administrative resolution flags.

---

## 3. Storefront Modules and Business Logic

### 3.1 Discovery and Live Search Autocomplete
The storefront navbar and mobile drawer incorporate debounced Alpine.js input listeners that query `/search/autocomplete` (or `/api/search/autocomplete/`) with a 250ms threshold. Results return structured product data including thumbnails, prices, discount badges, and direct links without full page reloads.

### 3.2 Dynamic Variant Switching
On product detail pages, selecting a color swatch dynamically swaps the displayed hero image, updates pricing and discount badges, and reflects variant-specific stock levels.

### 3.3 Cart Calculations and Shipping Fees
Cart totals calculate item subtotal, validate active coupon codes, and assess shipping fees. Subtotals below the free delivery threshold (INR 499) incur an INR 40 delivery fee, while qualifying subtotals receive free delivery.

### 3.4 Order Processing, Invoicing, and Cancellation
- **Checkout:** Selects from saved customer addresses or records new shipping details, confirms payment method selection, and creates order records.
- **Invoicing:** Generates printable invoices (`/orders/<id>/invoice`) containing itemized pricing, discounts, shipping address, and order metadata.
- **Cancellation:** Customers can cancel placed or confirmed orders. The cancellation workflow records the reason and timestamps the cancellation.

---

## 4. RESTful API Endpoints

The API is structured under `/api/` with consistent JSON response formats:

| Module | Endpoint | Method | Authentication | Description |
| :--- | :--- | :---: | :---: | :--- |
| **Auth** | `/api/auth/register/` | POST | Anonymous | Customer registration (assigns non-staff user) |
| **Auth** | `/api/auth/login/` | POST | Anonymous | Customer authentication and session initialization |
| **Auth** | `/api/auth/logout/` | POST | Authenticated | Terminates active customer session |
| **Auth** | `/api/auth/user/` | GET | Authenticated | Retrieves current user profile |
| **Auth** | `/api/auth/profile/update/` | POST | Authenticated | Updates name and email address |
| **Auth** | `/api/auth/password/change/` | POST | Authenticated | Changes password with current password verification |
| **Catalog** | `/api/categories/` | GET | Public | Lists active categories and subcategory hierarchies |
| **Catalog** | `/api/categories/<slug>/` | GET | Public | Retrieves category details and product listings |
| **Catalog** | `/api/products/` | GET | Public | Catalog query with sorting, price, and stock filters |
| **Catalog** | `/api/products/<slug>/` | GET | Public | Detailed product data with variants and reviews |
| **Search** | `/api/search/` | GET | Public | Keyword search across catalog |
| **Search** | `/api/search/autocomplete/` | GET | Public | Debounced suggestions for search bars |
| **Cart** | `/api/cart/` | GET | Authenticated | Retrieves active cart lines and price breakdown |
| **Cart** | `/api/cart/add/` | POST | Authenticated | Adds product and variant to cart |
| **Cart** | `/api/cart/update/<id>/` | POST | Authenticated | Modifies line item quantity |
| **Cart** | `/api/cart/remove/<id>/` | POST | Authenticated | Removes item from cart |
| **Cart** | `/api/cart/clear/` | POST | Authenticated | Clears all cart items |
| **Cart** | `/api/cart/move-to-wishlist/<id>/` | POST | Authenticated | Moves item from cart to wishlist |
| **Coupons** | `/api/coupons/` | GET | Public | Lists active promotional coupons |
| **Coupons** | `/api/coupons/apply/` | POST | Authenticated | Applies coupon code to active session |
| **Coupons** | `/api/coupons/remove/` | POST | Authenticated | Detaches coupon from active session |
| **Wishlist** | `/api/wishlist/` | GET | Authenticated | Lists saved wishlist items |
| **Wishlist** | `/api/wishlist/toggle/<id>/` | POST | Authenticated | Toggles product in customer wishlist |
| **Wishlist** | `/api/wishlist/move-to-cart/<id>/` | POST | Authenticated | Moves wishlist item into cart |
| **Address** | `/api/addresses/` | GET | Authenticated | Lists customer shipping addresses |
| **Address** | `/api/addresses/create/` | POST | Authenticated | Creates a new shipping address |
| **Address** | `/api/addresses/<id>/update/` | POST | Authenticated | Modifies an existing shipping address |
| **Address** | `/api/addresses/<id>/delete/` | POST | Authenticated | Deletes a shipping address |
| **Address** | `/api/addresses/<id>/default/` | POST | Authenticated | Sets default shipping destination |
| **Orders** | `/api/orders/` | GET | Authenticated | Lists authenticated customer's order history |
| **Orders** | `/api/orders/create/` | POST | Authenticated | Places a new order from cart |
| **Orders** | `/api/orders/<id>/` | GET | Authenticated | Retrieves detailed order tracking and items |
| **Orders** | `/api/orders/<id>/cancel/` | POST | Authenticated | Cancels an eligible order |
| **Orders** | `/api/orders/<id>/reorder/` | POST | Authenticated | Re-adds past order items to active cart |
| **Reviews** | `/api/products/<id>/reviews/create/` | POST | Authenticated | Submits customer review and rating |
| **Support** | `/api/contact/` | POST | Public | Submits customer contact inquiry |
| **Sync** | `/api/live-sync/version/` | GET | Public | Returns current store revision timestamp |
| **Sync** | `/api/live-sync/events/` | GET | Public | Delta events since specified timestamp |
| **Sync** | `/api/live-sync/stream/` | GET | Public | Server-Sent Events (SSE) live event stream |

---

## 5. Administrative Access and Security Architecture

### 5.1 Access Control Separation
- **Customer Layer:** Public registration creates standard users (`is_staff=False`, `is_superuser=False`). Customer views and APIs strictly filter data by `user=request.user`, preventing cross-customer access to orders, invoices, or addresses.
- **Administrative Layer:** Access to `/admin/` and all custom management views (`shop/admin_views.py`) requires authenticated staff credentials (`is_staff=True`). Unauthenticated or non-staff requests are redirected to `/admin/login/`.
- **Destructive Operations:** State-altering operations (status changes, deletions, toggles) enforce both `@staff_required` and `@require_POST`.

### 5.2 Session Management
`DualSessionMiddleware` inspects the incoming path:
- `/admin/*` requests utilize the `admin_sessionid` cookie.
- Storefront requests utilize the standard `sessionid` cookie.
- Prevents staff session invalidation during customer testing workflows.

---

## 6. Testing and Verification Results

The automated test suite in `shop/tests.py` verifies core functional areas across customer accounts, catalog browsing, cart calculations, order processing, and permissions.

### 6.1 Test Suite Execution
```text
Creating test database for alias 'default'...
....................
----------------------------------------------------------------------
Ran 20 tests in 18.387s

OK
Destroying test database for alias 'default'...
Found 20 test(s).
System check identified no issues (0 silenced).
```

### 6.2 Test Coverage Summary
- Profile updates, address management, and password changes.
- Category trees, faceted search, and debounced autocomplete endpoints.
- Cart additions, quantity updates, bi-directional cart-to-wishlist operations, and coupon discount validation.
- Checkout, tracking number assignment, order cancellation, tax invoices, and one-click re-ordering.
- System check: 0 issues identified.

---

## 7. Deployment Configuration

ShopKart is configured for deployment on Render paired with Neon PostgreSQL.

### 7.1 Infrastructure Specifications
- **Runtime:** Python 3.12
- **Process Manager:** Gunicorn WSGI server configured with a conservative worker profile (`--workers 1 --threads 4 --max-requests 500 --max-requests-jitter 50 --timeout 30`) to operate reliably within 512 MB memory constraints.
- **Static Asset Serving:** WhiteNoise with compressed file storage (`CompressedStaticFilesStorage`).
- **Database Driver:** `psycopg2-binary` managed via `dj-database-url` with `ssl_require=True` and connection health checks.

### 7.2 Current Limitations and Technical Context
- **Payment Processing:** Payment methods (COD, UPI, Card) are currently simulated without active third-party gateway webhooks (e.g., Stripe, Razorpay).
- **Inventory Deductions:** Checkout records order placements without decrementing physical stock quantity counters. Suitable for demonstration environments where stock should not deplete permanently.
- **Media Storage:** Committed catalog graphics in `static/` are served reliably. Administrative uploads performed on ephemeral cloud containers reset on instance restarts unless external persistent object storage (such as AWS S3 or Cloudinary) is connected.
