/**
 * API Service Layer
 * Centralized production-grade API communication handler
 * All backend requests flow through this layer
 */

class APIService {
  constructor(baseURL = '') {
    this.baseURL = baseURL || this.detectBaseURL();
    this.apiPrefix = '/api/v1';
    this.accessToken = localStorage.getItem('accessToken') || null;
    this.refreshToken = localStorage.getItem('refreshToken') || null;
    this.currentUser = null;
    this.requestTimeout = 30000; // 30s timeout
  }

  detectBaseURL() {
    // Auto-detect base URL based on current location
    const { protocol, hostname, port } = window.location;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return `${protocol}//${hostname}:${port || 8000}`;
    }
    return `${protocol}//${hostname}${port ? ':' + port : ''}`;
  }

  /**
   * Core HTTP Request Handler
   * @param {string} method - HTTP method
   * @param {string} path - API path (without base URL or prefix)
   * @param {Object} options - Request options
   * @returns {Promise} Response data
   */
  async request(method, path, options = {}) {
    const url = `${this.baseURL}${this.apiPrefix}${path}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    // Add authorization header if token exists
    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    const config = {
      method,
      headers,
      ...options,
      body: options.body ? JSON.stringify(options.body) : undefined,
    };

    try {
      const response = await fetch(url, config);

      // Handle 401 - try to refresh token
      if (response.status === 401 && this.refreshToken) {
        const refreshed = await this.refreshAccessToken();
        if (refreshed) {
          // Retry original request with new token
          headers['Authorization'] = `Bearer ${this.accessToken}`;
          config.headers = headers;
          return fetch(url, config).then(res => this.handleResponse(res));
        }
      }

      return this.handleResponse(response);
    } catch (error) {
      console.error('API Request Error:', error);
      throw {
        message: 'Network error. Please check your connection.',
        error,
        status: 0,
      };
    }
  }

  async handleResponse(response) {
    const contentType = response.headers.get('content-type');
    let data;

    try {
      data = contentType?.includes('json') ? await response.json() : await response.text();
    } catch (e) {
      data = null;
    }

    if (!response.ok) {
      const error = {
        status: response.status,
        message: data?.detail || data?.message || `HTTP ${response.status}`,
        data,
      };
      throw error;
    }

    return data;
  }

  /**
   * Token Management
   */
  setTokens(accessToken, refreshToken) {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
    localStorage.setItem('accessToken', accessToken);
    if (refreshToken) localStorage.setItem('refreshToken', refreshToken);
  }

  clearTokens() {
    this.accessToken = null;
    this.refreshToken = null;
    this.currentUser = null;
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('currentUser');
  }

  async refreshAccessToken() {
    if (!this.refreshToken) return false;

    try {
      const response = await this.request('POST', '/auth/refresh', {
        body: { refresh_token: this.refreshToken },
      });
      this.setTokens(response.access_token, response.refresh_token);
      return true;
    } catch (error) {
      console.warn('Token refresh failed:', error);
      this.clearTokens();
      return false;
    }
  }

  /**
   * AUTH ENDPOINTS
   */

  async register(email, username, password, fullName = '') {
    const data = await this.request('POST', '/auth/register', {
      body: { email, username, password, full_name: fullName },
    });
    this.setTokens(data.tokens.access_token, data.tokens.refresh_token);
    this.currentUser = data.user;
    localStorage.setItem('currentUser', JSON.stringify(data.user));
    return data;
  }

  async login(email, password) {
    const data = await this.request('POST', '/auth/login', {
      body: { email, password },
    });
    this.setTokens(data.tokens.access_token, data.tokens.refresh_token);
    this.currentUser = data.user;
    localStorage.setItem('currentUser', JSON.stringify(data.user));
    return data;
  }

  async telegramLogin(telegramData) {
    const data = await this.request('POST', '/auth/telegram/login', {
      body: telegramData,
    });
    this.setTokens(data.tokens.access_token, data.tokens.refresh_token);
    this.currentUser = data.user;
    localStorage.setItem('currentUser', JSON.stringify(data.user));
    return data;
  }

  async getCurrentUser() {
    if (this.currentUser) return this.currentUser;
    
    try {
      const user = await this.request('GET', '/auth/me');
      this.currentUser = user;
      localStorage.setItem('currentUser', JSON.stringify(user));
      return user;
    } catch (error) {
      console.warn('Failed to fetch current user:', error);
      return null;
    }
  }

  async logout() {
    this.clearTokens();
  }

  /**
   * WALLET ENDPOINTS
   */

  async createWallet(blockchainType, walletType = 'SEED', isPrimary = false) {
    return this.request('POST', '/wallets/create', {
      body: {
        blockchain: blockchainType,
        wallet_type: walletType,
        is_primary: isPrimary,
      },
    });
  }

  async importWallet(blockchainType, walletAddress, isPrimary = false) {
    return this.request('POST', '/wallets/import', {
      body: {
        blockchain: blockchainType,
        address: walletAddress,
        is_primary: isPrimary,
      },
    });
  }

  async getUserWallets() {
    return this.request('GET', '/wallets');
  }

  async getWalletDetail(walletId) {
    return this.request('GET', `/wallets/${walletId}`);
  }

  async setWalletAsPrimary(walletId) {
    return this.request('PUT', `/wallets/${walletId}/primary`, {
      body: { is_primary: true },
    });
  }

  /**
   * NFT ENDPOINTS
   */

  async mintNFT(walletId, name, description, imageUrl, royaltyPercentage = 0, metadata = {}) {
    return this.request('POST', '/nfts/mint', {
      body: {
        wallet_id: walletId,
        name,
        description,
        image_url: imageUrl,
        royalty_percentage: royaltyPercentage,
        metadata,
      },
    });
  }

  async getUserNFTs(skip = 0, limit = 50) {
    return this.request('GET', `/nfts/user?skip=${skip}&limit=${limit}`);
  }

  async getNFTDetail(nftId) {
    return this.request('GET', `/nfts/${nftId}`);
  }

  async transferNFT(nftId, toAddress, transactionHash = '') {
    return this.request('POST', `/nfts/${nftId}/transfer`, {
      body: {
        to_address: toAddress,
        transaction_hash: transactionHash,
      },
    });
  }

  async burnNFT(nftId, transactionHash = '') {
    return this.request('POST', `/nfts/${nftId}/burn`, {
      body: { transaction_hash: transactionHash },
    });
  }

  /**
   * MARKETPLACE ENDPOINTS
   */

  async getActiveListings(skip = 0, limit = 50, blockchain = null) {
    let path = `/marketplace/listings?skip=${skip}&limit=${limit}`;
    if (blockchain) path += `&blockchain=${blockchain}`;
    return this.request('GET', path);
  }

  async createListing(nftId, price, currency = 'USD', expiresAt = null) {
    return this.request('POST', '/marketplace/listings', {
      body: {
        nft_id: nftId,
        price,
        currency,
        expires_at: expiresAt,
      },
    });
  }

  async cancelListing(listingId) {
    return this.request('POST', `/marketplace/listings/${listingId}/cancel`);
  }

  async buyNow(listingId) {
    return this.request('POST', `/marketplace/listings/${listingId}/buy`, {
      body: { listing_id: listingId },
    });
  }

  async getUserListings(skip = 0, limit = 50) {
    return this.request('GET', `/marketplace/user/listings?skip=${skip}&limit=${limit}`);
  }

  async getUserOrders(skip = 0, limit = 50) {
    return this.request('GET', `/marketplace/user/orders?skip=${skip}&limit=${limit}`);
  }

  /**
   * OFFER & ORDER ENDPOINTS
   */

  async makeOffer(listingId, nftId, buyerId, offerPrice, currency = 'STARS', expiresAt = null) {
    return this.request('POST', '/marketplace/offers', {
      body: {
        listing_id: listingId,
        nft_id: nftId,
        buyer_id: buyerId,
        offer_price: offerPrice,
        currency,
        expires_at: expiresAt,
      },
    });
  }

  async acceptOffer(offerId) {
    return this.request('POST', `/marketplace/offers/${offerId}/accept`);
  }

  async rejectOffer(offerId) {
    return this.request('POST', `/marketplace/offers/${offerId}/reject`);
  }

  async getListingOffers(listingId, skip = 0, limit = 50) {
    return this.request('GET', `/marketplace/listings/${listingId}/offers?skip=${skip}&limit=${limit}`);
  }

  /**
   * ESCROW ENDPOINTS
   */

  async getEscrowDetail(escrowId) {
    return this.request('GET', `/marketplace/escrows/${escrowId}`);
  }

  /**
   * COLLECTION ENDPOINTS
   */

  async createCollection(name, description = '', blockchain = 'ethereum', imageUrl = '', bannerUrl = '') {
    return this.request('POST', '/collections', {
      body: {
        name,
        description,
        blockchain,
        image_url: imageUrl,
        banner_url: bannerUrl,
      },
    });
  }

  async getMyCollections(skip = 0, limit = 50) {
    return this.request('GET', `/collections/me?skip=${skip}&limit=${limit}`);
  }

  async getCollectionDetail(collectionId) {
    return this.request('GET', `/collections/${collectionId}`);
  }

  async getCollectionNFTs(collectionId, skip = 0, limit = 50) {
    return this.request('GET', `/collections/${collectionId}/nfts?skip=${skip}&limit=${limit}`);
  }

  /**
   * REFERRAL ENDPOINTS
   */

  async getReferralData() {
    return this.request('GET', '/referrals/me');
  }

  async getReferralNetwork() {
    return this.request('GET', '/referrals/network');
  }

  async applyReferralCode(referralCode) {
    return this.request('POST', '/referrals/apply', {
      body: { referral_code: referralCode },
    });
  }

  async getReferralStats() {
    return this.request('GET', '/referrals/stats');
  }

  /**
   * PAYMENT ENDPOINTS
   */

  async getPaymentStatus(transactionId) {
    return this.request('GET', `/payments/${transactionId}`);
  }

  async getStarsBalance() {
    return this.request('GET', '/payments/balance');
  }

  async getPaymentHistory(skip = 0, limit = 50, paymentType = null) {
    let path = `/payments/history?skip=${skip}&limit=${limit}`;
    if (paymentType) path += `&payment_type=${paymentType}`;
    return this.request('GET', path);
  }

  async initiateDeposit(walletId, amount, currency = 'USDT') {
    return this.request('POST', '/payments/web-app/deposit', {
      body: {
        wallet_id: walletId,
        amount,
        currency,
      },
    });
  }

  async initiateWithdrawal(walletId, amount, currency = 'USDT') {
    return this.request('POST', '/payments/web-app/withdrawal', {
      body: {
        wallet_id: walletId,
        amount,
        currency,
      },
    });
  }

  async initiateUSDTPayment(amount) {
    return this.request('POST', '/payments/usdt/initiate', {
      body: { amount },
    });
  }

  /**
   * TELEGRAM STARS PAYMENT
   */

  async createStarsInvoice(items, totalAmount, currency = 'XTR') {
    return this.request('POST', '/stars/invoice/create', {
      body: {
        item_ids: items,
        total_amount: totalAmount,
        currency,
      },
    });
  }

  async confirmStarsPayment(invoiceId, transactionId) {
    return this.request('POST', '/stars/payment/success', {
      body: {
        invoice_id: invoiceId,
        transaction_id: transactionId,
      },
    });
  }

  /**
   * TRANSACTION ENDPOINTS
   */

  async getTransactionHistory(skip = 0, limit = 50) {
    return this.request('GET', `/transactions?skip=${skip}&limit=${limit}`);
  }

  async pollTransactionStatus(transactionHash, maxAttempts = 30) {
    let attempts = 0;
    return new Promise((resolve, reject) => {
      const check = async () => {
        if (attempts >= maxAttempts) {
          reject(new Error('Transaction confirmation timeout'));
          return;
        }
        try {
          const tx = await this.request('GET', `/transactions/${transactionHash}`);
          if (tx.status === 'confirmed') {
            resolve(tx);
          } else {
            attempts++;
            setTimeout(check, 2000);
          }
        } catch (error) {
          reject(error);
        }
      };
      check();
    });
  }

  /**
   * ATTESTATION ENDPOINTS
   */

  async getNFTAttestations(nftId) {
    return this.request('GET', `/attestations/nft/${nftId}`);
  }

  /**
   * ACTIVITY ENDPOINTS
   */

  async getActivityLogs(skip = 0, limit = 50, activityType = null) {
    let path = `/activities?skip=${skip}&limit=${limit}`;
    if (activityType) path += `&activity_type=${activityType}`;
    return this.request('GET', path);
  }

  /**
   * ADMIN ENDPOINTS
   */

  async getAdminSettings() {
    return this.request('GET', '/admin/settings');
  }

  async updateAdminSettings(commissionRate, minPrice, maxPrice) {
    return this.request('PUT', '/admin/settings', {
      body: {
        commission_rate: commissionRate,
        min_listing_price: minPrice,
        max_listing_price: maxPrice,
      },
    });
  }

  async getAdminLogs(skip = 0, limit = 50, action = null) {
    let path = `/admin/logs?skip=${skip}&limit=${limit}`;
    if (action) path += `&action=${action}`;
    return this.request('GET', path);
  }

  /**
   * NOTIFICATION ENDPOINTS
   */

  async getNotifications(skip = 0, limit = 20) {
    return this.request('GET', `/notifications?skip=${skip}&limit=${limit}`);
  }

  async markNotificationAsRead(notificationId) {
    return this.request('PUT', `/notifications/${notificationId}/read`);
  }

  /**
   * SEARCH & FILTER
   */

  async searchNFTs(query, skip = 0, limit = 50) {
    return this.request('GET', `/nfts/search?q=${encodeURIComponent(query)}&skip=${skip}&limit=${limit}`);
  }

  async searchListings(query, skip = 0, limit = 50) {
    return this.request('GET', `/marketplace/search?q=${encodeURIComponent(query)}&skip=${skip}&limit=${limit}`);
  }

  /**
   * LOCK/UNLOCK ENDPOINTS
   */

  async lockNFT(nftId, reason = 'marketplace', lockedUntil = null) {
    return this.request('POST', `/nfts/${nftId}/lock`, {
      body: {
        lock_reason: reason,
        locked_until: lockedUntil,
      },
    });
  }

  async unlockNFT(nftId) {
    return this.request('POST', `/nfts/${nftId}/unlock`);
  }
}

// Create global instance
if (!window.api) {
  window.api = new APIService();
}
