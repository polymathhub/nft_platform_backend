/**
 * API Wrapper for Telegram WebApp Authentication
 * Re-exports telegramFetch and provides endpoints configuration
 * 
 * Purpose: Maintain compatibility with existing code that expects api.js
 * while using Telegram-based authentication from telegram-fetch.js
 */

import { telegramFetch, telegramApi } from './telegram-fetch.js';

/**
 * API endpoints configuration
 * Used by marketplace, wallet, profile, and mint pages
 */
const endpoints = {
  // User endpoints
  auth: {
    profile: '/api/auth/profile',
    check: '/api/auth/check',
    logout: '/api/auth/logout',
  },
  
  // V1 API endpoints (Telegram-authenticated)
  me: '/api/v1/me',
  user: {
    me: '/api/v1/me',
    profile: '/api/v1/user/profile',
    update: '/api/v1/user/update',
  },
  
  // NFT Management
  nft: {
    list: '/api/v1/nft/list',
    create: '/api/v1/nft/mint',
    get: (id) => `/api/v1/nft/${id}`,
    update: (id) => `/api/v1/nft/${id}`,
    delete: (id) => `/api/v1/nft/${id}`,
    transfer: (id) => `/api/v1/nft/${id}/transfer`,
    burn: (id) => `/api/v1/nft/${id}/burn`,
  },
  
  // Marketplace
  marketplace: {
    list: '/api/v1/marketplace',
    listings: '/api/v1/marketplace/listings',
    buy: (listingId) => `/api/v1/marketplace/listings/${listingId}/buy-now`,
    offer: (listingId) => `/api/v1/marketplace/listings/${listingId}/offer`,
    create: '/api/v1/marketplace/listings',
  },
  
  // Wallet Management
  wallet: {
    list: '/api/v1/wallets',
    get: (id) => `/api/v1/wallets/${id}`,
    create: '/api/v1/wallets',
    update: (id) => `/api/v1/wallets/${id}`,
  },
  
  // Collections
  collection: {
    list: '/api/v1/collections',
    get: (id) => `/api/v1/collections/${id}`,
  },
  
  // Notifications
  notification: {
    list: '/api/v1/notifications',
    get: (id) => `/api/v1/notifications/${id}`,
    markAsRead: (id) => `/api/v1/notifications/${id}/read`,
    markAllAsRead: '/api/v1/notifications/read-all',
  },
  
  // Testimonials/Reviews
  testimonial: {
    list: '/api/v1/testimonials',
    create: '/api/v1/testimonials',
  },
  
  // Payments
  payment: {
    create: '/api/payment/create',
    verify: '/api/payment/verify',
    status: (id) => `/api/payment/${id}/status`,
  },
};

/**
 * API client that wraps telegramFetch and adds Telegram authentication headers
 * Provides a familiar interface: api.get(), api.post(), api.put(), api.delete()
 */
const api = {
  /**
   * Perform GET request with Telegram authentication
   * @param {string} endpoint - API endpoint path
   * @param {Object} params - Query parameters
   * @returns {Promise} Response data
   */
  get: async (endpoint, params = {}) => {
    try {
      const url = new URL(endpoint, window.location.origin);
      Object.entries(params).forEach(([key, value]) => {
        if (value !== null && value !== undefined) {
          url.searchParams.append(key, value);
        }
      });
      return await telegramFetch(url.pathname + url.search);
    } catch (error) {
      console.error(`[API] GET ${endpoint} failed:`, error);
      throw error;
    }
  },

  /**
   * Perform POST request with Telegram authentication
   * @param {string} endpoint - API endpoint path
   * @param {Object} body - Request body
   * @param {Object} options - Additional fetch options
   * @returns {Promise} Response data
   */
  post: async (endpoint, body = {}, options = {}) => {
    try {
      return await telegramFetch(endpoint, {
        method: 'POST',
        body: JSON.stringify(body),
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });
    } catch (error) {
      console.error(`[API] POST ${endpoint} failed:`, error);
      throw error;
    }
  },

  /**
   * Perform PUT request with Telegram authentication
   * @param {string} endpoint - API endpoint path
   * @param {Object} body - Request body
   * @param {Object} options - Additional fetch options
   * @returns {Promise} Response data
   */
  put: async (endpoint, body = {}, options = {}) => {
    try {
      return await telegramFetch(endpoint, {
        method: 'PUT',
        body: JSON.stringify(body),
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });
    } catch (error) {
      console.error(`[API] PUT ${endpoint} failed:`, error);
      throw error;
    }
  },

  /**
   * Perform DELETE request with Telegram authentication
   * @param {string} endpoint - API endpoint path
   * @param {Object} options - Additional fetch options
   * @returns {Promise} Response data
   */
  delete: async (endpoint, options = {}) => {
    try {
      return await telegramFetch(endpoint, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });
    } catch (error) {
      console.error(`[API] DELETE ${endpoint} failed:`, error);
      throw error;
    }
  },

  /**
   * Perform PATCH request with Telegram authentication
   * @param {string} endpoint - API endpoint path
   * @param {Object} body - Request body
   * @param {Object} options - Additional fetch options
   * @returns {Promise} Response data
   */
  patch: async (endpoint, body = {}, options = {}) => {
    try {
      return await telegramFetch(endpoint, {
        method: 'PATCH',
        body: JSON.stringify(body),
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });
    } catch (error) {
      console.error(`[API] PATCH ${endpoint} failed:`, error);
      throw error;
    }
  },

  /**
   * Generic request method for advanced use cases
   * @param {string} endpoint - API endpoint path
   * @param {Object} options - Full fetch options
   * @returns {Promise} Response data
   */
  request: async (endpoint, options = {}) => {
    try {
      return await telegramFetch(endpoint, options);
    } catch (error) {
      console.error(`[API] ${options.method || 'GET'} ${endpoint} failed:`, error);
      throw error;
    }
  },
};

// Export both api and endpoints for use in other modules
export { api, endpoints, telegramFetch, telegramApi };
