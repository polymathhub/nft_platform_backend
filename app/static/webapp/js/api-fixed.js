/**
 * FIXED API CLIENT - Calls correct backend endpoints
 * ❌ REMOVED: /api/auth/profile, /api/auth/refresh
 * ✅ ADDED: /api/user/me (simple profile endpoint)
 * 
 * All requests automatically include Authorization header with token
 */

class APIClientFixed {
  constructor(baseURL = '') {
    this.baseURL = baseURL || window.location.origin;
    this.defaultTimeout = 30000;
  }

  /**
   * Get auth token from localStorage
   */
  getAuthToken() {
    return localStorage.getItem('auth_token');
  }

  /**
   * Make HTTP request
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

      // ✅ FIXED: Add Authorization header IF token exists
      const token = this.getAuthToken();
      if (token) {
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
        message = data.detail || data.message || data.error || message;
        code = data.code || code;
      }
    } catch (e) {
      message = response.statusText || message;
    }

    const error = new Error(message);
    error.code = code;
    error.status = response.status;
    
    // Handle 401 - token likely expired
    if (response.status === 401) {
      console.warn('[API] 401 Unauthorized - token may have expired');
      localStorage.removeItem('auth_token');
      window.dispatchEvent(new CustomEvent('auth:expired'));
    }
    
    return error;
  }

  // HTTP methods
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
}

// Global API instance
export const api = new APIClientFixed();

/**
 * ✅ FIXED API ENDPOINTS
 * Routes that actually exist on the backend
 */
export const endpoints = {
  // ✅ User Profile - FIXED endpoint
  user: {
    me: '/api/user/me',           // GET - requires Authorization header
    logout: '/api/user/logout',   // POST
  },

  // ✅ Telegram Auth - works with backend
  auth: {
    telegramLogin: '/api/v1/auth/telegram/login',  // POST
    tonLogin: '/api/v1/auth/ton/login',             // POST
  },

  // Example: Wallets (if implemented)
  wallets: {
    list: '/api/v1/wallets',
    get: (id) => `/api/v1/wallets/${id}`,
    create: '/api/v1/wallets/create',
  },

  // Example: NFTs (if implemented)
  nft: {
    mint: '/api/v1/nfts/mint',
    list: '/api/v1/nfts',
    get: (id) => `/api/v1/nfts/${id}`,
  },

  // Example: Marketplace (if implemented)
  marketplace: {
    listings: '/api/v1/marketplace/listings',
    listingsActive: '/api/v1/marketplace/listings',
  },

  // Example: Dashboard (if implemented)
  dashboard: {
    stats: '/api/v1/dashboard/stats',
    walletBalance: '/api/v1/dashboard/wallet/balance',
    nfts: '/api/v1/dashboard/nfts',
    recentTransactions: '/api/v1/dashboard/transactions/recent',
  },
};

export default api;
