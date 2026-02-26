/**
 * Data Integration Layer
 * Maps backend API to frontend state management
 * Database-first, backend-driven, production-ready
 */

class DataIntegrationService {
  constructor(apiService) {
    this.api = apiService;
    this.state = {
      user: null,
      listings: [],
      myNFTs: [],
      myListings: [],
      collections: [],
      referalData: null,
      paymentHistory: [],
      transactions: [],
      offers: [],
      order: null,
    };
    this.cache = new Map();
    this.cacheTTL = 60000; // 1 minute
  }

  /**
   * ==================== USER DATA ====================
   */

  /**
   * Fetch current authenticated user
   */
  async fetchCurrentUser() {
    try {
      const user = await this.api.getCurrentUser();
      this.state.user = user;
      this.setCacheItem('currentUser', user);
      return user;
    } catch (error) {
      console.error('Failed to fetch current user:', error);
      throw error;
    }
  }

  /**
   * Update user profile (is_creator, creator_name, etc)
   */
  async updateCreatorProfile(creatorName, creatorBio, creatorAvatarUrl) {
    try {
      const response = await this.api.request('PUT', '/auth/profile', {
        body: {
          is_creator: true,
          creator_name: creatorName,
          creator_bio: creatorBio,
          creator_avatar_url: creatorAvatarUrl,
        },
      });
      this.state.user = response;
      this.setCacheItem('currentUser', response);
      return response;
    } catch (error) {
      console.error('Failed to update creator profile:', error);
      throw error;
    }
  }

  /**
   * ==================== MARKETPLACE DATA ====================
   */

  /**
   * Fetch all active marketplace listings
   * Database-backed with real NFT data
   */
  async fetchMarketplaceListings(skip = 0, limit = 50, filters = {}) {
    const cacheKey = `listings:${skip}:${limit}:${JSON.stringify(filters)}`;
    const cached = this.getCacheItem(cacheKey);
    if (cached) return cached;

    try {
      const listings = await this.api.getActiveListings(skip, limit, filters.blockchain);
      
      // Enrich listing data with NFT details
      const enriched = listings.items.map(listing => ({
        ...listing,
        // Map backend field names to frontend expectations
        id: listing.id,
        nft_id: listing.nft_id,
        nft_name: listing.nft?.name || 'Unnamed NFT',
        nft_image: listing.nft?.image_url || '',
        price: listing.price,
        currency: listing.currency,
        seller_id: listing.seller_id,
        seller_name: listing.seller?.username || 'Anonymous',
        status: listing.status,
        created_at: listing.created_at,
        rarity_tier: listing.nft?.rarity_tier || 'common',
        descriptions: listing.nft?.description || '',
      }));

      this.state.listings = enriched;
      this.setCacheItem(cacheKey, enriched);
      return enriched;
    } catch (error) {
      console.error('Failed to fetch marketplace listings:', error);
      throw error;
    }
  }

  /**
   * ==================== NFT INVENTORY ====================
   */

  /**
   * Fetch user's NFTs
   */
  async fetchUserNFTs(skip = 0, limit = 50) {
    const cacheKey = `userNFTs:${skip}:${limit}`;
    const cached = this.getCacheItem(cacheKey);
    if (cached) return cached;

    try {
      const response = await this.api.getUserNFTs(skip, limit);
      const nfts = response.items || response;
      
      // Filter out locked NFTs (they appear in marketplace)
      const myNFTs = nfts.map(nft => ({
        ...nft,
        isLocked: nft.is_locked || nft.status === 'locked',
        isListable: !nft.is_locked && nft.status === 'minted',
      }));

      this.state.myNFTs = myNFTs;
      this.setCacheItem(cacheKey, myNFTs);
      return myNFTs;
    } catch (error) {
      console.error('Failed to fetch user NFTs:', error);
      throw error;
    }
  }

  /**
   * Mint new NFT
   */
  async mintNFT(walletId, name, description, imageUrl, royaltyPercentage = 0, metadata = {}) {
    try {
      const nft = await this.api.mintNFT(
        walletId,
        name,
        description,
        imageUrl,
        royaltyPercentage,
        metadata
      );
      // Invalidate cache
      this.invalidateCacheByPrefix('userNFTs');
      return nft;
    } catch (error) {
      console.error('Failed to mint NFT:', error);
      throw error;
    }
  }

  /**
   * ==================== USER LISTINGS ====================
   */

