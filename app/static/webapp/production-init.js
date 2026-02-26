/**
 * Production App Initialization
 * Wires APIService → DataIntegration → App State → UI
 */

class ProductionAppInitializer {
  constructor() {
    this.api = null;
    this.data = null;
    this.app = null;
    this.isInitialized = false;
  }

  /**
   * Initialize all services
   */
  async initialize() {
    try {
      console.log('[INIT] Starting production app initialization...');

      // 1. Initialize API Service
      this.api = window.api || new APIService();
      console.log('[INIT] ✓ API Service ready');

      // 2. Initialize Data Integration Service
      this.data = new window.DataIntegration(this.api);
      console.log('[INIT] ✓ Data Integration ready');

      // 3. Wait for Telegram API to be ready
      if (window.Telegram?.WebApp) {
        window.Telegram.WebApp.ready();
        console.log('[INIT] ✓ Telegram WebApp ready');
      }

      // 4. Fetch authenticated user (if token exists)
      try {
        const user = await this.data.fetchCurrentUser();
        console.log('[INIT] ✓ User authenticated:', user?.username);
      } catch (error) {
        console.warn('[INIT] ⚠ Not authenticated, loading as guest');
      }

      this.isInitialized = true;
      console.log('[INIT] ✓ Production app fully initialized');

      return this;
    } catch (error) {
      console.error('[INIT] ✗ Initialization failed:', error);
      throw error;
    }
  }

  /**
   * Enhanced marketplace loader
   * Loads real data from backend
   */
  async loadMarketplaceData(skip = 0, limit = 50, filters = {}) {
    try {
      console.log('[MARKET] Loading marketplace listings...');
      const listings = await this.data.fetchMarketplaceListings(skip, limit, filters);
      console.log('[MARKET] ✓ Loaded', listings.length, 'listings');
      return listings;
    } catch (error) {
      console.error('[MARKET] ✗ Failed to load marketplace:', error);
      return [];
    }
  }

  /**
   * Enhanced user inventory loader
   */
  async loadUserInventory(skip = 0, limit = 50) {
    try {
      console.log('[INVENTORY] Loading user NFTs...');
      const nfts = await this.data.fetchUserNFTs(skip, limit);
      console.log('[INVENTORY] ✓ Loaded', nfts.length, 'NFTs');
      return nfts;
    } catch (error) {
      console.error('[INVENTORY] ✗ Failed to load inventory:', error);
      return [];
    }
  }

  /**
   * Enhanced user listings loader
   */
  async loadMyListings(skip = 0, limit = 50) {
    try {
      console.log('[LISTINGS] Loading my listings...');
      const listings = await this.data.fetchUserListings(skip, limit);
      console.log('[LISTINGS] ✓ Loaded', listings.length, 'listings');
      return listings;
    } catch (error) {
      console.error('[LISTINGS] ✗ Failed to load my listings:', error);
      return [];
    }
  }

  /**
   * Create new listing with validation
   */
  async createListingFlow(nftId, price, currency = 'STARS', expiresAt = null) {
    try {
      console.log('[CREATE_LISTING] Creating listing for NFT:', nftId);
      
      // Validate inputs
      if (!nftId) throw new Error('NFT ID required');
      if (price <= 0) throw new Error('Price must be greater than 0');

      const listing = await this.data.createListing(nftId, price, currency, expiresAt);
      console.log('[CREATE_LISTING] ✓ Listing created:', listing.id);
      return listing;
    } catch (error) {
      console.error('[CREATE_LISTING] ✗ Failed:', error);
      throw error;
    }
  }

  /**
   * Purchase flow with offer + escrow
   */
  async purchaseFlow(listingId, nftId, buyerId, offerPrice, currency = 'STARS') {
    try {
      console.log('[PURCHASE] Starting purchase flow...');
      
      // Step 1: Make offer
      console.log('[PURCHASE] Step 1: Making offer...');
      const offer = await this.data.makeOffer(listingId, nftId, buyerId, offerPrice, currency);
      console.log('[PURCHASE] ✓ Offer created:', offer.id);

      // Step 2: Accept offer (auto-confirms in most cases)
      console.log('[PURCHASE] Step 2: Accepting offer...');
      const order = await this.data.acceptOffer(offer.id);
      console.log('[PURCHASE] ✓ Offer accepted, order created:', order.id);

      // Step 3: Monitor escrow + payment (polling)
      console.log('[PURCHASE] Step 3: Monitoring payment...');
      const escrow = await this.pollEscrowCompletion(order.escrow_id);
      console.log('[PURCHASE] ✓ Payment confirmed, escrow released');

      return { offer, order, escrow };
    } catch (error) {
      console.error('[PURCHASE] ✗ Purchase failed:', error);
      throw error;
    }
  }

