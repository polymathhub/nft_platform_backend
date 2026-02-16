/**
 * NFT Platform Web App - Production Ready
 * Telegram WebApp Integration with Full Backend Support
 * Mobile-First Responsive Design
 */

(function() {
  'use strict';

  console.log('[NFT Platform] Web App Starting...');

  // ========== DOM REFERENCES ==========
  const status = document.getElementById('status');
  const statusText = document.getElementById('statusText');
  const statusSpinner = document.getElementById('statusSpinner');
  const modal = document.getElementById('modal');
  const modalOverlay = document.getElementById('modalOverlay');

  if (!status || !modal) {
    console.error('[ERROR] Required DOM elements not found');
    document.body.innerHTML = '<h1>Error: Page failed to load. Please refresh.</h1>';
    return;
  }

  // ========== CONFIGURATION ==========
  const API_BASE = '/api/v1';
  const API_RETRY_ATTEMPTS = 3;
  const API_RETRY_DELAY = 500; // milliseconds
  const API_TIMEOUT = 20000; // milliseconds

  // ========== STATE ==========
  const state = {
    user: null,
    wallets: [],
    nfts: [],
    listings: [],
    marketplaceListings: []
  };

  // ========== UTILITIES ==========
  function log(msg, type = 'info') {
    const prefix = { info: '[INFO]', error: '[ERROR]', success: '[OK]', warn: '[WARN]' };
    console.log(`${prefix[type]} ${msg}`);
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
        if (status) status.style.display = 'none';
      }, 5000);
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
    if (!str) return '-';
    return str.length > len ? str.slice(0, len - 3) + '...' : str;
  }

  function formatAddr(addr) {
    if (!addr) return '-';
    return addr.slice(0, 6) + '...' + addr.slice(-4);
  }

  function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // ========== API CALLS WITH RETRY LOGIC ==========
  const API = {
    async fetch(endpoint, options = {}, attempt = 1) {
      const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
      let timeoutId;
      
      try {
        log(`[Attempt ${attempt}] Fetching: ${endpoint}`);
        
        const controller = new AbortController();
        timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);

        const response = await fetch(url, {
          method: options.method || 'GET',
          headers: {
            'Content-Type': 'application/json',
            ...options.headers
          },
          body: options.body ? JSON.stringify(options.body) : undefined,
          signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          const text = await response.text();
          const errorMsg = text.slice(0, 200);
          throw new Error(`HTTP ${response.status}: ${errorMsg}`);
        }

        const data = await response.json();
        log(`Response OK: ${endpoint}`, 'success');
        return data;
      } catch (err) {
        if (timeoutId) clearTimeout(timeoutId);
        
        if (attempt < API_RETRY_ATTEMPTS && this.shouldRetry(err)) {
          log(`Retrying ${attempt}/${API_RETRY_ATTEMPTS}: ${endpoint}`, 'warn');
          await sleep(API_RETRY_DELAY * attempt);
          return this.fetch(endpoint, options, attempt + 1);
        }
        
        log(`Failed: ${err.message}`, 'error');
        throw err;
      }
    },

    shouldRetry(err) {
      const msg = err.message;
      return msg.includes('Failed to fetch') || 
             msg.includes('timeout') || 
             msg.includes('NetworkError') ||
             msg.includes('AbortError');
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
      return this.fetch('/telegram/web-app/create-wallet', {
        method: 'POST',
        body: { user_id: userId, blockchain }
      });
    },

    async importWallet(userId, blockchain, address) {
      return this.fetch(`/telegram/web-app/import-wallet?user_id=${userId}`, {
        method: 'POST',
        body: { blockchain, address, name: `${blockchain} Wallet` }
      });
    },

    async mintNFT(userId, walletId, nftName, nftDescription, imageUrl = null) {
      return this.fetch('/telegram/web-app/mint', {
        method: 'POST',
        body: { user_id: userId, wallet_id: walletId, nft_name: nftName, nft_description: nftDescription, image_url: imageUrl }
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
    const name = state.user?.full_name || state.user?.telegram_username || 'User';
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
        showStatus('User not authenticated', 'error');
        return;
      }
      
      showStatus('Loading your dashboard data...', 'loading');
      log(`Fetching dashboard for: ${state.user.telegram_username}`);

      let dashboardData = null;
      try {
        dashboardData = await API.getDashboardData(state.user.id);
      } catch (err) {
        log(`Dashboard fetch error: ${err.message}`, 'error');
        dashboardData = { success: true, wallets: [], nfts: [], listings: [] };
      }

      if (!dashboardData?.success) {
        log('Invalid dashboard response, using empty state', 'warn');
        dashboardData = { success: true, wallets: [], nfts: [], listings: [] };
      }

      state.wallets = dashboardData.wallets || [];
      state.nfts = dashboardData.nfts || [];
      state.listings = dashboardData.listings || [];

      log(`Data loaded: ${state.wallets.length} wallets, ${state.nfts.length} NFTs, ${state.listings.length} listings`);

      try {
        const marketData = await API.getMarketplaceListings(50);
        state.marketplaceListings = marketData?.listings || [];
        log(`Marketplace loaded: ${state.marketplaceListings.length} listings`);
      } catch (err) {
        log(`Marketplace load failed: ${err.message}`, 'warn');
        state.marketplaceListings = [];
      }

      updateDashboard();
      updateWalletsList();
      updateNftsList();
      updateMarketplace();

      showStatus('Dashboard ready!', 'success');
      log('Dashboard fully loaded');

      setTimeout(() => {
        if (status) status.style.display = 'none';
      }, 2000);

    } catch (err) {
      log(`Dashboard load error: ${err.message}`, 'error');
      showStatus(`${err.message}`, 'error');
      
      updateDashboard();
      updateWalletsList();
      updateNftsList();
      updateMarketplace();
    }
  }

  // ========== EVENTS ==========
  function setupEvents() {
    document.querySelectorAll('.nav-item').forEach(item => {
      item.addEventListener('click', (e) => {
        e.preventDefault();
        switchPage(item.dataset.page);
      });
    });

    if (modalOverlay) {
      modalOverlay.addEventListener('click', closeModal);
    }
    const closeBtn = document.getElementById('closeModal');
    if (closeBtn) {
      closeBtn.addEventListener('click', closeModal);
    }

    const createWalletBtn = document.getElementById('createWalletBtn');
    const importWalletBtn = document.getElementById('importWalletBtn');
    if (createWalletBtn) createWalletBtn.addEventListener('click', window.createWalletModal);
    if (importWalletBtn) importWalletBtn.addEventListener('click', window.importWalletModal);

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

    const mintSelect = document.getElementById('mintWalletSelect');
    if (mintSelect && state.wallets.length) {
      mintSelect.innerHTML = state.wallets.map(w => 
        `<option value="${w.id}">${w.blockchain?.toUpperCase()} - ${formatAddr(w.address)}</option>`
      ).join('');
    }

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
      showStatus('Initializing NFT Dashboard...', 'loading');
      log('App initialization started');

      const hasTelegram = typeof window.Telegram !== 'undefined' && window.Telegram?.WebApp;
      
      log(`Telegram SDK available: ${hasTelegram}`);

      let authResponse = null;

      if (hasTelegram) {
        log('Telegram mode: Using Telegram WebApp SDK');

        try {
          window.Telegram.WebApp.ready?.();
          window.Telegram.WebApp.expand?.();
          
          const initData = window.Telegram?.WebApp?.initData;
          
          if (!initData) {
            throw new Error('Telegram WebApp not initialized properly');
          }

          log(`Telegram initData received (${initData.length} bytes)`);
          showStatus('Authenticating with Telegram...', 'loading');
          
          authResponse = await API.initSession(initData);

          if (!authResponse?.success) {
            throw new Error(authResponse?.error || 'Telegram authentication failed');
          }

          log(`Telegram authenticated: ${authResponse.user.telegram_username}`);
        } catch (err) {
          log(`Telegram auth failed: ${err.message}`, 'error');
          showStatus(`Authentication failed: ${err.message}`, 'error');
          return;
        }
      } else {
        log('Telegram SDK not detected', 'warn');
        showStatus('Please open this app inside Telegram', 'error');
        return;
      }

      if (!authResponse?.success || !authResponse?.user) {
        throw new Error('Invalid authentication response');
      }

      state.user = authResponse.user;
      log(`User authenticated: ${state.user.telegram_username} (${state.user.id.slice(0, 8)}...)`);

      updateUserInfo();
      setupEvents();

      await loadDashboard();

      log('App initialization complete');
      showStatus('Ready!', 'success');

    } catch (err) {
      log(`Init error: ${err.message}`, 'error');
      showStatus(`${err.message}`, 'error');
      
      setTimeout(() => {
        showStatus('Need help? Check browser console (F12)', 'info');
      }, 3000);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
