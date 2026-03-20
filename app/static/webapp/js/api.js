class APIClient {
  constructor(baseURL = '') {
    this.baseURL = baseURL || window.location.origin;
    this.defaultTimeout = 30000;
  }

  async request(endpoint, options = {}) {
    const {
      method = 'GET',
      headers = {},
      body = null,
      timeout = this.defaultTimeout,
      skipAuth = false,
    } = options;

    const url = new URL(endpoint, this.baseURL);
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const requestHeaders = {
        'Content-Type': 'application/json',
        ...headers,
      };

      // Add Authorization header if token exists
      const token = localStorage.getItem('token');
      if (token && !skipAuth) {
        requestHeaders['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(url, {
        method,
        headers: requestHeaders,
        body: body ? JSON.stringify(body) : null,
        signal: controller.signal,
        credentials: 'include',
      });

      clearTimeout(timeoutId);

      // Handle 401 (unauthorized) - attempt token refresh
      if (response.status === 401 && !skipAuth) {
        const refreshed = await this.refreshToken();
        if (refreshed) {
          return this.request(endpoint, { ...options, skipAuth: true });
        }
        window.dispatchEvent(new CustomEvent('auth:logout'));
        throw new Error('Authentication failed');
      }

      if (!response.ok) {
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

  async refreshToken() {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      
      // If no refresh token is available, can't refresh
      // For Telegram auth, we don't use refresh tokens - just re-authenticate
      if (!refreshToken) {
        console.warn('No refresh token available - Telegram auth will re-authenticate');
        return false;
      }

      // Note: Production endpoint /api/v1/auth/refresh may not exist yet
      // Fallback: Trigger re-authentication event instead
      console.warn('[API] Token refresh requested but endpoint not implemented');
      console.warn('[API] For Telegram Mini App, restart authentication via Telegram');
      
      window.dispatchEvent(new CustomEvent('auth:refresh-needed'));
      return false;
    } catch (error) {
      console.error('Token refresh failed:', error);
      return false;
    }
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
      const headers = {};
      
      // Add Authorization header if token exists
      const token = localStorage.getItem('token');
      if (token && !options.skipAuth) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(url, {
        method: 'POST',
        headers: headers,
        body: formData,
        signal: controller.signal,
        credentials: 'include',
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

// Namespace for API 
export const endpoints = {
  // Auth - Standard endpoints
  auth: {
    login: '/api/v1/auth/login',
    register: '/api/v1/auth/register',
    logout: '/api/user/logout',  // FIXED: Use correct logout endpoint
    refresh: null,  // NOTE: Not implemented - Telegram auth re-authenticates instead
    profile: '/api/user/me',  // FIXED: Use /api/user/me which actually exists
    oauthGoogle: '/api/v1/auth/oauth/google',
    oauthTwitter: '/api/v1/auth/oauth/twitter',
  },

  // Unified Auth - Telegram & TON Wallet
  unifiedAuth: {
    telegramLogin: '/api/v1/auth/telegram/login',
    tonLogin: '/api/v1/auth/ton/login',
    linkWallet: '/api/v1/auth/link-wallet',
    profile: '/api/user/me',  // FIXED: Use /api/user/me endpoint that exists
    logout: '/api/user/logout',  // FIXED: Use correct logout endpoint
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
