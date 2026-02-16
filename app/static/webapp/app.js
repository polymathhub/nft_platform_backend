(async function() {
  'use strict';

  // ========== STATE & CONFIG ==========
  const state = {
    user: null,
    wallets: [],
    nfts: [],
    listings: [],
    currentPage: 'dashboard'
  };

  const API_BASE = '/api/v1';
  const status = document.getElementById('status');
  const statusText = document.getElementById('statusText');
  const statusSpinner = document.getElementById('statusSpinner');
  const modal = document.getElementById('modal');
  const modalSpinner = document.getElementById('modalSpinner');

  // Request caching
  const cache = {};
  const pendingRequests = {};
  
  // ========== API SERVICE ==========
  const API = {
    async callEndpoint(urlOrPath, options = {}) {
      const url = urlOrPath.startsWith('http') ? urlOrPath : `${API_BASE}${urlOrPath}`;
      try {
        const response = await fetch(url, {
          method: options.method || 'GET',
          headers: { 
            'Content-Type': 'application/json',
            ...options.headers 
          },
          body: options.body ? JSON.stringify(options.body) : undefined
        });
        
        if (!response.ok) {
          const errorText = await response.text();
          const errorMsg = response.status === 401 ? 'Unauthorized' : `HTTP ${response.status}`;
          throw new Error(`${errorMsg}: ${errorText}`);
        }
        return await response.json();
      } catch (err) {
        console.error(`API Error [${url}]:`, err);
        throw err;
      }
    },

    async initSession(initData) {
      return this.callEndpoint(`/telegram/web-app/init?init_data=${encodeURIComponent(initData)}`);
    },

    async getUser(userId) {
      return this.callEndpoint(`/telegram/web-app/user?user_id=${userId}`);
    },

    async getWallets(userId) {
      return this.callEndpoint(`/telegram/web-app/wallets?user_id=${userId}`);
    },

    async getNFTs(userId) {
      return this.callEndpoint(`/telegram/web-app/nfts?user_id=${userId}`);
    },

    async getDashboardData(userId) {
      return this.callEndpoint(`/telegram/web-app/dashboard-data?user_id=${userId}`);
    },

    async getMarketplaceListings(limit = 100) {
      return this.callEndpoint(`/marketplace/listings?limit=${limit}`);
    },

    async getUserListings(userId) {
      return this.callEndpoint(`/marketplace/listings/user?user_id=${userId}`);
    },

    async createWallet(userId, blockchain) {
      return this.callEndpoint('/telegram/web-app/set-primary', {
        method: 'POST',
        body: { user_id: userId, blockchain }
      });
    },

    async mintNFT(userId, walletId, name, description) {
      return this.callEndpoint('/telegram/web-app/mint', {
        method: 'POST',
        body: { user_id: userId, wallet_id: walletId, nft_name: name, nft_description: description }
      });
    },

    async listNFT(userId, nftId, price, currency = 'ETH') {
      return this.callEndpoint('/telegram/web-app/list-nft', {
        method: 'POST',
        body: { user_id: userId, nft_id: nftId, price: parseFloat(price), currency }
      });
    }
  };

  // ========== UTIL FUNCTIONS ==========
  function showStatus(msg, type = 'info', showSpinner = type === 'info') {
    statusText.textContent = msg;
    status.className = `status-alert ${type}`;
    statusSpinner.style.display = showSpinner ? 'inline-block' : 'none';
    status.classList.remove('hidden');
    
    if (type !== 'info') {
      setTimeout(() => {
        status.classList.add('hidden');
        statusSpinner.style.display = 'none';
      }, 5000);
    }
  }

  function showModal(title, content) {
    document.getElementById('modalTitle').textContent = title;
    document.getElementById('modalBody').innerHTML = content;
    modal.style.display = 'flex';
  }

  function closeModal() {
    modal.style.display = 'none';
    modalSpinner.style.display = 'none';
  }

  function truncate(str, len = 20) {
    return str && str.length > len ? str.slice(0, len - 3) + '...' : str;
  }

  function formatAddr(addr) {
    return addr ? addr.slice(0, 6) + '...' + addr.slice(-4) : '—';
  }

  function showModalSpinner() {
    modalSpinner.style.display = 'block';
  }

  function hideModalSpinner() {
    modalSpinner.style.display = 'none';
  }

  // Performance: Intersection Observer for lazy loading images
  function setupLazyLoading() {
    const imageObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target;
          if (img.dataset.src) {
            img.src = img.dataset.src;
            img.removeAttribute('data-src');
            imageObserver.unobserve(img);
          }
        }
      });
    }, { rootMargin: '50px' });

    document.querySelectorAll('img[data-src]').forEach(img => imageObserver.observe(img));
  }

  // Debounced function to prevent excessive re-renders
  function debounceRender(fn, delay = 300) {
    let timeoutId;
    return function(...args) {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => fn(...args), delay);
    };
  }

  // ========== PAGE NAVIGATION ==========
  function switchPage(pageName) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    
    const page = document.getElementById(`${pageName}-page`);
    if (page) {
      page.classList.add('active');
      document.querySelector(`[data-page="${pageName}"]`)?.classList.add('active');
    }

    const titles = {
      dashboard: 'Dashboard',
      wallets: 'Wallet Management',
      nfts: 'My NFT Collection',
      mint: 'Create NFT',
      marketplace: 'Marketplace',
      profile: 'My Profile'
    };
    document.getElementById('pageTitle').textContent = titles[pageName] || 'NFT Platform';
    state.currentPage = pageName;
  }

  // ========== INITIALIZE APP ==========
  async function initApp() {
    showStatus('Initializing NFT Platform...', 'info', true);

    try {
      // Get Telegram init data
      const initData = window.Telegram?.WebApp?.initData;
      
      if (!initData) {
        console.error('No Telegram initData found');
        showStatus('Error: Not running in Telegram context', 'error', false);
        return;
      }

      // Mark app as ready
      if (window.Telegram?.WebApp?.ready) {
        window.Telegram.WebApp.ready();
      }
      
      showStatus('Authenticating...', 'info', true);
      
      // Authenticate with backend
      const authResponse = await API.initSession(initData);
      
      if (!authResponse.success) {
        throw new Error(authResponse.error || 'Authentication failed');
      }

      state.user = authResponse.user;
      
      showStatus('Loading dashboard...', 'info', true);
      updateUserInfo();
      setupEventListeners();
      
      // Load all dashboard data
      await loadDashboardData();
      
      showStatus('Connected successfully!', 'success', false);
      setTimeout(() => status.classList.add('hidden'), 2000);
      
    } catch (err) {
      console.error('Init error:', err);
      showStatus(`Error: ${err.message}`, 'error', false);
    }
  }

  // ========== UPDATE UI ==========
  function updateUserInfo() {
    const name = state.user?.first_name || state.user?.telegram_username || 'User';
    if (document.getElementById('userInfo')) {
      document.getElementById('userInfo').innerHTML = `
        <strong>${truncate(name, 15)}</strong>
        <small>@${truncate(state.user?.telegram_username || 'user', 12)}</small>
      `;
    }
  }

  // ========== LOAD DATA ==========
  async function loadDashboardData() {
    try {
      showStatus('Loading your data...', 'info', true);
      
      const dashboardData = await API.getDashboardData(state.user.id);
      
      state.wallets = Array.isArray(dashboardData.wallets) ? dashboardData.wallets : [];
      state.nfts = Array.isArray(dashboardData.nfts) ? dashboardData.nfts : [];
      state.listings = Array.isArray(dashboardData.listings) ? dashboardData.listings : [];

      updateDashboard();
      updateWalletsList();
      updateNftsList();
      updateMarketplace();
      
      showStatus('Data loaded', 'success', false);
    } catch (err) {
      console.error('Load data error:', err);
      showStatus(`Error loading data: ${err.message}`, 'error', false);
      
      // Show empty state
      state.wallets = [];
      state.nfts = [];
      state.listings = [];
      updateDashboard();
      updateWalletsList();
      updateNftsList();
      updateMarketplace();
    }
  }

  function updateDashboard() {
    // Calculate portfolio value from actual listing prices
    const portfolioValue = state.listings.reduce((sum, l) => sum + (parseFloat(l.price) || 0), 0);
    
    if (document.getElementById('portfolioValue')) {
      document.getElementById('portfolioValue').textContent = '$' + portfolioValue.toFixed(2);
    }
    if (document.getElementById('totalNfts')) {
      document.getElementById('totalNfts').textContent = state.nfts.length;
    }
    if (document.getElementById('totalWallets')) {
      document.getElementById('totalWallets').textContent = state.wallets.length;
    }
    if (document.getElementById('totalListings')) {
      document.getElementById('totalListings').textContent = state.listings.filter(l => l.active || l.status === 'active').length;
    }

    const activity = `
      <div class="activity-item">
        <span class="activity-type">Data synced</span>
        <span class="activity-time">Just now</span>
      </div>
    `;
    if (document.getElementById('recentActivity')) {
      document.getElementById('recentActivity').innerHTML = activity || '<p class="muted">No activity yet</p>';
    }

    const profileInfo = `
      <div class="profile-item">
        <span>Username:</span>
        <strong>@${state.user?.telegram_username || 'user'}</strong>
      </div>
      <div class="profile-item">
        <span>Name:</span>
        <strong>${state.user?.first_name || 'User'}</strong>
      </div>
      <div class="profile-item">
        <span>Wallets:</span>
        <strong>${state.wallets.length}</strong>
      </div>
    `;
    if (document.getElementById('profileInfo')) {
      document.getElementById('profileInfo').innerHTML = profileInfo;
    }

    const stats = `
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
        <div class="stat-label">Listings</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">$${portfolioValue.toFixed(0)}</div>
        <div class="stat-label">Value</div>
      </div>
    `;
    if (document.getElementById('profileStats')) {
      document.getElementById('profileStats').innerHTML = stats;
    }
  }

  function updateWalletsList() {
    const html = state.wallets.length === 0 
      ? '<p class="muted">No wallets yet. Create one to get started.</p>'
      : state.wallets.map(w => `
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
    
    if (document.getElementById('walletsList')) {
      document.getElementById('walletsList').innerHTML = html;
    }
  }

  function updateNftsList() {
    const html = state.nfts.length === 0
      ? '<p class="muted">No NFTs yet. Create one to get started.</p>'
      : state.nfts.map(nft => `
        <div class="card nft-card">
          <div class="nft-image">
            ${nft.image_url ? `<img src="${nft.image_url}" alt="${nft.name}" loading="lazy">` : '<div style="background:var(--bg-base);display:flex;align-items:center;justify-content:center;height:100%;">No Image</div>'}
          </div>
          <div class="nft-content">
            <div class="nft-name">${truncate(nft.name, 25)}</div>
            <div class="nft-collection">${nft.collection?.name || 'No Collection'}</div>
            <div class="nft-price">${nft.status || 'Minted'}</div>
          </div>
        </div>
      `).join('');
    
    if (document.getElementById('nftList')) {
      document.getElementById('nftList').innerHTML = html;
    }
  }

  function updateMarketplace() {
    const html = state.listings.length === 0
      ? '<p class="muted">No listings available</p>'
      : state.listings.map(l => `
        <div class="card nft-card">
          <div class="nft-image">
            ${l.nft?.image_url ? `<img src="${l.nft.image_url}" alt="NFT" loading="lazy">` : '<div style="background:var(--bg-base);display:flex;align-items:center;justify-content:center;height:100%;">Listing</div>'}
          </div>
          <div class="nft-content">
            <div class="nft-name">${truncate(l.nft?.name || 'NFT', 25)}</div>
            <div class="nft-collection">${l.nft?.collection?.name || 'Unknown'}</div>
            <div class="nft-price">${l.price ? '$' + parseFloat(l.price).toFixed(2) : 'N/A'}</div>
            <button class="btn btn-primary" style="width:100%;margin-top:8px;" onclick="window.viewListing('${l.id}')">View</button>
          </div>
        </div>
      `).join('');
    
    if (document.getElementById('marketplaceListings')) {
      document.getElementById('marketplaceListings').innerHTML = html;
    }
  }

  // ========== EVENT LISTENERS ==========
  function setupEventListeners() {
    // Navigation
    document.querySelectorAll('.nav-item').forEach(item => {
      item.addEventListener('click', (e) => {
        e.preventDefault();
        switchPage(item.dataset.page);
      });
    });

    // Modal controls
    const closeModalBtn = document.getElementById('closeModal');
    const modalOverlay = document.getElementById('modalOverlay');
    if (closeModalBtn) closeModalBtn.addEventListener('click', closeModal);
    if (modalOverlay) modalOverlay.addEventListener('click', closeModal);

    // Wallet buttons
    const createWalletBtn = document.getElementById('createWalletBtn');
    const importWalletBtn = document.getElementById('importWalletBtn');
    if (createWalletBtn) createWalletBtn.addEventListener('click', ShowCreateWalletModal);
    if (importWalletBtn) importWalletBtn.addEventListener('click', showImportWalletModal);

    // Mint form
    populateMintWalletSelect();
    const mintNftBtn = document.getElementById('mintNftBtn');
    if (mintNftBtn) mintNftBtn.addEventListener('click', submitMintForm);

    // Marketplace tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        if (btn.dataset.tab === 'listings') {
          const mlisting = document.getElementById('marketplaceListings');
          const mmy = document.getElementById('myListings');
          if (mlisting) mlisting.style.display = 'grid';
          if (mmy) mmy.style.display = 'none';
        } else {
          const mlisting = document.getElementById('marketplaceListings');
          const mmy = document.getElementById('myListings');
          if (mlisting) mlisting.style.display = 'none';
          if (mmy) mmy.style.display = 'grid';
        }
      });
    });

    // Mobile menu toggle
    const menuToggle = document.getElementById('menuToggle');
    if (menuToggle) {
      menuToggle.addEventListener('click', () => {
        const sidebar = document.getElementById('sidebar');
        sidebar.style.left = sidebar.style.left === '0px' ? '-280px' : '0px';
      });
    }
  }

  function populateMintWalletSelect() {
    const select = document.getElementById('mintWalletSelect');
    if (!select) return;
    
    if (!state.wallets || state.wallets.length === 0) {
      select.innerHTML = '<option>Create a wallet first</option>';
      return;
    }
    select.innerHTML = state.wallets.map(w => `
      <option value="${w.id}">${w.blockchain?.toUpperCase()} - ${formatAddr(w.address)}</option>
    `).join('');
  }

  async function submitMintForm() {
    const nameEl = document.getElementById('mintName');
    const descEl = document.getElementById('mintDesc');
    const walletEl = document.getElementById('mintWalletSelect');
    
    if (!nameEl || !descEl || !walletEl) {
      console.warn('Mint form elements not found');
      return;
    }
    
    const name = nameEl.value?.trim();
    const desc = descEl.value?.trim();
    const walletId = walletEl.value;

    if (!name || !desc || !walletId) {
      showStatus('Please fill in all required fields', 'error', false);
      return;
    }

    showStatus('Creating NFT...', 'info', true);
    try {
      const res = await API.mintNFT(state.user.id, walletId, name, desc);
      if (res.success) {
        showStatus('NFT created successfully!', 'success', false);
        nameEl.value = '';
        descEl.value = '';
        await loadDashboardData();
      } else {
        throw new Error(res.error || 'Creation failed');
      }
    } catch (err) {
      showStatus(`Error: ${err.message}`, 'error', false);
    }
  }

  function ShowCreateWalletModal() {
    const chains = ['ethereum', 'polygon', 'solana', 'ton'];
    const html = `
      <div class="form-group">
        <label>Select Blockchain</label>
        <select id="chainSelect" class="input-select">
          ${chains.map(c => `<option value="${c}">${c.charAt(0).toUpperCase() + c.slice(1)}</option>`).join('')}
        </select>
      </div>
      <button class="btn btn-primary btn-block" onclick="window.createWallet()">Create Wallet</button>
    `;
    showModal('Create New Wallet', html);
  }

  function showImportWalletModal() {
    const html = `
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
      <button class="btn btn-primary btn-block" onclick="window.importWallet()">Import Wallet</button>
    `;
    showModal('Import Wallet', html);
  }

  window.createWallet = async function() {
    const chain = document.getElementById('chainSelect')?.value;
    if (!chain) {
      showStatus('Please select a blockchain', 'error', false);
      return;
    }
    
    showStatus(`Creating ${chain} wallet...`, 'info', true);
    showModalSpinner();
    try {
      const res = await API.createWallet(state.user.id, chain);
      if (res.success) {
        showStatus('Wallet created successfully!', 'success', false);
        closeModal();
        await loadDashboardData();
      } else {
        throw new Error(res.error || 'Creation failed');
      }
    } catch (err) {
      showStatus(`Error: ${err.message}`, 'error', false);
      hideModalSpinner();
    }
  };

  window.importWallet = async function() {
    const addr = document.getElementById('importAddr')?.value?.trim();
    const chain = document.getElementById('importChain')?.value;
    
    if (!addr) {
      showStatus('Please enter an address', 'error', false);
      return;
    }
    if (!chain) {
      showStatus('Please select a blockchain', 'error', false);
      return;
    }
    
    showStatus('Importing wallet...', 'info', true);
    showModalSpinner();
    try {
      // TODO: Add import endpoint to API service
      showStatus('Import wallet functionality coming soon', 'info', false);
      hideModalSpinner();
    } catch (err) {
      showStatus(`Error: ${err.message}`, 'error', false);
      hideModalSpinner();
    }
  };

  window.showWalletDetails = function(id) {
    const w = state.wallets.find(x => x.id === id);
    if (!w) {
      showStatus('Wallet not found', 'error', false);
      return;
    }
    showModal('Wallet Details', `
      <div class="profile-section">
        <div class="profile-item"><span>Blockchain:</span><strong>${w.blockchain?.toUpperCase()}</strong></div>
        <div class="profile-item"><span>Address:</span><code style="word-break:break-all;font-size:12px;">${w.address}</code></div>
        <div class="profile-item"><span>Primary:</span><strong>${w.is_primary ? 'Yes' : 'No'}</strong></div>
        <div class="profile-item"><span>Created:</span><small>${new Date(w.created_at).toLocaleDateString()}</small></div>
      </div>
      <button class="btn btn-secondary btn-block" onclick="window.closeModal()">Close</button>
    `);
  };

  window.viewListing = function(id) {
    const listing = state.listings.find(l => l.id === id);
    if (!listing) {
      showStatus('Listing not found', 'error', false);
      return;
    }
    showModal('NFT Listing', `
      <div class="profile-section">
        <div class="profile-item"><span>NFT:</span><strong>${listing.nft?.name || 'Unknown'}</strong></div>
        <div class="profile-item"><span>Price:</span><strong>$${parseFloat(listing.price).toFixed(2)}</strong></div>
        <div class="profile-item"><span>Blockchain:</span><strong>${listing.blockchain?.toUpperCase()}</strong></div>
        <div class="profile-item"><span>Status:</span><strong>${listing.active || listing.status === 'active' ? 'For Sale' : 'Inactive'}</strong></div>
      </div>
      <button class="btn btn-primary btn-block">Make Offer</button>
      <button class="btn btn-secondary btn-block" onclick="window.closeModal()" style="margin-top:8px;">Close</button>
    `);
  };

  window.closeModal = closeModal;

  // ========== PAGE NAVIGATION ==========
  function switchPage(pageName) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    
    const page = document.getElementById(`${pageName}-page`);
    if (page) {
      page.classList.add('active');
      document.querySelector(`[data-page="${pageName}"]`)?.classList.add('active');
    }

    const titles = {
      dashboard: 'Dashboard',
      wallets: 'Wallet Management',
      nfts: 'My NFT Collection',
      mint: 'Create NFT',
      marketplace: 'Marketplace',
      profile: 'My Profile'
    };
    document.getElementById('pageTitle').textContent = titles[pageName] || 'NFT Platform';
    state.currentPage = pageName;
  }

  // Initialize app when Telegram is ready
  if (window.Telegram?.WebApp) {
    window.Telegram.WebApp.ready();
  }
  
  window.addEventListener('load', initApp);
})();

