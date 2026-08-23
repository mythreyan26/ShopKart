import { Platform } from 'react-native';

// Set your Django server URL here:
// Android Emulator uses 10.0.2.2 to access host machine localhost
// iOS Simulator uses localhost or 127.0.0.1
// For Physical Phones connected via Wi-Fi, use your computer's local IP (e.g. 192.168.1.X:8000)
export const BASE_URL = Platform.select({
  android: 'http://10.0.2.2:8000',
  ios: 'http://localhost:8000',
  default: 'http://localhost:8000',
});

export const API_ROOT = `${BASE_URL}/api`;

let cookieSession = '';

export const apiRequest = async (endpoint, options = {}) => {
  const url = endpoint.startsWith('http') ? endpoint : `${API_ROOT}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;
  
  const headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    ...(options.headers || {}),
  };

  if (cookieSession) {
    headers['Cookie'] = cookieSession;
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    // Save session cookies
    const setCookie = response.headers.get('set-cookie');
    if (setCookie) {
      cookieSession = setCookie;
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error(`API Request Error [${endpoint}]:`, error);
    throw error;
  }
};

export const api = {
  // Auth
  login: (username, password) => apiRequest('/auth/login/', { method: 'POST', body: JSON.stringify({ username, password }) }),
  register: (username, email, password) => apiRequest('/auth/register/', { method: 'POST', body: JSON.stringify({ username, email, password }) }),
  logout: () => apiRequest('/auth/logout/', { method: 'POST' }),
  getCurrentUser: () => apiRequest('/auth/user/'),

  // Catalog
  getCategories: () => apiRequest('/categories/'),
  getCategoryDetail: (slug, params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiRequest(`/categories/${slug}/` + (qs ? `?${qs}` : ''));
  },
  getProducts: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiRequest('/products/' + (qs ? `?${qs}` : ''));
  },
  getProductDetail: (slug) => apiRequest(`/products/${slug}/`),
  // Search & Autocomplete
  searchProducts: (query) => apiRequest(`/search/?q=${encodeURIComponent(query)}`),
  autocomplete: (query) => apiRequest(`/search/autocomplete/?q=${encodeURIComponent(query)}`),

  // Coupons
  getCoupons: () => apiRequest('/coupons/'),
  applyCoupon: (couponCode) => apiRequest('/coupons/apply/', { method: 'POST', body: JSON.stringify({ coupon_code: couponCode }) }),
  removeCoupon: () => apiRequest('/coupons/remove/', { method: 'POST' }),

  // Cart
  getCart: () => apiRequest('/cart/'),
  addToCart: (productId, colorId, quantity = 1) => apiRequest('/cart/add/', { method: 'POST', body: JSON.stringify({ product_id: productId, color_id: colorId, quantity }) }),
  updateCart: (itemId, action, quantity) => apiRequest(`/cart/update/${itemId}/`, { method: 'POST', body: JSON.stringify({ action, quantity }) }),
  removeFromCart: (itemId) => apiRequest(`/cart/remove/${itemId}/`, { method: 'POST' }),

  // Wishlist
  getWishlist: () => apiRequest('/wishlist/'),
  toggleWishlist: (productId) => apiRequest(`/wishlist/toggle/${productId}/`, { method: 'POST' }),

  // Address
  getAddresses: () => apiRequest('/addresses/'),
  createAddress: (addressData) => apiRequest('/addresses/create/', { method: 'POST', body: JSON.stringify(addressData) }),

  // Orders
  getOrders: () => apiRequest('/orders/'),
  getOrderDetail: (orderId) => apiRequest(`/orders/${orderId}/`),
  createOrder: (addressId, paymentMethod = 'cod') => apiRequest('/orders/create/', { method: 'POST', body: JSON.stringify({ address_id: addressId, payment_method: paymentMethod }) }),
};

export default api;
