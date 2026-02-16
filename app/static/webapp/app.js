/**
 * NFT Platform Web App - Production Ready
 * Optimized for reliability, no hanging issues
 */

(function() {
  'use strict';

  console.log('🚀 NFT Platform App Starting...');

  // ========== DOM REFERENCES ==========
  const status = document.getElementById('status');
  const statusText = document.getElementById('statusText');
  const statusSpinner = document.getElementById('statusSpinner');
  const modal = document.getElementById('modal');
  const modalOverlay = document.getElementById('modalOverlay');

  // Check DOM is ready
  if (!status || !modal) {
    console.error('❌ Required DOM elements not found');
    document.body.innerHTML = '<h1>Error: Page failed to load. Please refresh.</h1>';
    return;
  }

  // ========== STATE ==========
  const state = {
    user: null,
    wallets: [],
    nfts: [],
    listings: [],
    marketplaceListings: [],
    myListings: []
  };

  const API_BASE = '/api/v1';

  // ========== UTILITIES ==========
  function log(msg, type = 'info') {
    const emoji = { info: 'ℹ️', error: '❌', success: '✅', warn: '⚠️' };
    console.log(`${emoji[type]} ${msg}`);
  }

  function showStatus(msg, type = 'info') {
    log(msg, type);
    if (!statusText) return;
    
    statusText.textContent = msg;
    status.className = `status-alert ${type}`;
    status.style.display = 'block';
    
    if (statusSpinner) {
      statusSpinner.style.display = ['info', 'loading'].includes(type) ? 'inline-block' : 'none';
    }

    if (!['info', 'loading'].includes(type)) {
      setTimeout(() => {
        status.style.display = 'none';
      }, 4000);
    }
  }

  function closeModal() {
    if (modal) modal.style.display = 'none';
  }

  function showModal(title, html) {
    if (!modal) return;
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    if (modalTitle) modalTitle.textContent = title;
    if (modalBody) modalBody.innerHTML = html;
    modal.style.display = 'flex';
  }

  function truncate(str, len = 20) {
    if (!str) return '—';
    return str.length > len ? str.slice(0, len - 3) + '...' : str;
  }

  function formatAddr(addr) {
    if (!addr) return '—';
    return addr.slice(0, 6) + '...' + addr.slice(-4);
  }

  // ========== API CALLS ==========
  const API = {
    async fetch(endpoint, options = {}) {
      const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
      try {
        log(`Fetching: ${endpoint}`);
        const response = await fetch(url, {
          method: options.method || 'GET',
          headers: {
            'Content-Type': 'application/json',
            ...options.headers
          },
          body: options.body ? JSON.stringify(options.body) : undefined,
          timeout: 15000
        });

        if (!response.ok) {
          const text = await response.text();
          throw new Error(`HTTP ${response.status}: ${text.slice(0, 100)}`);
        }

        const data = await response.json();
        log(`Response from ${endpoint}: OK`);
        return data;
      } catch (err) {
        log(`API Error: ${err.message}`, 'error');
        throw err;
      }
    },

    async initSession(initData) {
      return this.fetch(`/telegram/web-app/init?init_data=${encodeURIComponent(initData)}`);
    },

    async getDashboardData(userId) {
      return this.fetch(`/telegram/web-app/dashboard-data?user_id=${userId}`);
    },

    async getMarketplaceListings(limit = 50) {
      return this.fetch(`/telegram/web-app/marketplace/listings?limit=${limit}`);
    },

    async getMyListings(userId) {
      return this.fetch(`/telegram/web-app/marketplace/mylistings?user_id=${userId}`);
    },

    async createWallet(userId, blockchain) {
      return this.fetch('/wallets/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ user_id: userId, blockchain }).toString()
      });
    },

    async importWallet(userId, blockchain, address) {
      return this.fetch(`/wallets/import?user_id=${userId}`, {
        method: 'POST',
        body: { blockchain, address, name: `${blockchain} Imported` }
      });
    },

    async mintNFT(userId, walletId, nftName, nftDescription) {
      return this.fetch('/telegram/web-app/mint', {
        method: 'POST',
        body: { user_id: userId, wallet_id: walletId, nft_name: nftName, nft_description: nftDescription }
      });
    },

    async listNFT(userId, nftId, price, currency = 'ETH') {
      return this.fetch('/telegram/web-app/list-nft', {
        method: 'POST',
        body: { user_id: userId, nft_id: nftId, price: parseFloat(price), currency }
      });
    },

    async transferNFT(userId, nftId, toAddress) {
      return this.fetch('/telegram/web-app/transfer', {
        method: 'POST',
        body: { user_id: userId, nft_id: nftId, to_address: toAddress }
      });
    },

    async burnNFT(userId, nftId) {
      return this.fetch('/telegram/web-app/burn', {
        method: 'POST',
        body: { user_id: userId, nft_id: nftId }
      });
    },

    async setPrimaryWallet(userId, walletId) {
      return this.fetch('/telegram/web-app/set-primary', {
        method: 'POST',
        body: { user_id: userId, wallet_id: walletId }
      });
    },

    async makeOffer(userId, listingId, offerPrice) {
      return this.fetch('/telegram/web-app/make-offer', {
        method: 'POST',
        body: { user_id: userId, listing_id: listingId, offer_price: parseFloat(offerPrice) }
      });
    },

    async cancelListing(userId, listingId) {
      return this.fetch('/telegram/web-app/cancel-listing', {
        method: 'POST',
        body: { user_id: userId, listing_id: listingId }
      });
    }
  };

  // ========== UI UPDATES ==========
  function updateUserInfo() {
    const userInfo = document.getElementById('userInfo');
    if (!userInfo) return;
    const name = state.user?.first_name || state.user?.telegram_username || 'User';
    userInfo.innerHTML = `<strong>${truncate(name, 15)}</strong><small>@${truncate(state.user?.telegram_username || 'user', 12)}</small>`;
  }

  function updateDashboard() {
    const portfolioValue = state.nfts.length * 100;
    const safeSet = (id, value) => {
      const el = document.getElementById(id);
      if (el) el.textContent = value;
    };

    safeSet('totalWallets', state.wallets.length);
    safeSet('totalNfts', state.nfts.length);
    safeSet('totalListings', state.listings.filter(l => l.active).length);
    safeSet('portfolioValue', '$' + portfolioValue.toFixed(2));
  }

  function updateWalletsList() {
    const container = document.getElementById('walletsList');
    if (!container) return;
    
    if (!state.wallets.length) {
      container.innerHTML = '<p class="muted">No wallets yet. Create one to get started.</p>';
      return;
    }

    container.innerHTML = state.wallets.map(w => `
      <div class="card wallet-card">
        <div class="wallet-blockchain">
          <strong>${w.blockchain?.toUpperCase() || 'Wallet'}</strong>
          ${w.is_primary ? '<span class="blockchain-badge">Primary</span>' : ''}
        </div>
        <div class="wallet-address">${formatAddr(w.address)}</div>
        <div class="wallet-actions">
          <button class="btn btn-secondary" onclick="window.showWalletDetails('${w.id}')">Details</button>
        </div>
      </div>
    `).join('');
  }

  function updateNftsList() {
    const container = document.getElementById('nftList');
    if (!container) return;

    if (!state.nfts.length) {
      container.innerHTML = '<p class="muted">No NFTs yet. Mint one to get started.</p>';
      return;
    }

    container.innerHTML = state.nfts.map(nft => `
      <div class="card nft-card">
        <div class="nft-image">
          ${nft.image_url ? `<img src="${nft.image_url}" alt="${nft.name}" loading="lazy" onerror="this.style.display='none'">` : '<div style="background:var(--bg-base);height:200px;display:flex;align-items:center;justify-content:center;">No Image</div>'}
        </div>
        <div class="nft-content">
          <div class="nft-name">${truncate(nft.name, 25)}</div>
          <div class="nft-price">NFT</div>
        </div>
      </div>
    `).join('');
  }

  function updateMarketplace() {
    const listings = document.getElementById('marketplaceListings');
    if (!listings) return;

    if (!state.marketplaceListings.length) {
      listings.innerHTML = '<p class="muted">No listings available</p>';
      return;
    }

    listings.innerHTML = state.marketplaceListings.map(l => `
      <div class="card nft-card">
        <div class="nft-image">
          ${l.image_url ? `<img src="${l.image_url}" alt="NFT" loading="lazy" onerror="this.style.display='none'">` : '<div style="background:var(--bg-base);height:200px;display:flex;align-items:center;justify-content:center;">Listing</div>'}
        </div>
        <div class="nft-content">
          <div class="nft-name">${truncate(l.nft_name || 'NFT', 25)}</div>
          <div class="nft-price">$${l.price?.toFixed(2) || '0.00'}</div>
          <button class="btn btn-primary" style="width:100%;margin-top:8px;" onclick="window.viewListing('${l.id}')">View</button>
        </div>
      </div>
    `).join('');
  }

  // ========== PAGE NAVIGATION ==========
  function switchPage(pageName) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

    const page = document.getElementById(`${pageName}-page`);
    if (page) page.classList.add('active');

    const navItem = document.querySelector(`[data-page="${pageName}"]`);
    if (navItem) navItem.classList.add('active');

    const titles = {
      dashboard: 'Dashboard',
      wallets: 'Wallet Management',
      nfts: 'My NFT Collection',
      mint: 'Create NFT',
      marketplace: 'Marketplace',
      profile: 'My Profile'
    };
    const pageTitle = document.getElementById('pageTitle');
    if (pageTitle) pageTitle.textContent = titles[pageName] || 'NFT Platform';
  }

  // ========== MODAL HANDLERS ==========
  window.showWalletDetails = function(walletId) {
    const wallet = state.wallets.find(w => w.id === walletId);
    if (!wallet) return;
    showModal('Wallet Details', `
      <div class="profile-section">
        <div class="profile-item"><span>Blockchain:</span><strong>${wallet.blockchain?.toUpperCase()}</strong></div>
        <div class="profile-item"><span>Address:</span><code style="word-break:break-all;">${wallet.address}</code></div>
        <div class="profile-item"><span>Primary:</span><strong>${wallet.is_primary ? 'Yes' : 'No'}</strong></div>
      </div>
      ${!wallet.is_primary ? `<button class="btn btn-secondary btn-block" onclick="window.setPrimary('${wallet.id}')">Set as Primary</button>` : ''}
      <button class="btn btn-secondary btn-block" style="margin-top:8px;" onclick="window.closeModal()">Close</button>
    `);
  };

  window.viewListing = function(listingId) {
    const listing = state.marketplaceListings.find(l => l.id === listingId);
    if (!listing) return;
    showModal('NFT Details', `
      <div class="profile-section">
        <div class="profile-item"><span>NFT:</span><strong>${listing.nft_name || 'Unknown'}</strong></div>
        <div class="profile-item"><span>Price:</span><strong>$${listing.price?.toFixed(2) || '0.00'}</strong></div>
        <div class="profile-item"><span>Currency:</span><strong>${listing.currency || 'ETH'}</strong></div>
      </div>
      <button class="btn btn-primary btn-block" onclick="window.makeOfferPrompt('${listing.id}')">Make Offer</button>
      <button class="btn btn-secondary btn-block" style="margin-top:8px;" onclick="window.closeModal()">Close</button>
    `);
  };

  window.createWalletModal = function() {
    showModal('Create New Wallet', `
      <div class="form-group">
        <label>Select Blockchain</label>
        <select id="chainSelect" class="input-select">
          <option value="ethereum">Ethereum</option>
          <option value="polygon">Polygon</option>
          <option value="solana">Solana</option>
          <option value="ton">TON</option>
        </select>
      </div>
      <button class="btn btn-primary btn-block" onclick="window.submitCreateWallet()">Create</button>
    `);
  };

  window.importWalletModal = function() {
    showModal('Import Wallet', `
      <div class="form-group">
        <label>Wallet Address</label>
        <input type="text" id="importAddr" placeholder="0x..." class="input-text">
      </div>
      <div class="form-group">
        <label>Blockchain</label>
        <select id="importChain" class="input-select">
          <option value="ethereum">Ethereum</option>
          <option value="polygon">Polygon</option>
          <option value="solana">Solana</option>
          <option value="ton">TON</option>
        </select>
      </div>
      <button class="btn btn-primary btn-block" onclick="window.submitImportWallet()">Import</button>
    `);
  };

  // ========== ACTION HANDLERS ==========
  window.submitCreateWallet = async function() {
    const chain = document.getElementById('chainSelect')?.value;
    if (!chain || !state.user) return;
    
    try {
      showStatus(`Creating ${chain} wallet...`, 'loading');
      await API.createWallet(state.user.id, chain);
      showStatus('Wallet created!', 'success');
      closeModal();
      loadDashboard();
    } catch (err) {
      showStatus(`Error: ${err.message}`, 'error');
    }
  };

  window.submitImportWallet = async function() {
    const addr = document.getElementById('importAddr')?.value;
    const chain = document.getElementById('importChain')?.value;
    if (!addr || !chain || !state.user) return;

    try {
      showStatus('Importing wallet...', 'loading');
      await API.importWallet(state.user.id, chain, addr);
      showStatus('Wallet imported!', 'success');
      closeModal();
      loadDashboard();
    } catch (err) {
      showStatus(`Error: ${err.message}`, 'error');
    }
  };

  window.setPrimary = async function(walletId) {
    if (!state.user) return;
    try {
      showStatus('Setting primary wallet...', 'loading');
      await API.setPrimaryWallet(state.user.id, walletId);
      showStatus('Primary wallet updated!', 'success');
      closeModal();
      loadDashboard();
    } catch (err) {
      showStatus(`Error: ${err.message}`, 'error');
    }
  };

  window.closeModal = closeModal;

  // ========== LOAD DATA ==========
  async function loadDashboard() {
    try {
      if (!state.user) {
        showStatus('Error: User not authenticated', 'error');
        return;
      }
      
      showStatus('Loading data...', 'loading');
      log(`Loading dashboard for user: ${state.user.telegram_username} (${state.user.id.slice(0, 8)}...)`);

      const dashboardData = await API.getDashboardData(state.user.id);
      log(`Dashboard response received: success=${dashboardData?.success}`);
      log(`  Wallets: ${dashboardData?.wallets?.length || 0}`);
      log(`  NFTs: ${dashboardData?.nfts?.length || 0}`);
      log(`  Own Listings: ${dashboardData?.listings?.length || 0}`);

      if (!dashboardData?.success) {
        throw new Error('Invalid response from server');
      }

      state.wallets = dashboardData.wallets || [];
      state.nfts = dashboardData.nfts || [];
      state.listings = dashboardData.listings || [];

      log(`State updated: wallets=${state.wallets.length}, nfts=${state.nfts.length}, listings=${state.listings.length}`);

      try {
        const marketData = await API.getMarketplaceListings(50);
        state.marketplaceListings = marketData?.listings || [];
        log(`Marketplace listings loaded: ${state.marketplaceListings.length}`);
      } catch (e) {
        log(`Marketplace load failed: ${e.message}`, 'warn');
        state.marketplaceListings = [];
      }

      updateDashboard();
      updateWalletsList();
      updateNftsList();
      updateMarketplace();

      showStatus('Data loaded!', 'success');
      setTimeout(() => {
        if (status) status.style.display = 'none';
      }, 2000);
    } catch (err) {
      log(`Load failed: ${err.message}`, 'error');
      showStatus(`Error: ${err.message}`, 'error');
    }
  }

  // ========== EVENTS ==========
  function setupEvents() {
    // Navigation
    document.querySelectorAll('.nav-item').forEach(item => {
      item.addEventListener('click', (e) => {
        e.preventDefault();
        switchPage(item.dataset.page);
      });
    });

    // Modal
    if (modalOverlay) {
      modalOverlay.addEventListener('click', closeModal);
    }
    const closeBtn = document.getElementById('closeModal');
    if (closeBtn) {
      closeBtn.addEventListener('click', closeModal);
    }

    // Wallet buttons
    const createWalletBtn = document.getElementById('createWalletBtn');
    const importWalletBtn = document.getElementById('importWalletBtn');
    if (createWalletBtn) createWalletBtn.addEventListener('click', window.createWalletModal);
    if (importWalletBtn) importWalletBtn.addEventListener('click', window.importWalletModal);

    // Mint button
    const mintBtn = document.getElementById('mintNftBtn');
    if (mintBtn) {
      mintBtn.addEventListener('click', async () => {
        const name = document.getElementById('mintName')?.value;
        const desc = document.getElementById('mintDesc')?.value;
        const walletId = document.getElementById('mintWalletSelect')?.value;

        if (!name || !desc || !walletId || !state.user) {
          showStatus('Please fill all fields', 'error');
          return;
        }

        try {
          showStatus('Creating NFT...', 'loading');
          await API.mintNFT(state.user.id, walletId, name, desc);
          showStatus('NFT created!', 'success');
          document.getElementById('mintName').value = '';
          document.getElementById('mintDesc').value = '';
          loadDashboard();
        } catch (err) {
          showStatus(`Error: ${err.message}`, 'error');
        }
      });
    }

    // Populate mint wallet dropdown
    const mintSelect = document.getElementById('mintWalletSelect');
    if (mintSelect && state.wallets.length) {
      mintSelect.innerHTML = state.wallets.map(w => 
        `<option value="${w.id}">${w.blockchain?.toUpperCase()} - ${formatAddr(w.address)}</option>`
      ).join('');
    }

    // Marketplace tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const tab = btn.dataset.tab;
        if (tab === 'listings') {
          const el = document.getElementById('marketplaceListings');
          const el2 = document.getElementById('myListings');
          if (el) el.style.display = 'grid';
          if (el2) el2.style.display = 'none';
        } else {
          const el = document.getElementById('marketplaceListings');
          const el2 = document.getElementById('myListings');
          if (el) el.style.display = 'none';
          if (el2) el2.style.display = 'grid';
        }
      });
    });
  }

  // ========== INIT ==========
  async function init() {
    try {
      showStatus('Starting app...', 'loading');
      log('App init started');

      // Development mode: Check for test user ID in URL
      const urlParams = new URLSearchParams(window.location.search);
      const testUserId = urlParams.get('user_id');
      
      let authResponse = null;

      if (testUserId) {
        // Development/test mode - use provided user ID
        log('📝 Development mode: Using test user ID from URL', 'info');
        authResponse = {
          success: true,
          user: {
            id: testUserId,
            telegram_id: 999999,
            telegram_username: 'test_user',
            first_name: 'Test',
            last_name: 'User'
          }
        };
      } else if (window.Telegram?.WebApp) {
        // Production mode - use Telegram
        log('📱 Telegram mode: Using Telegram WebApp', 'info');
        window.Telegram.WebApp.ready?.();

        const initData = window.Telegram?.WebApp?.initData;
        if (!initData) {
          showStatus('Error: Telegram auth not available', 'error');
          return;
        }

        // Auth via Telegram
        showStatus('Authenticating...', 'loading');
        authResponse = await API.initSession(initData);
      } else {
        // No Telegram and no test mode
        showStatus('Error: Not running in Telegram. Use ?user_id=UUID for testing', 'error');
        log('How to test: Add ?user_id=YOUR_USER_UUID_HERE to the URL', 'warn');
        return;
      }

      if (!authResponse?.success) {
        throw new Error(authResponse?.error || 'Auth failed');
      }

      state.user = authResponse.user;
      log(`User authenticated: ${state.user.telegram_username} (${state.user.id.slice(0, 8)}...)`);

      // Setup UI
      updateUserInfo();
      setupEvents();

      // Load data
      await loadDashboard();

      showStatus('Ready!', 'success');
    } catch (err) {
      log(`Init error: ${err.message}`, 'error');
      showStatus(`Error: ${err.message}`, 'error');
    }
  }

  // Start when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
