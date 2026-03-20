/**
 * Service Worker for GiftedForge NFT Platform
 * Optimized for Telegram Mini App stability
 * 
 * Strategy:
 * - Cache only static assets (CSS, fonts, images)
 * - Network-first strategy for JS and HTML, especially auth/dashboard pages
 * - Remove / or dashboard pages from STATIC_ASSETS pre-cache.
 * - Gracefully handle fetch errors without forcing app reload.
 */

const CACHE_VERSION = 'v2.0.0';
const CACHE_NAME = `gifted-forge-${CACHE_VERSION}`;
const RUNTIME_CACHE = `gifted-forge-runtime-${CACHE_VERSION}`;
const IMAGE_CACHE = `gifted-forge-images-${CACHE_VERSION}`;
const FONT_CACHE = `gifted-forge-fonts-${CACHE_VERSION}`;

// Only cache truly static assets that NEVER change
const STATIC_ASSETS = [
  '/webapp/css/variables.css',
  '/webapp/css/base.css',
  '/webapp/css/layout.css',
  '/webapp/css/components.css',
  '/webapp/css/navbar.css',
];

// Install: Cache only immutable static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    Promise.all([
      // Cache immutable static assets
      caches.open(CACHE_NAME)
        .then((cache) => {
          console.log('[SW] Caching static assets...');
          return cache.addAll(STATIC_ASSETS)
            .catch(err => {
              console.warn('[SW] Some static assets failed to cache:', err);
              // Continue even if some fail
            });
        }),
      // DO NOT pre-cache HTML pages - they must always be fresh
      // DO NOT pre-cache JS files - they change and cause reload loops
    ])
  );
  
  // Skip waiting to allow quick updates (but user must close/reopen app)
  self.skipWaiting?.();
});

// Activate: Clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME && 
              cacheName !== RUNTIME_CACHE && 
              cacheName !== IMAGE_CACHE &&
              cacheName !== FONT_CACHE) {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  
  self.clients.claim?.();
});

// Fetch: Intelligent caching strategy for Telegram Mini App stability
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Only handle GET requests
  if (request.method !== 'GET') {
    return;
  }

  // 1. API requests - Network first with cache fallback
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Cache successful responses
          if (response.ok && response.status === 200) {
            caches.open(RUNTIME_CACHE).then((cache) => {
              cache.put(request, response.clone());
            });
          }
          return response;
        })
        .catch((fetchError) => {
          // Network failed, try cache
          return caches.match(request)
            .then((cached) => {
              if (cached) {
                console.log('[SW] API offline, using cached response:', url.pathname);
                return cached;
              }
              // No cache available, return offline response
              return createOfflineResponse();
            });
        })
    );
    return;
  }

  // 2. Images - Cache first (images rarely change)
  if (request.destination === 'image' || url.pathname.match(/\.(jpg|jpeg|png|gif|webp|svg)$/i)) {
    event.respondWith(
      caches.open(IMAGE_CACHE)
        .then((cache) => {
          return cache.match(request)
            .then((cached) => {
              // Return cached image immediately, update in background
              return cached || fetch(request)
                .then((response) => {
                  if (response.ok) {
                    cache.put(request, response.clone());
                  }
                  return response;
                })
                .catch(() => {
                  // Return a blank image or cached version on error
                  return caches.match('/webapp/img/placeholder.png')
                    .then(placeholder => placeholder || new Response('', { status: 404 }));
                });
            });
        })
    );
    return;
  }

  // 3. Fonts - Cache first (fonts never change)
  if (url.pathname.match(/\.(woff|woff2|ttf|eot)$/i)) {
    event.respondWith(
      caches.open(FONT_CACHE)
        .then((cache) => {
          return cache.match(request)
            .then((cached) => {
              if (cached) return cached;
              
              return fetch(request)
                .then((response) => {
                  if (response.ok) {
                    cache.put(request, response.clone());
                  }
                  return response;
                })
                .catch(() => new Response('', { status: 404 }));
            });
        })
    );
    return;
  }

  // 4. CSS - Cache first (CSS rarely changes within a version)
  if (request.destination === 'style' || url.pathname.endsWith('.css')) {
    event.respondWith(
      caches.open(CACHE_NAME)
        .then((cache) => {
          return cache.match(request)
            .then((cached) => {
              if (cached) return cached;
              
              return fetch(request)
                .then((response) => {
                  if (response.ok) {
                    cache.put(request, response.clone());
                  }
                  return response;
                })
                .catch(() => {
                  console.warn('[SW] CSS fetch failed, no cache available:', url.pathname);
                  return new Response('', { status: 404 });
                });
            });
        })
    );
    return;
  }

  // 5. JavaScript - ALWAYS network first (prevents version mismatches)
  // If SW gives old JS, it may conflict with old HTML and cause refresh loops
  if (request.destination === 'script' || url.pathname.endsWith('.js')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response.ok) {
            // Cache successful responses for offline fallback ONLY
            caches.open(RUNTIME_CACHE).then((cache) => {
              cache.put(request, response.clone());
            });
          }
          return response;
        })
        .catch((fetchError) => {
          // Network failed - only use cache as last resort
          return caches.match(request)
            .then((cached) => {
              if (cached) {
                console.log('[SW] JS offline, using cached version:', url.pathname);
                return cached;
              }
              // No cache, return error (browser will handle gracefully)
              console.error('[SW] JS fetch failed and no cache available:', url.pathname);
              return new Response(
                `console.error('Failed to load ${url.pathname}');`,
                { 
                  status: 503,
                  headers: { 'Content-Type': 'application/javascript' } 
                }
              );
            });
        })
    );
    return;
  }

  // 6. HTML pages - ALWAYS network first (crucial for Telegram Mini App)
  // Fresh HTML ensures auth state matches auth tokens
  if (request.destination === 'document' || url.pathname.endsWith('.html') || 
      url.pathname === '/' || url.pathname === '/webapp/') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response.ok) {
            // Cache HTML for offline fallback ONLY
            caches.open(RUNTIME_CACHE).then((cache) => {
              cache.put(request, response.clone());
            });
          }
          return response;
        })
        .catch((fetchError) => {
          // Network failed, try cache
          return caches.match(request)
            .then((cached) => {
              if (cached) {
                console.log('[SW] HTML offline, using cached version:', url.pathname);
                return cached;
              }
              // No cache, return offline page
              return createOfflineResponse();
            });
        })
    );
    return;
  }

  // 7. Default - Network first, cache fallback
  event.respondWith(
    fetch(request)
      .then((response) => {
        if (response.ok) {
          caches.open(RUNTIME_CACHE).then((cache) => {
            cache.put(request, response.clone());
          });
        }
        return response;
      })
      .catch((fetchError) => {
        // Try cache
        return caches.match(request)
          .catch(() => createOfflineResponse());
      })
  );
});

/**
 * Create offline response
 * Used when network is unavailable and no cache exists
 */
function createOfflineResponse() {
  return new Response(
    JSON.stringify({
      status: 'offline',
      message: 'You are offline. Please check your internet connection.',
    }),
    {
      status: 503,
      statusText: 'Service Unavailable',
      headers: { 
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache'
      },
    }
  );
}

/**
 * Handle messages from clients
 * Currently only handles skip-waiting notifications
 */
self.addEventListener('message', (event) => {
  if (event.data?.type === 'SKIP_WAITING') {
    console.log('[SW] Update available - will activate on next load');
    self.skipWaiting?.();
  }
});
