# ShopKart — Modern E-Commerce Platform & Multi-Device App

A modern, Amazon/Flipkart-style online store built with **Django 5 + Tailwind CSS + Alpine.js**, now featuring full **Universal Multi-Device App Support** (Progressive Web App + Mobile App + REST API).

## Latest Features & Architecture

🛍️ **Coupons & Promo Codes Engine**
- Dynamic promo code engine with percentage discounts (e.g. `WELCOME10`, `SAVE20`) and fixed cash discounts (e.g. `FLAT100`, `FESTIVE500`).
- Minimum order subtotal conditions, maximum discount caps, active validity toggles.
- Integrated into Cart, Checkout, Order records, and REST API.

🔍 **Instant Search Autocomplete**
- Debounced live search suggestions in the desktop navbar and mobile search drawer.
- Displays instant product thumbnails, price, discount badges, ratings, and one-click navigation.

📦 **Order Status Tracking Stepper & Printable Tax Invoice**
- Visual 4-step delivery progress bar: `Placed` → `Packed` → `Shipped` → `Delivered`.
- Printable receipt `/orders/<id>/invoice` with itemized prices, coupon discounts, customer address, and tax invoice metadata.

👤 **User Profile & Address Book Hub**
- Dedicated `/profile` hub displaying customer lifetime spend, total orders, wishlist counters, and editable account details.
- Comprehensive Address Book Manager: Add new addresses, set default shipping address, delete outdated addresses.

⭐ **Customer Rating Breakdown & Reviews**
- Visual 5-star rating distribution breakdown on product details pages.
- Verified buyer review submission form with star ratings and headlines.

🔔 **Floating Toast Notification System**
- Modern floating animated toast alerts for instant feedback (item added, coupon applied, profile updated).

📱 **Universal Multi-Device App Experience**
- **Installable PWA**: 1-click installation on Android, iOS Safari, Windows, macOS, and Linux.
- **Mobile Bottom Navigation Bar**: Quick thumb access to Home, Explore, Wishlist, Cart, and Account.
- **Sticky Purchase Bar**: Quick mobile Add-to-Cart and Buy Now buttons.
- **Offline Fallback Screen**: Service worker precaching with offline screen (`/offline/`).

⚡ **Full RESTful JSON API Engine (`/api/`)**
- Complete JSON endpoints covering Auth, Catalog, Live Search Autocomplete, Cart, Coupons, Wishlist, Addresses, Orders, and Reviews.

📲 **React Native + Expo Cross-Platform Mobile Client (`mobile_app/`)**
- Dedicated mobile application codebase in `mobile_app/` ready to run on physical Android and iOS phones via Expo Go.

## Getting started

```bash
# 1. Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Apply database migrations
python manage.py migrate

# 4. Load demo data (8 categories, 33 products, sample reviews)
python manage.py seed_data

# 5. (Optional) create an admin account
python manage.py createsuperuser

# 6. Run the dev server
python manage.py runserver
```

Visit **http://127.0.0.1:8000/**

### Demo login
- Username: `demo_buyer`
- Password: `demopass123`

### Admin panel
Visit `/admin` with the superuser account you created to manage categories, products,
orders, and reviews (Jazzmin theme included).

## Notes

- Styling is done via the **Tailwind CSS CDN** (no Node/build step required) plus
  **Alpine.js** for interactivity (dropdowns, mobile menu, banner rotation, tabs). This
  requires an internet connection in the browser to load those CDN scripts.
- Product/category images are custom-generated SVG "studio" artwork (soft gradients +
  icon), stored under `static/images/gen/`. Swap in real product photography any time by
  uploading through the Django admin — the layout and image handling are unchanged.
- Payments are simulated (Cash on Delivery / UPI / Card selection with no gateway
  integration) — wire up Razorpay/Stripe when you're ready to go live.
- `DEBUG = True` and a SQLite database are configured for local development. Switch to
  Postgres + `DEBUG = False` + proper `ALLOWED_HOSTS` before deploying.
