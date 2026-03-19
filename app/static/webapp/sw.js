/**
 * Service Worker for GiftedForge NFT Platform
 * Handles offline caching, asset versioning, and performance optimization
 */

const CACHE_VERSION = 'v1.0.0';
const CACHE_NAME = `gifted-forge-${CACHE_VERSION}`;
const RUNTIME_CACHE = `gifted-forge-runtime-${CACHE_VERSION}`;
const IMAGE_CACHE = `gifted-forge-images-${CACHE_VERSION}`;

// Assets to cache on install
const STATIC_ASSETS = [
  '/',
  '/webapp/',
  '/webapp/dashboard.html',
  '/webapp/marketplace.html',
  '/webapp/dashboard.html',
  '/webapp/profile.html',
  '/webapp/wallet.html',
  '/webapp/navbar.css',
  '/webapp/js/marketplace.js',
  '/webapp/js/tonconnect.js',
  '/webapp/js/auth.js',
  '/webapp/css/variables.css',
  '/webapp/css/base.css',
  '/webapp/css/layout.css',
  '/webapp/css/components.css',
  'https://telegram.org/js/telegram-web-app.js',
  'https://cdn.jsdelivr.net/gh/ton-connect/ui@latest/dist/tonconnect-ui.min.js',
  'https://cdn.jsdelivr.net/gh/ton-connect/ui@latest/dist/tonconnect-ui.min.css',
];

// Install: Cache critical assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[SW] Caching static assets...');
        return cache.addAll(STATIC_ASSETS)
          .catch(err => {
            console.warn('[SW] Some assets failed to cache:', err);
            // Continue even if some assets fail
            return STATIC_ASSETS
              .filter(url => !url.includes('://'))
              .reduce((promise, url) => {
                return promise.then(() =>
                  cache.add(url).catch(() => console.warn(`[SW] Failed to cache: ${url}`))
                );
              }, Promise.resolve());
          });
      })
      // REMOVED skipWaiting() - prevents aggressive takeover causing violent refreshes
  );
});

// Activate: Clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME && 
              cacheName !== RUNTIME_CACHE && 
              cacheName !== IMAGE_CACHE) {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
    // REMOVED clients.claim() - prevents forcing new SW on existing clients
  );
});

// Fetch: Intelligent caching strategy
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Strategy 1: API requests - Network first, cache fallback
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response.ok) {
            const cache = caches.open(RUNTIME_CACHE);
            cache.then((c) => c.put(request, response.clone()));
          }
          return response;
        })
        .catch(() => {
          return caches.match(request)
            .then((cached) => cached || createOfflineResponse());
        })
    );
    return;
  }

  // Strategy 2: Images - Cache first, network fallback
  if (request.destination === 'image' || url.pathname.includes('/img/') || url.pathname.includes('/images/')) {
    event.respondWith(
      caches.open(IMAGE_CACHE)
        .then((cache) => {
          return cache.match(request)
            .then((cached) => {
              const fetchPromise = fetch(request)
                .then((response) => {
                  if (response.ok) {
                    cache.put(request, response.clone());
                  }
                  return response;
                })
                .catch(() => cached);
              
              return cached || fetchPromise;
            });
        })
    );
    return;
  }

  // Strategy 3: Static assets - Cache first
  if (request.destination === 'style' || 
      request.destination === 'script' || 
      url.pathname.endsWith('.woff') ||
      url.pathname.endsWith('.woff2') ||
      url.pathname.endsWith('.ttf')) {
    event.respondWith(
      caches.match(request)
        .then((cached) => cached || fetch(request)
          .then((response) => {
            if (response.ok && request.method === 'GET') {
              caches.open(CACHE_NAME).then((c) => c.put(request, response.clone()));
            }
            return response;
          })
        )
    );
    return;
  }

  // Strategy 4: HTML pages - Cache first strategy
  // CHANGED from 'stale-while-revalidate' to 'cache-first'
  // This prevents background network requests that cause violent page refreshes
  if (request.destination === 'document' || url.pathname.endsWith('.html')) {
    event.respondWith(
      caches.match(request)
        .then((cached) => {
          // Return cached HTML immediately without background fetch
          if (cached) {
            return cached;
          }
          // Only fetch from network if not in cache
          return fetch(request)
            .then((response) => {
              if (response.ok && request.method === 'GET') {
                caches.open(CACHE_NAME).then((c) => c.put(request, response.clone()));
              }
              return response;
            })
            .catch(() => createOfflineResponse());
        })
    );
    return;
  }

  // Default: Network first, cache fallback
  event.respondWith(
    fetch(request)
      .then((response) => {
        if (response.ok && request.method === 'GET') {
          caches.open(RUNTIME_CACHE).then((c) => c.put(request, response.clone()));
        }
        return response;
      })
      .catch(() => caches.match(request))
  );
});

// Create offline response
function createOfflineResponse() {
  return new Response(
    JSON.stringify({
      status: 'offline',
      message: 'You are offline. Some features may not be available.',
    }),
    {
      status: 503,
      headers: { 'Content-Type': 'application/json' },
    }
  );
}

// Handle messages from clients
// DISABLED: Removed skipWaiting to prevent aggressive SW takeover
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    // Intentionally NOT calling skipWaiting()
    // New SW updates wait until user closes/reopens app
    console.log('[SW] Update available - will activate on next app visit');
  }
});
