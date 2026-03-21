class APIClient {
  constructor(baseURL = '') {
    this.baseURL = baseURL || window.location.origin;
    this.defaultTimeout = 30000;
  }

  /**
   * Make a request with credentials (session cookie included automatically)
   * 
   * AUTHENTICATION NOTE:
   * - No Bearer tokens (old system removed)
   * - Uses httpOnly session cookies set by server on /api/auth/telegram
   * - credentials: 'include' automatically sends cookies
   * - If 401 received, session expired - user must re-authenticate via Telegram
   */
  async request(endpoint, options = {}) {
    const {
      method = 'GET',
      headers = {},
      body = null,
      timeout = this.defaultTimeout,
    } = options;

    const url = new URL(endpoint, this.baseURL);
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const requestHeaders = {
        'Content-Type': 'application/json',
        ...headers,
      };

      // NOTE: No Bearer token injection here
      // Session cookie is sent automatically via credentials: 'include'

      const response = await fetch(url, {
        method,
        headers: requestHeaders,
        body: body ? JSON.stringify(body) : null,
        signal: controller.signal,
        credentials: 'include', // IMPORTANT: Send session cookie
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        // 401 means session expired - requires re-authentication
        if (response.status === 401) {
          console.warn('[API] Session expired (401) - user must re-authenticate');
          window.dispatchEvent(
            new CustomEvent('auth:expired', {
              detail: { endpoint, method },
            })
          );
        }

        const error = await this.handleErrorResponse(response);
        throw error;
      }

      const contentType = response.headers.get('content-type');
      if (contentType?.includes('application/json')) {
        return await response.json();
      }

      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      if (error.name === 'AbortError') {
        throw new Error(`Request timeout after ${timeout}ms`);
      }
      throw error;
    }
  }

  async handleErrorResponse(response) {
    let message = `HTTP ${response.status}`;
    let code = response.status;
    const contentType = response.headers.get('content-type');

    try {
      if (contentType?.includes('application/json')) {
        const data = await response.json();
        message = data.message || data.error || message;
        code = data.code || code;
      }
    } catch (e) {
      message = response.statusText || message;
    }

    const error = new Error(message);
    error.code = code;
    error.status = response.status;
    return error;
  }

  async get(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'GET' });
  }

  async post(endpoint, body, options = {}) {
    return this.request(endpoint, { ...options, method: 'POST', body });
  }

  async put(endpoint, body, options = {}) {
    return this.request(endpoint, { ...options, method: 'PUT', body });
  }

  async patch(endpoint, body, options = {}) {
    return this.request(endpoint, { ...options, method: 'PATCH', body });
  }

  async delete(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'DELETE' });
  }

  async upload(endpoint, formData, options = {}) {
    const url = new URL(endpoint, this.baseURL);
    const controller = new AbortController();
    const timeout = options.timeout || this.defaultTimeout;
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      // NOTE: No Authorization header for uploads - session cookie handles auth
      
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
        signal: controller.signal,
        credentials: 'include', // IMPORTANT: Send session cookie
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw await this.handleErrorResponse(response);
      }

      return await response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      if (error.name === 'AbortError') {
        throw new Error(`Request timeout after ${timeout}ms`);
      }
      throw error;
    }
  }
}

// Global API instance
export const api = new APIClient();

/**
 * API Endpoint Reference
 * 
 * AUTHENTICATION (NEW SYSTEM):
 * - POST /api/auth/telegram - Authenticate using Telegram initData
 * - GET /api/auth/profile - Get current user profile (requires session)
 * - GET /api/auth/me - Get current user (alternative endpoint)
 * - POST /api/auth/logout - Logout and clear session
 * 
 * Session is managed via httpOnly cookie set by server.
 * No Bearer tokens. No refresh tokens.
 */
