/**
 * NFT Platform - Complete Web App v2
 * Production-ready Telegram WebApp with full backend integration
 * All features: Wallets, NFTs, Marketplace, Minting, Transfers
 */

(() => {
  'use strict';

  // ========== DOM ELEMENTS ==========
  const dom = {
    app: document.getElementById('app'),
    sidebar: document.getElementById('sidebar'),
    mainContent: document.getElementById('mainContent'),
    pages: {},
    status: document.getElementById('status'),
    statusText: document.getElementById('statusText'),
    statusSpinner: document.getElementById('statusSpinner'),
    userInfo: document.getElementById('userInfo'),
    modal: document.getElementById('modal'),
    modalTitle: document.getElementById('modalTitle'),
    modalBody: document.getElementById('modalBody'),
    modalOverlay: document.getElementById('modalOverlay'),
  };

  // Get all page elements
  document.querySelectorAll('[data-page]').forEach(el => {
    dom.pages[el.dataset.page] = el;
  });

  // ========== CONFIGURATION ==========
  const CONFIG = {
    API_BASE: '/api/v1/telegram',
    RETRY_ATTEMPTS: 3,
    RETRY_DELAY: 500,
    TIMEOUT: 20000,
  };

  // ========== STATE ==========
  const state = {
    user: null,
    wallets: [],
    nfts: [],
    listings: [],
    currentPage: 'dashboard',
    initData: null,
  };

  // ========== UTILITIES ==========
  function log(msg, type = 'log') {
    const prefix = { log: '[INFO]', error: '[ERROR]', warn: '[WARN]' };
    console.log(`${prefix[type] || '[' + type.toUpperCase() + ']'} ${msg}`);
  }

  function showStatus(msg, type = 'info') {
    log(msg, type === 'error' ? 'error' : 'log');
    if (!dom.statusText) return;
    
    dom.statusText.textContent = msg;
    dom.status.className = `status-alert ${type}`;
    dom.status.style.display = 'block';
    
    if (dom.statusSpinner) {
      dom.statusSpinner.style.display = ['info', 'loading'].includes(type) ? 'block' : 'none';
    }

    if (type === 'success' || type === 'error') {
      setTimeout(() => {
        if (dom.status) dom.status.style.display = 'none';
      }, 4000);
    }
  }

  function showModal(title, html, buttons = []) {
    if (!dom.modal) return;
    if (dom.modalTitle) dom.modalTitle.textContent = title;
    if (dom.modalBody) dom.modalBody.innerHTML = html;
    
    // Add buttons if provided
    let buttonsHtml = '';
    if (buttons.length) {
      buttonsHtml = `<div style="display:flex;gap:10px;margin-top:20px;">` +
        buttons.map(btn => `<button onclick="${btn.action}" class="btn ${btn.class || 'btn-primary'}" style="flex:1;">${btn.label}</button>`).join('') +
        `</div>`;
      if (dom.modalBody) dom.modalBody.innerHTML += buttonsHtml;
    }
    
    dom.modal.style.display = 'flex';
  }

  function closeModal() {
    if (dom.modal) dom.modal.style.display = 'none';
  }

  // ========== IMAGE PROTECTION ==========
  /**
   * Protect images from being copied, downloaded, or saved
   * Disables: right-click, drag-and-drop, keyboard shortcuts (Ctrl+S, Ctrl+C)
   */
  function protectImage(element) {
    if (!element) return;

    // Disable right-click context menu
    element.addEventListener('contextmenu', (e) => {
      e.preventDefault();
      e.stopPropagation();
      return false;
    });

    // Disable drag and drop
    element.addEventListener('dragstart', (e) => {
      e.preventDefault();
      e.stopPropagation();
      return false;
    });

    // Disable selection
    element.addEventListener('selectstart', (e) => {
      e.preventDefault();
      return false;
    });

    // Disable pointer events to prevent saving
    if (element.tagName === 'IMG') {
      element.style.pointerEvents = 'none';
      element.style.userSelect = 'none';
      element.style.WebkitUserSelect = 'none';
    }
  }

  /**
   * Protect all NFT images on the current page
   */
  function protectAllImages() {
    // Protect all img elements with NFT images
    document.querySelectorAll('img[alt*="NFT"], img[alt*="nft"], img[src*="image"]').forEach(img => {
      protectImage(img);
    });

    // Protect background images (div elements with background-image style)
    document.querySelectorAll('[style*="background-image"]').forEach(div => {
      protectImage(div);
      // Additional protection for background images
      div.style.userSelect = 'none';
      div.style.WebkitUserSelect = 'none';
    });
  }

  /**
   * Add global keyboard shortcut protection
   */
  function protectKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
      // Block Ctrl+S (Save), Ctrl+C (Copy), Ctrl+A (Select All) on images
      if ((e.ctrlKey || e.metaKey) && (e.key === 's' || e.key === 'c')) {
        // Only block if the event target or any parent is an image-related element
        let target = e.target;
        let isImageElement = false;
        
        while (target && target !== document) {
          if (target.tagName === 'IMG' || 
              target.style?.backgroundImage || 
              target.className?.includes('nft') ||
              target.className?.includes('image')) {
            isImageElement = true;
            break;
          }
          target = target.parentElement;
        }

        if (isImageElement) {
          e.preventDefault();
          e.stopPropagation();
          return false;
        }
      }
    }, true);

    // Block Print Screen / Prt Sc
    document.addEventListener('keydown', (e) => {
      if (e.key === 'PrintScreen') {
        e.preventDefault();
        return false;
      }
    });
  }

  /**
   * Apply additional CSS protections
   */
  function applyImageProtectionStyles() {
    // Check if style tag already exists
    if (document.getElementById('nft-image-protection-styles')) {
      return;
    }

    const style = document.createElement('style');
    style.id = 'nft-image-protection-styles';
    style.textContent = `
      /* NFT Image Protection */
      img[alt*="NFT"],
      img[alt*="nft"],
      img[src*="image"],
      [style*="background-image"] {
        user-select: none !important;
        -webkit-user-select: none !important;
        -moz-user-select: none !important;
        -ms-user-select: none !important;
        pointer-events: none !important;
        -webkit-touch-callout: none !important;
        -webkit-user-drag: none !important;
      }

      /* Prevent drag on NFT images */
      img {
        -webkit-user-drag: none;
        -khtml-user-drag: none;
        -moz-user-drag: none;
        -o-user-drag: none;
        user-drag: none;
      }

      /* Disable text selection in NFT containers */
      .card img,
      [class*="nft"] img {
        -webkit-user-select: none;
        user-select: none;
      }
    `;
    document.head.appendChild(style);
  }

  function switchPage(pageName) {
    // Hide all pages
    Object.values(dom.pages).forEach(page => {
      if (page) page.style.display = 'none';
    });
    
    // Show selected page
    if (dom.pages[pageName]) {
      dom.pages[pageName].style.display = 'block';
      state.currentPage = pageName;
      
      // Update nav
      document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.page === pageName) item.classList.add('active');
      });
      
      // Update page title
      const titles = {
        dashboard: 'Dashboard',
        wallets: 'My Wallets',
        nfts: 'My NFTs',
        mint: 'Create NFT',
        marketplace: 'Marketplace',
        profile: 'Profile',
        help: 'Help & Support',
      };
      document.getElementById('pageTitle').textContent = titles[pageName] || 'NFT Platform';
      
      // Load page data
      loadPageData(pageName);
      
      // Apply image protection
      protectAllImages();
    }
  }

  async function loadPageData(pageName) {
    try {
      switch(pageName) {
        case 'dashboard': await updateDashboard(); break;
        case 'wallets': await updateWalletsList(); break;
        case 'nfts': await updateNftList(); break;
        case 'marketplace': await updateMarketplaceList(); break;
        case 'profile': await updateProfilePage(); break;
      }
      // Protect images after loading page data
      setTimeout(protectAllImages, 100);
    } catch (err) {
      log(`Error loading ${pageName}: ${err.message}`, 'error');
    }
  }

  // ========== API LAYER ==========
  const API = {
    async _fetch(endpoint, options = {}, attempt = 1) {
      const url = `${CONFIG.API_BASE}${endpoint}`;
      const method = options.method || 'GET';
      
      try {
        log(`[Attempt ${attempt}] ${method} ${url}`);
        
        // MANDATORY: Inject Telegram init_data for ALL POST/PUT requests
        // This MUST be present for Telegram signature verification
        if (method !== 'GET') {
          const body = Object.assign({}, options.body || {});
          
          // Get fresh initData from WebApp SDK or state
          let initData = state.initData;
          if (!initData && typeof window.Telegram !== 'undefined' && window.Telegram.WebApp) {
            initData = window.Telegram.WebApp.initData;
          }
          
          // Always set init_data if available (required for auth)
          if (initData) {
            body.init_data = initData;
          } else {
            log(`WARNING: No init_data available for POST to ${endpoint}`, 'warn');
          }
          
          // Always set user_id if available
          if (state.user && state.user.id) {
            body.user_id = state.user.id;
          }
          
          // Validate request payload can be serialized
          try {
            options.body = body;
          } catch (e) {
            log(`Error preparing request body: ${e.message}`, 'error');
            throw e;
          }
        }

        let fetchOptions = {
          method,
          headers: {
            'Content-Type': 'application/json',
            Accept: 'application/json',
            ...options.headers,
          },
          credentials: 'same-origin',
        };

        // Serialize body with error handling
        if (options.body) {
          try {
            fetchOptions.body = JSON.stringify(options.body);
          } catch (e) {
            log(`JSON serialization failed: ${e.message}`, 'error');
            throw new Error(`Invalid request body: ${e.message}`);
          }
        }
        
        const response = await fetch(url, fetchOptions);
        
        // Debug response status
        if (!response.ok) {
          log(`[${response.status}] ${method} ${endpoint} failed`, 'warn');
        }
        
        // Fail fast on 401/403 - auth errors
        if (response.status === 401 || response.status === 403) {
          log(`${method} ${endpoint} auth failed: ${response.status}`, 'error');
          throw new Error('Authentication failed - Telegram init_data required');
        }
        
        let data;
        try {
          data = await response.json();
        } catch (e) {
          log(`Invalid JSON response from server: ${response.status}`, 'error');
          throw new Error(`Server error: ${response.status}`);
        }
        
        if (!response.ok) {
          log(`${method} ${endpoint} failed: ${response.status} - ${JSON.stringify(data)}`, 'error');
          if (attempt < CONFIG.RETRY_ATTEMPTS) {
            await new Promise(r => setTimeout(r, CONFIG.RETRY_DELAY * attempt));
            return this._fetch(endpoint, options, attempt + 1);
          }
          // Extract detail from response
          const errorMsg = data?.detail || data?.error || `HTTP ${response.status}`;
          throw new Error(errorMsg);
        }
        
        // Ensure response is valid object
        if (!data || typeof data !== 'object') {
          throw new Error('Invalid response from server');
        }
        
        log(`${method} ${endpoint} succeeded`, 'log');
        return data;
      } catch (err) {
        log(`API error on attempt ${attempt}: ${err.message}`, 'error');
        if (attempt < CONFIG.RETRY_ATTEMPTS) {
          await new Promise(r => setTimeout(r, CONFIG.RETRY_DELAY * attempt));
          return this._fetch(endpoint, options, attempt + 1);
        }
        // Return graceful error object instead of throwing
        const errorMsg = err.message || 'Unknown error';
        log(`Final API error for ${endpoint}: ${errorMsg}`, 'error');
        showStatus(`Error: ${errorMsg}`, 'error');
        return { success: false, error: errorMsg, detail: errorMsg };
      }
    },

    // Auth endpoints
    async initSession(initData) {
      // Store initData in state for subsequent authenticated requests
      try {
        state.initData = initData;
      } catch (e) {}
      return this._fetch(`/web-app/init?init_data=${encodeURIComponent(initData)}`);
    },

    // User endpoints
    async getUser(userId) {
      const initData = state.initData || (window.Telegram?.WebApp?.initData || '');
      return this._fetch(`/web-app/user?user_id=${userId}&init_data=${encodeURIComponent(initData)}`);
    },

    // Wallet endpoints
    async getWallets(userId) {
      const initData = state.initData || (window.Telegram?.WebApp?.initData || '');
      return this._fetch(`/web-app/wallets?user_id=${userId}&init_data=${encodeURIComponent(initData)}`);
    },

    async createWallet(blockchain, walletType = 'custodial', isPrimary = false) {
      const initData = state.initData || (window.Telegram?.WebApp?.initData || '');
      return this._fetch(`/web-app/create-wallet`, {
        method: 'POST',
        body: { blockchain, wallet_type: walletType, is_primary: isPrimary, init_data: initData }
      });
    },

    async importWallet(blockchain, address, publicKey = null, isPrimary = false) {
      const initData = state.initData || (window.Telegram?.WebApp?.initData || '');
      return this._fetch(`/web-app/import-wallet`, {
        method: 'POST',
        body: { blockchain, address, public_key: publicKey, is_primary: isPrimary, init_data: initData }
      });
    },

    async setPrimaryWallet(walletId, userId = null) {
      const initData = state.initData || (window.Telegram?.WebApp?.initData || '');
      const body = { wallet_id: walletId, init_data: initData };
      if (userId) body.user_id = userId;
      return this._fetch(`/web-app/set-primary`, {
        method: 'POST',
        body,
      });
    },

    // NFT endpoints
    async getNfts(userId) {
      const initData = state.initData || (window.Telegram?.WebApp?.initData || '');
      return this._fetch(`/web-app/nfts?user_id=${userId}&init_data=${encodeURIComponent(initData)}`);
    },

    async mintNft(userId, walletId, nftName, description, imageUrl = null) {
      const initData = state.initData || (window.Telegram?.WebApp?.initData || '');
      return this._fetch(`/web-app/mint`, {
        method: 'POST',
        body: {
          user_id: userId,
          wallet_id: walletId,
          nft_name: nftName,
          nft_description: description,
          image_url: imageUrl,
          init_data: initData,
        }
      });
    },

    async burnNft(userId, nftId) {
      const initData = state.initData || (window.Telegram?.WebApp?.initData || '');
      return this._fetch(`/web-app/burn`, {
        method: 'POST',
        body: { user_id: userId, nft_id: nftId, init_data: initData }
      });
    },

    async transferNft(userId, nftId, toAddress) {
      const initData = state.initData || (window.Telegram?.WebApp?.initData || '');
      return this._fetch(`/web-app/transfer`, {
        method: 'POST',
        body: { user_id: userId, nft_id: nftId, to_address: toAddress, init_data: initData }
      });
    },

    // Marketplace endpoints
    async getMarketplaceListings(limit = 50) {
      return this._fetch(`/web-app/marketplace/listings?limit=${limit}`);
    },

    async getMyListings(userId) {
      const initData = state.initData || (window.Telegram?.WebApp?.initData || '');
      return this._fetch(`/web-app/marketplace/mylistings?user_id=${userId}&init_data=${encodeURIComponent(initData)}`);
    },

    async listNft(userId, nftId, price, currency = 'USDT') {
      const initData = state.initData || (window.Telegram?.WebApp?.initData || '');
      return this._fetch(`/web-app/list-nft`, {
        method: 'POST',
        body: { user_id: userId, nft_id: nftId, price: parseFloat(price), currency, init_data: initData }
      });
    },

    async makeOffer(userId, listingId, offerPrice) {
      const initData = state.initData || (window.Telegram?.WebApp?.initData || '');
      return this._fetch(`/web-app/make-offer`, {
        method: 'POST',
        body: { user_id: userId, listing_id: listingId, offer_price: parseFloat(offerPrice), init_data: initData }
      });
    },

    async cancelListing(userId, listingId) {
      const initData = state.initData || (window.Telegram?.WebApp?.initData || '');
      return this._fetch(`/web-app/cancel-listing`, {
        method: 'POST',
        body: { user_id: userId, listing_id: listingId, init_data: initData }
      });
    },

    // Dashboard endpoints
    async getDashboardData(userId) {
      const initData = state.initData || (window.Telegram?.WebApp?.initData || '');
      return this._fetch(`/web-app/dashboard-data?user_id=${userId}&init_data=${encodeURIComponent(initData)}`);
    },
  };

  // Ui update 

  function formatAddress(addr) {
    if (!addr || addr.length < 10) return addr;
    return addr.slice(0, 6) + '...' + addr.slice(-4);
  }

  function formatCurrency(num) {
    return parseFloat(num).toFixed(2);
  }

  async function updateDashboard() {
    try {
      if (!state.user || !state.user.id) {
        showStatus('User not authenticated', 'error');
        return;
      }

      showStatus('Loading dashboard...', 'loading');
      
      const dashData = await API.getDashboardData(state.user.id);
      
      if (!dashData || !dashData.success) {
        throw new Error(dashData?.error || dashData?.detail || 'Failed to load dashboard');
      }
      
      const wallets = dashData.wallets || [];
      const nfts = dashData.nfts || [];
      const listings = dashData.listings || [];
      
      // Populate state so wallets and NFTs are available for actions
      state.wallets = wallets;
      state.nfts = nfts;
      state.listings = listings;
      
      // Update stats
      const stats = document.getElementById('dashboardStats');
      if (stats) {
        const portfolioValue = (nfts.length * 100).toFixed(2);
        stats.innerHTML = `
          <div class="stat-box">
            <div class="stat-label">Wallets</div>
            <div class="stat-value">${wallets.length}</div>
          </div>
          <div class="stat-box">
            <div class="stat-label">NFTs</div>
            <div class="stat-value">${nfts.length}</div>
          </div>
          <div class="stat-box">
            <div class="stat-label">Listings</div>
            <div class="stat-value">${listings.filter(l => l.active || l.status === 'ACTIVE').length}</div>
          </div>
          <div class="stat-box">
            <div class="stat-label">Est. Value</div>
            <div class="stat-value">$${portfolioValue}</div>
          </div>
        `;
      }
      
      // Update recent wallets
      const recentWallets = document.getElementById('recentWallets');
      if (recentWallets && wallets.length) {
        recentWallets.innerHTML = wallets.slice(0, 3).map(w => `
          <div class="card" style="padding:12px;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
              <div>
                <strong>${(w.blockchain || 'Unknown').toUpperCase()}</strong>
                ${w.is_primary ? '<span class="blockchain-badge primary-badge">Primary</span>' : ''}
              </div>
              <code style="font-size:11px;">${formatAddress(w.address || '')}</code>
            </div>
          </div>
        `).join('');
      }
      
      // Update recent NFTs
      const recentNfts = document.getElementById('recentNfts');
      if (recentNfts && nfts.length) {
        recentNfts.innerHTML = nfts.slice(0, 3).map(nft => `
          <div class="card" style="padding:12px;">
            <div style="display:flex;gap:12px;">
              ${nft.image_url ? `
                <img src="${nft.image_url}" 
                     alt="${nft.name}" 
                     style="width:40px;height:40px;border-radius:4px;object-fit:cover;" 
                     onerror="this.style.display='none'">
              ` : ''}
              <div style="flex:1;min-width:0;">
                <strong>${nft.name || 'NFT'}</strong>
                <div style="font-size:12px;color:var(--text-secondary);">${(nft.blockchain || 'Unknown').toUpperCase()}</div>
              </div>
            </div>
          </div>
        `).join('');
      }
      
      showStatus('Dashboard loaded', 'success');
    } catch (err) {
      log(`Dashboard error: ${err.message}`, 'error');
      showStatus(`Error: ${err.message}`, 'error');
    }
  }

  async function updateWalletsList() {
    try {
      if (!state.user || !state.user.id) {
        showStatus('User not authenticated', 'error');
        return;
      }

      showStatus('Loading wallets...', 'loading');
      
      const data = await API.getWallets(state.user.id);
      if (!data || !data.success) throw new Error(data?.error || data?.detail || 'Failed to load wallets');
      
      state.wallets = data.wallets || [];
      
      const container = document.getElementById('walletsList');
      if (!container) return;
      
      if (!state.wallets.length) {
        container.innerHTML = '<div class="card"><p style="color:var(--text-secondary);">No wallets yet. Create one to get started.</p></div>';
        return;
      }
      
      container.innerHTML = state.wallets.map(w => `
        <div class="card">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
            <div>
              <strong>${(w.blockchain || 'Wallet').toUpperCase()}</strong>
              ${w.is_primary ? '<span class="blockchain-badge primary-badge">Primary</span>' : ''}
            </div>
            <small style="color:var(--text-secondary);">${new Date(w.created_at || Date.now()).toLocaleDateString()}</small>
          </div>
          <code style="display:block;word-break:break-all;padding:12px;background:rgba(0,0,0,0.2);border-radius:4px;font-size:11px;margin-bottom:12px;">${w.address || 'N/A'}</code>
          <div style="display:flex;gap:10px;flex-wrap:wrap;">
            <button class="btn btn-secondary" onclick="if(window.showWalletDetails)window.showWalletDetails('${w.id}')" style="flex:1;min-width:80px;">Details</button>
            <button class="btn btn-secondary" onclick="if(window.depositModal)window.depositModal('${w.id}')" style="flex:1;min-width:80px;">Deposit</button>
            <button class="btn btn-secondary" onclick="if(window.withdrawalModal)window.withdrawalModal('${w.id}')" style="flex:1;min-width:80px;">💸 Withdraw</button>
            ${!w.is_primary ? `<button class="btn btn-secondary" onclick="if(window.setPrimary)window.setPrimary('${w.id}')" style="flex:1;min-width:80px;">Set Primary</button>` : ''}
          </div>
        </div>
      `).join('');
      
      showStatus('Wallets loaded', 'success');
    } catch (err) {
      log(`Wallets error: ${err.message}`, 'error');
      showStatus(`Error: ${err.message}`, 'error');
    }
  }

  async function updateNftList() {
    try {
      showStatus('Loading NFTs...', 'loading');
      
      const data = await API.getNfts(state.user.id);
      if (!data.success) throw new Error(data.error || 'Failed to load NFTs');
      
      state.nfts = data.nfts || [];
      
      const container = document.getElementById('nftList');
      if (!container) return;
      
      if (!state.nfts.length) {
        container.innerHTML = '<div class="card"><p style="color:var(--text-secondary);">No NFTs yet. Create one to get started.</p></div>';
        return;
      }
      
      container.innerHTML = state.nfts.map(nft => `
        <div class="card">
          <div class="nft-image-container" style="width:100%;height:200px;border-radius:8px;margin-bottom:12px;background:linear-gradient(135deg,#7c5cff,#4c6ef5);background-size:cover;background-position:center;display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden;">
            ${nft.image_url ? `
              <img src="${nft.image_url}" 
                   alt="${nft.name}" 
                   style="width:100%;height:100%;object-fit:cover;" 
                   onerror="this.parentElement.innerHTML='<span style=\\"color:rgba(255,255,255,0.5);font-size:12px;\\">Image failed to load</span>'">
            ` : `<span style="color:rgba(255,255,255,0.5);font-size:12px;">No image</span>`}
          </div>
          <div style="margin-bottom:12px;">
            <strong>${nft.name}</strong>
            <p style="font-size:12px;color:var(--text-secondary);margin-top:4px;">${nft.description || 'No description'}</p>
          </div>
          <div style="display:flex;gap:8px;margin-bottom:12px;">
            <span class="blockchain-badge">${nft.blockchain?.toUpperCase()}</span>
            <span class="blockchain-badge" style="background:${nft.status === 'LISTED' ? '#ff6b6b' : '#51cf66'};">${nft.status || 'UNLISTED'}</span>
          </div>
          <div style="display:flex;gap:10px;">
            <button class="btn btn-secondary" onclick="window.showNftDetails('${nft.id}')">Details</button>
            ${nft.status !== 'LISTED' ? `<button class="btn btn-secondary" onclick="window.listNftModal('${nft.id}')">Sell</button>` : ''}
          </div>
        </div>
      `).join('');
      
      showStatus('NFTs loaded', 'success');
    } catch (err) {
      log(`NFTs error: ${err.message}`, 'error');
      showStatus(`Error: ${err.message}`, 'error');
    }
  }

  async function updateMarketplaceList() {
    try {
      showStatus('Loading marketplace...', 'loading');
      
      const data = await API.getMarketplaceListings(50);
      if (!data.success) throw new Error(data.error || 'Failed to load marketplace');
      
      state.listings = data.listings || [];
      
      const container = document.getElementById('marketplaceList');
      if (!container) return;
      
      if (!state.listings.length) {
        container.innerHTML = '<div class="card"><p style="color:var(--text-secondary);">No listings available right now.</p></div>';
        return;
      }
      
      container.innerHTML = state.listings.map(listing => `
        <div class="card">
          <div class="listing-image-container" style="width:100%;height:200px;border-radius:8px;margin-bottom:12px;background:linear-gradient(135deg,#7c5cff,#4c6ef5);background-size:cover;background-position:center;display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden;">
            ${listing.image_url ? `
              <img src="${listing.image_url}" 
                   alt="${listing.nft_name}" 
                   style="width:100%;height:100%;object-fit:cover;" 
                   onerror="this.parentElement.innerHTML='<span style=\\"color:rgba(255,255,255,0.5);font-size:12px;\\">Image failed to load</span>'">
            ` : `<span style="color:rgba(255,255,255,0.5);font-size:12px;">No image</span>`}
          </div>
          <div style="margin-bottom:12px;">
            <strong>${listing.nft_name}</strong>
            <div style="font-size:12px;color:var(--text-secondary);margin-top:4px;">By <strong>${listing.seller_name || 'Anonymous'}</strong></div>
          </div>
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
            <div>
              <div style="font-size:14px;font-weight:bold;">$${formatCurrency(listing.price)}</div>
              <div style="font-size:12px;color:var(--text-secondary);">${listing.currency}</div>
            </div>
            <span class="blockchain-badge">${listing.blockchain?.toUpperCase()}</span>
          </div>
          <button class="btn btn-primary" onclick="window.buyNftModal('${listing.id}')">Buy Now</button>
        </div>
      `).join('');
      
      showStatus('Marketplace loaded', 'success');
    } catch (err) {
      log(`Marketplace error: ${err.message}`, 'error');
      showStatus(`Error: ${err.message}`, 'error');
    }
  }

  async function updateProfilePage() {
    try {
      if (!state.user) throw new Error('User not loaded');
      
      const container = document.getElementById('profilePage');
      if (!container) return;
      
      container.innerHTML = `
        <div class="card">
          <h3>Profile Information</h3>
          <div style="margin-top:20px;">
            <div class="profile-item">
              <span>Name:</span>
              <strong>${state.user.full_name || 'N/A'}</strong>
            </div>
            <div class="profile-item">
              <span>Username:</span>
              <strong>@${state.user.telegram_username || 'N/A'}</strong>
            </div>
            <div class="profile-item">
              <span>Telegram ID:</span>
              <code style="font-size:11px;">${state.user.telegram_id}</code>
            </div>
            <div class="profile-item">
              <span>Email:</span>
              <strong>${state.user.email || 'Not set'}</strong>
            </div>
            <div class="profile-item">
              <span>Status:</span>
              <strong>${state.user.is_verified ? 'Verified' : 'Unverified'}</strong>
            </div>
            <div class="profile-item">
              <span>Role:</span>
              <strong style="text-transform:capitalize;">${state.user.user_role || 'user'}</strong>
            </div>
            <div class="profile-item">
              <span>Joined:</span>
              <strong>${new Date(state.user.created_at).toLocaleDateString()}</strong>
            </div>
          </div>
        </div>
        <div class="card" style="margin-top:20px;">
          <h3>Stats</h3>
          <div class="stats-grid" style="margin-top:20px;display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:16px;">
            <div class="stat-box">
              <div class="stat-label">Wallets</div>
              <div class="stat-value">${state.wallets.length}</div>
            </div>
            <div class="stat-box">
              <div class="stat-label">NFTs</div>
              <div class="stat-value">${state.nfts.length}</div>
            </div>
            <div class="stat-box">
              <div class="stat-label">Listings</div>
              <div class="stat-value">${state.listings.filter(l => l.active || l.status === 'ACTIVE').length}</div>
            </div>
          </div>
        </div>
      `;
    } catch (err) {
      log(`Profile error: ${err.message}`, 'error');
    }
  }

  //MODAL FUNCTIONS

  window.showWalletDetails = function(walletId) {
    const wallet = state.wallets.find(w => w.id === walletId);
    if (!wallet) return;
    
    showModal(`${wallet.blockchain?.toUpperCase()} Wallet`, `
      <div style="font-size:13px;">
        <div class="profile-item">
          <span>Address:</span>
          <code style="word-break:break-all;font-size:11px;">${wallet.address}</code>
        </div>
        <div class="profile-item">
          <span>Primary:</span>
          <strong>${wallet.is_primary ? 'Yes' : 'No'}</strong>
        </div>
        <div class="profile-item">
          <span>Created:</span>
          <strong>${new Date(wallet.created_at).toLocaleString()}</strong>
        </div>
      </div>
    `, [
      { label: 'Close', action: 'closeModal()', class: 'btn-secondary' }
    ]);
  };

  // Set a wallet as primary (used by wallet list actions)
  window.setPrimary = async function(walletId) {
    try {
      if (!state.user) {
        showStatus('User not authenticated', 'error');
        return;
      }

      showStatus('Setting primary wallet...', 'loading');
      const result = await API.setPrimaryWallet(walletId, state.user.id);

      if (!result.success) throw new Error(result.error || 'Failed to set primary wallet');

      showStatus('Primary wallet updated!', 'success');
      closeModal();
      await updateWalletsList();
      await updateDashboard();
    } catch (err) {
      showStatus(`Error: ${err.message}`, 'error');
    }
  };

  window.showNftDetails = function(nftId) {
    const nft = state.nfts.find(n => n.id === nftId);
    if (!nft) return;
    
    showModal(`${nft.name}`, `
      <div class="modal-nft-image" style="width:100%;height:250px;border-radius:8px;margin-bottom:12px;background:linear-gradient(135deg,#7c5cff,#4c6ef5);background-size:cover;background-position:center;display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden;">
        ${nft.image_url ? `
          <img src="${nft.image_url}" 
               alt="${nft.name}" 
               style="width:100%;height:100%;object-fit:cover;" 
               onerror="this.parentElement.innerHTML='<span style=\\"color:rgba(255,255,255,0.5);\\">Image failed to load</span>'">
        ` : `<span style="color:rgba(255,255,255,0.5);">No image</span>`}
      </div>
      <div style="font-size:13px;">
        <div class="profile-item">
          <span>Blockchain:</span>
          <strong>${nft.blockchain?.toUpperCase()}</strong>
        </div>
        <div class="profile-item">
          <span>Status:</span>
          <strong>${nft.status || 'UNLISTED'}</strong>
        </div>
        <div class="profile-item">
          <span>Description:</span>
          <p style="margin-top:4px;color:var(--text-secondary);">${nft.description || 'No description'}</p>
        </div>
      </div>
    `, [
      { label: nft.status !== 'LISTED' ? 'Sell NFT' : 'View Listing', action: `listNftModal('${nft.id}')`, class: 'btn-primary' },
      { label: 'Close', action: 'closeModal()', class: 'btn-secondary' }
    ]);
  };

  window.listNftModal = function(nftId) {
    showModal('List NFT for Sale', `
      <div style="display:flex;flex-direction:column;gap:12px;">
        <div>
          <label>Price (USD)</label>
          <input type="number" id="listPrice" placeholder="Enter price" style="width:100%;padding:10px;border:1px solid var(--border);border-radius:4px;background:rgba(0,0,0,0.2);color:#fff;" min="0" step="0.01">
        </div>
        <div>
          <label>Currency</label>
          <select id="listCurrency" style="width:100%;padding:10px;border:1px solid var(--border);border-radius:4px;background:rgba(0,0,0,0.2);color:#fff;">
            <option>USD</option>
            <option>EUR</option>
            <option>GBP</option>
            <option>ETH</option>
            <option>USDT</option>
          </select>
        </div>
      </div>
    `, [
      { label: 'List NFT', action: `submitListNft('${nftId}')`, class: 'btn-primary' },
      { label: 'Cancel', action: 'closeModal()', class: 'btn-secondary' }
    ]);
  };

  window.submitListNft = async function(nftId) {
    try {
      const price = document.getElementById('listPrice')?.value;
      const currency = document.getElementById('listCurrency')?.value || 'USDT';
      
      if (!price) throw new Error('Please enter a price');
      if (!state.user?.id) throw new Error('User not authenticated');
      
      showStatus('Listing NFT...', 'loading');
      const result = await API.listNft(state.user.id, nftId, price, currency);
      
      if (!result.success) throw new Error(result.error || 'Failed to list NFT');
      
      closeModal();
      showStatus('NFT listed successfully!', 'success');
      await updateNftList();
    } catch (err) {
      showStatus(`Error: ${err.message}`, 'error');
    }
  };

  window.buyNftModal = function(listingId) {
    showModal('Make Offer', `
      <div>
        <label>Offer Price (USD)</label>
        <input type="number" id="offerPrice" placeholder="Enter your offer" style="width:100%;padding:10px;border:1px solid var(--border);border-radius:4px;background:rgba(0,0,0,0.2);color:#fff;" min="0" step="0.01">
      </div>
    `, [
      { label: 'Submit Offer', action: `submitOffer('${listingId}')`, class: 'btn-primary' },
      { label: 'Cancel', action: 'closeModal()', class: 'btn-secondary' }
    ]);
  };

  window.submitOffer = async function(listingId) {
    try {
      const price = document.getElementById('offerPrice')?.value;
      if (!price) throw new Error('Please enter an offer price');
      if (!state.user?.id) throw new Error('User not authenticated');
      
      showStatus('Submitting offer...', 'loading');
      const result = await API.makeOffer(state.user.id, listingId, price);
      
      if (!result.success) throw new Error(result.error || 'Failed to submit offer');
      
      closeModal();
      showStatus('Offer submitted!', 'success');
      await updateMarketplaceList();
    } catch (err) {
      showStatus(`Error: ${err.message}`, 'error');
    }
  };

  // Direct buy / make offer helper
  window.buyNow = async function(listingId, offerPrice) {
    try {
      if (!state.user || !state.user.id) return showStatus('User not authenticated', 'error');
      if (!offerPrice) throw new Error('Offer price required');

      showStatus('Processing purchase...', 'loading');
      const result = await API.makeOffer(state.user.id, listingId, parseFloat(offerPrice));

      if (!result.success) throw new Error(result.error || 'Purchase failed');

      showStatus('Purchase submitted!', 'success');
      await updateMarketplaceList();
      await updateDashboard();
    } catch (err) {
      showStatus(`Error: ${err.message}`, 'error');
    }
  };

  window.cancelListing = async function(listingId) {
    try {
      if (!state.user || !state.user.id) return showStatus('User not authenticated', 'error');
      showStatus('Cancelling listing...', 'loading');
      const res = await API.cancelListing(state.user.id, listingId);
      if (!res.success) throw new Error(res.error || 'Cancel failed');
      showStatus('Listing cancelled', 'success');
      await updateMarketplaceList();
      await updateDashboard();
    } catch (err) {
      showStatus(`Error: ${err.message}`, 'error');
    }
  };

  // ========== DEPOSIT / WITHDRAWAL FUNCTIONS ==========
  
  window.depositModal = function(walletId) {
    showModal(' Deposit USDT', `
      <div style="display:flex;flex-direction:column;gap:12px;text-align:center;">
        <p style="color:var(--text-secondary);font-size:13px;">Send USDT to your wallet to increase your balance</p>
        <div style="background:rgba(255,255,255,0.05);padding:12px;border-radius:8px;border:1px solid rgba(255,255,255,0.1);">
          <label style="display:block;margin-bottom:8px;font-size:12px;color:var(--text-secondary);">Amount (USDT)</label>
          <input type="number" id="depositAmount" placeholder="Enter amount" style="width:100%;padding:10px;border:1px solid var(--border);border-radius:4px;background:rgba(0,0,0,0.2);color:#fff;font-size:14px;" min="1" step="0.01">
        </div>
      </div>
    `, [
      { label: 'Initiate Deposit', action: `submitDeposit('${walletId}')`, class: 'btn-primary' },
      { label: 'Cancel', action: 'closeModal()', class: 'btn-secondary' }
    ]);
  };

  window.submitDeposit = async function(walletId) {
    try {
      const amount = parseFloat(document.getElementById('depositAmount')?.value);
      if (!amount || amount < 1) throw new Error('Minimum deposit is 1 USDT');
      
      showStatus('Initiating deposit...', 'loading');
      
      // Use web-app endpoint if available, otherwise fall back to direct endpoint
      let depositPath = `/api/v1/payments/web-app/deposit`;
      let requestBody = {
        user_id: state.user?.id || '',
        wallet_id: walletId,
        amount: amount,
        blockchain: 'ethereum', // default blockchain  
        init_data: state.initData || '',
      };
      
      const result = await API._fetch(depositPath, {
        method: 'POST',
        body: requestBody
      });
      
      if (!result.success && result.error) {
        // Try alternative endpoint if first fails
        depositPath = `/api/v1/payments/deposit/initiate`;
        requestBody = {
          wallet_id: walletId,
          amount: amount,
        };
        
        const altResult = await API._fetch(depositPath, {
          method: 'POST',
          body: requestBody
        });
        
        if (altResult.success) {
          result.success = altResult.success;
          result.payment_id = altResult.payment_id;
          result.deposit_address = altResult.deposit_address;
          result.currency = altResult.currency || 'USDT';
          result.blockchain = altResult.blockchain || 'ethereum';
        } else {
          throw new Error(altResult.error || result.error || 'Failed to initiate deposit');
        }
      }
      
      if (!result.success) throw new Error(result.error || 'Failed to initiate deposit');
      
      closeModal();
      showModal('📋 Deposit Instructions', `
        <div style="display:flex;flex-direction:column;gap:12px;font-size:13px;">
          <div style="background:rgba(76,175,80,0.1);padding:12px;border-radius:8px;border-left:4px solid #4CAF50;">
            <p><strong>Deposit Address:</strong></p>
            <code style="display:block;background:rgba(0,0,0,0.3);padding:8px;margin:8px 0;word-break:break-all;border-radius:4px;font-size:11px;">${result.deposit_address}</code>
            <button onclick="navigator.clipboard.writeText('${result.deposit_address}');alert('Copied!')" class="btn btn-secondary" style="width:100%;margin-top:8px;font-size:12px;">📋 Copy Address</button>
          </div>
          <div style="background:rgba(33,150,243,0.1);padding:12px;border-radius:8px;border-left:4px solid #2196F3;">
            <strong>Send this amount:</strong> ${result.amount} ${result.currency}
          </div>
          <div style="background:rgba(255,152,0,0.1);padding:12px;border-radius:8px;border-left:4px solid #FF9800;">
            <strong>On blockchain:</strong> ${(result.blockchain || 'ethereum').toUpperCase()}
          </div>
          <p style="color:var(--text-secondary);margin-top:8px;">⏱ This deposit is valid for 24 hours. After sending, come back to confirm the transaction.</p>
        </div>
      `, [
        { label: 'Confirmed Deposit', action: `confirmDepositModal('${result.payment_id}')`, class: 'btn-primary' },
        { label: 'Close', action: 'closeModal()', class: 'btn-secondary' }
      ]);
    } catch (err) {
      log(`Deposit error: ${err.message}`, 'error');
      showStatus(`Error: ${err.message}`, 'error');
    }
  };

  window.confirmDepositModal = function(paymentId) {
    showModal('Confirm Deposit', `
      <div style="display:flex;flex-direction:column;gap:12px;">
        <p style="color:var(--text-secondary);font-size:13px;">Paste your transaction hash to confirm the deposit</p>
        <div>
          <label style="display:block;margin-bottom:6px;font-size:12px;">Transaction Hash</label>
          <input type="text" id="txHash" placeholder="0x..." style="width:100%;padding:10px;border:1px solid var(--border);border-radius:4px;background:rgba(0,0,0,0.2);color:#fff;font-size:12px;font-family:monospace;">
        </div>
      </div>
    `, [
      { label: 'Confirm', action: `submitConfirmDeposit('${paymentId}')`, class: 'btn-primary' },
      { label: 'Cancel', action: 'closeModal()', class: 'btn-secondary' }
    ]);
  };

  window.submitConfirmDeposit = async function(paymentId) {
    try {
      const txHash = document.getElementById('txHash')?.value?.trim();
      if (!txHash || txHash.length < 10) throw new Error('Invalid transaction hash');
      
      showStatus('Confirming deposit...', 'loading');
      
      let confirmPath = `/api/v1/payments/deposit/confirm`;
      const result = await API._fetch(confirmPath, {
        method: 'POST',
        body: {
          payment_id: paymentId,
          transaction_hash: txHash,
        }
      });
      
      if (!result.success) throw new Error(result.error || 'Failed to confirm deposit');
      
      closeModal();
      showStatus('Deposit confirmed! Your balance will update once verified.', 'success');
      log(`Deposit confirmed: ${paymentId}`, 'log');
      await updateDashboard();
    } catch (err) {
      log(`Deposit confirmation error: ${err.message}`, 'error');
      showStatus(`Error: ${err.message}`, 'error');
    }
  };

  window.withdrawalModal = function(walletId) {
    showModal(' Withdraw USDT', `
      <div style="display:flex;flex-direction:column;gap:12px;">
        <div>
          <label style="display:block;margin-bottom:6px;font-size:12px;">Amount to Withdraw (USDT)</label>
          <input type="number" id="withdrawAmount" placeholder="Enter amount" style="width:100%;padding:10px;border:1px solid var(--border);border-radius:4px;background:rgba(0,0,0,0.2);color:#fff;" min="1" step="0.01">
        </div>
        <div>
          <label style="display:block;margin-bottom:6px;font-size:12px;">Destination Address</label>
          <input type="text" id="destAddress" placeholder="0x... or other address" style="width:100%;padding:10px;border:1px solid var(--border);border-radius:4px;background:rgba(0,0,0,0.2);color:#fff;font-size:12px;">
        </div>
        <div>
          <label style="display:block;margin-bottom:6px;font-size:12px;">Blockchain (optional)</label>
          <select id="destBlockchain" style="width:100%;padding:10px;border:1px solid var(--border);border-radius:4px;background:rgba(0,0,0,0.2);color:#fff;">
            <option value="">Same as source</option>
            <option value="ethereum">Ethereum</option>
            <option value="polygon">Polygon</option>
            <option value="arbitrum">Arbitrum</option>
            <option value="optimism">Optimism</option>
            <option value="avalanche">Avalanche</option>
            <option value="base">Base</option>
          </select>
        </div>
      </div>
    `, [
      { label: 'Withdraw', action: `submitWithdrawal('${walletId}')`, class: 'btn-primary' },
      { label: 'Cancel', action: 'closeModal()', class: 'btn-secondary' }
    ]);
  };

  window.submitWithdrawal = async function(walletId) {
    try {
      const amount = parseFloat(document.getElementById('withdrawAmount')?.value);
      const destAddress = document.getElementById('destAddress')?.value?.trim();
      const destBlockchain = document.getElementById('destBlockchain')?.value || undefined;
      
      if (!amount || amount < 1) throw new Error('Minimum withdrawal is 1 USDT');
      if (!destAddress || destAddress.length < 20) throw new Error('Invalid destination address');
      
      showStatus('Processing withdrawal request...', 'loading');
      
      let withdrawPath = `/api/v1/payments/web-app/withdrawal`;
      let requestBody = {
        user_id: state.user?.id || '',
        wallet_id: walletId,
        amount: amount,
        destination_address: destAddress,
        blockchain: destBlockchain || 'ethereum',
        init_data: state.initData || '',
      };
      
      let result = await API._fetch(withdrawPath, {
        method: 'POST',
        body: requestBody
      });
      
      if (!result.success && result.error) {
        // Try alternative endpoint
        withdrawPath = `/api/v1/payments/withdrawal/initiate`;
        requestBody = {
          wallet_id: walletId,
          amount: amount,
          destination_address: destAddress,
          destination_blockchain: destBlockchain,
        };
        
        const altResult = await API._fetch(withdrawPath, {
          method: 'POST',
          body: requestBody
        });
        
        if (altResult.success) {
          result.success = altResult.success;
          result.payment_id = altResult.payment_id;
          result.currency = altResult.currency || 'USDT';
          result.platform_fee = altResult.platform_fee || '0';
        } else {
          throw new Error(altResult.error || result.error || 'Failed to initiate withdrawal');
        }
      }
      
      if (!result.success) throw new Error(result.error || 'Failed to initiate withdrawal');
      
      closeModal();
      showModal('⏳ Withdrawal Pending', `
        <div style="display:flex;flex-direction:column;gap:12px;font-size:13px;">
          <div style="background:rgba(76,175,80,0.1);padding:12px;border-radius:8px;">
            <strong>Withdrawal Created</strong><br>
            ${result.amount} ${result.currency} will be sent to your address.
          </div>
          <div style="background:rgba(255,152,0,0.1);padding:12px;border-radius:8px;border-left:4px solid #FF9800;">
            <strong>Fee:</strong> ${result.platform_fee || '2%'}
          </div>
          <p style="color:var(--text-secondary);">Withdrawal will be processed within 5 minutes.</p>
        </div>
      `, [
        { label: 'Done', action: 'closeModal()', class: 'btn-primary' }
      ]);
      
      log(`Withdrawal initiated: ${result.payment_id}`, 'log');
      await updateDashboard();
    } catch (err) {
      log(`Withdrawal error: ${err.message}`, 'error');
      showStatus(`Error: ${err.message}`, 'error');
    }
  };

  window.closeModal = closeModal;

  //NAVIGATION
  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const pageName = item.dataset.page;
      if (pageName) switchPage(pageName);
    });
  });

  //  PAGE ACTION
  const pageActions = {
    async createWallet() {
      showModal('Create Wallet', `
        <div style="display:flex;flex-direction:column;gap:12px;">
          <div>
            <label>Blockchain</label>
            <select id="blockchainSelect" style="width:100%;padding:10px;border:1px solid var(--border);border-radius:4px;background:rgba(0,0,0,0.2);color:#fff;">
              <option value="bitcoin">Bitcoin</option>
              <option value="ethereum">Ethereum</option>
              <option value="solana">Solana</option>
              <option value="ton">TON</option>
              <option value="polygon">Polygon</option>
              <option value="avalanche">Avalanche</option>
              <option value="arbitrum">Arbitrum</option>
              <option value="optimism">Optimism</option>
              <option value="base">Base</option>
            </select>
          </div>
          <div style="display:flex;gap:10px;align-items:center;">
            <input type="checkbox" id="setPrimary" checked>
            <label style="margin:0;">Set as Primary</label>
          </div>
        </div>
      `, [
        { label: 'Create', action: 'pageActions.submitCreateWallet()', class: 'btn-primary' },
        { label: 'Cancel', action: 'closeModal()', class: 'btn-secondary' }
      ]);
    },

    async importWallet() {
      showModal('Import Wallet', `
        <div style="display:flex;flex-direction:column;gap:12px;">
          <div>
            <label>Blockchain</label>
            <select id="importBlockchain" style="width:100%;padding:10px;border:1px solid var(--border);border-radius:4px;background:rgba(0,0,0,0.2);color:#fff;">
              <option value="bitcoin">Bitcoin</option>
              <option value="ethereum">Ethereum</option>
              <option value="solana">Solana</option>
              <option value="ton">TON</option>
              <option value="polygon">Polygon</option>
              <option value="avalanche">Avalanche</option>
            </select>
          </div>
          <div>
            <label>Address</label>
            <input type="text" id="importAddress" placeholder="0x..." style="width:100%;padding:10px;border:1px solid var(--border);border-radius:4px;background:rgba(0,0,0,0.2);color:#fff;">
          </div>
          <div style="display:flex;gap:10px;align-items:center;">
            <input type="checkbox" id="importSetPrimary">
            <label style="margin:0;">Set as Primary</label>
          </div>
        </div>
      `, [
        { label: 'Import', action: 'pageActions.submitImportWallet()', class: 'btn-primary' },
        { label: 'Cancel', action: 'closeModal()', class: 'btn-secondary' }
      ]);
    },

    async submitImportWallet() {
      try {
        const blockchain = document.getElementById('importBlockchain')?.value;
        const address = document.getElementById('importAddress')?.value;
        const isPrimary = document.getElementById('importSetPrimary')?.checked === true;

        if (!blockchain || !address) throw new Error('Please select blockchain and enter address');

        showStatus('Importing wallet...', 'loading');
        const result = await API.importWallet(blockchain, address, null, isPrimary);

        if (!result.success) throw new Error(result.error || 'Failed to import wallet');

        closeModal();
        showStatus('Wallet imported!', 'success');
        await updateWalletsList();
        await updateDashboard();
      } catch (err) {
        showStatus(`Error: ${err.message}`, 'error');
      }
    },

    async submitCreateWallet() {
      try {
        if (!state.user || !state.user.id) {
          showStatus('User not authenticated', 'error');
          log('Wallet creation failed: user not authenticated', 'error');
          return;
        }

        const blockchain = document.getElementById('blockchainSelect')?.value?.toLowerCase();
        const isPrimary = document.getElementById('setPrimary')?.checked === true;
        
        if (!blockchain) throw new Error('Please select a blockchain');
        
        log(`Creating wallet on ${blockchain} (primary=${isPrimary})`, 'log');
        showStatus('Creating wallet...', 'loading');
        
        const result = await API.createWallet(blockchain, 'custodial', isPrimary);
        
        log(`Create wallet response: ${JSON.stringify(result)}`, 'log');
        
        if (!result || !result.success) {
          const errorMsg = result?.error || result?.detail || result?.message || 'Failed to create wallet';
          log(`Wallet creation error: ${errorMsg}`, 'error');
          throw new Error(errorMsg);
        }
        
        closeModal();
        log(`Wallet created successfully: ${result.wallet?.id}`, 'log');
        showStatus('Wallet created successfully! 🎉', 'success');
        
        // Reload wallet data
        await updateWalletsList();
        await updateDashboard();
      } catch (err) {
        log(`Wallet creation failed: ${err.message}`, 'error');
        showStatus(`Error: ${err.message}`, 'error');
      }
    }

    async mintNft() {
      if (!state.user || !state.user.id) {
        showStatus('User not authenticated', 'error');
        return;
      }

      // Ensure wallets are loaded
      if (!state.wallets || state.wallets.length === 0) {
        try {
          showStatus('Loading wallets...', 'loading');
          const data = await API.getWallets(state.user.id);
          if (data.success) {
            state.wallets = data.wallets || [];
          }
        } catch (e) {
          log(`Failed to load wallets: ${e.message}`, 'error');
        }
      }

      if (!state.wallets || state.wallets.length === 0) {
        showModal('No Wallets', `
          <div style="text-align:center;">
            <p>You need to create a wallet before minting NFTs.</p>
            <p style="color:var(--text-secondary);font-size:12px;">A wallet holds your NFTs on a blockchain.</p>
          </div>
        `, [
          { label: 'Create Wallet', action: 'pageActions.createWallet()', class: 'btn-primary' },
          { label: 'Cancel', action: 'closeModal()', class: 'btn-secondary' }
        ]);
        return;
      }
      
      showModal('Create NFT', `
        <div style="display:flex;flex-direction:column;gap:12px;">
          <div>
            <label>Wallet</label>
            <select id="mintWalletSelect" style="width:100%;padding:10px;border:1px solid var(--border);border-radius:4px;background:rgba(0,0,0,0.2);color:#fff;">
              ${state.wallets.map(w => `<option value="${w.id}">${w.blockchain?.toUpperCase()}</option>`).join('')}
            </select>
          </div>
          <div>
            <label>NFT Name</label>
            <input type="text" id="mintName" placeholder="Enter NFT name" style="width:100%;padding:10px;border:1px solid var(--border);border-radius:4px;background:rgba(0,0,0,0.2);color:#fff;">
          </div>
          <div>
            <label>Description</label>
            <textarea id="mintDesc" placeholder="Enter description" style="width:100%;padding:10px;border:1px solid var(--border);border-radius:4px;background:rgba(0,0,0,0.2);color:#fff;resize:none;height:80px;"></textarea>
          </div>
          <div>
            <label>Image URL (Optional)</label>
            <input type="url" id="mintImage" placeholder="https://..." style="width:100%;padding:10px;border:1px solid var(--border);border-radius:4px;background:rgba(0,0,0,0.2);color:#fff;" oninput="this._imagePreviewTimeout = setTimeout(() => { const img = document.getElementById('imagePreview'); const url = this.value; if (url && url.startsWith('http')) { img.src = url; img.style.display='block'; } else { img.style.display='none'; } }, 500)">
          </div>
          <div id="imagePreviewContainer" style="width:100%;height:150px;border-radius:8px;background:linear-gradient(135deg,#7c5cff,#4c6ef5);background-size:cover;overflow:hidden;margin-top:8px;display:flex;align-items:center;justify-content:center;">
            <img id="imagePreview" src="" alt="Preview" style="display:none;width:100%;height:100%;object-fit:cover;" onerror="this.style.display='none'; this.parentElement.innerHTML='<span style=\\"color:rgba(255,255,255,0.5);\\">Image failed to load</span>'">
          </div>
        </div>
      `, [
        { label: 'Create NFT', action: 'pageActions.submitMintNft()', class: 'btn-primary' },
        { label: 'Cancel', action: 'closeModal()', class: 'btn-secondary' }
      ]);
    },

    async submitMintNft() {
      try {
        if (!state.user || !state.user.id) {
          showStatus('User not authenticated', 'error');
          return;
        }

        const walletId = document.getElementById('mintWalletSelect')?.value;
        const name = document.getElementById('mintName')?.value;
        const desc = document.getElementById('mintDesc')?.value;
        const image = document.getElementById('mintImage')?.value;
        
        if (!walletId) throw new Error('Please select a wallet');
        if (!name || name.trim().length === 0) throw new Error('Please enter an NFT name');
        
        showStatus('Minting NFT...', 'loading');
        const result = await API.mintNft(state.user.id, walletId, name, desc, image || null);
        
        if (!result || !result.success) throw new Error(result?.error || result?.detail || 'Failed to mint NFT');
        
        closeModal();
        showStatus('NFT minted successfully!', 'success');
        await updateNftList();
        await updateDashboard();
      } catch (err) {
        showStatus(`Error: ${err.message}`, 'error');
      }
    },

    async viewBalance() {
      switchPage('balance');
      await pageActions.refreshBalance();
    },

    async refreshBalance() {
      try {
        showStatus('Loading balance...', 'loading');
        
        const response = await API._fetch(`/api/v1/payments/balance`);
        if (response.error) throw new Error(response.error);
        
        const balance = response || {};
        const total = balance.total_balance_usdt || 0;
        const pending = balance.pending_deposits_usdt || 0;
        const available = balance.available_balance_usdt || 0;
        
        // Update balance display in dashboard
        const dashDisplay = document.getElementById('balanceDisplay');
        if (dashDisplay) dashDisplay.textContent = `$${total.toFixed(2)} USDT`;
        
        // Update balance display in balance page
        const largeDisplay = document.getElementById('balanceDisplayLarge');
        if (largeDisplay) largeDisplay.textContent = `$${total.toFixed(2)} USDT`;
        
        const confirmedEl = document.getElementById('confirmedBalance');
        if (confirmedEl) confirmedEl.textContent = `$${total.toFixed(2)}`;
        
        const pendingEl = document.getElementById('pendingBalance');
        if (pendingEl) pendingEl.textContent = `$${pending.toFixed(2)}`;
        
        const availEl = document.getElementById('availableBalance');
        if (availEl) availEl.textContent = `$${available.toFixed(2)}`;
        
        // Update wallet balances
        const walletBalancesList = document.getElementById('walletBalancesList');
        if (walletBalancesList && balance.wallets) {
          walletBalancesList.innerHTML = balance.wallets.map(w => `
            <div class="card" style="padding:12px;margin-bottom:8px;">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                  <strong>${w.blockchain?.toUpperCase()}</strong>
                  ${w.is_primary ? '<span class="blockchain-badge primary-badge">Primary</span>' : ''}
                </div>
                <div style="text-align:right;">
                  <div style="font-size:14px;font-weight:600;">$${w.balance?.toFixed(2)}</div>
                  <div style="font-size:11px;color:var(--text-secondary);">${w.address.substring(0, 12)}...</div>
                </div>
              </div>
            </div>
          `).join('');
        }
        
        // Update payment history
        const historyResponse = await API._fetch(`/api/v1/payments/history?limit=5`);
        const paymentHistoryList = document.getElementById('paymentHistoryList');
        if (paymentHistoryList && historyResponse.history) {
          paymentHistoryList.innerHTML = historyResponse.history.length ? 
            historyResponse.history.map(tx => `
              <div class="card" style="padding:12px;margin-bottom:8px;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                  <div>
                    <div style="font-weight:600;">${tx.type === 'deposit' ? ' Deposit' : ' Withdrawal'}</div>
                    <div style="font-size:11px;color:var(--text-secondary);">${new Date(tx.created_at).toLocaleString()}</div>
                  </div>
                  <div style="text-align:right;">
                    <div style="font-weight:600;color:${tx.type === 'deposit' ? '#51cf66' : '#ff6b6b'}">${tx.type === 'deposit' ? '+' : '-'}$${tx.amount?.toFixed(2)}</div>
                    <div style="font-size:11px;color:var(--text-secondary)">${tx.status}</div>
                  </div>
                </div>
              </div>
            `).join('') : '<div class="card"><p style="color:var(--text-secondary);">No transactions yet</p></div>';
        }
        
        showStatus('Balance updated', 'success');
      } catch (err) {
        showStatus(`Error: ${err.message}`, 'error');
      }
    },

    async depositQuick() {
      if (!state.wallets.length) {
        showStatus('Please create a wallet first', 'error');
        return;
      }
      
      const primaryWallet = state.wallets.find(w => w.is_primary) || state.wallets[0];
      window.depositModal(primaryWallet.id);
    },

    async quickDeposit() {
      if (!state.wallets.length) {
        showStatus('Please create a wallet first', 'error');
        return;
      }
      
      const primaryWallet = state.wallets.find(w => w.is_primary) || state.wallets[0];
      window.depositModal(primaryWallet.id);
    },

    async quickWithdraw() {
      if (!state.wallets.length) {
        showStatus('Please create a wallet first', 'error');
        return;
      }
      
      const primaryWallet = state.wallets.find(w => w.is_primary) || state.wallets[0];
      window.withdrawalModal(primaryWallet.id);
    },
  };

  window.pageActions = pageActions;

  // ========== INITIALIZATION ==========
  
  async function initWithTelegram() {
    /**
     * Initialize WebApp with real Telegram initData
     * initData MUST be present for all backend communications
     */
    if (typeof window.Telegram === 'undefined' || !window.Telegram.WebApp) {
      showStatus('This app must be opened from Telegram Bot', 'error');
      log('Telegram WebApp SDK not available', 'error');
      return null;
    }

    try {
      // Ready WebApp UI
      if (typeof window.Telegram.WebApp.ready === 'function') {
        window.Telegram.WebApp.ready();
      }
      if (typeof window.Telegram.WebApp.expand === 'function') {
        window.Telegram.WebApp.expand();
      }

      // Get initData - REQUIRED for Telegram signature verification
      let initData = window.Telegram?.WebApp?.initData;
      
      // Fallback: try URL params
      if (!initData) {
        const urlParams = new URLSearchParams(window.location.search);
        initData = urlParams.get('tgWebAppData') || urlParams.get('init_data');
      }

      // Validate initData is present and non-empty
      if (!initData || typeof initData !== 'string' || initData.trim().length === 0) {
        throw new Error(
          'Unable to obtain Telegram authentication data. ' +
          'Please ensure the app is opened from Telegram bot using /start command.'
        );
      }

      log(`Telegram initData received: ${initData.substring(0, 50)}...`);
      showStatus('Authenticating with Telegram...', 'loading');

      // Send initData to backend for signature verification
      const authResult = await API.initSession(initData);
      
      // Check for authentication success
      if (!authResult || !authResult.success) {
        const errorMsg = authResult?.detail || authResult?.error || 'Telegram authentication failed';
        throw new Error(errorMsg);
      }
      
      // Extract user data from response
      const user = authResult?.user;
      if (!user || !user.id) {
        throw new Error('No user data in authentication response');
      }

      // Store user in state
      state.user = user;
      log(`✓ Authenticated: ${user.telegram_username || user.full_name}`);
      return user;
      
    } catch (err) {
      const errorMsg = err.message || 'Unknown authentication error';
      log(`Telegram auth failed: ${errorMsg}`, 'error');
      showStatus(`Authentication Error: ${errorMsg}`, 'error');
      return null;
    }
  }

  async function init() {
    try {
      showStatus('Initializing NFT Platform...', 'loading');
      log('=== App Initialization Starting ===');

      // Initialize image protection system
      applyImageProtectionStyles();
      protectKeyboardShortcuts();

      // Authenticate with Telegram - MUST succeed before proceeding
      const user = await initWithTelegram();
      
      if (!user || !user.id) {
        throw new Error('Telegram authentication failed - cannot proceed without valid user session');
      }

      // User authenticated - update UI
      if (dom.userInfo && state.user) {
        const avatar = state.user.avatar_url 
          ? `<img src="${state.user.avatar_url}" alt="Avatar" style="width:36px;height:36px;border-radius:50%;margin-right:10px;">`
          : '';
        const fullName = state.user.full_name || state.user.telegram_username || 'User';
        dom.userInfo.innerHTML = `${avatar}<div><strong>${fullName}</strong><br><small>@${state.user.telegram_username || 'user'}</small></div>`;
      }

      // Load initial dashboard data
      await loadPageData('dashboard');

      // Apply final image protection
      protectAllImages();

      showStatus('Ready!', 'success');
      log('=== App Initialization Complete ===');

    } catch (err) {
      const errorMsg = err.message || 'Initialization failed';
      log(`Init failed: ${errorMsg}`, 'error');
      showStatus(errorMsg, 'error');
      // Prevent further execution - auth is mandatory
      setTimeout(() => {
        if (dom.app) dom.app.style.opacity = '0.5';
      }, 2000);
    }
  }

  // Start app when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
