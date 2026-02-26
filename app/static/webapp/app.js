/**
 * GiftedForge - Telegram Mini App (Production Edition)
 * State-driven, cache-aware NFT marketplace
 * No external dependencies, Telegram-native first
 */

(() => {
  'use strict';

  // ========== DOM REFERENCES ==========
  const dom = {
    app: document.getElementById('app'),
    mainContent: document.getElementById('mainContent'),
    pages: {},
    navTabs: Array.from(document.querySelectorAll('.nav-tab')),
    modalOverlay: document.getElementById('modalOverlay'),
    toastContainer: null,
  };

  document.querySelectorAll('.page').forEach((el) => {
    dom.pages[el.dataset.page] = el;
  });

  // ========== ENHANCED STATE SYSTEM ==========
  const app = {
    // UI State
    ui: {
      currentPage: 'market',
      modals: {
        item: null,        // { item, type }
        referral: null,
        profile: null,
        settings: null,
      },
      filters: {
        market: 'all',
        sort: 'recent',
        search: '',
      },
      loading: new Set(),         // granular loading
      errors: new Map(),
      navCollapsed: false,
    },

    // User State
    user: null,
    auth: {
      initData: null,
      isAuthenticated: false,
      sessionId: null,
      lastAuthCheck: 0,
    },

    // Data State (with cache metadata)
    data: {
      listings: {
        items: [],
        total: 0,
        page: 0,
        lastFetch: 0,
        ttl: 60000,        // 1 min
      },
      myItems: {
        items: [],
        total: 0,
        lastFetch: 0,
        ttl: 120000,       // 2 min
      },
      referrals: {
        code: null,
        earnings: 0,
        referredCount: 0,
        pendingRewards: 0,
        history: [],
        network: [],
        lastFetch: 0,
        ttl: 300000,       // 5 min
      },
      transactions: {
        items: [],
        total: 0,
        lastFetch: 0,
        ttl: 300000,
      },
      profile: null,
      profileStats: null,
    },

    // Cart State
    cart: {
      items: [],
      total: 0,
      currency: 'STARS',
      status: 'open',
    },

    // Creator State
    creator: {
      isCreator: false,
      drafts: [],
      published: [],
      earnings: 0,
      totalSold: 0,
    },
  };

  // ========== CONFIG ==========
  const CONFIG = {
    API_BASE: '/api/v1',
    TIMEOUT: 15000,
    RETRY_ATTEMPTS: 2,
    STAR_TO_USDT: 0.004,
    CACHE_DURATION: 60000,
  };

  // ========== UTILITIES ==========
  function log(msg, type = 'log') {
    console.log(`[${type.toUpperCase()}] ${msg}`);
  }

  function showToast(msg, type = 'info', duration = 3000) {
    if (!dom.toastContainer) {
      dom.toastContainer = document.createElement('div');
      dom.toastContainer.id = 'toastContainer';
      dom.toastContainer.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 3000;
        padding: 16px;
        display: flex;
        flex-direction: column;
        gap: 8px;
        pointer-events: none;
      `;
      document.body.appendChild(dom.toastContainer);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast--${type}`;
    toast.textContent = msg;
    toast.style.cssText = `
      padding: 12px 16px;
      border-radius: 8px;
      font-size: 14px;
      font-weight: 500;
      animation: slideDown 0.3s ease;
      pointer-events: auto;
      cursor: pointer;
      ${type === 'success' ? 'background: rgba(52, 211, 153, 0.1); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.3);' : ''}
      ${type === 'error' ? 'background: rgba(255, 59, 48, 0.1); color: #ff3b30; border: 1px solid rgba(255, 59, 48, 0.3);' : ''}
      ${type === 'info' ? 'background: rgba(0, 136, 204, 0.1); color: #0088cc; border: 1px solid rgba(0, 136, 204, 0.3);' : ''}
    `;

    dom.toastContainer.appendChild(toast);
    window.haptic?.light();

    const timeout = setTimeout(() => {
      toast.style.animation = 'slideUp 0.3s ease';
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 300);
    }, duration);

    toast.addEventListener('click', () => {
      clearTimeout(timeout);
      toast.remove();
    });
  }

  // ========== CACHE HELPERS ==========
  const apiCache = new Map();

  function shouldRefresh(dataKey) {
    const data = app.data[dataKey];
    if (!data) return true;
    return Date.now() - data.lastFetch > data.ttl;
  }

  function cacheSet(key, data) {
    apiCache.set(key, { data, timestamp: Date.now() });
  }

  function cacheGet(key) {
    const cached = apiCache.get(key);
    if (cached && Date.now() - cached.timestamp < CONFIG.CACHE_DURATION) {
      return cached.data;
    }
    return null;
  }

  // ========== API LAYER ==========
  async function apiCall(endpoint, options = {}) {
    const { method = 'GET', body = null, cache = true } = options;
    const cacheKey = `${endpoint}:${JSON.stringify(options)}`;

    // Check cache for GET requests
    if (method === 'GET' && cache) {
      const cached = cacheGet(cacheKey);
      if (cached) {
        log(`Cache hit: ${endpoint}`, 'log');
        return cached;
      }
    }

    try {
      const fetchOptions = {
        method,
        headers: { 'Content-Type': 'application/json' },
        signal: AbortSignal.timeout(CONFIG.TIMEOUT),
      };

      if (body) fetchOptions.body = JSON.stringify(body);

      const response = await fetch(`${CONFIG.API_BASE}${endpoint}`, fetchOptions);

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      const data = await response.json();

      // Cache success
      if (method === 'GET' && cache) {
        cacheSet(cacheKey, data);
      }

      return data;
    } catch (error) {
      log(`API Error [${endpoint}]: ${error.message}`, 'error');
      
      // Try stale cache on error
      const cached = apiCache.get(cacheKey);
      if (cached) {
        log(`Using stale cache for ${endpoint}`, 'warn');
        return cached.data;
      }

      throw error;
    }
  }

  // ========== TELEGRAM INTEGRATION ==========
  function initTelegramWebApp() {
    if (window.Telegram?.WebApp) {
      const webApp = window.Telegram.WebApp;
      webApp.ready();
      webApp.setHeaderColor('#0a0e27');
      webApp.setBackgroundColor('#0a0e27');

      app.auth.initData = webApp.initData;
      app.auth.isAuthenticated = !!webApp.initData;

      window.haptic = {
        light: () => webApp.HapticFeedback?.impactOccurred?.('light'),
        medium: () => webApp.HapticFeedback?.impactOccurred?.('medium'),
        heavy: () => webApp.HapticFeedback?.impactOccurred?.('heavy'),
        selection: () => webApp.HapticFeedback?.selectionChanged?.(),
        notification: (type = 'success') => webApp.HapticFeedback?.notificationOccurred?.(type),
      };

      log('Telegram WebApp initialized');
    }
  }

  // ========== TELEGRAM STARS PAYMENT FLOW ==========
  
  /**
   * Initialize Telegram Stars payment for cart items.
   * Creates invoice, calculates commissions, initiates payment.
   */
  async function initiateTelegramStarsPayment() {
    if (!app.cart.items.length) {
      showToast('Cart is empty', 'error');
      return;
    }

    try {
      app.ui.loading.add('checkout');

      // Process each item in cart using real production purchase flow
      const cartTotal = app.cart.items.reduce((sum, item) => sum + (item.price || 0), 0);
      const invoiceId = generateInvoiceId();

      // Process purchases via production system
      const results = [];
      for (const item of app.cart.items) {
        try {
          const result = await window.prodApp.purchaseFlow(
            item.id,                    // listingId
            item.nft_id,               // nftId
            app.user.id,               // buyerId
            item.price,                // offerPrice
            'STARS'                    // currency
          );
          results.push(result);
          log(`Purchase completed for ${item.name}`, 'success');
        } catch (itemError) {
          log(`Failed to purchase ${item.name}: ${itemError.message}`, 'error');
        }
      }

      if (results.length > 0) {
        showToast(`${results.length} purchase(s) successful! 🎉`, 'success');
        window.haptic?.notification?.('success');
        app.cart.items = [];
        app.cart.total = 0;
        
        // Reload marketplace and inventory
        await loadMarketplace();
        await loadMyItems();
        router.navigate('market');
      } else {
        showToast('No purchases completed', 'error');
      }
    } catch (error) {
      showToast(`Checkout failed: ${error.message}`, 'error');
      log(`Checkout error: ${error.message}`, 'error');
    } finally {
      app.ui.loading.delete('checkout');
    }
  }

  /**
   * Generate unique invoice ID.
   */
  function generateInvoiceId() {
    const timestamp = Date.now().toString(36);
    const random = Math.random().toString(36).substring(2, 10);
    return `inv_${timestamp}_${random}`;
  }

  /**
   * Show payment breakdown modal with commission details.
   */
  function showPaymentBreakdown(invoiceData) {
    const breakdown = `
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--spacing); margin: var(--spacing) 0;">
        <div style="background: rgba(0,136,204,0.1); padding: var(--spacing); border-radius: 8px;">
          <div style="font-size: 12px; color: #888; margin-bottom: 4px;">Total Amount</div>
          <div style="font-size: 20px; font-weight: bold; color: #fff;">${invoiceData.total_stars} ⭐</div>
        </div>
        <div style="background: rgba(100,200,50,0.1); padding: var(--spacing); border-radius: 8px;">
          <div style="font-size: 12px; color: #888; margin-bottom: 4px;">Creator Gets</div>
          <div style="font-size: 20px; font-weight: bold; color: #64c832;">${invoiceData.net_creator_payout} ⭐</div>
        </div>
      </div>
      <div style="margin-top: var(--spacing); padding: var(--spacing); background: rgba(255,255,255,0.05); border-radius: 8px;">
        <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 8px;">
          <span>Platform Fee (2%)</span>
          <span style="color: #ff6b6b;">-${invoiceData.platform_commission} ⭐</span>
        </div>
        ${invoiceData.referral_commission > 0 ? `
          <div style="display: flex; justify-content: space-between; font-size: 13px; color: #888;">
            <span>Your Referral Bonus</span>
            <span style="color: #4ecdc4;">+${invoiceData.referral_commission} ⭐</span>
          </div>
        ` : ''}
      </div>
    `;

    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
      <button class="modal-close" onclick="document.getElementById('itemModal').style.display='none'">✕</button>
      <div style="margin-top: 24px;">
        <div class="modal-title">Complete Purchase</div>
        ${breakdown}
      </div>
      <button onclick="initiateTelegramStarsPayment()" style="width: 100%; margin-top: var(--spacing); padding: 12px; background: #0088cc; color: white; border: none; border-radius: 8px; font-weight: 600; cursor: pointer;">
        Pay with Telegram Stars ⭐
      </button>
      <button onclick="document.getElementById('itemModal').style.display='none'" style="width: 100%; margin-top: 8px; padding: 12px; background: rgba(255,255,255,0.1); color: white; border: none; border-radius: 8px; font-weight: 600; cursor: pointer;">
        Cancel
      </button>
    `;

    const modalEl = document.getElementById('itemModal');
    const oldModal = modalEl.querySelector('.modal');
    if (oldModal) oldModal.remove();
    modalEl.appendChild(modal);
    modalEl.style.display = 'flex';
  }

  /**
   * Callback when Telegram payment dialog closes.
   * Handles both success and cancellation.
   */
  function onTelegramPaymentClosed(isSuccessful) {
    if (isSuccessful) {
      showToast('Payment processing... ⏳', 'info');
      // Payment handler will be called via webhook/callback
      // For now, we poll for payment confirmation
      pollPaymentStatus();
    } else {
      showToast('Payment cancelled', 'info');
    }
  }

  /**
   * Poll server for payment confirmation status.
   * In production, use WebSocket or Server-Sent Events for real-time updates.
   */
  async function pollPaymentStatus(maxAttempts = 30) {
    let attempts = 0;
    const initialBalance = app.user?.stars_balance || 0;

    const checkStatus = async () => {
      if (attempts >= maxAttempts) {
        showToast('Payment confirmation timeout. Please check your balance.', 'error');
        return;
      }

      try {
        // Check user's current balance to infer if payment succeeded
        const user = await apiCall('/auth/me');
        
        if (user.stars_balance > initialBalance) {
          // Stars increased = payment succeeded!
          const earnedStars = user.stars_balance - initialBalance;
          
          app.user = user;
          app.cart.items = [];
          
          showToast(`Payment confirmed! +${earnedStars} ⭐`, 'success');
          window.haptic?.notification?.('success');
          
          // Reload data
          renderCartPage();
          await loadMyItems();
          await loadTransactions();
          
          log(`Payment confirmed, balance: ${user.stars_balance}`, 'success');
          return;
        }
      } catch (error) {
        log(`Payment status check failed: ${error.message}`, 'warn');
      }

      attempts++;
      // Wait before next attempt (exponential backoff)
      setTimeout(checkStatus, Math.min(1000 * (attempts / 5), 5000));
    };

    checkStatus();
  }

  /**
   * Calculate commission breakdown for transparency.
   */
  function calculateCommissions(totalStars, hasReferrer = true) {
    const platformRate = 0.02; // 2%
    const referralRate = 0.1; // 10% of platform fee

    const platformFee = Math.floor(totalStars * platformRate);
    const referralCommission = hasReferrer ? Math.floor(platformFee * referralRate) : 0;
    const creatorPayout = totalStars - platformFee;

    return {
      total: totalStars,
      platformFee,
      referralCommission,
      creatorPayout,
    };
  }

  // ========== WALLET SIGN-IN FLOW ==========

  /**
   * Initialize wallet sign-in flow.
   * Supports MetaMask, WalletConnect, and other EVM wallets.
   */
  async function initWalletSignIn() {
    try {
      // Check for Web3 provider (MetaMask, etc.)
      if (!window.ethereum) {
        showToast('Please install MetaMask or use a Web3 wallet', 'error');
        return;
      }

      showToast('Requesting wallet connection...', 'info');

      // Request account access
      const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
      const walletAddress = accounts[0].toLowerCase();

      log(`Wallet connected: ${walletAddress}`, 'success');

      // Get sign-in message from backend
      const messageData = await apiCall('/stars/wallet/message', { cache: false });

      // Sign the message with the wallet
      const signature = await window.ethereum.request({
        method: 'personal_sign',
        params: [messageData.message, walletAddress],
      });

      log(`Message signed`, 'success');

      // Send signature to backend for authentication
      const authData = await apiCall('/stars/wallet/signin', {
        method: 'POST',
        body: {
          wallet_address: walletAddress,
          chain: 'ethereum',
          message: messageData.message,
          signature: signature,
        },
        cache: false,
      });

      // Store auth token
      localStorage.setItem('auth_token', authData.access_token);
      app.auth.token = authData.access_token;
      app.auth.isAuthenticated = true;

      // Load user data
      app.user = {
        id: authData.user_id,
        username: authData.username,
        telegram_id: walletAddress,
      };

      showToast(`Signed in as ${authData.is_new ? 'new user' : authData.username}! 🔐`, 'success');
      window.haptic?.notification?.('success');

      log(`Wallet authentication successful`, 'success');

      // Redirect to marketplace
      router.navigate('market');
      await render();
    } catch (error) {
      if (error.code === 4001) {
        showToast('Wallet connection cancelled', 'info');
      } else {
        showToast(`Wallet sign-in failed: ${error.message}`, 'error');
      }
      log(`Wallet sign-in error: ${error.message}`, 'error');
    }
  }
  class Modal {
    constructor(type, data = {}) {
      this.type = type;
      this.data = data;
      this.errors = new Map();
      this.loading = false;
    }

    static types = {
      itemDetail: 'showItemDetailModal',
      referralShare: 'showReferralModal',
      profileEdit: 'showProfileModal',
      checkout: 'showCheckoutModal',
    };

    close() {
      app.ui.modals[this.type === 'itemDetail' ? 'item' : this.type] = null;
      render();
    }
  }

  function showModal(title, content, actions = []) {
    const modal = dom.modalOverlay;
    let existingModal = modal.querySelector('.modal');

    if (existingModal) {
      existingModal.remove();
    }

    const modalEl = document.createElement('div');
    modalEl.className = 'modal';
    modalEl.innerHTML = `
      <button class="modal-close" onclick="window.__closeModal()">✕</button>
      <div style="margin-top: 24px;">
        ${title ? `<div class="modal-title">${title}</div>` : ''}
        ${content}
      </div>
      ${
        actions.length
          ? `
        <div style="display: flex; flex-direction: column; gap: 8px; margin-top: var(--spacing);">
          ${actions
            .map(
              (action) => `
            <button 
              class="modal-button ${action.type === 'primary' ? 'primary' : 'secondary'}"
              onclick="window.__handleModalAction(${action.id})"
            >
              ${action.label}
            </button>
          `
            )
            .join('')}
        </div>
      `
          : ''
      }
    `;

    // Store actions globally for safe invocation
    window.__modalActions = actions;

    modal.appendChild(modalEl);
    modal.classList.add('active');
    window.haptic?.light();
  }

  window.__closeModal = function () {
    dom.modalOverlay.classList.remove('active');
    const modal = dom.modalOverlay.querySelector('.modal');
    if (modal) modal.remove();
    app.ui.modals = { item: null, referral: null, profile: null, settings: null };
    window.__modalActions = [];
  };

  window.__handleModalAction = function (actionId) {
    const action = window.__modalActions[actionId];
    if (action && action.handler) action.handler();
  };

  // ========== ROUTER & NAVIGATION ==========
  const router = {
    pages: ['market', 'create', 'stars', 'cart', 'myitems', 'profile', 'creator'],
    history: [],

    navigate(page, params = {}) {
      if (!this.pages.includes(page)) return;

      app.ui.currentPage = page;
      app.ui.modals = {};

      loadPageContent(page, params);
      render();
    },

    back() {
      if (this.history.length === 0) return;
      const { page } = this.history.pop();
      app.ui.currentPage = page;
      render();
    },
  };

  function loadPageContent(page, params = {}) {
    switch (page) {
      case 'market':
        if (shouldRefresh('listings')) loadMarketplace();
        break;
      case 'myitems':
        if (shouldRefresh('myItems')) loadMyItems();
        break;
      case 'stars':
        if (shouldRefresh('referrals')) loadReferrals();
        loadTransactions();
        break;
      case 'profile':
        loadProfile();
        break;
      case 'creator':
        loadCreatorStats();
        break;
    }
  }

  // ========== MARKETPLACE PAGE ==========
  async function loadMarketplace() {
    app.ui.loading.add('market');
    app.ui.errors.delete('market');

    try {
      // Load real marketplace data from database via ProductionInit
      const listings = await window.prodApp.loadMarketplaceData(0, 50);
      app.data.listings = {
        items: listings || [],
        total: listings?.length || 0,
        page: 0,
        lastFetch: Date.now(),
        ttl: 60000,
      };
      app.ui.loading.delete('market');
    } catch (error) {
      app.ui.errors.set('market', error.message);
      app.ui.loading.delete('market');
      showToast(`Failed to load marketplace: ${error.message}`, 'error');
    }
  }

  function createCollectibleCard(item, type = 'listing') {
    const card = document.createElement('div');
    card.className = 'collectible-card';

    const status = item.status || 'minted';
    const statusLabel = status === 'listed' ? 'Listed' : 'Minted';
    const statusClass = status === 'listed' ? 'listed' : 'minted';

    const imageUrl = item.image_url || item.image || 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="200"%3E%3Crect fill="%23142031" width="200" height="200"/%3E%3Ctext x="100" y="100" text-anchor="middle" dy=".3em" fill="%238892b0" font-size="14"%3ENo Image%3C/text%3E%3C/svg%3E';

    card.innerHTML = `
      <div class="collectible-image-container">
        <img src="${imageUrl}" alt="${item.name || 'Collectible'}" class="collectible-image" loading="lazy" />
        <div class="collectible-status ${statusClass}">${statusLabel}</div>
      </div>
      <div class="collectible-info">
        <div class="collectible-name">${item.name || 'Unnamed'}</div>
        ${item.price ? `<div class="collectible-price"><span class="collectible-price-stars">${item.price}</span> ⭐</div>` : ''}
        ${item.rarity_tier ? `<div class="collectible-rarity">${item.rarity_tier}</div>` : ''}
      </div>
    `;

    card.addEventListener('click', () => {
      showItemModal(item, type);
    });

    return card;
  }

  function showItemModal(item, type = 'listing') {
    const rarity = item.rarity_tier || item.rarity || 'Common';
    const imageUrl = item.image_url || item.image || '';

    const actions = [];
    if (type === 'listing') {
      actions.push({
        id: 0,
        label: `Buy Now - ${item.price} ⭐`,
        type: 'primary',
        handler: () => addToCart(item.id),
      });
      actions.push({
        id: 1,
        label: 'Make Offer...',
        type: 'secondary',
        handler: () => showToast('Make offer feature coming soon', 'info'),
      });
    } else if (type === 'myitem') {
      const isListed = item.status === 'listed';
      actions.push({
        id: 0,
        label: isListed ? 'Unlist' : 'List for Sale',
        type: 'primary',
        handler: () => toggleListing(item.id),
      });
      actions.push({
        id: 1,
        label: 'View Details',
        type: 'secondary',
        handler: () => showToast('View details coming soon', 'info'),
      });
    }

    const content = `
      <img src="${imageUrl}" alt="${item.name}" class="modal-image" />
      <div class="modal-subtitle">${rarity.toUpperCase()}</div>
      <div class="modal-section">
        <div class="modal-section-label">Description</div>
        <div class="modal-section-value">${item.description || 'No description'}</div>
      </div>
      ${item.price ? `
        <div class="modal-section">
          <div class="modal-section-label">Price</div>
          <div class="modal-section-value">${item.price} ⭐</div>
        </div>
      ` : ''}
      ${item.attributes && Object.keys(item.attributes).length ? `
        <div class="modal-section">
          <div class="modal-section-label">Attributes</div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
            ${Object.entries(item.attributes).map(([key, value]) => `
              <div style="padding: 8px; background: var(--tg-bg); border-radius: 6px; text-align: center; font-size: 12px;">
                <div style="color: var(--tg-text-secondary); margin-bottom: 2px;">${key}</div>
                <div style="color: var(--tg-text); font-weight: 600;">${value}</div>
              </div>
            `).join('')}
          </div>
        </div>
      ` : ''}
    `;

    showModal(item.name, content, actions);
  }

  function addToCart(itemId) {
    const item = app.data.listings.items.find((l) => l.id === itemId);
    if (!item) return;

    const exists = app.cart.items.find((c) => c.id === itemId);
    if (!exists) {
      app.cart.items.push(item);
      app.cart.total += item.price || 0;
      window.haptic?.notification?.('success');
      showToast('Added to cart!', 'success');
      window.__closeModal();
      render();
    } else {
      showToast('Already in cart', 'info');
    }
  }

  function toggleListing(itemId) {
    showToast('Toggle listing feature coming soon', 'info');
  }

  // ========== MY ITEMS PAGE ==========
  async function loadMyItems() {
    app.ui.loading.add('myItems');

    try {
      // Load real user NFT inventory from database
      const nfts = await window.prodApp.loadUserInventory(0, 50);
      app.data.myItems = {
        items: nfts || [],
        total: nfts?.length || 0,
        lastFetch: Date.now(),
        ttl: 120000,
      };
      app.ui.loading.delete('myItems');
    } catch (error) {
      app.ui.errors.set('myItems', error.message);
      app.ui.loading.delete('myItems');
      showToast(`Failed to load items: ${error.message}`, 'error');
    }
  }

  // ========== REFERRALS PAGE ==========
  async function loadReferrals() {
    if (!app.user || !app.user.id) return;

    try {
      // Load real referral data from database
      const referralData = await window.prodApp.data.fetchReferralData();
      const referralStats = await window.prodApp.data.fetchReferralStats();

      app.data.referrals = {
        code: referralData?.code,
        earnings: referralData?.lifetime_earnings || 0,
        referredCount: referralData?.referred_count || 0,
        pendingRewards: referralStats?.pending_commissions || 0,
        network: referralData?.referred_users || [],
        history: referralStats?.commission_history || [],
        lastFetch: Date.now(),
        ttl: 300000,
      };
    } catch (error) {
      log(`Referral load failed: ${error.message}`, 'warn');
    }
  }

  async function loadTransactions() {
    try {
      // Load real payment history from database
      const paymentHistory = await window.prodApp.data.fetchPaymentHistory();
      app.data.transactions = {
        items: paymentHistory || [],
        total: paymentHistory?.length || 0,
        lastFetch: Date.now(),
        ttl: 300000,
      };
    } catch (error) {
      log(`Transaction load failed: ${error.message}`, 'warn');
    }
  }

  function copyReferralLink() {
    const code = app.data.referrals.code;
    if (!code) {
      showToast('No referral code available', 'error');
      return;
    }

    const link = `https://t.me/giftedforge_bot?start=ref_${code}`;

    if (navigator.clipboard) {
      navigator.clipboard.writeText(link);
      showToast('Referral link copied! 📋', 'success');
    } else {
      const tmp = document.createElement('textarea');
      tmp.value = link;
      document.body.appendChild(tmp);
      tmp.select();
      document.execCommand('copy');
      document.body.removeChild(tmp);
      showToast('Link copied!', 'success');
    }

    window.haptic?.medium();
  }

  // ========== PROFILE PAGE ==========
  async function loadProfile() {
    try {
      const [user, stats] = await Promise.all([
        apiCall('/auth/me'),
        apiCall('/users/me/stats'),
      ]);

      app.user = user;
      app.creator.isCreator = user.is_creator || false;
      app.data.profile = user;
      app.data.profileStats = stats;
    } catch (error) {
      log(`Profile load failed: ${error.message}`, 'warn');
      showToast('Failed to load profile', 'error');
    }
  }

  async function loadCreatorStats() {
    if (!app.creator.isCreator) return;

    try {
      const data = await apiCall('/creator/stats');
      app.creator.earnings = data.total_earnings || 0;
      app.creator.totalSold = data.total_sold || 0;
      app.creator.published = data.published_items || [];
    } catch (error) {
      log(`Creator stats load failed: ${error.message}`, 'warn');
    }
  }

  async function toggleCreatorMode() {
    const isEnabling = !app.creator.isCreator;
    app.ui.loading.add('creator');
    
    try {
      if (isEnabling) {
        // Use production setup creator profile flow
        const result = await window.prodApp.setupCreatorProfile(
          app.user?.username || 'Creator',
          'Emerging NFT creator',
          app.user?.avatar_url || ''
        );
        app.user.is_creator = true;
        app.creator.isCreator = true;
        showToast('Creator mode enabled! 🎨', 'success');
      } else {
        app.creator.isCreator = false;
        showToast('Creator mode disabled', 'info');
      }
      render();
    } catch (error) {
      showToast(`Failed to toggle creator mode: ${error.message}`, 'error');
      app.creator.isCreator = !isEnabling;
    } finally {
      app.ui.loading.delete('creator');
    }
  }

  async function saveCreatorProfile() {
    const name = document.getElementById('creatorName')?.value?.trim();
    const bio = document.getElementById('creatorBio')?.value?.trim();

    if (!name || name.length < 3) {
      showToast('Creator name must be at least 3 characters', 'error');
      return;
    }

    try {
      // Use real production creator profile setup
      await window.prodApp.setupCreatorProfile(name, bio, app.user?.avatar_url || '');
      showToast('Creator profile saved! 🎨', 'success');
      app.user.creator_name = name;
      app.user.creator_bio = bio;
      app.user.is_creator = true;
    } catch (error) {
      showToast(`Error: ${error.message}`, 'error');
    }
  }

  async function logoutApp() {
    app.user = null;
    app.auth.isAuthenticated = false;
    app.data = { listings: { items: [], total: 0, lastFetch: 0, ttl: 60000 }, myItems: { items: [], total: 0, lastFetch: 0, ttl: 120000 }, referrals: { code: null, earnings: 0, referredCount: 0, pendingRewards: 0, history: [], network: [], lastFetch: 0, ttl: 300000 }, transactions: { items: [], total: 0, lastFetch: 0, ttl: 300000 }, profile: null, profileStats: null };
    router.navigate('market');
    showToast('Logged out', 'success');
  }

  // ========== PAGE RENDERING ==========
  async function render() {
    const page = router.currentPage || 'market';

    // Hide all pages
    document.querySelectorAll('[data-page]').forEach(p => p.style.display = 'none');

    // Show current page
    const currentPageEl = document.querySelector(`[data-page="${page}"]`);
    if (currentPageEl) currentPageEl.style.display = 'block';

    // Update nav highlight
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelector(`.nav-btn[data-page="${page}"]`)?.classList.add('active');

    // Load page content
    switch (page) {
      case 'market':
        if (shouldRefresh('listings')) await loadMarketplace();
        renderMarketplace();
        break;

      case 'create':
        renderCreatePage();
        break;

      case 'stars':
        if (shouldRefresh('transactions')) await loadTransactions();
        if (shouldRefresh('referrals')) await loadReferrals();
        renderStarsPage();
        break;

      case 'cart':
        renderCartPage();
        break;

      case 'my-items':
        if (shouldRefresh('myItems')) await loadMyItems();
        renderMyItemsPage();
        break;

      case 'profile':
        if (shouldRefresh('profile')) await loadProfile();
        renderProfilePage();
        break;
    }
  }

  function renderMarketplace() {
    const grid = document.getElementById('marketGrid');
    const empty = document.getElementById('marketEmpty');
    const listings = app.data.listings.items;

    if (!listings.length) {
      empty.style.display = 'flex';
      grid.style.display = 'none';
      return;
    }

    empty.style.display = 'none';
    grid.style.display = 'grid';
    grid.innerHTML = '';

    listings.forEach(item => {
      const card = createCollectibleCard(item, 'market');
      card.addEventListener('click', () => showItemModal(item));
      grid.appendChild(card);
    });

    if (app.ui.loading.has('market')) {
      grid.innerHTML += '<div style="grid-column:1/-1;text-align:center;padding:20px;color:#888;">Loading...</div>';
    }
  }

  function renderCartPage() {
    const grid = document.getElementById('cartGrid');
    const empty = document.getElementById('cartEmpty');
    const totalEl = document.getElementById('cartTotal');

    if (!app.cart.items.length) {
      empty.style.display = 'flex';
      grid.style.display = 'none';
      return;
    }

    empty.style.display = 'none';
    grid.style.display = 'grid';
    grid.innerHTML = '';

    let total = 0;
    app.cart.items.forEach(item => {
      total += item.price || 0;
      const card = document.createElement('div');
      card.className = 'collectible-card';
      card.innerHTML = `
        <img src="${item.image_url}" alt="${item.name}" class="card-img">
        <h3>${item.name}</h3>
        <p class="price">${item.price} ⭐</p>
        <button class="remove-btn" data-id="${item.id}">Remove</button>
      `;
      grid.appendChild(card);

      card.querySelector('.remove-btn').addEventListener('click', (e) => {
        e.preventDefault();
        removeFromCart(item.id);
      });
    });

    totalEl.textContent = total;
  }

  function removeFromCart(itemId) {
    app.cart.items = app.cart.items.filter(i => i.id !== itemId);
    renderCartPage();
    showToast('Removed from cart', 'success');
    window.haptic?.light();
  }

  function renderCreatePage() {
    const formEl = document.getElementById('createForm');
    if (!formEl) return;

    formEl.addEventListener('submit', handleCreateSubmit);
    document.getElementById('imageUpload')?.addEventListener('change', handleImageUpload);
  }

  async function handleImageUpload(e) {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (evt) => {
      app.creator.drafts.imageData = evt.target.result;
      const preview = document.getElementById('imagePreview');
      if (preview) preview.src = evt.target.result;
      showToast('Image loaded', 'success');
    };
    reader.readAsDataURL(file);
  }

  async function handleCreateSubmit(e) {
    e.preventDefault();

    const name = document.getElementById('nftName')?.value?.trim();
    const description = document.getElementById('nftDesc')?.value?.trim();
    const imageData = app.creator.drafts.imageData;
    const royaltyPercentage = parseInt(document.getElementById('royalty')?.value || 0);

    if (!name || !description || !imageData) {
      showToast('Please fill all fields', 'error');
      return;
    }

    app.ui.loading.add('create');

    try {
      // Get primary wallet for minting
      const wallet = app.user?.wallets?.[0];
      if (!wallet) {
        showToast('No wallet available. Create one first.', 'error');
        return;
      }

      // Use real production mint flow
      const nft = await window.prodApp.mintNFTFlow(
        wallet.id,
        name,
        description,
        imageData,
        royaltyPercentage
      );

      showToast(`NFT minted successfully! ID: ${nft.id}`, 'success');
      window.haptic?.notification?.('success');
      
      // Reset form and reload inventory
      app.creator.drafts = {};
      document.getElementById('createForm')?.reset();
      await loadMyItems();
      router.navigate('my-items');
    } catch (error) {
      showToast(`Error: ${error.message}`, 'error');
    } finally {
      app.ui.loading.delete('create');
    }
  }

  function renderStarsPage() {
    const balanceEl = document.getElementById('starsBalance');
    const refCodeEl = document.getElementById('refCode');
    const copyBtnEl = document.getElementById('copyRefBtn');
    const referralNetworkEl = document.getElementById('referralNetwork');

    if (balanceEl && app.user?.stars_balance) {
      balanceEl.textContent = app.user.stars_balance;
    }

    if (refCodeEl && app.data.referrals?.code) {
      refCodeEl.textContent = app.data.referrals.code;
      copyBtnEl?.addEventListener('click', copyReferralLink);
    }

    if (referralNetworkEl && app.data.referrals?.network?.length) {
      referralNetworkEl.innerHTML = app.data.referrals.network
        .map(
          ref => `
        <div class="referral-item">
          <span>${ref.user_name || 'User'}</span>
          <span class="earnings">+${ref.earnings || 0} ⭐</span>
        </div>
      `
        )
        .join('');
    }

    const transHistoryEl = document.getElementById('transactionHistory');
    if (transHistoryEl && app.data.transactions?.items?.length) {
      transHistoryEl.innerHTML = app.data.transactions.items
        .map(
          tx => `
        <div class="transaction-item">
          <span>${tx.description || 'Transaction'}</span>
          <span class="amount">${tx.type === 'earn' ? '+' : '-'}${tx.amount} ⭐</span>
        </div>
      `
        )
        .join('');
    }
  }

  function renderMyItemsPage() {
    const grid = document.getElementById('myItemsGrid');
    const empty = document.getElementById('myitemsEmpty');
    const items = app.data.myItems.items;

    if (!items.length) {
      empty.style.display = 'flex';
      grid.style.display = 'none';
      return;
    }

    empty.style.display = 'none';
    grid.style.display = 'grid';
    grid.innerHTML = '';

    items.forEach(item => {
      const card = createCollectibleCard(item, 'myItems');
      card.addEventListener('click', () => showItemModal(item));
      grid.appendChild(card);
    });
  }

  function renderProfilePage() {
    const nameEl = document.getElementById('userName');
    const statsEl = document.getElementById('stats');
    const logoutBtnEl = document.getElementById('logoutBtn');
    const creatorToggleEl = document.getElementById('creatorToggle');

    if (nameEl && app.user?.username) {
      nameEl.textContent = app.user.username;
    }

    if (statsEl && app.data.profileStats) {
      statsEl.innerHTML = `
        <div class="stat-card">
          <span class="stat-label">Items Owned</span>
          <span class="stat-value">${app.data.profileStats.owned_items || 0}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">Items Created</span>
          <span class="stat-value">${app.data.profileStats.created_items || 0}</span>
        </div>
      `;
    }

    if (logoutBtnEl) {
      logoutBtnEl.addEventListener('click', logoutApp);
    }

    if (creatorToggleEl) {
      creatorToggleEl.checked = app.creator.isCreator;
      creatorToggleEl.addEventListener('change', toggleCreatorMode);
    }

    const creatorFormEl = document.getElementById('creatorForm');
    if (creatorFormEl) {
      creatorFormEl.style.display = app.creator.isCreator ? 'block' : 'none';
      creatorFormEl.addEventListener('submit', (e) => {
        e.preventDefault();
        saveCreatorProfile();
      });
    }
  }

  // ========== EVENT BINDINGS ==========
  function bindEvents() {
    // Nav tabs
    document.querySelectorAll('.nav-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const page = btn.dataset.page || btn.getAttribute('data-page');
        router.navigate(page);
        render();
        window.haptic?.light();
      });
    });

    // Filter buttons (marketplace)
    document.querySelectorAll('.filter-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const filter = btn.dataset.filter;
        if (app.ui.filters.has(filter)) {
          app.ui.filters.delete(filter);
        } else {
          app.ui.filters.add(filter);
        }
        btn.classList.toggle('active');
        renderMarketplace();
        window.haptic?.selection();
      });
    });

    // Checkout button
    document.getElementById('checkoutBtn')?.addEventListener('click', () => {
      if (!app.cart.items.length) {
        showToast('Cart is empty', 'info');
        return;
      }

      // Show payment breakdown and initiate Telegram Stars payment
      const cartTotal = app.cart.items.reduce((sum, i) => sum + (i.price || 0), 0);
      const hasReferrer = app.user?.referred_by_id ? true : false;
      const commissions = calculateCommissions(cartTotal, hasReferrer);

      const summary = `
        <div style="font-size: 28px; font-weight: bold; text-align: center; margin: var(--spacing) 0;">
          ${cartTotal} ⭐
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--spacing); margin: var(--spacing) 0;">
          <div style="background: rgba(0,136,204,0.1); padding: var(--spacing); border-radius: 8px; text-align: center;">
            <div style="font-size: 11px; color: #888;">Platform Fee (2%)</div>
            <div style="font-size: 16px; color: #ff6b6b; font-weight: bold; margin-top: 4px;">-${commissions.platformFee} ⭐</div>
          </div>
          <div style="background: rgba(100,200,50,0.1); padding: var(--spacing); border-radius: 8px; text-align: center;">
            <div style="font-size: 11px; color: #888;">You Receive</div>
            <div style="font-size: 16px; color: #64c832; font-weight: bold; margin-top: 4px;">+${cartTotal} ⭐</div>
          </div>
        </div>
        ${hasReferrer && commissions.referralCommission > 0 ? `
          <div style="background: rgba(78,205,196,0.1); padding: var(--spacing); border-radius: 8px; text-align: center; margin-top: var(--spacing);">
            <div style="font-size: 11px; color: #888;">Referral Bonus</div>
            <div style="font-size: 14px; color: #4ecdc4; font-weight: bold; margin-top: 4px;">+${commissions.referralCommission} ⭐</div>
          </div>
        ` : ''}
      `;

      showModal('Complete Purchase', summary, [
        { label: 'Pay with Stars ⭐', type: 'primary', handler: initiateTelegramStarsPayment },
        { label: 'Cancel', type: 'secondary', handler: () => { document.getElementById('itemModal').style.display = 'none'; } }
      ]);

      window.haptic?.medium();
    });

    // Modal close button
    document.getElementById('closeModal')?.addEventListener('click', () => {
      app.ui.modals.active = null;
      document.getElementById('itemModal').style.display = 'none';
    });
  }

  // ========== INITIALIZATION ==========
  async function init() {
    log('Initializing app...', 'info');

    // Telegram SDK setup
    if (window.Telegram?.WebApp) {
      tg.ready();
      tg.setHeaderColor('#0a0e27');
      tg.setBackgroundColor('#0a0e27');
      initTelegramIntegration();

      app.auth.isAuthenticated = !!tg.initDataUnsafe?.user?.id;
      if (app.auth.isAuthenticated) {
        app.user = tg.initDataUnsafe.user;
        app.auth.token = localStorage.getItem('auth_token') || tg.initData;
      }
    }

    // Bind all event listeners
    bindEvents();

    // Handle deep link (referral code)
    const startParam = tg.initDataUnsafe?.start_param;
    if (startParam?.startsWith('ref_')) {
      const refCode = startParam.replace('ref_', '');
      await apiCall('/referrals/apply', {
        method: 'POST',
        body: { referral_code: refCode },
      });
      showToast('Referral code applied! 🎉', 'success');
    }

    // Load initial page
    router.navigate('market');
    await render();

    log('App ready!', 'success');
  }

  // Start app on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