  /**
   * Poll escrow status until completion
   */
  async pollEscrowCompletion(escrowId, maxAttempts = 30) {
    let attempts = 0;
    const pollInterval = 2000; // 2 seconds

    return new Promise((resolve, reject) => {
      const check = async () => {
        if (attempts >= maxAttempts) {
          reject(new Error('Payment confirmation timeout'));
          return;
        }

        try {
          const escrow = await this.api.request('GET', `/marketplace/escrows/${escrowId}`);
          if (escrow.status === 'released') {
            resolve(escrow);
            return;
          }
          attempts++;
          setTimeout(check, pollInterval);
        } catch (error) {
          reject(error);
        }
      };
      check();
    });
  }

  /**
   * Creator profile setup
   */
  async setupCreatorProfile(creatorName, creatorBio, creatorAvatarUrl = '') {
    try {
      console.log('[CREATOR] Setting up creator profile...');
      const user = await this.data.updateCreatorProfile(creatorName, creatorBio, creatorAvatarUrl);
      console.log('[CREATOR] ✓ Creator profile set:', creatorName);
      return user;
    } catch (error) {
      console.error('[CREATOR] ✗ Failed to set creator profile:', error);
      throw error;
    }
  }

  /**
   * Create NFT collection
   */
  async createCollectionFlow(name, description = '', imageUrl = '', bannerUrl = '') {
    try {
      console.log('[COLLECTION] Creating collection:', name);
      const collection = await this.data.createCollection(name, description, 'ethereum', imageUrl, bannerUrl);
      console.log('[COLLECTION] ✓ Collection created:', collection.id);
      return collection;
    } catch (error) {
      console.error('[COLLECTION] ✗ Failed:', error);
      throw error;
    }
  }

  /**
   * Referral application flow
   */
  async applyReferralFlow(referralCode) {
    try {
      console.log('[REFERRAL] Applying referral code:', referralCode);
      const result = await this.data.applyReferralCode(referralCode);
      console.log('[REFERRAL] ✓ Referral applied');
      
      // Reload referral data
      const referralData = await this.data.fetchReferralData();
      console.log('[REFERRAL] ✓ Referral data updated');
      
      return { result, referralData };
    } catch (error) {
      console.error('[REFERRAL] ✗ Failed:', error);
      throw error;
    }
  }

  /**
   * Load all dashboard data
   */
  async loadDashboardData() {
    try {
      console.log('[DASHBOARD] Loading dashboard data...');
      
      const [user, balance, referralData, paymentHistory, listings] = await Promise.all([
        this.data.state.user || this.data.fetchCurrentUser(),
        this.data.fetchStarsBalance(),
        this.data.fetchReferralData(),
        this.data.fetchPaymentHistory(0, 10),
        this.data.fetchUserListings(0, 10),
      ]);

      console.log('[DASHBOARD] ✓ Dashboard data loaded');
      
      return {
        user,
        balance,
        referralData,
        paymentHistory,
        listings,
      };
    } catch (error) {
      console.error('[DASHBOARD] ✗ Failed to load dashboard:', error);
      return null;
    }
  }

  /**
   * Mint new NFT
   */
  async mintNFTFlow(walletId, name, description, imageUrl, royaltyPercentage = 0, collectionId = null) {
    try {
      console.log('[MINT] Minting NFT:', name);
      
      const metadata = collectionId ? { collection_id: collectionId } : {};
      const nft = await this.data.mintNFT(walletId, name, description, imageUrl, royaltyPercentage, metadata);
      
      console.log('[MINT] ✓ NFT minted:', nft.id);
      return nft;
    } catch (error) {
      console.error('[MINT] ✗ Failed to mint:', error);
      throw error;
    }
  }

  /**
   * Get current app state
   */
  getState() {
    return {
      api: this.api,
      data: this.data,
      currentUser: this.data.state.user,
      listings: this.data.state.listings,
      myNFTs: this.data.state.myNFTs,
      myListings: this.data.state.myListings,
      collections: this.data.state.collections,
      referralData: this.data.state.referralData,
      isInitialized: this.isInitialized,
    };
  }

  /**
   * Handle errors gracefully
   */
  handleError(error, context = 'Unknown') {
    return this.data.handleError(error, context);
  }
}

// Initialize globally
if (!window.appInit) {
  window.ProductionInitializer = ProductionAppInitializer;
}

// Auto-initialize on DOMContentLoaded if not in iframe
if (typeof document !== 'undefined' && !window.skipAutoInit) {
  const autoInit = () => {
    if (window.api && window.DataIntegration) {
      console.log('[AUTO-INIT] Auto-initializing production app...');
      window.prodApp = new ProductionAppInitializer();
      window.prodApp.initialize().catch(error => {
        console.error('[AUTO-INIT] Failed:', error);
      });
    } else {
      // Retry after dependencies are loaded
      setTimeout(autoInit, 100);
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', autoInit);
  } else {
    autoInit();
  }
}
