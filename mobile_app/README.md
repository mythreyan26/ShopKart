# ShopKart Mobile App (React Native + Expo)

Cross-platform mobile application for **ShopKart**, powered by React Native and connecting to the Django REST API backend.

---

## Features

- 📱 **Multi-Platform**: Runs on **Android**, **iOS**, and **Web**.
- 🏠 **Storefront**: Hero promotions, trending deals, bestsellers, live search.
- 📦 **Interactive Catalog**: Hierarchical categories, subcategories, price sorting and filter chips.
- 🎨 **Dynamic Color Variants**: Live price, stock, and gallery preview per color variant.
- 🛒 **Full Cart & Checkout Flow**: Add/Update/Remove items, delivery fee thresholds, saved addresses, payment methods (COD / UPI / Card).
- ❤️ **Wishlist**: 1-tap save and instant move to cart.
- 👤 **User Accounts & Orders**: Registration, login, profile, and order status tracking.

---

## Getting Started

### 1. Prerequisites
- **Node.js** (v18 or newer)
- **Expo CLI** (bundled with `npx expo`)
- Physical phone with **Expo Go** app (free on Google Play Store / Apple App Store) OR Android/iOS Emulator

### 2. Configure Backend Server URL
Open `src/services/api.js` and set `BASE_URL`:
- **Android Emulator**: `http://10.0.2.2:8000` (default)
- **iOS Simulator**: `http://localhost:8000`
- **Physical Phone**: Replace with your computer's local Wi-Fi IP (e.g. `http://192.168.1.15:8000`)

> Make sure your Django dev server is running on the computer:
> ```bash
> python manage.py runserver 0.0.0.0:8000
> ```

### 3. Install Dependencies
```bash
cd mobile_app
npm install
```

### 4. Run the Mobile App
```bash
npx expo start
```

- Scan the QR code with **Expo Go** (Android) or **Camera** (iOS) to test live on your phone.
- Press `a` to run on Android emulator.
- Press `i` to run on iOS simulator.
- Press `w` to run on Web browser.