  /**
   * Fetch user's active listings
   */
  async fetchUserListings(skip = 0, limit = 50) {
    const cacheKey = `userListings:${skip}:${limit}`;
    const cached = this.getCacheItem(cacheKey);
    if (cached) return cached;

    try {
      const response = await this.api.getUserListings(skip, limit);
      const listings = response.items || response;
      
      this.state.myListings = listings;
      this.setCacheItem(cacheKey, listings);
      return listings;
    } catch (error) {
      console.error('Failed to fetch user listings:', error);
      throw error;
    }
  }

  /**
   * Create new listing
   */
  async createListing(nftId, price, currency = 'STARS', expiresAt = null) {
    try {
      const listing = await this.api.createListing(nftId, price, currency, expiresAt);
      // Invalidate caches
      this.invalidateCacheByPrefix('userListings');
      this.invalidateCacheByPrefix('listings');
      this.invalidateCacheByPrefix('userNFTs');
      return listing;
    } catch (error) {
      console.error('Failed to create listing:', error);
      throw error;
    }
  }

  /**
   * Cancel listing
   */
  async cancelListing(listingId) {
    try {
      const result = await this.api.cancelListing(listingId);
      // Invalidate caches
      this.invalidateCacheByPrefix('userListings');
      this.invalidateCacheByPrefix('listings');
      this.invalidateCacheByPrefix('userNFTs');
      return result;
    } catch (error) {
      console.error('Failed to cancel listing:', error);
      throw error;
    }
  }

  /**
   * ==================== OFFERS & PURCHASE ====================
   */

  /**
   * Make an offer on a listing
   */
  async makeOffer(listingId, nftId, buyerId, offerPrice, currency = 'STARS', expiresAt = null) {
    try {
      const offer = await this.api.makeOffer(
        listingId,
        nftId,
        buyerId,
        offerPrice,
        currency,
        expiresAt
      );
      // Invalidate offer caches
      this.invalidateCacheByPrefix('offers');
      return offer;
    } catch (error) {
      console.error('Failed to make offer:', error);
      throw error;
    }
  }

  /**
   * Accept offer (buy/sell confirmation)
   */
  async acceptOffer(offerId) {
    try {
      const order = await this.api.acceptOffer(offerId);
      this.state.order = order;
      // Invalidate all marketplace caches
      this.invalidateCacheByPrefix('offers');
      this.invalidateCacheByPrefix('listings');
      this.invalidateCacheByPrefix('userListings');
      this.invalidateCacheByPrefix('userNFTs');
      return order;
    } catch (error) {
      console.error('Failed to accept offer:', error);
      throw error;
    }
  }

  /**
   * ==================== COLLECTIONS ====================
   */

  /**
   * Fetch user's collections
   */
  async fetchUserCollections(skip = 0, limit = 50) {
    const cacheKey = `userCollections:${skip}:${limit}`;
    const cached = this.getCacheItem(cacheKey);
    if (cached) return cached;

    try {
      const response = await this.api.getMyCollections(skip, limit);
      const collections = response.items || response;
      this.state.collections = collections;
      this.setCacheItem(cacheKey, collections);
      return collections;
    } catch (error) {
      console.error('Failed to fetch user collections:', error);
      throw error;
    }
  }

  /**
   * Create new collection
   */
  async createCollection(name, description = '', blockchain = 'ethereum', imageUrl = '', bannerUrl = '') {
    try {
      const collection = await this.api.createCollection(
        name,
        description,
        blockchain,
        imageUrl,
        bannerUrl
      );
      this.invalidateCacheByPrefix('userCollections');
      return collection;
    } catch (error) {
      console.error('Failed to create collection:', error);
      throw error;
    }
  }

  /**
   * ==================== REFERRAL SYSTEM ====================
   */

  /**
   * Fetch user's referral data
   */
  async fetchReferralData() {
    const cacheKey = 'referralData';
    const cached = this.getCacheItem(cacheKey);
    if (cached) return cached;

    try {
      const referralData = await this.api.getReferralData();
      this.state.referralData = referralData;
      this.setCacheItem(cacheKey, referralData);
      return referralData;
    } catch (error) {
      console.error('Failed to fetch referral data:', error);
      // Return empty referral if not found
      return {
        code: null,
        earnings: 0,
        referredCount: 0,
        pendingRewards: 0,
        status: 'inactive',
      };
    }
  }

  /**
   * Apply referral code
   */
  async applyReferralCode(referralCode) {
    try {
      const result = await this.api.applyReferralCode(referralCode);
      // Invalidate referral cache
      this.invalidateCacheByPrefix('referralData');
      return result;
    } catch (error) {
      console.error('Failed to apply referral code:', error);
      throw error;
    }
  }

