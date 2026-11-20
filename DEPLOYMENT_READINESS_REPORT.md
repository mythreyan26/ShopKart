# ShopKart — Production Deployment Readiness & Implementation Report
**Target Environment:** Render (Free Web Service) + Neon (Serverless PostgreSQL)  
**Author:** Senior Django & DevOps Engineering  
**Date:** November 20, 2026  
**Implementation Status:** COMPLETED LOCALLY & FULLY VERIFIED (No Git commit/push executed)  

---

## Executive Summary

The production deployment configuration for **ShopKart** on **Render** with **Neon PostgreSQL** has been fully implemented and verified locally. All corrections identified during the architectural reviews have been applied.

All 11 implementation and safety requirements have been met:
* **Zero code modifications** were made to checkout, orders, inventory, coupons, authentication, REST APIs, or frontend components.
* All existing committed catalogue images (61 product images and 36 category images) are verified intact on disk with zero missing files.
* Unit test coverage remains **100% passing (20/20 tests)**.
* Django system checks report **0 issues**.
* Migrations are synchronized with the creation of `shop/migrations/0007_alter_address_options.py`.
* A dedicated, clean catalogue fixture (`catalog_fixtures.json`) has been exported, completely omitting all demo accounts, customer addresses, carts, wishlists, and order histories.

---

## 1. Inventory Functionality & Portfolio Showcase Suitability

### 1.1 Impact of Checkout Stock Logic
A code-level audit of `shop/views.py` (`checkout_view`) and `shop/api_views.py` (`api_checkout`) confirms:
* **Checkout Stock Behavior:** When an order is placed, an `Order` and associated `OrderItem` records are created, but `Product.quantity` and `ProductColor.quantity` are **not** decremented.
* **Order Cancellation Behavior:** When an order is cancelled (`cancel_order` / `cancel_order_item`), the logic executes `item.product.quantity += item.quantity`. Because stock was never deducted at checkout, cancellation increments the counter above its original level.
* **Admin Stock Dashboard:** The Miguel Studio stock control dashboard (`/admin/inventory/`) displays inventory and allows manual restocking, but the counter is disconnected from customer purchases.

### 1.2 Portfolio Suitability Classification

**CLASSIFICATION: HIGHLY SUITABLE FOR PORTFOLIO DEMONSTRATION**

* **Why it is ideal for a portfolio demo:**
  Recruiters, hiring managers, and prospective clients evaluate UI polish (Miguel Studio admin, responsive mobile drawer, sticky desktop filters), the browse-to-buy customer journey, promo codes, 4-step delivery tracking stepper, printable tax invoice, real-time Live Sync, and PWA capabilities.
  In a demo environment, **non-decrementing stock is an advantage**: visitors can test placing orders repeatedly without draining the catalogue and leaving the store empty or "sold out" for subsequent visitors.
* **Commercial Retail Caveat:**
  For real-world retail with physical inventory, failing to decrement inventory leads to overselling. Implementing `select_for_update()` and atomic deductions within `transaction.atomic()` will be required before processing real customer transactions with actual payment gateways.

---

## 2. Static and Media Files Delivery Architecture

### 2.1 Configuration Review
* **`STATIC_URL`:** `'/static/'`
* **`STATIC_ROOT`:** `BASE_DIR / 'staticfiles'`
* **`STATICFILES_DIRS`:** `[ BASE_DIR / 'static' ]`
* **`MEDIA_URL`:** `'/images/'`
* **`MEDIA_ROOT`:** `BASE_DIR / 'static'`
* **`STORAGES`:**
  ```python
  STORAGES = {
      "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
      "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
  }
  ```
* **URL Routing:** `re_path(r'^images/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT})` in `ms_project/urls.py`.

