/**
 * Service Worker for GiftedForge NFT Platform
 * MINIMAL IMPLEMENTATION - No auto-updates, no page reloads
 * 
 * Purpose: Simple offline support and caching only
 * Strategy: Cache static assets, network-first for everything else
 */

const CACHE_VERSION = 'v1';
const CACHE_NAME = `gifted-forge-${CACHE_VERSION}`;

// Install: Minimal setup, no pre-caching
self.addEventListener('install', (event) => {
  // Just skip waiting, don't pre-cache anything
  self.skipWaiting?.();
});

// Activate: Clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim?.();
});

// Fetch: Network-first, cache as fallback
self.addEventListener('fetch', (event) => {
  const { request } = event;
  
  // Only handle GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Always try network first
  event.respondWith(
    fetch(request)
      .then((response) => {
        // Cache successful responses
        if (response.ok && response.status === 200) {
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, response.clone());
          }).catch(() => {
            // Cache operation failed, but don't break the response
          });
        }
        return response;
      })
      .catch(() => {
        // Network failed, try cache
        return caches.match(request)
          .then((cached) => {
            if (cached) {
              return cached;
            }
            // No cache available, return offline page or error
            return new Response('Offline - No cached response available', {
              status: 503,
              statusText: 'Service Unavailable'
            });
          });
      })
  );
});
