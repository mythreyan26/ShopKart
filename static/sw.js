const CACHE_NAME = 'shopkart-v1.0.4';
const OFFLINE_URL = '/offline/';

const PRECACHE_ASSETS = [
  '/',
  '/offline/',
  '/static/manifest.json',
  '/static/css/style.css',
  '/static/images/icons/icon-192.png',
  '/static/images/icons/icon-512.png',
  '/static/images/icons/apple-touch-icon.png',
  'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
];

// Install event - precache core shell
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(PRECACHE_ASSETS).catch((err) => {
        console.warn('Some precache assets failed to fetch:', err);
      });
    }).then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches and purge any cached admin paths
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keyList) => {
      return Promise.all(
        keyList.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    }).then(() => caches.open(CACHE_NAME)).then((cache) => {
      return cache.keys().then((requests) => {
        return Promise.all(
          requests.map((req) => {
            const u = new URL(req.url);
            if (u.pathname.startsWith('/admin') || u.pathname.startsWith('/api/')) {
              return cache.delete(req);
            }
          })
        );
      });
    }).then(() => self.clients.claim())
  );
});

// Fetch event - Stale-while-revalidate for static, Network-first for HTML pages
self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);

  // Skip non-GET and chrome-extension requests
  if (request.method !== 'GET' || url.protocol.startsWith('chrome-extension')) {
    return;
  }

  // Never intercept Django Admin routes, admin assets, or API endpoints - let browser handle directly
  if (url.pathname.startsWith('/admin') || url.pathname.startsWith('/api/') || url.pathname.includes('admin_custom') || url.pathname.includes('/admin/')) {
    return;
  }

  // Handle navigation (HTML page requests)
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Cache a clone of the page for offline viewing
          if (response.status === 200) {
            const copy = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
          }
          return response;
        })
        .catch(async () => {
          // Quick retry after 500ms in case local server was auto-reloading code changes
          try {
            await new Promise((r) => setTimeout(r, 500));
            const retryRes = await fetch(request);
            if (retryRes && retryRes.ok) {
              const copy = retryRes.clone();
              caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
              return retryRes;
            }
          } catch (retryErr) {
            // Server really offline
          }

          // Try to get from cache
          const cachedResponse = await caches.match(request);
          if (cachedResponse) {
            return cachedResponse;
          }
          // Fallback to offline page
          const offlinePage = await caches.match(OFFLINE_URL);
          return offlinePage || new Response('Offline - No connection available', {
            status: 503,
            statusText: 'Service Unavailable',
            headers: new Headers({ 'Content-Type': 'text/plain' }),
          });
        })
    );
    return;
  }

  // Handle static assets (images, fonts, stylesheets, scripts)
  if (
    request.destination === 'style' ||
    request.destination === 'script' ||
    request.destination === 'image' ||
    request.destination === 'font'
  ) {
    event.respondWith(
      caches.match(request).then((cachedResponse) => {
        if (cachedResponse) {
          // Fetch update in background (stale-while-revalidate)
          fetch(request).then((networkResponse) => {
            if (networkResponse && networkResponse.status === 200) {
              caches.open(CACHE_NAME).then((cache) => cache.put(request, networkResponse));
            }
          }).catch(() => {/* Ignore background fetch failure */});
          return cachedResponse;
        }

        return fetch(request).then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const copy = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
          }
          return networkResponse;
        }).catch(() => {
          // Offline image placeholder could go here
          return new Response('', { status: 408, statusText: 'Request timed out.' });
        });
      })
    );
    return;
  }

  // Default network-first for other requests
  event.respondWith(
    fetch(request).catch(() => caches.match(request))
  );
});
