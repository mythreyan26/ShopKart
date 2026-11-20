# ShopKart — E-Commerce Platform & Multi-Device Application

ShopKart is a full-featured e-commerce platform built with Django 5, Tailwind CSS, and Alpine.js, supporting web, Progressive Web App (PWA), and mobile clients.

## Architecture and Core Features

### Promotional Codes and Discounts
- Dynamic coupon engine supporting percentage discounts and fixed value reductions.
- Enforces minimum order subtotals, maximum discount limits, and validity periods.
- Integrated across cart calculations, checkout, order records, and API endpoints.

### Search and Autocomplete
- Debounced live search suggestions available in navigation bars and mobile drawers.
- Displays product thumbnails, pricing, discount tags, and direct product navigation.

### Order Tracking and Invoicing
- Visual multi-step fulfillment tracking: Placed, Packed, Shipped, Delivered.
- Printable invoices (`/orders/<id>/invoice`) with itemized pricing, customer address details, and tax metadata.

### Customer Account and Address Management
- Profile dashboard displaying order history, wishlist summaries, and account information.
- Address book allowing users to add, set default shipping destinations, and delete addresses.

### Product Reviews and Ratings
- Star rating breakdown and distribution display on product pages.
- Verified customer review submissions with star ratings and comments.

### Real-Time Alerts
- Non-blocking notification toasts for actions such as cart updates and coupon validation.

### Progressive Web App and Mobile Client
- Installable PWA with service worker caching and offline fallback (`/offline/`).
- Mobile navigation drawer, sticky purchase action bar, and responsive touch layout.
- Cross-platform React Native and Expo client codebase located in `mobile_app/`.

### RESTful JSON API
- Structured endpoints under `/api/` covering authentication, catalog browsing, cart operations, coupons, wishlists, address books, orders, and reviews.

## Getting Started

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Apply database migrations
python manage.py migrate

# 4. Load initial catalog data (or seed data for testing)
python manage.py loaddata catalog_fixtures.json

# 5. Create an administrative superuser (optional)
python manage.py createsuperuser

# 6. Start the development server
python manage.py runserver
```

Open **http://127.0.0.1:8000/** in your browser.

### Administration
Access the administrative portal at `/admin` using your superuser credentials.

## Deployment Notes

- Frontend interactivity relies on Alpine.js and Tailwind CSS CDN scripts.
- Catalog imagery is committed under `static/uploads/` and `static/images/` and served via Django's static handlers. For high-volume production deployments with frequent administrative uploads, configure persistent object storage (e.g., AWS S3 or Cloudinary).
- Production deployment on Render with PostgreSQL requires setting `DATABASE_URL` and `DJANGO_SECRET_KEY` while ensuring `DEBUG=False`.
