# ShopKart — Modern E-Commerce Website (Django)

A full redesign of the original ShopKart project into a modern, Amazon/Flipkart-style
online store, built with **Django 5 + Tailwind CSS + Alpine.js**.

## What's new in this rebuild

**Design**
- Complete visual overhaul: sticky navbar with live search, category strip, cart/wishlist
  badges, mobile drawer menu
- Auto-rotating hero banner, category quick-links, trending/featured/bestseller rails
- Premium studio-style gradient product & category artwork (generated in-house — no
  external stock photos needed to get a polished look)
- Fully responsive (mobile, tablet, desktop)

**New features (previously missing)**
- A fully working **cart**: add / increase / decrease / remove, live subtotal & free
  delivery threshold
- **Checkout flow**: multiple saved addresses, payment method selection (COD / UPI / Card
  — demo only, no real payment processing), order placement
- **Order history** and order detail pages
- **Wishlist**: toggle from any product card or the product page
- **Product reviews & ratings** (1–5 stars, average rating shown on cards)
- **Search** across product name, brand, description and category
- **Category filters**: price range + sort (price low/high, newest)

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
