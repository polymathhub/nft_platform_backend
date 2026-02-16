/**
 * NFT Platform - Complete Web App v2
 * Production-ready Telegram WebApp with full backend integration
 * All features: Wallets, NFTs, Marketplace, Minting, Transfers
 */

(() => {
  'use strict';

  console.log('=== NFT Platform Web App v2 Initializing ===');

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
        
        let fetchOptions = {
          method,
          headers: {
            'Content-Type': 'application/json',
            ...options.headers,
          },
          timeout: CONFIG.TIMEOUT,
        };
        
        if (options.body) {
          fetchOptions.body = JSON.stringify(options.body);
        }
        
        const response = await fetch(url, fetchOptions);
        const data = await response.json();
        
        if (!response.ok) {
          log(`${method} ${endpoint} failed: ${response.status} - ${JSON.stringify(data)}`, 'error');
          if (attempt < CONFIG.RETRY_ATTEMPTS) {
            await new Promise(r => setTimeout(r, CONFIG.RETRY_DELAY * attempt));
            return this._fetch(endpoint, options, attempt + 1);
          }
          throw new Error(data.detail || `HTTP ${response.status}`);
        }
        
        log(`${method} ${endpoint} succeeded`, 'log');
        return data;
      } catch (err) {
        log(`API error on attempt ${attempt}: ${err.message}`, 'error');
        if (attempt < CONFIG.RETRY_ATTEMPTS) {
          await new Promise(r => setTimeout(r, CONFIG.RETRY_DELAY * attempt));
          return this._fetch(endpoint, options, attempt + 1);
        }
        throw err;
      }
    },

    // Auth endpoints
    async initSession(initData) {
      return this._fetch(`/web-app/init?init_data=${encodeURIComponent(initData)}`);
    },

    // User endpoints
    async getUser(userId) {
      return this._fetch(`/web-app/user?user_id=${userId}`);
    },

    // Wallet endpoints
    async getWallets(userId) {
      return this._fetch(`/web-app/wallets?user_id=${userId}`);
    },

    async createWallet(blockchain, walletType = 'custodial', isPrimary = false) {
      return this._fetch(`/web-app/create-wallet`, {
        method: 'POST',
        body: { blockchain, wallet_type: walletType, is_primary: isPrimary }
      });
    },

    async importWallet(blockchain, address, publicKey = null, isPrimary = false) {
      return this._fetch(`/web-app/import-wallet`, {
        method: 'POST',
        body: { blockchain, address, public_key: publicKey, is_primary: isPrimary }
      });
    },

    async setPrimaryWallet(walletId) {
      return this._fetch(`/web-app/set-primary`, {
        method: 'POST',
        body: { wallet_id: walletId }
      });
    },

    // NFT endpoints
    async getNfts(userId) {
      return this._fetch(`/web-app/nfts?user_id=${userId}`);
    },

    async mintNft(walletId, nftName, description, imageUrl = null) {
      return this._fetch(`/web-app/mint`, {
        method: 'POST',
        body: {
          wallet_id: walletId,
          nft_name: nftName,
          nft_description: description,
          image_url: imageUrl,
        }
      });
    },

    async burnNft(nftId) {
      return this._fetch(`/web-app/burn`, {
        method: 'POST',
        body: { nft_id: nftId }
      });
    },

    async transferNft(nftId, toAddress) {
      return this._fetch(`/web-app/transfer`, {
        method: 'POST',
        body: { nft_id: nftId, to_address: toAddress }
      });
    },

    // Marketplace endpoints
    async getMarketplaceListings(limit = 50) {
      return this._fetch(`/web-app/marketplace/listings?limit=${limit}`);
    },

    async getMyListings(userId) {
      return this._fetch(`/web-app/marketplace/mylistings?user_id=${userId}`);
    },

    async listNft(nftId, price, currency = 'USD') {
      return this._fetch(`/web-app/list-nft`, {
        method: 'POST',
        body: { nft_id: nftId, price: parseFloat(price), currency }
      });
    },

    async makeOffer(listingId, offerPrice) {
      return this._fetch(`/web-app/make-offer`, {
        method: 'POST',
        body: { listing_id: listingId, offer_price: parseFloat(offerPrice) }
      });
    },

    async cancelListing(listingId) {
      return this._fetch(`/web-app/cancel-listing`, {
        method: 'POST',
        body: { listing_id: listingId }
      });
    },

    // Dashboard endpoints
    async getDashboardData(userId) {
      return this._fetch(`/web-app/dashboard-data?user_id=${userId}`);
    },
  };

  // ========== UI UPDATES ==========

  function formatAddress(addr) {
    if (!addr || addr.length < 10) return addr;
    return addr.slice(0, 6) + '...' + addr.slice(-4);
  }

  function formatCurrency(num) {
    return parseFloat(num).toFixed(2);
  }

  async function updateDashboard() {
    try {
      showStatus('Loading dashboard...', 'loading');
      
      const dashData = await API.getDashboardData(state.user.id);
      
      if (!dashData.success) throw new Error(dashData.error || 'Failed to load dashboard');
      
      const wallets = dashData.wallets || [];
      const nfts = dashData.nfts || [];
      const listings = dashData.listings || [];
      
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
                <strong>${w.blockchain?.toUpperCase()}</strong>
                ${w.is_primary ? '<span class="blockchain-badge primary-badge">Primary</span>' : ''}
              </div>
              <code style="font-size:11px;">${formatAddress(w.address)}</code>
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
              ${nft.image_url ? `<img src="${nft.image_url}" alt="${nft.name}" style="width:40px;height:40px;border-radius:4px;">` : ''}
              <div style="flex:1;min-width:0;">
                <strong>${nft.name}</strong>
                <div style="font-size:12px;color:var(--text-secondary);">${nft.blockchain?.toUpperCase()}</div>
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
      showStatus('Loading wallets...', 'loading');
      
      const data = await API.getWallets(state.user.id);
      if (!data.success) throw new Error(data.error || 'Failed to load wallets');
      
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
              <strong>${w.blockchain?.toUpperCase() || 'Wallet'}</strong>
              ${w.is_primary ? '<span class="blockchain-badge primary-badge">Primary</span>' : ''}
            </div>
            <small style="color:var(--text-secondary);">${new Date(w.created_at).toLocaleDateString()}</small>
          </div>
          <code style="display:block;word-break:break-all;padding:12px;background:rgba(0,0,0,0.2);border-radius:4px;font-size:11px;margin-bottom:12px;">${w.address}</code>
          <div style="display:flex;gap:10px;">
            <button class="btn btn-secondary" onclick="window.showWalletDetails('${w.id}')">Details</button>
            ${!w.is_primary ? `<button class="btn btn-secondary" onclick="window.setPrimary('${w.id}')">Set Primary</button>` : ''}
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
          ${nft.image_url ? `
            <div style="width:100%;height:200px;background:linear-gradient(135deg,#7c5cff,#4c6ef5);border-radius:8px;margin-bottom:12px;background-image:url('${nft.image_url}');background-size:cover;background-position:center;"></div>
          ` : ''}
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
          ${listing.image_url ? `
            <div style="width:100%;height:200px;background:linear-gradient(135deg,#7c5cff,#4c6ef5);border-radius:8px;margin-bottom:12px;background-image:url('${listing.image_url}');background-size:cover;background-position:center;"></div>
          ` : ''}
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
              <strong>${state.user.is_verified ? 'Verified ✓' : 'Unverified'}</strong>
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

  // ========== MODAL FUNCTIONS ==========

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

  window.showNftDetails = function(nftId) {
    const nft = state.nfts.find(n => n.id === nftId);
    if (!nft) return;
    
    showModal(`${nft.name}`, `
      ${nft.image_url ? `<img src="${nft.image_url}" alt="${nft.name}" style="width:100%;max-height:200px;border-radius:8px;margin-bottom:12px;">` : ''}
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
      const currency = document.getElementById('listCurrency')?.value || 'USD';
      
      if (!price) throw new Error('Please enter a price');
      
      showStatus('Listing NFT...', 'loading');
      const result = await API.listNft(nftId, price, currency);
      
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
      
      showStatus('Submitting offer...', 'loading');
      const result = await API.makeOffer(listingId, price);
      
      if (!result.success) throw new Error(result.error || 'Failed to submit offer');
      
      closeModal();
      showStatus('Offer submitted!', 'success');
      await updateMarketplaceList();
    } catch (err) {
      showStatus(`Error: ${err.message}`, 'error');
    }
  };

  window.closeModal = closeModal;

  // ========== NAVIGATION ==========
  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const pageName = item.dataset.page;
      if (pageName) switchPage(pageName);
    });
  });

  // ========== PAGE ACTIONS ==========
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

    async submitCreateWallet() {
      try {
        const blockchain = document.getElementById('blockchainSelect')?.value;
        const isPrimary = document.getElementById('setPrimary')?.checked === true;
        
        showStatus('Creating wallet...', 'loading');
        const result = await API.createWallet(blockchain, 'custodial', isPrimary);
        
        if (!result.success) throw new Error(result.error || 'Failed to create wallet');
        
        closeModal();
        showStatus('Wallet created!', 'success');
        await updateWalletsList();
      } catch (err) {
        showStatus(`Error: ${err.message}`, 'error');
      }
    },

    async mintNft() {
      if (!state.wallets.length) {
        showStatus('Please create a wallet first', 'error');
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
            <input type="url" id="mintImage" placeholder="https://..." style="width:100%;padding:10px;border:1px solid var(--border);border-radius:4px;background:rgba(0,0,0,0.2);color:#fff;">
          </div>
        </div>
      `, [
        { label: 'Mint', action: 'pageActions.submitMint()', class: 'btn-primary' },
        { label: 'Cancel', action: 'closeModal()', class: 'btn-secondary' }
      ]);
    },

    async submitMint() {
      try {
        const walletId = document.getElementById('mintWalletSelect')?.value;
        const name = document.getElementById('mintName')?.value;
        const desc = document.getElementById('mintDesc')?.value;
        const image = document.getElementById('mintImage')?.value;
        
        if (!name) throw new Error('Please enter an NFT name');
        
        showStatus('Minting NFT...', 'loading');
        const result = await API.mintNft(walletId, name, desc, image || null);
        
        if (!result.success) throw new Error(result.error || 'Failed to mint NFT');
        
        closeModal();
        showStatus('NFT minted successfully!', 'success');
        await updateNftList();
      } catch (err) {
        showStatus(`Error: ${err.message}`, 'error');
      }
    },
  };

  window.pageActions = pageActions;

  // ========== INITIALIZATION ==========
  async function init() {
    try {
      showStatus('Initializing NFT Platform...', 'loading');
      log('Initialization started');

      // Check for Telegram WebApp
      if (typeof window.Telegram === 'undefined' || !window.Telegram.WebApp) {
        throw new Error('This app must be opened in Telegram');
      }

      // Initialize Telegram WebApp
      window.Telegram.WebApp.ready?.();
      window.Telegram.WebApp.expand?.();

      const initData = window.Telegram?.WebApp?.initData;
      if (!initData) {
        throw new Error('Failed to get Telegram init data');
      }

      log(`Init data received (${initData.length} bytes)`);
      showStatus('Authenticating...', 'loading');

      // Get session and user
      const authResult = await API.initSession(initData);
      if (!authResult.success || !authResult.user) {
        throw new Error(authResult.error || 'Authentication failed');
      }

      state.user = authResult.user;
      log(`Authenticated: ${state.user.telegram_username}`);

      // Update user info in header
      if (dom.userInfo) {
        const avatar = state.user.avatar_url ? `<img src="${state.user.avatar_url}" alt="Avatar" style="width:36px;height:36px;border-radius:50%;margin-right:10px;">` : '';
        dom.userInfo.innerHTML = `${avatar}<div><strong>${state.user.full_name}</strong><br><small>@${state.user.telegram_username}</small></div>`;
      }

      // Load initial data
      await loadPageData('dashboard');

      showStatus('Ready!', 'success');
      log('Initialization complete');

    } catch (err) {
      log(`Init error: ${err.message}`, 'error');
      showStatus(err.message, 'error');
      
      setTimeout(() => {
        showStatus('Check browser console (F12) for details', 'info');
      }, 3000);
    }
  }

  // Start app when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
