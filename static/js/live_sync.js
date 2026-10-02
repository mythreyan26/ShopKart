/**
 * ShopKart Real-Time Live Sync Client
 * 
 * Automatically detects and synchronizes modifications made in Django Admin
 * (products, prices, stock, order statuses, categories, coupons) on the live store
 * in real-time without requiring the customer to manually refresh the page.
 */

(function () {
  'use strict';

  let currentVersion = 0;
  let pollInterval = null;
  let isUpdating = false;
  let isInitialized = false;

  // -------------------------------------------------------------
  // Floating Toast Notifications for Real-Time Events
  // -------------------------------------------------------------
  function showLiveToast(message, icon = '⚡', type = 'info') {
    let container = document.getElementById('shopkart-live-toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'shopkart-live-toast-container';
      container.className = 'fixed top-20 right-4 sm:right-6 z-50 space-y-2.5 max-w-md w-full pointer-events-none px-2 sm:px-0';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    const bgColors = {
      success: 'bg-emerald-950/95 text-emerald-100 border-emerald-700/70 shadow-emerald-900/30',
      warning: 'bg-amber-950/95 text-amber-100 border-amber-700/70 shadow-amber-900/30',
      error: 'bg-rose-950/95 text-rose-100 border-rose-700/70 shadow-rose-900/30',
      info: 'bg-navy/95 text-white border-orange-500/50 shadow-orange-500/20',
    };
    const colorClass = bgColors[type] || bgColors.info;

    toast.className = `pointer-events-auto rounded-2xl p-4 shadow-2xl border backdrop-blur-md flex items-center justify-between gap-3 text-sm transition-all duration-300 transform translate-y-2 opacity-0 ${colorClass}`;
    toast.innerHTML = `
      <div class="flex items-center gap-3">
        <span class="text-xl shrink-0">${icon}</span>
        <div>
          <p class="text-[10px] font-extrabold tracking-wider uppercase text-orange-300">Live Store Sync</p>
          <p class="font-semibold text-xs sm:text-sm leading-snug text-white">${message}</p>
        </div>
      </div>
      <button class="p-1 text-slate-400 hover:text-white rounded-lg transition" onclick="this.parentElement.remove()">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
      </button>
    `;

    container.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
      toast.classList.remove('translate-y-2', 'opacity-0');
      toast.classList.add('translate-y-0', 'opacity-100');
    });

    // Auto remove after 5 seconds
    setTimeout(() => {
      toast.classList.remove('translate-y-0', 'opacity-100');
      toast.classList.add('translate-y-2', 'opacity-0');
      setTimeout(() => toast.remove(), 350);
    }, 5000);
  }

  // -------------------------------------------------------------
  // Live Sync Status Badge (Discreet bottom-left indicator)
  // -------------------------------------------------------------
  function renderLiveStatusBadge() {
    if (document.getElementById('live-sync-indicator')) return;
    const badge = document.createElement('div');
    badge.id = 'live-sync-indicator';
    badge.className = 'fixed bottom-20 md:bottom-4 left-4 z-40 bg-navy/90 text-white text-[10px] font-bold px-2.5 py-1 rounded-full shadow-lg border border-white/10 backdrop-blur-xs flex items-center gap-1.5 opacity-70 hover:opacity-100 transition duration-200 pointer-events-none select-none';
    badge.innerHTML = `
      <span class="relative flex h-2 w-2">
        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
        <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
      </span>
      <span class="tracking-wide">Live Sync</span>
    `;
    document.body.appendChild(badge);
  }

  function pulseBadge() {
    const badge = document.getElementById('live-sync-indicator');
    if (badge) {
      badge.classList.remove('opacity-70');
      badge.classList.add('opacity-100', 'scale-105');
      setTimeout(() => {
        badge.classList.remove('scale-105');
        badge.classList.add('opacity-70');
      }, 1000);
    }
  }

  // -------------------------------------------------------------
  // Page Type Detection (Robust Regex Matching)
  // -------------------------------------------------------------
  function getPageContext() {
    const path = window.location.pathname.replace(/\/$/, '') || '/';

    // 1. Order details: /orders/12 or /orders/12/invoice
    const orderDetailMatch = path.match(/^\/orders\/(\d+)/);
    if (orderDetailMatch) {
      return { type: 'order_detail', id: orderDetailMatch[1] };
    }

    // 2. Orders list: /orders
    if (path === '/orders') {
      return { type: 'orders_list' };
    }

    // 3. User profile: /profile
    if (path === '/profile') {
      return { type: 'profile' };
    }

    // 4. Product details: /collections/<category>/<product>
    const prodDetailMatch = path.match(/^\/collections\/([^\/]+)\/([^\/]+)$/);
    if (prodDetailMatch) {
      return { type: 'product_detail', categorySlug: prodDetailMatch[1], slug: prodDetailMatch[2] };
    }

    // 5. Catalog pages: /, /search, /collections, /category/...
    if (path === '/' || path === '/search' || path.startsWith('/collections') || path.startsWith('/category')) {
      return { type: 'catalog' };
    }

    // 6. Cart & Checkout: /cart, /checkout
    if (path === '/cart' || path === '/checkout') {
      return { type: 'cart' };
    }

    return { type: 'general' };
  }

  // -------------------------------------------------------------
  // Seamless Background DOM Container Refresher
  // -------------------------------------------------------------
  async function refreshMainContentSilently() {
    if (isUpdating) return;
    isUpdating = true;
    try {
      const currentScroll = window.scrollY;
      const res = await fetch(window.location.href, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        cache: 'no-store'
      });
      if (!res.ok) return;
      const htmlText = await res.text();
      const parser = new DOMParser();
      const newDoc = parser.parseFromString(htmlText, 'text/html');

      const newMain = newDoc.querySelector('main');
      const oldMain = document.querySelector('main');
      if (newMain && oldMain) {
        oldMain.innerHTML = newMain.innerHTML;

        // Re-initialize Alpine on the new DOM tree if available
        if (window.Alpine) {
          window.Alpine.initTree(oldMain);
        }
        window.scrollTo({ top: currentScroll, behavior: 'instant' });
      }
    } catch (e) {
      console.warn('[LiveSync] Silent refresh error:', e);
    } finally {
      setTimeout(() => { isUpdating = false; }, 350);
    }
  }

  // -------------------------------------------------------------
  // Master Event Dispatcher
  // -------------------------------------------------------------
  function dispatchLiveEvent(event) {
    if (!event || !event.entity_type) return;
    pulseBadge();

    const ctx = getPageContext();
    const details = event.details || {};

    // -------------------------------------------------------------
    // 1. ORDER EVENTS
    // -------------------------------------------------------------
    if (event.entity_type === 'order') {
      const orderId = details.id;
      const statusDisplay = details.status_display || details.status || 'Updated';

      if (ctx.type === 'order_detail') {
        // User is currently viewing /orders/<id>
        if (!ctx.id || String(ctx.id) === String(orderId)) {
          showLiveToast(`Order #${orderId} status updated to "${statusDisplay}"!`, '📦', 'success');
          refreshMainContentSilently();
        }
      } else if (ctx.type === 'orders_list') {
        // User is currently viewing /orders (My Orders list)
        showLiveToast(`Order #${orderId} status updated to "${statusDisplay}"!`, '📦', 'success');
        refreshMainContentSilently();
      } else if (ctx.type === 'profile') {
        // User is on /profile (Customer Profile Hub)
        showLiveToast(`Order #${orderId} status updated to "${statusDisplay}"!`, '📦', 'success');
        refreshMainContentSilently();
      } else {
        // User is on another page
        showLiveToast(`Order #${orderId} status: "${statusDisplay}"`, '📦', 'info');
      }
    }

    // -------------------------------------------------------------
    // 2. PRODUCT EVENTS
    // -------------------------------------------------------------
    else if (event.entity_type === 'product') {
      if (ctx.type === 'product_detail') {
        const matchesCurrent = (details.slug && details.slug === ctx.slug) || (details.id && String(details.id) === String(ctx.id));
        if (matchesCurrent) {
          if (details.status === true || event.action === 'deleted') {
            showLiveToast(`Product "${details.name || 'this item'}" was unlisted by the store manager.`, '⚠️', 'warning');
            setTimeout(() => window.location.reload(), 1500);
          } else {
            showLiveToast(`Price & stock updated for "${details.name || 'Product'}" (Now ₹${Math.round(details.selling_price || 0).toLocaleString('en-IN')})`, '⚡', 'success');
            refreshMainContentSilently();
          }
        } else {
          // Different product was edited; refresh page to update related items/recommendations
          refreshMainContentSilently();
        }
      } else if (ctx.type === 'catalog' || ctx.type === 'cart' || ctx.type === 'orders_list') {
        const actionDesc = event.action === 'created' ? 'added to' : (event.action === 'deleted' ? 'removed from' : 'updated in');
        showLiveToast(`"${details.name || 'Catalog item'}" was ${actionDesc} the store catalog.`, '⚡', 'info');
        refreshMainContentSilently();
      }
    }

    // -------------------------------------------------------------
    // 3. CATEGORY EVENTS
    // -------------------------------------------------------------
    else if (event.entity_type === 'category') {
      showLiveToast(`Category "${details.name || 'Department'}" updated.`, '📁', 'info');
      refreshMainContentSilently();
    }

    // -------------------------------------------------------------
    // 4. COUPON EVENTS
    // -------------------------------------------------------------
    else if (event.entity_type === 'coupon') {
      if (ctx.type === 'cart') {
        showLiveToast(`Coupon "${details.code || 'Promo'}" updated by store manager.`, '🎟️', 'info');
        refreshMainContentSilently();
      }
    }
  }

  // -------------------------------------------------------------
  // Fast Heartbeat Poller (Sub-second / 1.5s responsive sync)
  // -------------------------------------------------------------
  async function checkLiveSyncUpdates() {
    try {
      const res = await fetch('/api/live-sync/version/', { cache: 'no-store' });
      if (!res.ok) return;
      const data = await res.json();
      const serverVersion = data.version;

      if (!isInitialized) {
        currentVersion = serverVersion;
        isInitialized = true;
        return;
      }

      if (serverVersion > currentVersion) {
        // Fetch all events that occurred between currentVersion and serverVersion
        const eventsRes = await fetch(`/api/live-sync/events/?since=${currentVersion}`, { cache: 'no-store' });
        currentVersion = serverVersion;
        if (eventsRes.ok) {
          const eventsData = await eventsRes.json();
          (eventsData.events || []).forEach(ev => dispatchLiveEvent(ev));
        }
      }
    } catch (err) {
      // Gracefully ignore network hiccups
    }
  }

  // -------------------------------------------------------------
  // Initialization
  // -------------------------------------------------------------
  function initLiveSync() {
    renderLiveStatusBadge();
    checkLiveSyncUpdates();
    // Run heartbeat every 1500ms for instant real-time live synchronization
    pollInterval = setInterval(checkLiveSyncUpdates, 1500);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initLiveSync);
  } else {
    initLiveSync();
  }
})();