  /**
   * Get referral stats
   */
  async fetchReferralStats() {
    const cacheKey = 'referralStats';
    const cached = this.getCacheItem(cacheKey);
    if (cached) return cached;

    try {
      const stats = await this.api.getReferralStats();
      this.setCacheItem(cacheKey, stats);
      return stats;
    } catch (error) {
      console.error('Failed to fetch referral stats:', error);
      throw error;
    }
  }

  /**
   * ==================== PAYMENTS & BALANCE ====================
   */

  /**
   * Get current stars balance
   */
  async fetchStarsBalance() {
    try {
      const response = await this.api.getStarsBalance();
      const balance = response.balance || response.stars_balance || 0;
      if (this.state.user) {
        this.state.user.stars_balance = balance;
      }
      return balance;
    } catch (error) {
      console.error('Failed to fetch stars balance:', error);
      throw error;
    }
  }

  /**
   * Fetch payment history
   */
  async fetchPaymentHistory(skip = 0, limit = 50, paymentType = null) {
    const cacheKey = `paymentHistory:${skip}:${limit}:${paymentType || 'all'}`;
    const cached = this.getCacheItem(cacheKey);
    if (cached) return cached;

    try {
      const response = await this.api.getPaymentHistory(skip, limit, paymentType);
      const payments = response.items || response;
      this.state.paymentHistory = payments;
      this.setCacheItem(cacheKey, payments);
      return payments;
    } catch (error) {
      console.error('Failed to fetch payment history:', error);
      throw error;
    }
  }

  /**
   * Initiate deposit (buy stars)
   */
  async initiateDeposit(walletId, amount, currency = 'USDT') {
    try {
      const payment = await this.api.initiateDeposit(walletId, amount, currency);
      this.invalidateCacheByPrefix('paymentHistory');
      return payment;
    } catch (error) {
      console.error('Failed to initiate deposit:', error);
      throw error;
    }
  }

  /**
   * Initiate withdrawal (cash out stars)
   */
  async initiateWithdrawal(walletId, amount, currency = 'USDT') {
    try {
      const payment = await this.api.initiateWithdrawal(walletId, amount, currency);
      this.invalidateCacheByPrefix('paymentHistory');
      return payment;
    } catch (error) {
      console.error('Failed to initiate withdrawal:', error);
      throw error;
    }
  }

  /**
   * ==================== TELEGRAM STARS PAYMENT ====================
   */

  /**
   * Create Telegram stars invoice
   */
  async createStarsInvoice(items, totalAmount, currency = 'XTR') {
    try {
      const invoice = await this.api.createStarsInvoice(items, totalAmount, currency);
      return invoice;
    } catch (error) {
      console.error('Failed to create stars invoice:', error);
      throw error;
    }
  }

  /**
   * Confirm Telegram stars payment
   */
  async confirmStarsPayment(invoiceId, transactionId) {
    try {
      const result = await this.api.confirmStarsPayment(invoiceId, transactionId);
      // Invalidate all user data caches
      this.invalidateCacheByPrefix('paymentHistory');
      this.invalidateCacheByPrefix('currentUser');
      return result;
    } catch (error) {
      console.error('Failed to confirm stars payment:', error);
      throw error;
    }
  }

  /**
   * ==================== CACHE MANAGEMENT ====================
   */

  setCacheItem(key, data) {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
    });
  }

  getCacheItem(key) {
    const item = this.cache.get(key);
    if (!item) return null;
    if (Date.now() - item.timestamp > this.cacheTTL) {
      this.cache.delete(key);
      return null;
    }
    return item.data;
  }

  invalidateCacheByPrefix(prefix) {
    for (const key of this.cache.keys()) {
      if (key.startsWith(prefix)) {
        this.cache.delete(key);
      }
    }
  }

  clearAllCache() {
    this.cache.clear();
  }

  /**
   * ==================== ERROR HANDLING ====================
   */

  /**
   * Handle API errors gracefully
   */
  handleError(error, context = 'Unknown error') {
    const message = error.message || error.detail || 'An error occurred';
    console.error(`[${context}] ${message}`, error);
    
    return {
      error: true,
      message,
      context,
      timestamp: new Date().toISOString(),
    };
  }
}

// Export globally
if (!window.DataIntegration) {
  window.DataIntegration = DataIntegrationService;
}