### 2.2 Serving Mechanism: WhiteNoise vs. Django `serve`
* **WhiteNoise (`/static/`):** WhiteNoise is mounted on `STATIC_URL`. During deployment, `python manage.py collectstatic --noinput` copies all static assets into `STATIC_ROOT` (`staticfiles/`), applying gzip/Brotli compression. WhiteNoise serves CSS, JS, fonts, and PWA assets.
* **Media Handling (`/images/`):** Model image fields return paths like `uploads/prod_laptop.jpg`. Templates render `{{ product.product_image.url }}`, producing `/images/uploads/prod_laptop.jpg`. **WhiteNoise does NOT serve `/images/`**; requests matching `^images/(?P<path>.*)$` are routed to Django’s `serve` view, resolving directly from `settings.MEDIA_ROOT` (`BASE_DIR / 'static'`).

### 2.3 Verification of Committed Images vs. Runtime Uploads
* **Committed Catalogue Images (Verified Intact):**
  A full filesystem sweep verified that all **61 product images** and **36 category images** referenced by catalogue models exist on disk under `static/uploads/` and `static/images/`. Because these files are tracked in Git, Render clones them into the deployment container, ensuring all storefront photos display without broken links.
* **Runtime Admin Uploads (Ephemeral Container Disk):**
  Any *new* product photos or variant images uploaded through the admin panel in production will be saved to `static/uploads/` on Render's **ephemeral local filesystem**. When Render restarts or sleeps on the Free tier, newly uploaded files will be lost. For long-term production use, external cloud storage (Cloudinary or AWS S3) is recommended.

---

## 3. Gunicorn Sizing for Render 512 MB Free Instance

### 3.1 Resource Realities
Render Free Tier enforces a hard **512 MB RAM ceiling**. Any memory breach immediately triggers the Linux cgroup OOM killer, killing the process with **Exit Code 137**.

