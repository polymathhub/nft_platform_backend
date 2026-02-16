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
    const avatar = state.user?.avatar_url ? `<img src="${state.user.avatar_url}" alt="Avatar" style="width:32px;height:32px;border-radius:50%;margin-right:8px;">` : '';
    userInfo.innerHTML = `${avatar}<div><strong>${truncate(name, 20)}</strong><br><small>@${truncate(state.user?.telegram_username || 'anon', 15)}</small></div>`;
  }

  function updateDashboard() {
    const portfolioValue = (state.nfts.length * 100).toFixed(2);
    const safeSet = (id, value) => {
      const el = document.getElementById(id);
      if (el) el.textContent = value;
    };

    safeSet('totalWallets', state.wallets.length);
    safeSet('totalNfts', state.nfts.length);
    safeSet('totalListings', state.listings.filter(l => l.active).length);
    safeSet('portfolioValue', `$${portfolioValue}`);

    // Update profile Section
    const profileInfo = document.getElementById('profileInfo');
    if (profileInfo && state.user) {
      profileInfo.innerHTML = `
        <div class="profile-item"><span>Name:</span><strong>${state.user.full_name || 'N/A'}</strong></div>
        <div class="profile-item"><span>Username:</span><strong>@${state.user.telegram_username || 'N/A'}</strong></div>
        <div class="profile-item"><span>Telegram ID:</span><code style="font-size:11px;">${state.user.telegram_id || 'N/A'}</code></div>
        <div class="profile-item"><span>Status:</span><strong>${state.user.is_verified ? 'Verified' : 'Unverified'}</strong></div>
        <div class="profile-item"><span>Role:</span><strong style="text-transform:capitalize;">${state.user.user_role || 'user'}</strong></div>
        <div class="profile-item"><span>Joined:</span><strong>${state.user.created_at ? new Date(state.user.created_at).toLocaleDateString() : 'N/A'}</strong></div>
      `;
    }

    const profileStats = document.getElementById('profileStats');
    if (profileStats) {
      profileStats.innerHTML = `
        <div class="stat-box"><div class="stat-label">Wallets</div><div class="stat-value">${state.wallets.length}</div></div>
        <div class="stat-box"><div class="stat-label">NFTs</div><div class="stat-value">${state.nfts.length}</div></div>
        <div class="stat-box"><div class="stat-label">Listings</div><div class="stat-value">${state.listings.filter(l => l.active).length}</div></div>
        <div class="stat-box"><div class="stat-label">Value</div><div class="stat-value">$${portfolioValue}</div></div>
      `;
    }
  }

  function updateWalletsList() {
    const container = document.getElementById('walletsList');
    if (!container) return;
    
    if (!state.wallets.length) {
      container.innerHTML = '<div class="card"><p class="muted">No wallets yet. Create one to get started.</p></div>';
      return;
    }

    container.innerHTML = state.wallets.map(w => `
      <div class="card wallet-card">
        <div class="wallet-header">
          <div class="wallet-blockchain">
            <strong>${w.blockchain?.toUpperCase() || 'Wallet'}</strong>
            ${w.is_primary ? '<span class="blockchain-badge primary-badge">Primary</span>' : ''}
          </div>
          <small class="muted">${new Date(w.created_at || Date.now()).toLocaleDateString()}</small>
        </div>
        <div class="wallet-address" style="word-break:break-all;margin:12px 0;font-family:monospace;font-size:12px;color:var(--text-secondary);">${w.address}</div>
        <div class="wallet-actions">
          <button class="btn btn-secondary" style="flex:1;" onclick="window.showWalletDetails('${w.id}')">Details</button>
          ${!w.is_primary ? `<button class="btn btn-secondary" style="flex:1;margin-left:8px;" onclick="window.setPrimary('${w.id}')">Make Primary</button>` : ''}
        </div>
      </div>
    `).join('');
  }

  function updateNftsList() {
    const container = document.getElementById('nftList');
    if (!container) return;

    if (!state.nfts.length) {
      container.innerHTML = '<div class="card"><p class="muted">No NFTs yet. Mint one to get started.</p></div>';
      return;
    }

    container.innerHTML = state.nfts.map((nft, idx) => `
      <div class="card nft-card" data-nft-id="${nft.id || idx}">
        <div class="nft-image">
          ${nft.image_url ? `<img src="${nft.image_url}" alt="${nft.name}" loading="lazy" style="width:100%;height:100%;object-fit:cover;" onerror="this.style.display='none'">` : '<div style="background:linear-gradient(135deg,var(--primary),var(--secondary));height:200px;display:flex;align-items:center;justify-content:center;color:white;font-weight:bold;">NFT</div>'}
        </div>
        <div class="nft-content">
          <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:8px;">
            <div class="nft-name">${truncate(nft.name, 22)}</div>
            <span class="blockchain-badge" style="font-size:11px;">${nft.blockchain?.toUpperCase() || 'NFT'}</span>
          </div>
          <small class="muted">Status: ${nft.status || 'Owned'}</small>
          <div class="wallet-actions" style="margin-top:12px;">
            <button class="btn btn-secondary" style="flex:1;font-size:12px;" onclick="window.showNFTDetails('${nft.id || idx}')">View</button>
            <button class="btn btn-secondary" style="flex:1;margin-left:8px;font-size:12px;" onclick="window.listNFTModal('${nft.id || idx}')">Sell</button>
          </div>
        </div>
      </div>
    `).join('');
  }

  function updateMarketplace() {
    const listings = document.getElementById('marketplaceListings');
    if (!listings) return;

    if (!state.marketplaceListings.length) {
      listings.innerHTML = '<div class="card"><p class="muted">No listings available. Check back soon!</p></div>';
      return;
    }

    listings.innerHTML = state.marketplaceListings.map((l, idx) => `
      <div class="card nft-card" data-listing-id="${l.id || idx}">
        <div class="nft-image">
          ${l.image_url ? `<img src="${l.image_url}" alt="${l.nft_name}" loading="lazy" style="width:100%;height:100%;object-fit:cover;" onerror="this.style.display='none'">` : '<div style="background:linear-gradient(135deg,var(--secondary),var(--primary));height:200px;display:flex;align-items:center;justify-content:center;color:white;font-weight:bold;">NFT</div>'}
        </div>
        <div class="nft-content">
          <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:8px;">
            <div class="nft-name">${truncate(l.nft_name || 'NFT', 20)}</div>
            <span class="blockchain-badge" style="font-size:11px;">${l.blockchain?.toUpperCase() || 'NFT'}</span>
          </div>
          ${l.seller_name ? `<small class="muted">By ${truncate(l.seller_name, 18)}</small>` : ''}
          <div style="margin:8px 0;">
            <div style="color:var(--primary);font-weight:bold;font-size:1.1rem;">${l.price?.toFixed(2) || '0.00'} ${l.currency || 'ETH'}</div>
          </div>
          <div class="wallet-actions" style="margin-top:12px;">
            <button class="btn btn-primary" style="flex:1;font-size:12px;" onclick="window.makeOfferPrompt('${l.id || idx}')">Buy Now</button>
            <button class="btn btn-secondary" style="flex:1;margin-left:8px;font-size:12px;" onclick="window.viewListing('${l.id || idx}')">Details</button>
          </div>
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
        <div class="profile-item"><span>Address:</span><code style="word-break:break-all;font-size:11px;">${wallet.address}</code></div>
        <div class="profile-item"><span>Primary:</span><strong>${wallet.is_primary ? 'Yes' : 'No'}</strong></div>
        <div class="profile-item"><span>Created:</span><strong>${new Date(wallet.created_at || Date.now()).toLocaleDateString()}</strong></div>
      </div>
      ${!wallet.is_primary ? `<button class="btn btn-secondary btn-block" onclick="window.setPrimary('${wallet.id}')">Set as Primary</button>` : ''}
      <button class="btn btn-secondary btn-block" style="margin-top:8px;" onclick="window.closeModal()">Close</button>
    `);
  };

  window.showNFTDetails = function(nftId) {
    const nft = state.nfts.find(n => n.id === nftId);
    if (!nft) return;
    showModal('NFT Details', `
      ${nft.image_url ? `<img src="${nft.image_url}" alt="${nft.name}" style="width:100%;max-height:300px;object-fit:cover;border-radius:8px;margin-bottom:16px;">` : ''}
      <div class="profile-section">
        <div class="profile-item"><span>Name:</span><strong>${nft.name}</strong></div>
        <div class="profile-item"><span>Blockchain:</span><strong>${nft.blockchain?.toUpperCase()}</strong></div>
        <div class="profile-item"><span>Status:</span><strong>${nft.status || 'Owned'}</strong></div>
        ${nft.description ? `<div class="profile-item"><span>Description:</span><p style="margin-top:8px;">${nft.description}</p></div>` : ''}
        ${nft.minted_at ? `<div class="profile-item"><span>Minted:</span><strong>${new Date(nft.minted_at).toLocaleDateString()}</strong></div>` : ''}
      </div>
      <button class="btn btn-primary btn-block" onclick="window.listNFTModal('${nftId}')">List for Sale</button>
      <button class="btn btn-secondary btn-block" style="margin-top:8px;" onclick="window.closeModal()">Close</button>
    `);
  };

  window.listNFTModal = function(nftId) {
    const nft = state.nfts.find(n => n.id === nftId);
    if (!nft) return;
    showModal('List NFT for Sale', `
      <div class="form-group">
        <label>NFT: <strong>${nft.name}</strong></label>
      </div>
      <div class="form-group">
        <label>Price</label>
        <input type="number" id="listPrice" class="input-text" placeholder="0.00" min="0" step="0.01" />
      </div>
      <div class="form-group">
        <label>Currency</label>
        <select id="listCurrency" class="input-select">
          <option value="ETH">ETH</option>
          <option value="MATIC">MATIC</option>
          <option value="SOL">SOL</option>
          <option value="USD">USD</option>
        </select>
      </div>
      <button class="btn btn-primary btn-block" onclick="window.submitListNFT('${nftId}')">List NFT</button>
    `);
  };

  window.submitListNFT = async function(nftId) {
    const price = document.getElementById('listPrice')?.value;
    const currency = document.getElementById('listCurrency')?.value;
    if (!price || !currency || !state.user) {
      showStatus('Please fill all fields', 'error');
      return;
    }

    try {
      showStatus('Listing NFT...', 'loading');
      await API.listNFT(state.user.id, nftId, price, currency);
      showStatus('NFT listed successfully!', 'success');
      closeModal();
      await loadDashboard();
    } catch (err) {
      showStatus(`Error listing NFT: ${err.message}`, 'error');
    }
  };

  window.makeOfferPrompt = function(listingId) {
    const listing = state.marketplaceListings.find(l => l.id === listingId);
    if (!listing) return;
    showModal('Make Offer', `
      <div class="profile-section">
        <div class="profile-item"><span>NFT:</span><strong>${listing.nft_name}</strong></div>
        <div class="profile-item"><span>Listed Price:</span><strong>${listing.price?.toFixed(2)} ${listing.currency || 'ETH'}</strong></div>
      </div>
      <div class="form-group">
        <label>Your Offer</label>
        <input type="number" id="offerPrice" class="input-text" placeholder="Your offer amount" min="0" step="0.01" />
      </div>
      <button class="btn btn-primary btn-block" onclick="window.submitOffer('${listingId}')">Submit Offer</button>
      <button class="btn btn-secondary btn-block" style="margin-top:8px;" onclick="window.closeModal()">Cancel</button>
    `);
  };

  window.submitOffer = async function(listingId) {
    const offerPrice = document.getElementById('offerPrice')?.value;
    if (!offerPrice || !state.user) {
      showStatus('Please enter an offer amount', 'error');
      return;
    }

    try {
      showStatus('Submitting offer...', 'loading');
      await API.makeOffer(state.user.id, listingId, offerPrice);
      showStatus('Offer submitted!', 'success');
      closeModal();
      await loadDashboard();
    } catch (err) {
      showStatus(`Error submitting offer: ${err.message}`, 'error');
    }
  };

  window.viewListing = function(listingId) {
    const listing = state.marketplaceListings.find(l => l.id === listingId);
    if (!listing) return;
    showModal('NFT Listing Details', `
      ${listing.image_url ? `<img src="${listing.image_url}" alt="${listing.nft_name}" style="width:100%;max-height:250px;object-fit:cover;border-radius:8px;margin-bottom:16px;">` : ''}
      <div class="profile-section">
        <div class="profile-item"><span>NFT:</span><strong>${listing.nft_name || 'Unknown'}</strong></div>
        <div class="profile-item"><span>Seller:</span><strong>${listing.seller_name || 'Anonymous'}</strong></div>
        <div class="profile-item"><span>Price:</span><strong style="color:var(--primary);">${listing.price?.toFixed(2) || '0.00'} ${listing.currency || 'ETH'}</strong></div>
        ${listing.blockchain ? `<div class="profile-item"><span>Blockchain:</span><strong>${listing.blockchain.toUpperCase()}</strong></div>` : ''}
        ${listing.nft_description ? `<div class="profile-item"><span>Description:</span><p style="margin-top:8px;">${listing.nft_description}</p></div>` : ''}
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
          <option value="">-- Choose a blockchain --</option>
          <option value="ethereum">Ethereum (ETH)</option>
          <option value="polygon">Polygon (MATIC)</option>
          <option value="solana">Solana (SOL)</option>
          <option value="ton">TON Blockchain</option>
        </select>
      </div>
      <p class="muted" style="font-size:12px;margin-bottom:16px;">A new wallet will be created on the selected blockchain.</p>
      <button class="btn btn-primary btn-block" onclick="window.submitCreateWallet()">Create Wallet</button>
      <button class="btn btn-secondary btn-block" style="margin-top:8px;" onclick="window.closeModal()">Cancel</button>
    `);
  };

  window.importWalletModal = function() {
    showModal('Import Existing Wallet', `
      <div class="form-group">
        <label>Wallet Address</label>
        <input type="text" id="importAddr" placeholder="0x1234...abcd" class="input-text">
      </div>
      <div class="form-group">
        <label>Blockchain</label>
        <select id="importChain" class="input-select">
          <option value="">-- Choose a blockchain --</option>
          <option value="ethereum">Ethereum (ETH)</option>
          <option value="polygon">Polygon (MATIC)</option>
          <option value="solana">Solana (SOL)</option>
          <option value="ton">TON Blockchain</option>
        </select>
      </div>
      <p class="muted" style="font-size:12px;margin-bottom:16px;">Enter an existing wallet address to import it.</p>
      <button class="btn btn-primary btn-block" onclick="window.submitImportWallet()">Import Wallet</button>
      <button class="btn btn-secondary btn-block" style="margin-top:8px;" onclick="window.closeModal()">Cancel</button>
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
      
      showStatus('Loading your dashboard...', 'loading');
      log(`Fetching data for: ${state.user.telegram_username || state.user.id}`);

      // Fetch user's dashboard data (wallets, NFTs, listings)
      let dashboardData = null;
      try {
        dashboardData = await API.getDashboardData(state.user.id);
      } catch (err) {
        log(`Dashboard fetch failed: ${err.message}`, 'error');
        dashboardData = { success: true, wallets: [], nfts: [], listings: [] };
      }

      if (!dashboardData?.success) {
        log('Invalid dashboard response, using empty defaults', 'warn');
        dashboardData = { success: true, wallets: [], nfts: [], listings: [] };
      }

      state.wallets = dashboardData.wallets || [];
      state.nfts = dashboardData.nfts || [];
      state.listings = dashboardData.listings || [];

      log(`Loaded: ${state.wallets.length} wallets, ${state.nfts.length} NFTs, ${state.listings.length} listings`, 'success');

      // Fetch marketplace listings (available for purchase)
      let marketData = null;
      try {
        marketData = await API.getMarketplaceListings(50);
        state.marketplaceListings = marketData?.listings || [];
        log(`Marketplace: ${state.marketplaceListings.length} listings available`, 'success');
      } catch (err) {
        log(`Marketplace fetch failed: ${err.message}`, 'warn');
        state.marketplaceListings = [];
      }

      // Populate user info and dashboard UI
      updateUserInfo();
      updateDashboard();
      updateWalletsList();
      updateNftsList();
      updateMarketplace();

      // Reinitialize event listeners now that DOM is updated with data
      setupEvents();

      showStatus('Dashboard loaded!', 'success');
      log('All data loaded successfully');

      setTimeout(() => {
        if (status) status.style.display = 'none';
      }, 2000);

    } catch (err) {
      log(`Dashboard error: ${err.message}`, 'error');
      showStatus(`Error: ${err.message}`, 'error');
      
      // Render empty state
      updateDashboard();
      updateWalletsList();
      updateNftsList();
      updateMarketplace();
      setupEvents();
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

    // Mint form
    const mintBtn = document.getElementById('mintNftBtn');
    if (mintBtn) {
      mintBtn.addEventListener('click', async () => {
        const name = document.getElementById('mintName')?.value?.trim();
        const desc = document.getElementById('mintDesc')?.value?.trim();
        const imageUrl = document.getElementById('mintImage')?.value?.trim() || null;
        const walletId = document.getElementById('mintWalletSelect')?.value;

        if (!name || !desc) {
          showStatus('Please fill in Name and Description', 'error');
          return;
        }

        if (!walletId || !state.user) {
          showStatus('Please select a wallet', 'error');
          return;
        }

        try {
          showStatus('Creating NFT...', 'loading');
          await API.mintNFT(state.user.id, walletId, name, desc, imageUrl);
          showStatus('NFT created successfully!', 'success');
          document.getElementById('mintName').value = '';
          document.getElementById('mintDesc').value = '';
          document.getElementById('mintImage').value = '';
          document.getElementById('mintAttributes').value = '';
          await loadDashboard();
          switchPage('nfts');
        } catch (err) {
          showStatus(`Error creating NFT: ${err.message}`, 'error');
        }
      });
    }

    // Populate mint wallet dropdown after dashboard loads
    const mintSelect = document.getElementById('mintWalletSelect');
    if (mintSelect && state.wallets.length > 0) {
      mintSelect.innerHTML = `<option value="">-- Select wallet --</option>` + state.wallets.map(w => 
        `<option value="${w.id}">${w.blockchain?.toUpperCase()} - ${formatAddr(w.address)}</option>`
      ).join('');
    }

    // Marketplace tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const tab = btn.dataset.tab;
        const marketListings = document.getElementById('marketplaceListings');
        const myListings = document.getElementById('myListings');
        
        if (tab === 'listings') {
          if (marketListings) marketListings.style.display = 'grid';
          if (myListings) myListings.style.display = 'none';
        } else {
          if (marketListings) marketListings.style.display = 'none';
          if (myListings) myListings.style.display = 'grid';
        }
      });
    });

    // NFT filter
    const nftFilter = document.getElementById('nftFilter');
    if (nftFilter) {
      nftFilter.addEventListener('change', (e) => {
        const filter = e.target.value;
        document.querySelectorAll('[data-nft-id]').forEach(card => {
          if (filter === 'all') {
            card.style.display = 'block';
          } else if (filter === 'listed') {
            card.style.display = card.dataset.status === 'listed' ? 'block' : 'none';
          } else if (filter === 'unlisted') {
            card.style.display = card.dataset.status !== 'listed' ? 'block' : 'none';
          }
        });
      });
    }

    // Search marketplace
    const searchInput = document.getElementById('searchMarketplace');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        document.querySelectorAll('[data-listing-id]').forEach(card => {
          const title = card.querySelector('.nft-name')?.textContent || '';
          card.style.display = title.toLowerCase().includes(query) ? 'block' : 'none';
        });
      });
    }

    // Sort marketplace
    const sortSelect = document.getElementById('sortMarketplace');
    if (sortSelect) {
      sortSelect.addEventListener('change', (e) => {
        const sort = e.target.value;
        log(`Sort method: ${sort}`, 'info');
        // In production, would re-fetch with sort parameter
      });
    }
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
