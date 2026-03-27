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
  // V1 API endpoints (Telegram-authenticated)
  me: '/api/v1/me',
  user: {
    me: '/api/v1/me',
    profile: '/api/v1/user/profile',
    update: '/api/v1/user/update',
  },
  
  // NFT Management
  nft: {
    list: '/api/v1/nfts',
    collection: '/api/v1/nfts/user/collection',
    create: '/api/v1/nfts/mint',
    mint: '/api/v1/nfts/mint',
    get: (id) => `/api/v1/nfts/${id}`,
    details: (id) => `/api/v1/nfts/${id}`,
    update: (id) => `/api/v1/nfts/${id}`,
    delete: (id) => `/api/v1/nfts/${id}`,
    transfer: (id) => `/api/v1/nfts/${id}/transfer`,
    burn: (id) => `/api/v1/nfts/${id}/burn`,
    lock: (id) => `/api/v1/nfts/${id}/lock`,
    unlock: (id) => `/api/v1/nfts/${id}/unlock`,
  },
  
  // Marketplace
  marketplace: {
    list: '/api/v1/marketplace/listings',
    listings: '/api/v1/marketplace/listings',
    active: '/api/v1/marketplace/listings',
    userListings: '/api/v1/marketplace/listings/user',
    create: '/api/v1/marketplace/listings',
    cancel: (listingId) => `/api/v1/marketplace/listings/${listingId}/cancel`,
    buy: (listingId) => `/api/v1/marketplace/listings/${listingId}/buy`,
    buyNow: (listingId) => `/api/v1/marketplace/listings/${listingId}/buy`,
    offer: '/api/v1/marketplace/offers',
    makeOffer: (listingId) => `/api/v1/marketplace/listings/${listingId}/offer`,
    acceptOffer: (offerId) => `/api/v1/marketplace/offers/${offerId}/accept`,
    rejectOffer: (offerId) => `/api/v1/marketplace/offers/${offerId}/reject`,
    offers: (listingId) => `/api/v1/marketplace/listings/${listingId}/offers`,
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
    balance: '/api/v1/payments/balance',
    history: '/api/v1/payments/history',
    create: '/api/v1/payments/deposit',
    initiate: '/api/v1/payments/initiate-deposit',
    confirm: '/api/v1/payments/deposit-confirm',
    verify: '/api/v1/payments/verify',
    status: (id) => `/api/v1/payments/${id}/status`,
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

  /**
   * Upload file with Telegram authentication
   * @param {string} endpoint - API endpoint path
   * @param {FormData} formData - Form data containing file(s)
   * @param {Object} options - Additional fetch options
   * @returns {Promise} Response data
   */
  upload: async (endpoint, formData, options = {}) => {
    try {
      if (!(formData instanceof FormData)) {
        throw new Error('formData must be a FormData instance');
      }
      
      // Build headers - NEVER include Content-Type for FormData
      // The browser MUST set it with the multipart boundary
      const headers = { ...options.headers };
      delete headers['Content-Type']; // Ensure no Content-Type override
      
      return await telegramFetch(endpoint, {
        method: 'POST',
        body: formData,
        headers, // Browser will add: Content-Type: multipart/form-data; boundary=...
        ...options,
      });
    } catch (error) {
      console.error(`[API] UPLOAD ${endpoint} failed:`, error);
      throw error;
    }
  },
};

// Export both api and endpoints for use in other modules
export { api, endpoints, telegramFetch, telegramApi };