### 3.2 Implemented Configuration
In both [render.yaml](file:///c:/Users/MYTHREYAN/OneDrive/Desktop/Mythreyan/MS_Projects/ShopKart/render.yaml) and [Procfile](file:///c:/Users/MYTHREYAN/OneDrive/Desktop/Mythreyan/MS_Projects/ShopKart/Procfile), the start command is configured as:
```bash
gunicorn ms_project.wsgi:application --workers 1 --threads 4 --max-requests 500 --max-requests-jitter 50 --timeout 30 --bind 0.0.0.0:$PORT
```

**Technical Rationale:**
* **`--workers 1 --threads 4`**: Single master and single worker process minimizes baseline memory overhead, leaving maximal RAM available for database connection buffers and concurrent requests.
* **`--max-requests 500 --max-requests-jitter 50`**: Automatically recycles the worker process after ~500 requests to clear Python memory fragmentation and prevent cumulative memory leaks.
* **`--timeout 30`**: Drops stalled requests before they hold worker threads hostage.

---

## 4. Summary of Modified Files & Changes

### 4.1 `requirements.txt`
Added PostgreSQL driver and database URL parsing dependencies:
```text
psycopg2-binary>=2.9.9
dj-database-url>=2.1.0
```

### 4.2 `ms_project/settings.py`
1. **Dynamic Database Parsing:**
   ```python
   database_url = os.getenv('DATABASE_URL')
   if database_url:
       DATABASES = {
           'default': dj_database_url.parse(
               database_url,
               conn_max_age=0,  # Recommended for serverless PgBouncer on Neon
               conn_health_checks=True,
               ssl_require=True,
           )
       }
   else:
       DATABASES = {
           'default': {
               'ENGINE': 'django.db.backends.sqlite3',
               'NAME': BASE_DIR / 'db.sqlite3',
           }
       }
   ```
2. **Mandatory Production `SECRET_KEY`:**
   ```python
   SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
   if not SECRET_KEY:
       if not DEBUG:
           raise ImproperlyConfigured("DJANGO_SECRET_KEY environment variable is required in production (when DEBUG=False).")
       SECRET_KEY = 'django-insecure-*@u*b=nl8e3u%kjw=%v+3!l)((hm@o=+k^+-yxguxqy=!owu8+'
   ```
3. **Secure `ALLOWED_HOSTS`:**
   ```python
   raw_allowed_hosts = os.getenv('ALLOWED_HOSTS', '')
   if raw_allowed_hosts:
       ALLOWED_HOSTS = [h.strip() for h in raw_allowed_hosts.split(',') if h.strip()]
   elif DEBUG:
       ALLOWED_HOSTS = ['*']
   else:
       ALLOWED_HOSTS = ['.onrender.com', 'localhost', '127.0.0.1']
   ```
4. **Development-Only `X_FRAME_OPTIONS`:**
   ```python
   if DEBUG:
       X_FRAME_OPTIONS = 'ALLOWALL'
   else:
       X_FRAME_OPTIONS = 'SAMEORIGIN'
   ```

### 4.3 `build.sh`
Removed all automated demo fixture loading:
```bash
#!/usr/bin/env bash
set -o errexit

echo "--- Installing dependencies ---"
pip install --upgrade pip
pip install -r requirements.txt

echo "--- Collecting static assets with WhiteNoise ---"
python manage.py collectstatic --noinput

echo "--- Applying database schema migrations ---"
python manage.py migrate

echo "--- ShopKart build completed successfully! ---"
```

### 4.4 `render.yaml` & `Procfile`
* Updated start command to conservative Gunicorn settings.
* Added `DATABASE_URL` environment variable with `sync: false`.

### 4.5 `shop/migrations/0007_alter_address_options.py`
Generated clean model metadata migration for `Address`:
```python
class Migration(migrations.Migration):
    dependencies = [('shop', '0006_order_cancellation_reason_order_cancelled_at_and_more')]
    operations = [
        migrations.AlterModelOptions(
            name='address',
            options={'verbose_name': 'Address', 'verbose_name_plural': 'Addresses'},
        ),
    ]
```

### 4.6 `catalog_fixtures.json` (New Catalogue-Only Fixture)
Exported clean fixture containing **only** storefront catalogue models:
* `shop.Category` (40 records)
* `shop.Product` (61 records)
* `shop.ProductColor` (17 records)
* `shop.ProductColorImage` (42 records)
* `shop.ProductImage` (12 records)
* `shop.Coupon` (7 records)
* **Zero demo users, zero fake orders, zero dummy addresses.**

---

## 5. Verification & Test Execution Results

| Test / Check | Command Executed | Result | Notes |
| :--- | :--- | :--- | :--- |
| **Django System Checks** | `manage.py check` | **PASSED** | 0 issues identified, 0 silenced |
| **Unit Test Suite** | `manage.py test` | **PASSED (20/20)** | Full project test suite passed in 18.38s |
| **Database Migrations** | `manage.py showmigrations` | **PASSED** | All migrations applied, including `0007` |
| **Static Collection Execution**| `manage.py collectstatic --noinput` | **PASSED** | 763 static files collected and compressed in `staticfiles/` |
| **Catalogue Image Check** | Python path verification | **PASSED** | 61/61 product images & 36/36 category images verified on disk |
| **Fail-Fast `SECRET_KEY`** | Automated script test | **PASSED** | `ImproperlyConfigured` raised when key is empty in production |
| **PostgreSQL & PgBouncer** | Connection test to Neon | **PASSED** | Driver loaded, connected to host over SSL, authenticated |

---

## 6. One-Time Production Setup Instructions

Once deployed to Render, perform the following one-time setup via the **Render Shell**:

### Step 1: Initialize Storefront Catalogue
Populate the empty database with catalogue data (categories, products, variants, coupons):
```bash
python manage.py loaddata catalog_fixtures.json
```

### Step 2: Reset PostgreSQL Sequences
Synchronize PostgreSQL auto-increment counters so new records do not conflict with existing IDs:
```bash
python manage.py sqlsequencereset shop | python manage.py dbshell
```

### Step 3: Create Production Administrator
Create your superuser account for the Miguel Studio admin dashboard:
```bash
python manage.py createsuperuser
```

---

## 7. Git & Deployment Safety
* **Zero Git commits or pushes were made.**
* All changes are staged locally in your working directory.
* Review the git status:
  * Modified: `Procfile`, `build.sh`, `ms_project/settings.py`, `render.yaml`, `requirements.txt`, `README.md`
  * Untracked: `catalog_fixtures.json`, `shop/migrations/0007_alter_address_options.py`, `DEPLOYMENT_READINESS_REPORT.md`