export const endpoints = {
  // Auth - Telegram WebApp Only (NEW SYSTEM)
  auth: {
    telegram: '/api/auth/telegram',  // POST: Authenticate with Telegram initData
    profile: '/api/auth/profile',     // GET: Get current user profile
    me: '/api/auth/me',               // GET: Alternative profile endpoint
    logout: '/api/auth/logout',       // POST: Logout and clear session
    check: '/api/auth/check',         // GET: Check if auth is available
  },

  // Legacy auth endpoints (deprecated - kept for backward compatibility only)
  // NOTE: These no longer work. Use /api/auth/* endpoints instead.
  authLegacy: {
    login: '/api/v1/auth/login',                 // DEPRECATED
    register: '/api/v1/auth/register',           // DEPRECATED
    refresh: null,                               // REMOVED: Not needed with Telegram auth
    oauthGoogle: '/api/v1/auth/oauth/google',   // DEPRECATED
    oauthTwitter: '/api/v1/auth/oauth/twitter', // DEPRECATED
  },

  // Users
  users: {
    get: (id) => `/api/users/${id}`,
    update: (id) => `/api/users/${id}`,
    list: '/api/users',
  },

  // Wallets - v1 API
  wallets: {
    list: '/api/v1/wallets',
    get: (id) => `/api/v1/wallets/${id}`,
    create: '/api/v1/wallets/create',
    import: '/api/v1/wallets/import',
    generate: '/api/v1/wallets/generate',
    setPrimary: '/api/v1/wallets/set-primary',
    balance: (userId) => `/api/v1/wallets/user/${userId}/balance`,
    connect: '/api/v1/wallets/connect',
    disconnect: (id) => `/api/v1/wallets/${id}/disconnect`,
  },

  // NFTs - v1 API
  nft: {
    mint: '/api/v1/nfts/mint',
    list: '/api/v1/nfts',
    get: (id) => `/api/v1/nfts/${id}`,
    details: (id) => `/api/v1/nfts/${id}`,
    userCollection: '/api/v1/nfts/user/collection',
    create: '/api/v1/nfts/mint',
    update: (id) => `/api/v1/nfts/${id}`,
    delete: (id) => `/api/v1/nfts/${id}`,
    metadata: (id) => `/api/v1/nfts/${id}/metadata`,
    transfer: (id) => `/api/v1/nfts/${id}/transfer`,
    burn: (id) => `/api/v1/nfts/${id}/burn`,
  },

  // Images/Media Upload - v1 API
  images: {
    upload: '/api/v1/images/upload',
    get: (id) => `/api/v1/images/${id}`,
    proxy: '/api/v1/images/proxy',
  },
  marketplace: {
    listingsActive: '/api/v1/marketplace/listings',
    listingsUser: '/api/v1/marketplace/listings/user',
    listings: '/api/v1/marketplace/listings',
    getOrder: (orderId) => `/api/v1/marketplace/orders/${orderId}`,
    userOrders: '/api/v1/marketplace/orders',
    collectionStats: (collectionId) => `/api/v1/marketplace/collections/${collectionId}/stats`,
    listingOffers: (listingId) => `/api/v1/marketplace/listings/${listingId}/offers`,
    valuateNFT: (nftId) => `/api/v1/marketplace/nfts/${nftId}/valuation`,
    priceRange: '/api/v1/marketplace/listings/price-range',
    buy: (id) => `/api/v1/marketplace/listings/${id}/buy`,
    cancel: (id) => `/api/v1/marketplace/listings/${id}/cancel`,
  },

  // Collections
  collections: {
    list: '/api/collections',
    get: (id) => `/api/collections/${id}`,
    create: '/api/collections',
    update: (id) => `/api/collections/${id}`,
    nfts: (id) => `/api/collections/${id}/nfts`,
  },

  // Dashboard - v1 API
  dashboard: {
    stats: '/api/v1/dashboard/stats',
    walletBalance: '/api/v1/dashboard/wallet/balance',
    nfts: '/api/v1/dashboard/nfts',
    recentTransactions: '/api/v1/dashboard/transactions/recent',
  },

  // Activity
  activity: {
    list: '/api/activity',
    get: (id) => `/api/activity/${id}`,
    userActivity: (userId) => `/api/activity/user/${userId}`,
  },

  // Transactions
  transactions: {
    list: '/api/transactions',
    get: (id) => `/api/transactions/${id}`,
    pending: '/api/transactions/pending',
    status: (id) => `/api/transactions/${id}/status`,
  },

  // Referrals - v1 API
  referrals: {
    me: '/api/v1/referrals/me',
    network: '/api/v1/referrals/network',
    applyCode: '/api/v1/referrals/apply',
    earnings: '/api/v1/referrals/earnings',
  },

  // Admin
  admin: {
    users: '/api/admin/users',
    nfts: '/api/admin/nfts',
    marketplace: '/api/admin/marketplace',
    settings: '/api/admin/settings',
    analytics: '/api/admin/analytics',
  },
};

export default api;
