/**
 * TELEGRAM INIT DATA FETCH WRAPPER
 * 
 * Automatically adds Telegram WebApp initData header to all API requests.
 * 
 * Usage:
 * const user = await telegramFetch('/api/v1/me');
 * const data = await telegramFetch('/api/v1/nft/list', { method: 'POST', body: {...} });
 */

/**
 * Get Telegram WebApp initData from window.Telegram.WebApp
 * @returns {string} initData or empty string if not in Telegram
 */
function getTelegramInitData() {
  try {
    if (typeof window !== 'undefined' && window.Telegram?.WebApp?.initData) {
      return window.Telegram.WebApp.initData;
    }
  } catch (e) {
    console.warn('[Telegram] Failed to get initData:', e.message);
  }
  return '';
}

/**
 * Fetch wrapper that automatically includes Telegram initData header
 * 
 * @param {string} url - API endpoint
 * @param {Object} options - Fetch options (method, body, headers, etc.)
 * @returns {Promise} Fetch response
 * 
 * @example
 * // GET request
 * const user = await telegramFetch('/api/v1/me');
 * 
 * // POST request
 * const result = await telegramFetch('/api/v1/nft/mint', {
 *   method: 'POST',
 *   body: JSON.stringify({ name: 'My NFT' })
 * });
 */
async function telegramFetch(url, options = {}) {
  // Get Telegram initData
  const initData = getTelegramInitData();
  
  if (!initData) {
    console.warn('[TG Fetch] No Telegram initData available - will likely get 401');
  }
  
  // Prepare headers
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  
  // Add Telegram authentication header
  if (initData) {
    headers['X-Telegram-Init-Data'] = initData;
  }
  
  // Make request
  const fullUrl = url.startsWith('http') ? url : `${window.location.origin}${url}`;
  
  try {
    console.debug(`[TG Fetch] ${options.method || 'GET'} ${url}`);
    
    // Delegate to central apiFetch when available to ensure initData is attached
    try {
      const mod = await import('./core/api.js');
      if (mod && mod.apiFetch) {
        // apiFetch returns the fetch Response object
        const response = await mod.apiFetch(fullUrl, { ...options, headers });

        // If apiFetch returned a Response-like object, continue below
        // Note: older callers expect JSON or null on 401
        if (!response) return null;

        // Reuse response handling below by assigning to local variable
        var _response = response;
        // Move on to generic handling with `_response`
      } else {
        const response = await fetch(fullUrl, { ...options, headers });
        var _response = response;
      }
      const response = _response;

      // Log status
      if (!response.ok) {
        console.warn(`[TG Fetch] ${response.status} ${response.statusText} on ${url}`);
      }

      // Parse response
      const contentType = response.headers.get('content-type');
      if (contentType?.includes('application/json')) {
        const data = await response.json();

        // Treat 401 as unauthenticated but not an exception to allow seamless navigation
        if (response.status === 401) {
          console.info('[TG Fetch] 401 Unauthorized — returning null to indicate guest user');
          return null;
        }

        if (!response.ok) {
          throw {
            status: response.status,
            statusText: response.statusText,
            ...data
          };
        }

        return data;
      }

      if (!response.ok) {
        // Non-JSON 401 -> return null, other errors still throw
        if (response.status === 401) {
          console.info('[TG Fetch] 401 Unauthorized (non-JSON) — returning null');
          return null;
        }
        throw new Error(`${response.status} ${response.statusText}`);
      }

      return response;
  } catch (error) {
    console.error('[TG Fetch] Error:', error.message || error);
    throw error;
  }
}

/**
 * Global API namespace using telegramFetch
 */
const telegramApi = {
  // Identity
  me: () => telegramFetch('/api/v1/me'),
  refresh: () => telegramFetch('/api/v1/me/refresh'),
  logout: () => telegramFetch('/api/v1/me/logout'),
  
  // NFTs
  mintNFT: (data) => telegramFetch('/api/v1/nft/mint', { method: 'POST', body: JSON.stringify(data) }),
  listNFTs: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return telegramFetch(`/api/v1/nft/list?${qs}`);
  },
  getNFT: (id) => telegramFetch(`/api/v1/nft/${id}`),
  
  // Wallets
  listWallets: () => telegramFetch('/api/v1/wallets'),
  getWallet: (id) => telegramFetch(`/api/v1/wallets/${id}`),
  
  // Marketplace
  listMarketplace: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return telegramFetch(`/api/v1/marketplace?${qs}`);
  },
  buyNFT: (nftId, data) => telegramFetch(`/api/v1/marketplace/buy/${nftId}`, { method: 'POST', body: JSON.stringify(data) }),
  
  // Generic GET/POST wrapper
  get: (endpoint, params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return telegramFetch(`${endpoint}?${qs}`);
  },
  post: (endpoint, data) => telegramFetch(endpoint, { method: 'POST', body: JSON.stringify(data) }),
  put: (endpoint, data) => telegramFetch(endpoint, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (endpoint) => telegramFetch(endpoint, { method: 'DELETE' }),
};

// Export for use in other scripts
// Export for CommonJS
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { telegramFetch, telegramApi };
}

// Export for ES6 modules
export { telegramFetch, telegramApi };
