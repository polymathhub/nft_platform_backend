(async function() {
  'use strict';

  // ========== STATE & CONFIG ==========
  const state = {
    user: null,
    wallets: [],
    nfts: [],
    listings: [],
    myListings: [],
    balance: 0,
    referralInfo: null,
    currentPage: 'dashboard',
    loading: false
  };

  const API_BASE = '/api/v1';
  
  // DOM Elements
  const status = document.getElementById('status');
  const statusText = document.getElementById('statusText');
  const statusSpinner = document.getElementById('statusSpinner');
  const modal = document.getElementById('modal');
  const modalContent = document.getElementById('modalContent') || document.getElementById('modalBody');
  const modalTitle = document.getElementById('modalTitle');
  const modalSpinner = document.getElementById('modalSpinner');
  const closeModalBtn = document.getElementById('closeModal');
  const modalOverlay = document.getElementById('modalOverlay');

  // ========== UTILITY FUNCTIONS ==========
  function showStatus(message, type = 'info', showSpinner = false) {
    if (!status || !statusText) return;
    statusText.textContent = message;
    status.className = `status status-${type}`;
    if (showSpinner) {
      if (statusSpinner) statusSpinner.classList.remove('hidden');
      status.classList.remove('hidden');
    } else {
      if (statusSpinner) statusSpinner.classList.add('hidden');
      status.classList.remove('hidden');
      setTimeout(() => status.classList.add('hidden'), 3000);
    }
  }

  function showModal(title, htmlContent, showSpinner = false) {
    if (!modal || !modalContent || !modalTitle) return;
    modalTitle.textContent = title;
    modalContent.innerHTML = htmlContent;
    modal.classList.remove('hidden');
    if (showSpinner) {
      if (modalSpinner) modalSpinner.classList.remove('hidden');
    } else {
      if (modalSpinner) modalSpinner.classList.add('hidden');
    }
  }

  function closeModal() {
    if (modal) modal.classList.add('hidden');
    if (modalContent) modalContent.innerHTML = '';
    if (modalSpinner) modalSpinner.classList.add('hidden');
  }

  function escapeHtml(text) {
    if (!text) return '';
    const map = {
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, m => map[m]);
  }

  function formatAddr(addr) {
    if (!addr) return 'N/A';
    return addr.length > 20 ? addr.slice(0, 10) + '...' + addr.slice(-8) : addr;
  }

  function truncate(str, len = 20) {
    return str && str.length > len ? str.slice(0, len - 3) + '...' : str;
  }

  function switchPage(pageName) {
    document.querySelectorAll('.page').forEach(p => p.classList.add('hidden'));
    document.querySelectorAll('[data-nav]').forEach(n => n.classList.remove('active'));
    
    const page = document.getElementById(`${pageName}-page`);
    if (page) {
      page.classList.remove('hidden');
      document.querySelector(`[data-nav="${pageName}"]`)?.classList.add('active');
    }

    const titles = {
      dashboard: 'Dashboard',
      wallets: 'Wallets',
      nfts: 'My NFTs',
      mint: 'Mint NFT',
      marketplace: 'Marketplace',
      balance: 'Balance',
      referral: 'Referrals',
      profile: 'Profile'
    };
    
    const pageTitle = document.getElementById('pageTitle');
    if (pageTitle) pageTitle.textContent = titles[pageName] || 'NFT Platform';
    state.currentPage = pageName;
  }

  // ========== API SERVICE ==========
  const API = {
    async callEndpoint(urlOrPath, options = {}) {
      const url = urlOrPath.startsWith('http') ? urlOrPath : `${API_BASE}${urlOrPath}`;
      try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 30000); // 30s timeout
        
        const response = await fetch(url, {
          method: options.method || 'GET',
          headers: { 
            'Content-Type': 'application/json',
            ...options.headers 
          },
          body: options.body ? JSON.stringify(options.body) : undefined,
          signal: controller.signal
        });
        
        clearTimeout(timeout);
        
        if (!response.ok) {
          const errorText = await response.text();
          const msg = response.status === 401 ? 'Unauthorized' : 
                      response.status === 404 ? 'Not found' :
                      response.status === 500 ? 'Server error' :
                      `HTTP ${response.status}`;
          throw new Error(`${msg}: ${errorText.slice(0, 100)}`);
        }
        return await response.json();
      } catch (err) {
        if (err.name === 'AbortError') {
          console.error(`API Timeout [${url}]`);
          throw new Error('Request timeout - please check your connection');
        }
        if (err instanceof TypeError && err.message.includes('Failed to fetch')) {
          console.error(`API Network Error [${url}]`);
          throw new Error('Network error - unable to reach server');
        }
        console.error(`API Error [${url}]:`, err);
        throw err;
      }
    },

    // AUTH
    async initSession(initData) {
      return this.callEndpoint(`/telegram/web-app/init?init_data=${encodeURIComponent(initData)}`);
    },

    // USER
    async getUser(userId) {
      return this.callEndpoint(`/telegram/web-app/user?user_id=${userId}`);
    },

    async getDashboardData(userId) {
      return this.callEndpoint(`/telegram/web-app/dashboard-data?user_id=${userId}`);
    },

    // WALLETS
    async getWallets(userId) {
      return this.callEndpoint(`/telegram/web-app/wallets?user_id=${userId}`);
    },

    async createWallet(userId, blockchain) {
      return this.callEndpoint('/telegram/web-app/create-wallet', {
        method: 'POST',
        body: { user_id: userId, blockchain }
      });
    },

    async importWallet(userId, address, blockchain) {
      return this.callEndpoint('/telegram/web-app/import-wallet', {
        method: 'POST',
        body: { user_id: userId, address, blockchain }
      });
    },

    async setPrimaryWallet(userId, walletId, blockchain) {
      return this.callEndpoint('/telegram/web-app/set-primary', {
        method: 'POST',
        body: { user_id: userId, wallet_id: walletId, blockchain }
      });
    },

    // NFTs
    async getNFTs(userId) {
      return this.callEndpoint(`/telegram/web-app/nfts?user_id=${userId}`);
    },

    async mintNFT(userId, walletId, name, description) {
      return this.callEndpoint('/telegram/web-app/mint', {
        method: 'POST',
        body: { user_id: userId, wallet_id: walletId, nft_name: name, nft_description: description }
      });
    },

    async transferNFT(userId, nftId, toAddress) {
      return this.callEndpoint('/telegram/web-app/transfer', {
        method: 'POST',
        body: { user_id: userId, nft_id: nftId, to_address: toAddress }
      });
    },

    async burnNFT(userId, nftId) {
      return this.callEndpoint('/telegram/web-app/burn', {
        method: 'POST',
        body: { user_id: userId, nft_id: nftId }
      });
    },

    // MARKETPLACE
    async listNFT(userId, nftId, price, currency = 'ETH') {
      return this.callEndpoint('/telegram/web-app/list-nft', {
        method: 'POST',
        body: { user_id: userId, nft_id: nftId, price: parseFloat(price), currency }
      });
    },

    async getMarketplaceListings(limit = 100) {
      return this.callEndpoint(`/telegram/web-app/marketplace/listings?limit=${limit}`);
    },

    async getMyListings(userId) {
      return this.callEndpoint(`/telegram/web-app/marketplace/mylistings?user_id=${userId}`);
    },

    async makeOffer(userId, listingId, offerPrice) {
      return this.callEndpoint('/telegram/web-app/make-offer', {
        method: 'POST',
        body: { user_id: userId, listing_id: listingId, offer_price: parseFloat(offerPrice) }
      });
    },

    async cancelListing(userId, listingId) {
      return this.callEndpoint('/telegram/web-app/cancel-listing', {
        method: 'POST',
        body: { user_id: userId, listing_id: listingId }
      });
    },

    // BALANCE & PAYMENTS
    async getBalance(userId) {
      return this.callEndpoint(`/payments/balance?user_id=${userId}`);
    },

    async getPaymentHistory(userId, limit = 50) {
      return this.callEndpoint(`/payments/history?user_id=${userId}&limit=${limit}`);
    },

    async initiateDeposit(userId, amount, blockchain) {
      return this.callEndpoint('/payments/deposit/initiate', {
        method: 'POST',
        body: { user_id: userId, amount, blockchain }
      });
    },

    async confirmDeposit(userId, txHash) {
      return this.callEndpoint('/payments/deposit/confirm', {
        method: 'POST',
        body: { user_id: userId, tx_hash: txHash }
      });
    },

    async initiateWithdrawal(userId, amount, destination) {
      return this.callEndpoint('/payments/withdrawal/initiate', {
        method: 'POST',
        body: { user_id: userId, amount, destination }
      });
    },

    // REFERRALS
    async getReferralInfo(userId) {
      return this.callEndpoint(`/referrals/me?user_id=${userId}`);
    },

    async applyReferralCode(userId, code) {
      return this.callEndpoint('/referrals/apply', {
        method: 'POST',
        body: { user_id: userId, referral_code: code }
      });
    },

    async getReferralStats(userId) {
      return this.callEndpoint(`/referrals/stats?user_id=${userId}`);
    }
  };

  // ========== INITIALIZATION ==========
  async function initApp() {
    try {
      const initData = window.Telegram?.WebApp?.initData;
      
      if (!initData) {
        throw new Error('Telegram context required - WebApp must be opened from Telegram');
      }

      if (window.Telegram?.WebApp?.ready) {
        window.Telegram.WebApp.ready();
      }
      
      showStatus('Authenticating...', 'info', true);
      
      const authResponse = await API.initSession(initData);
      
      if (!authResponse.success && !authResponse.user) {
        throw new Error(authResponse.error || 'Authentication failed');
      }

      state.user = authResponse.user;
      
      showStatus('Loading dashboard...', 'info', true);
      updateUserDisplay();
      setupEventListeners();
      
      await loadAllData();
      
      showStatus('Connected!', 'success', false);
      switchPage('dashboard');
      
    } catch (err) {
      console.error('Init error:', err);
      showStatus(`Error: ${err.message}`, 'error', false);
    }
  }

  async function loadAllData() {
    try {
      showStatus('Syncing data...', 'info', true);
      
      const dashboardData = await API.getDashboardData(state.user.id);
      
      state.wallets = Array.isArray(dashboardData.wallets) ? dashboardData.wallets : [];
      state.nfts = Array.isArray(dashboardData.nfts) ? dashboardData.nfts : [];
      state.listings = Array.isArray(dashboardData.listings) ? dashboardData.listings : [];
      
      // Load marketplace listings
      try {
        const marketplaceData = await API.getMarketplaceListings(50);
        state.listings = Array.isArray(marketplaceData.listings) ? marketplaceData.listings : state.listings;
      } catch (e) {
        console.warn('Failed to load marketplace:', e);
      }

      // Load my listings
      try {
        const myListingsData = await API.getMyListings(state.user.id);
        state.myListings = Array.isArray(myListingsData.listings) ? myListingsData.listings : [];
      } catch (e) {
        console.warn('Failed to load my listings:', e);
      }

      // Load balance
      try {
        const balanceData = await API.getBalance(state.user.id);
        state.balance = balanceData.balance || 0;
      } catch (e) {
        console.warn('Failed to load balance:', e);
      }

      // Load referral info
      try {
        const refData = await API.getReferralInfo(state.user.id);
        state.referralInfo = refData;
      } catch (e) {
        console.warn('Failed to load referral info:', e);
      }

      updateDashboard();
      updateWalletsList();
      updateNFTsList();
      updateMarketplace();
      updateBalance();
      updateReferralInfo();
      
      showStatus('Data loaded', 'success', false);
    } catch (err) {
      console.error('Load data error:', err);
      showStatus(`Error loading data: ${err.message}`, 'error', false);
    }
  }

  // ========== UI UPDATES ==========
  function updateUserDisplay() {
    const name = state.user?.first_name || state.user?.telegram_username || 'User';
    const userInfo = document.getElementById('userInfo');
    if (userInfo) {
      userInfo.innerHTML = `
        <strong>${truncate(name, 15)}</strong>
        <small>@${truncate(state.user?.telegram_username || 'user', 12)}</small>
      `;
    }
  }

  function updateDashboard() {
    const portfolioValue = state.listings.reduce((sum, l) => sum + (parseFloat(l.price) || 0), 0);
    
    const elements = {
      portfolioValue: '$' + portfolioValue.toFixed(2),
      totalNfts: state.nfts.length,
      totalWallets: state.wallets.length,
      totalListings: state.listings.filter(l => l.active || l.status === 'active').length,
      userBalance: '$' + (state.balance || 0).toFixed(2)
    };

    Object.entries(elements).forEach(([id, value]) => {
      const el = document.getElementById(id);
      if (el) el.textContent = value;
    });

    // Profile info
    const profileInfo = document.getElementById('profileInfo');
    if (profileInfo) {
      profileInfo.innerHTML = `
        <div class="profile-item">
          <span>User:</span>
          <strong>@${state.user?.telegram_username || 'user'}</strong>
        </div>
        <div class="profile-item">
          <span>Wallets:</span>
          <strong>${state.wallets.length}</strong>
        </div>
        <div class="profile-item">
          <span>NFTs:</span>
          <strong>${state.nfts.length}</strong>
        </div>
      `;
    }

    // Stats
    const stats = document.getElementById('profileStats');
    if (stats) {
      stats.innerHTML = `
        <div class="stat-item">
          <div class="stat-value">${state.nfts.length}</div>
          <div class="stat-label">NFTs</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">${state.wallets.length}</div>
          <div class="stat-label">Wallets</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">${state.listings.filter(l => l.active || l.status === 'active').length}</div>
          <div class="stat-label">Listed</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">$${portfolioValue.toFixed(0)}</div>
          <div class="stat-label">Value</div>
        </div>
      `;
    }
  }

  function updateWalletsList() {
    const container = document.getElementById('walletsList');
    if (!container) return;

    if (state.wallets.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <p>No wallets yet</p>
          <button class="btn btn-primary" onclick="window.showCreateWalletModal()">Create Wallet</button>
        </div>
      `;
      return;
    }

    container.innerHTML = state.wallets.map((w, idx) => `
      <div class="card wallet-card">
        <div class="wallet-blockchain">
          <strong>${w.blockchain?.toUpperCase() || 'Wallet'}</strong>
          ${w.is_primary ? '<span class="badge-primary">Primary</span>' : ''}
        </div>
        <div class="wallet-address" title="${w.address}">${formatAddr(w.address)}</div>
        <div class="wallet-actions">
          <button class="btn btn-sm btn-secondary" onclick="window.showWalletDetails(${idx})">Details</button>
          ${!w.is_primary ? `<button class="btn btn-sm btn-secondary" onclick="window.setPrimary(${idx})">Set Primary</button>` : ''}
        </div>
      </div>
    `).join('');
  }

  function updateNFTsList() {
    const container = document.getElementById('nftList');
    if (!container) return;

    if (state.nfts.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <p>No NFTs yet</p>
          <button class="btn btn-primary" onclick="window.switchPage('mint')">Mint NFT</button>
        </div>
      `;
      return;
    }

    container.innerHTML = state.nfts.map((nft, idx) => `
      <div class="card nft-card">
        <div class="nft-image">
          ${nft.image_url ? `<img src="${nft.image_url}" alt="${nft.name}" loading="lazy">` : '<div class="nft-placeholder">No Image</div>'}
        </div>
        <div class="nft-content">
          <div class="nft-name">${truncate(nft.name, 20)}</div>
          <div class="nft-collection">${nft.collection?.name || 'Collection'}</div>
          <div class="nft-actions">
            <button class="btn btn-sm btn-primary" onclick="window.listNFTModal(${idx})">List</button>
            <button class="btn btn-sm btn-secondary" onclick="window.nftDetails(${idx})">View</button>
          </div>
        </div>
      </div>
    `).join('');
  }

  function updateMarketplace() {
    const container = document.getElementById('marketplaceListings');
    if (!container) return;

    if (state.listings.length === 0) {
      container.innerHTML = '<p class="empty-state">No listings available</p>';
      return;
    }

    container.innerHTML = state.listings.map((listing, idx) => `
      <div class="card nft-card">
        <div class="nft-image">
          ${listing.nft?.image_url ? `<img src="${listing.nft.image_url}" alt="NFT" loading="lazy">` : '<div class="nft-placeholder">Listing</div>'}
        </div>
        <div class="nft-content">
          <div class="nft-name">${truncate(listing.nft?.name || 'NFT', 20)}</div>
          <div class="nft-collection">${listing.nft?.collection?.name || 'Unknown'}</div>
          <div class="nft-price">$${parseFloat(listing.price || 0).toFixed(2)}</div>
          <button class="btn btn-primary btn-block" onclick="window.viewMarketplaceListing(${idx})">Make Offer</button>
        </div>
      </div>
    `).join('');

    // My listings tab
    const myListingsContainer = document.getElementById('myListings');
    if (myListingsContainer) {
      if (state.myListings.length === 0) {
        myListingsContainer.innerHTML = '<p class="empty-state">No active listings</p>';
      } else {
        myListingsContainer.innerHTML = state.myListings.map((listing, idx) => `
          <div class="card nft-card">
            <div class="nft-image">
              ${listing.nft?.image_url ? `<img src="${listing.nft.image_url}" alt="NFT" loading="lazy">` : '<div class="nft-placeholder">Listing</div>'}
            </div>
            <div class="nft-content">
              <div class="nft-name">${truncate(listing.nft?.name || 'NFT', 20)}</div>
              <div class="nft-price">Listed at $${parseFloat(listing.price || 0).toFixed(2)}</div>
              <button class="btn btn-danger btn-block" onclick="window.cancelMyListing(${idx})">Cancel</button>
            </div>
          </div>
        `).join('');
      }
    }
  }

  function updateBalance() {
    const container = document.getElementById('balanceInfo');
    if (container) {
      container.innerHTML = `
        <div class="balance-card">
          <div class="balance-amount">$${(state.balance || 0).toFixed(2)}</div>
          <div class="balance-actions">
            <button class="btn btn-primary" onclick="window.showDepositModal()">Deposit</button>
            <button class="btn btn-secondary" onclick="window.showWithdrawModal()">Withdraw</button>
          </div>
        </div>
      `;
    }
  }

  function updateReferralInfo() {
    const container = document.getElementById('referralInfo');
    if (!container || !state.referralInfo) return;

    container.innerHTML = `
      <div class="referral-card">
        <div class="referral-code">
          <strong>Your Code:</strong>
          <code>${state.referralInfo.referral_code || 'N/A'}</code>
          <button class="btn btn-sm btn-secondary" onclick="window.copyReferralCode('${state.referralInfo.referral_code}')">Copy</button>
        </div>
        <div class="referral-stats">
          <div class="stat">
            <span>Referrals:</span>
            <strong>${state.referralInfo.referral_count || 0}</strong>
          </div>
          <div class="stat">
            <span>Earnings:</span>
            <strong>$${(state.referralInfo.total_earnings || 0).toFixed(2)}</strong>
          </div>
        </div>
      </div>
      <div class="referral-input">
        <label>Apply Referral Code</label>
        <div style="display:flex;gap:8px;">
          <input type="text" id="referralCodeInput" placeholder="Enter code" class="input-text" style="flex:1;">
          <button class="btn btn-primary" onclick="window.applyReferralCode()">Apply</button>
        </div>
      </div>
    `;
  }

  // ========== MODAL FUNCTIONS & EVENT HANDLERS ==========
  window.showCreateWalletModal = function() {
    const chains = ['ethereum', 'polygon', 'solana', 'ton', 'bitcoin'];
    showModal('Create Wallet', `
      <div class="form-group"><label>Blockchain</label><select id="chainSelect" class="input-select">${chains.map(c => `<option value="${c}">${c.toUpperCase()}</option>`).join('')}</select></div>
      <button class="btn btn-primary btn-block" onclick="window.createWallet()">Create</button>
      <button class="btn btn-secondary btn-block" style="margin-top:8px;" onclick="window.showImportWalletModal()">Import</button>
    `);
  };

  window.showImportWalletModal = function() {
    const chains = ['ethereum', 'polygon', 'solana', 'ton', 'bitcoin'];
    showModal('Import Wallet', `
      <div class="form-group"><label>Address</label><input type="text" id="importAddr" placeholder="Address" class="input-text"></div>
      <div class="form-group"><label>Blockchain</label><select id="importChain" class="input-select">${chains.map(c => `<option value="${c}">${c.toUpperCase()}</option>`).join('')}</select></div>
      <button class="btn btn-primary btn-block" onclick="window.importWallet()">Import</button>
    `);
  };

  window.createWallet = async function() {
    const chain = document.getElementById('chainSelect')?.value;
    if (!chain) { showStatus('Select blockchain', 'error', false); return; }
    showStatus('Creating wallet...', 'info', true);
    try {
      const res = await API.createWallet(state.user.id, chain);
      if (res.success || res.wallet) { showStatus('Wallet created!', 'success', false); closeModal(); await loadAllData(); }
      else throw new Error(res.error || 'Failed');
    } catch (err) { showStatus(`Error: ${err.message}`, 'error', false); }
  };

  window.importWallet = async function() {
    const addr = document.getElementById('importAddr')?.value?.trim();
    const chain = document.getElementById('importChain')?.value;
    if (!addr || !chain) { showStatus('Fill all fields', 'error', false); return; }
    showStatus('Importing...', 'info', true);
    try {
      const res = await API.importWallet(state.user.id, addr, chain);
      if (res.success || res.wallet) { showStatus('Imported!', 'success', false); closeModal(); await loadAllData(); }
      else throw new Error(res.error || 'Failed');
    } catch (err) { showStatus(`Error: ${err.message}`, 'error', false); }
  };

  window.showWalletDetails = function(idx) {
    const w = state.wallets[idx];
    if (!w) return;
    showModal('Wallet Details', `
      <div><strong>${w.blockchain?.toUpperCase()}</strong><br><code style="font-size:11px;word-break:break-all;">${w.address}</code></div>
      <div style="margin-top:12px;"><strong>Primary:</strong> ${w.is_primary ? 'Yes' : 'No'}</div>
      <button class="btn btn-secondary btn-block" style="margin-top:12px;" onclick="window.closeModal()">Close</button>
    `);
  };

  window.setPrimary = async function(idx) {
    const w = state.wallets[idx];
    if (!w || w.is_primary) return;
    showStatus('Setting primary...', 'info', true);
    try {
      const res = await API.setPrimaryWallet(state.user.id, w.id, w.blockchain);
      if (res.success) { showStatus('Updated!', 'success', false); await loadAllData(); closeModal(); }
      else throw new Error(res.error || 'Failed');
    } catch (err) { showStatus(`Error: ${err.message}`, 'error', false); }
  };

  window.showMintModal = function() {
    if (state.wallets.length === 0) { showStatus('Create wallet first', 'error', false); return; }
    showModal('Mint NFT', `
      <div class="form-group"><label>Wallet</label><select id="mintWallet" class="input-select">${state.wallets.map((w, i) => `<option value="${w.id}">${w.blockchain?.toUpperCase()}</option>`).join('')}</select></div>
      <div class="form-group"><label>Name</label><input type="text" id="mintName" placeholder="NFT name" class="input-text"></div>
      <div class="form-group"><label>Description</label><textarea id="mintDesc" placeholder="Description" class="input-text" rows="2"></textarea></div>
      <button class="btn btn-primary btn-block" onclick="window.submitMint()">Mint</button>
      <button class="btn btn-secondary btn-block" style="margin-top:8px;" onclick="window.closeModal()">Cancel</button>
    `);
  };

  window.submitMint = async function() {
    const walletId = document.getElementById('mintWallet')?.value;
    const name = document.getElementById('mintName')?.value?.trim();
    const desc = document.getElementById('mintDesc')?.value?.trim();
    if (!name || !desc || !walletId) { showStatus('Fill all fields', 'error', false); return; }
    showStatus('Creating...', 'info', true);
    try {
      const res = await API.mintNFT(state.user.id, walletId, name, desc);
      if (res.success || res.nft) { showStatus('Created!', 'success', false); closeModal(); await loadAllData(); switchPage('nfts'); }
      else throw new Error(res.error || 'Failed');
    } catch (err) { showStatus(`Error: ${err.message}`, 'error', false); }
  };

  window.nftDetails = function(idx) {
    const nft = state.nfts[idx];
    if (!nft) return;
    showModal('NFT Details', `
      <div><strong>${nft.name}</strong><br><small>${nft.collection?.name || 'Collection'}</small></div>
      <p style="font-size:12px;margin-top:8px;color:var(--color-text-secondary);">${nft.description || 'N/A'}</p>
      <button class="btn btn-primary btn-block" style="margin-top:12px;" onclick="window.listNFTModal(${idx})">List for Sale</button>
      <button class="btn btn-danger btn-block" style="margin-top:8px;" onclick="window.burnNFTConfirm(${idx})">Burn</button>
      <button class="btn btn-secondary btn-block" style="margin-top:8px;" onclick="window.closeModal()">Close</button>
    `);
  };

  window.listNFTModal = function(idx) {
    const nft = state.nfts[idx];
    if (!nft) return;
    showModal('List NFT', `
      <div class="form-group"><label>NFT: ${nft.name}</label></div>
      <div class="form-group"><label>Price</label><input type="number" id="listPrice" placeholder="0.00" min="0" step="0.01" class="input-text"></div>
      <div class="form-group"><label>Currency</label><select id="listCurrency" class="input-select"><option>ETH</option><option>USDT</option><option>USD</option></select></div>
      <button class="btn btn-primary btn-block" onclick="window.confirmListNFT(${idx})">List</button>
      <button class="btn btn-secondary btn-block" style="margin-top:8px;" onclick="window.closeModal()">Cancel</button>
    `);
  };

  window.confirmListNFT = async function(idx) {
    const nft = state.nfts[idx];
    const price = document.getElementById('listPrice')?.value;
    const currency = document.getElementById('listCurrency')?.value || 'ETH';
    if (!price || parseFloat(price) <= 0) { showStatus('Invalid price', 'error', false); return; }
    showStatus('Listing...', 'info', true);
    try {
      const res = await API.listNFT(state.user.id, nft.id, price, currency);
      if (res.success || res.listing) { showStatus('Listed!', 'success', false); closeModal(); await loadAllData(); }
      else throw new Error(res.error || 'Failed');
    } catch (err) { showStatus(`Error: ${err.message}`, 'error', false); }
  };

  window.burnNFTConfirm = function(idx) {
    const nft = state.nfts[idx];
    showModal('Burn NFT', `
      <p style="color:var(--color-status-error);">Are you sure? This cannot be undone.</p>
      <p style="font-size:12px;margin-top:8px;">Burning ${nft.name}</p>
      <button class="btn btn-danger btn-block" style="margin-top:12px;" onclick="window.burnNFT(${idx})">Confirm</button>
      <button class="btn btn-secondary btn-block" style="margin-top:8px;" onclick="window.closeModal()">Cancel</button>
    `);
  };

  window.burnNFT = async function(idx) {
    const nft = state.nfts[idx];
    showStatus('Burning...', 'info', true);
    try {
      const res = await API.burnNFT(state.user.id, nft.id);
      if (res.success || res.nft) { showStatus('Burned!', 'success', false); closeModal(); await loadAllData(); }
      else throw new Error(res.error || 'Failed');
    } catch (err) { showStatus(`Error: ${err.message}`, 'error', false); }
  };

  window.viewMarketplaceListing = function(idx) {
    const l = state.listings[idx];
    if (!l) return;
    showModal('Make Offer', `
      <div><strong>${l.nft?.name || 'NFT'}</strong><br><small>$${parseFloat(l.price || 0).toFixed(2)}</small></div>
      <div class="form-group" style="margin-top:12px;"><label>Your Offer</label><input type="number" id="offerPrice" placeholder="0.00" min="0" step="0.01" class="input-text"></div>
      <button class="btn btn-primary btn-block" onclick="window.submitOffer(${idx})">Submit</button>
      <button class="btn btn-secondary btn-block" style="margin-top:8px;" onclick="window.closeModal()">Cancel</button>
    `);
  };

  window.submitOffer = async function(idx) {
    const listing = state.listings[idx];
    const offerPrice = document.getElementById('offerPrice')?.value;
    if (!offerPrice || parseFloat(offerPrice) <= 0) { showStatus('Invalid offer', 'error', false); return; }
    showStatus('Sending offer...', 'info', true);
    try {
      const res = await API.makeOffer(state.user.id, listing.id, offerPrice);
      if (res.success || res.offer) { showStatus('Offer sent!', 'success', false); closeModal(); await loadAllData(); }
      else throw new Error(res.error || 'Failed');
    } catch (err) { showStatus(`Error: ${err.message}`, 'error', false); }
  };

  window.cancelMyListing = async function(idx) {
    const listing = state.myListings[idx];
    if (!listing) return;
    showStatus('Canceling...', 'info', true);
    try {
      const res = await API.cancelListing(state.user.id, listing.id);
      if (res.success) { showStatus('Canceled!', 'success', false); await loadAllData(); switchPage('marketplace'); }
      else throw new Error(res.error || 'Failed');
    } catch (err) { showStatus(`Error: ${err.message}`, 'error', false); }
  };

  window.showDepositModal = function() {
    const chains = ['ethereum', 'polygon', 'solana', 'ton', 'bitcoin'];
    showModal('Deposit', `
      <div class="form-group"><label>Amount (USD)</label><input type="number" id="depositAmount" placeholder="0.00" min="0" step="0.01" class="input-text"></div>
      <div class="form-group"><label>Blockchain</label><select id="depositChain" class="input-select">${chains.map(c => `<option value="${c}">${c.toUpperCase()}</option>`).join('')}</select></div>
      <button class="btn btn-primary btn-block" onclick="window.initDeposit()">Continue</button>
      <button class="btn btn-secondary btn-block" style="margin-top:8px;" onclick="window.closeModal()">Cancel</button>
    `);
  };

  window.initDeposit = async function() {
    const amount = document.getElementById('depositAmount')?.value;
    const chain = document.getElementById('depositChain')?.value;
    if (!amount || parseFloat(amount) <= 0 || !chain) { showStatus('Invalid input', 'error', false); return; }
    showStatus('Initiating...', 'info', true);
    try {
      await API.initiateDeposit(state.user.id, parseFloat(amount), chain);
      showStatus('Initiated!', 'success', false);
      closeModal();
    } catch (err) { showStatus(`Error: ${err.message}`, 'error', false); }
  };

  window.showWithdrawModal = function() {
    showModal('Withdraw', `
      <div class="form-group"><label>Amount (USD)</label><input type="number" id="withdrawAmount" placeholder="0.00" min="0" step="0.01" class="input-text"></div>
      <div class="form-group"><label>Address</label><input type="text" id="withdrawAddr" placeholder="Wallet address" class="input-text"></div>
      <button class="btn btn-primary btn-block" onclick="window.initWithdraw()">Request</button>
      <button class="btn btn-secondary btn-block" style="margin-top:8px;" onclick="window.closeModal()">Cancel</button>
    `);
  };

  window.initWithdraw = async function() {
    const amount = document.getElementById('withdrawAmount')?.value;
    const addr = document.getElementById('withdrawAddr')?.value;
    if (!amount || parseFloat(amount) <= 0 || !addr) { showStatus('Fill all fields', 'error', false); return; }
    showStatus('Processing...', 'info', true);
    try {
      await API.initiateWithdrawal(state.user.id, parseFloat(amount), addr);
      showStatus('Submitted!', 'success', false);
      closeModal();
    } catch (err) { showStatus(`Error: ${err.message}`, 'error', false); }
  };

  window.applyReferralCode = async function() {
    const code = document.getElementById('referralCodeInput')?.value?.trim();
    if (!code) { showStatus('Enter code', 'error', false); return; }
    showStatus('Applying...', 'info', true);
    try {
      const res = await API.applyReferralCode(state.user.id, code);
      if (res.success) { showStatus('Applied!', 'success', false); await loadAllData(); }
      else throw new Error(res.error || 'Invalid');
    } catch (err) { showStatus(`Error: ${err.message}`, 'error', false); }
  };

  window.copyReferralCode = function(code) {
    navigator.clipboard.writeText(code);
    showStatus('Copied!', 'success', false);
  };

  window.switchPage = switchPage;
  window.closeModal = closeModal;

  // ========== EVENT LISTENERS ==========
  function setupEventListeners() {
    document.querySelectorAll('[data-nav]').forEach(item => {
      item.addEventListener('click', (e) => { e.preventDefault(); switchPage(item.dataset.nav); });
    });

    if (closeModalBtn) closeModalBtn.addEventListener('click', closeModal);
    if (modalOverlay) modalOverlay.addEventListener('click', closeModal);

    const createWalletBtn = document.getElementById('createWalletBtn');
    const importWalletBtn = document.getElementById('importWalletBtn');
    const mintBtn = document.getElementById('mintBtn');
    const refreshBtn = document.getElementById('refreshBtn');

    if (createWalletBtn) createWalletBtn.addEventListener('click', window.showCreateWalletModal);
    if (importWalletBtn) importWalletBtn.addEventListener('click', window.showImportWalletModal);
    if (mintBtn) mintBtn.addEventListener('click', window.showMintModal);
    if (refreshBtn) refreshBtn.addEventListener('click', async () => { showStatus('Refreshing...', 'info', true); await loadAllData(); });

    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const marketplace = document.getElementById('marketplaceListings');
        const myListings = document.getElementById('myListings');
        if (btn.dataset.tab === 'marketplace' && marketplace && myListings) {
          marketplace.style.display = 'grid';
          myListings.style.display = 'none';
        } else if (btn.dataset.tab === 'mylistings' && marketplace && myListings) {
          marketplace.style.display = 'none';
          myListings.style.display = 'grid';
        }
      });
    });
  }

  // ========== INIT ==========
  if (window.Telegram?.WebApp) window.Telegram.WebApp.ready();
  
  // Global error handlers for stability
  window.addEventListener('error', (event) => {
    console.error('Uncaught error:', event.error);
    showStatus(`Error: ${event.error?.message || 'Unknown error'}`, 'error', false);
  });
  
  window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    showStatus(`Error: ${event.reason?.message || 'Request failed'}`, 'error', false);
  });
  
  window.addEventListener('load', initApp);
  setInterval(async () => {
    if (state.user && state.currentPage === 'dashboard') {
      try { await loadAllData(); } catch (e) {
        console.warn('Auto-refresh failed:', e);
      }
    }
  }, 30000);

})();

