(async function() {
  'use strict';

  // ========== STATE & CONFIG ==========
  const state = {
    user: null,
    wallets: [],
    nfts: [],
    listings: [],
    myListings: [],
    currentPage: 'dashboard'
  };

  const API_BASE = '/api/v1';
  const status = document.getElementById('status');
  const statusText = document.getElementById('statusText');
  const statusSpinner = document.getElementById('statusSpinner');
  const modal = document.getElementById('modal');
  const modalSpinner = document.getElementById('modalSpinner');

  // Request caching and debouncing
  const cache = {};
  const pendingRequests = {};
  let debounceTimers = {};

  // ========== UTIL FUNCTIONS ==========
  function showStatus(msg, type = 'info', showSpinner = type === 'info') {
    statusText.textContent = msg;
    status.className = `status-alert ${type}`;
    statusSpinner.style.display = showSpinner ? 'inline-block' : 'none';
    
    if (type !== 'info') {
      setTimeout(() => {
        status.classList.add('hidden');
        statusSpinner.style.display = 'none';
      }, 4000);
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

  function showModalSpinner() {
    modalSpinner.style.display = 'block';
  }

  function hideModalSpinner() {
    modalSpinner.style.display = 'none';
  }

  function truncate(str, len = 20) {
    return str && str.length > len ? str.slice(0, len - 3) + '...' : str;
  }

  function formatAddr(addr) {
    return addr ? addr.slice(0, 6) + '...' + addr.slice(-4) : '—';
  }

  // Optimized fetch with caching and deduplication
  async function cachedFetch(url, options = {}) {
    // Return cached response if available and not expired
    if (cache[url] && cache[url].expires > Date.now()) {
      return cache[url].data;
    }

    // If request already in progress, return existing promise
    if (pendingRequests[url]) {
      return pendingRequests[url];
    }

    // Create new request promise
    pendingRequests[url] = fetch(url, options)
      .then(async r => {
        if (!r.ok) {
          const text = await r.text();
          console.error(`API error ${r.status}:`, text);
          throw new Error(`API error ${r.status}: ${text}`);
        }
        return r.json();
      })
      .then(data => {
        // Cache for 60 seconds
        cache[url] = { data, expires: Date.now() + 60000 };
        delete pendingRequests[url];
        return data;
      })
      .catch(err => {
        delete pendingRequests[url];
        console.error(`Fetch error for ${url}:`, err);
        throw err;
      });

    return pendingRequests[url];
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
    if (window.performance && window.performance.mark) {
      performance.mark('app-start');
    }
    
    showStatus('Initializing NFT Platform...', 'info', true);

    // Check if in Telegram context or development mode
    const isDevelopment = !window.Telegram?.WebApp;
    const initData = window.Telegram?.WebApp?.initData || window.Telegram?.WebApp?.initDataUnsafe;
    
    if (!isDevelopment && !initData) {
      showStatus('Please open this app from Telegram', 'error', false);
      return;
    }

    if (!isDevelopment) {
      window.Telegram.WebApp.ready();
    }
    
    showStatus('Authenticating...', 'info', true);

    try {
      let authResponse;
      
      if (isDevelopment) {
        // Development mode: use mock authentication
        console.warn('Running in development mode (not in Telegram)');
        authResponse = {
          success: true,
          user: {
            id: 'dev-user-123',
            telegram_id: 123456789,
            telegram_username: 'developer',
            first_name: 'Test',
            last_name: 'User',
            email: 'dev@example.com'
          }
        };
        
        // Add mock data for development
        state.wallets = [
          {
            id: 'wallet-1',
            name: 'Ethereum Wallet',
            blockchain: 'ethereum',
            address: '0x1234567890abcdef1234567890abcdef12345678',
            is_primary: true,
            created_at: '2024-01-15T10:30:00'
          },
          {
            id: 'wallet-2',
            name: 'Solana Wallet',
            blockchain: 'solana',
            address: 'So11111111111111111111111111111111111111112',
            is_primary: false,
            created_at: '2024-01-20T14:22:00'
          },
          {
            id: 'wallet-3',
            name: 'Polygon Wallet',
            blockchain: 'polygon',
            address: '0xabcdefabcdefabcdefabcdefabcdefabcdefabcd',
            is_primary: false,
            created_at: '2024-02-01T08:15:00'
          }
        ];
        
        state.nfts = [
          {
            id: 'nft-1',
            name: 'Cosmic Nebula #42',
            global_nft_id: 'cosmic-42',
            description: 'A stunning visualization of a cosmic nebula',
            blockchain: 'ethereum',
            status: 'minted',
            image_url: 'https://picsum.photos/400/400?random=1',
            collection: { name: 'Space Series' },
            minted_at: '2024-01-10T11:00:00',
            created_at: '2024-01-10T11:00:00'
          },
          {
            id: 'nft-2',
            name: 'Digital Art Genesis #1',
            global_nft_id: 'art-genesis-1',
            description: 'The first piece in the Digital Art Genesis collection',
            blockchain: 'solana',
            status: 'minted',
            image_url: 'https://picsum.photos/400/400?random=2',
            collection: { name: 'Digital Art Genesis' },
            minted_at: '2024-02-05T15:30:00',
            created_at: '2024-02-05T15:30:00'
          },
          {
            id: 'nft-3',
            name: 'Pixel Dreams #88',
            global_nft_id: 'pixel-88',
            description: 'Retro pixel art meets modern blockchain',
            blockchain: 'polygon',
            status: 'minted',
            image_url: 'https://picsum.photos/400/400?random=3',
            collection: { name: 'Pixel Dreams' },
            minted_at: '2024-02-10T09:45:00',
            created_at: '2024-02-10T09:45:00'
          },
          {
            id: 'nft-4',
            name: 'Abstract Waves #15',
            global_nft_id: 'waves-15',
            description: 'Flowing abstract waves in motion',
            blockchain: 'ethereum',
            status: 'minted',
            image_url: 'https://picsum.photos/400/400?random=4',
            collection: { name: 'Abstract Series' },
            minted_at: '2024-02-12T13:20:00',
            created_at: '2024-02-12T13:20:00'
          }
        ];
        
        state.listings = [
          {
            id: 'listing-1',
            nft_id: 'nft-1',
            nft: state.nfts[0],
            nft_name: 'Cosmic Nebula #42',
            price: 2.5,
            currency: 'ETH',
            blockchain: 'ethereum',
            status: 'active',
            image_url: 'https://picsum.photos/400/400?random=1',
            active: true
          },
          {
            id: 'listing-2',
            nft_id: 'nft-2',
            nft: state.nfts[1],
            nft_name: 'Digital Art Genesis #1',
            price: 125.0,
            currency: 'SOL',
            blockchain: 'solana',
            status: 'active',
            image_url: 'https://picsum.photos/400/400?random=2',
            active: true
          },
          {
            id: 'listing-3',
            nft_id: 'nft-3',
            nft: state.nfts[2],
            nft_name: 'Pixel Dreams #88',
            price: 850.0,
            currency: 'MATIC',
            blockchain: 'polygon',
            status: 'active',
            image_url: 'https://picsum.photos/400/400?random=3',
            active: true
          }
        ];
      } else {
        // Production mode: authenticate with backend
        authResponse = await cachedFetch(`${API_BASE}/telegram/web-app/init?init_data=${encodeURIComponent(initData)}`);
      }

      if (!authResponse.success) throw new Error(authResponse.error || 'Auth failed');

      state.user = authResponse.user;
      
      if (window.performance && window.performance.mark) {
        performance.mark('auth-complete');
      }
      
      showStatus('Connected successfully!', 'success', false);
      updateUserInfo();
      setupEventListeners();
      setupLazyLoading();
      
      // Load dashboard data
      if (window.performance && window.performance.mark) {
        performance.mark('data-load-start');
      }
      
      await loadDashboardData();
      
      if (window.performance && window.performance.mark) {
        performance.mark('data-load-complete');
        performance.measure('auth-time', 'app-start', 'auth-complete');
        performance.measure('data-load-time', 'data-load-start', 'data-load-complete');
      }
      
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

  async function loadDashboardData() {
    try {
      const isDevelopment = !window.Telegram?.WebApp;
      
      // Skip API call in development mode since we already have mock data
      if (!isDevelopment) {
        // Use optimized combined endpoint instead of 3 separate calls
        const data = await cachedFetch(`${API_BASE}/telegram/web-app/dashboard-data?user_id=${state.user.id}`);

        state.wallets = Array.isArray(data.wallets) ? data.wallets : [];
        state.nfts = Array.isArray(data.nfts) ? data.nfts : [];
        state.listings = Array.isArray(data.listings) ? data.listings : [];
      }
      // else: use already-loaded mock data from initApp()

      updateDashboard();
      updateWalletsList();
      updateNftsList();
      updateMarketplace();
    } catch (err) {
      console.error('Load data error:', err);
      // Provide default empty data to allow UI to render
      state.wallets = [];
      state.nfts = [];
      state.listings = [];
      updateDashboard();
      updateWalletsList();
      updateNftsList();
      updateMarketplace();
      showStatus('Data loaded (empty)', 'info', false);
    }
  }

  function updateDashboard() {
    const portfolioValue = state.nfts.length * 100;
    
    // Safely update DOM elements, checking existence first
    if (document.getElementById('portfolioValue')) document.getElementById('portfolioValue').textContent = '$' + portfolioValue.toFixed(2);
    if (document.getElementById('totalNfts')) document.getElementById('totalNfts').textContent = state.nfts.length;
    if (document.getElementById('totalWallets')) document.getElementById('totalWallets').textContent = state.wallets.length;
    if (document.getElementById('totalListings')) document.getElementById('totalListings').textContent = state.listings.filter(l => l.active).length;

    const activity = `
      <div class="activity-item">
        <span class="activity-type">Platform Ready</span>
        <span class="activity-time">Just now</span>
      </div>
    `;
    if (document.getElementById('recentActivity')) document.getElementById('recentActivity').innerHTML = activity;

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
        <span>Wallets Connected:</span>
        <strong>${state.wallets.length}</strong>
      </div>
    `;
    if (document.getElementById('profileInfo')) document.getElementById('profileInfo').innerHTML = profileInfo;

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
        <div class="stat-value">${state.listings.filter(l => l.active).length}</div>
        <div class="stat-label">Listings</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">$${portfolioValue.toFixed(0)}</div>
        <div class="stat-label">Value</div>
      </div>
    `;
    if (document.getElementById('profileStats')) document.getElementById('profileStats').innerHTML = stats;
  }

  function updateWalletsList() {
    const html = state.wallets.map(w => `
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
      document.getElementById('walletsList').innerHTML = html || '<p class="muted">No wallets yet</p>';
    }
  }

  function updateNftsList() {
    const html = state.nfts.map(nft => `
      <div class="card nft-card">
        <div class="nft-image">${nft.image_url ? `<img src="${nft.image_url}" alt="${nft.name}" loading="lazy">` : '<div style="background:var(--bg-base);display:flex;align-items:center;justify-content:center;height:100%;">No Image</div>'}</div>
        <div class="nft-content">
          <div class="nft-name">${truncate(nft.name, 25)}</div>
          <div class="nft-collection">${nft.collection?.name || 'No Collection'}</div>
          <div class="nft-price">$${(Math.random() * 10000).toFixed(0)}</div>
        </div>
      </div>
    `).join('');
    if (document.getElementById('nftList')) {
      document.getElementById('nftList').innerHTML = html || '<p class="muted">No NFTs yet</p>';
    }
  }

  function updateMarketplace() {
    const html = state.listings.map(l => `
      <div class="card nft-card">
        <div class="nft-image">${l.nft?.image_url ? `<img src="${l.nft.image_url}" alt="NFT" loading="lazy">` : '<div style="background:var(--bg-base);display:flex;align-items:center;justify-content:center;height:100%;">Marketplace Item</div>'}</div>
        <div class="nft-content">
          <div class="nft-name">${truncate(l.nft?.name || 'NFT', 25)}</div>
          <div class="nft-collection">${l.nft?.collection?.name || 'Unknown'}</div>
          <div class="nft-price">$${l.price?.toFixed(2) || '0.00'}</div>
          <button class="btn btn-primary" style="width:100%;margin-top:8px;" onclick="window.viewListing('${l.id}')">View</button>
        </div>
      </div>
    `).join('');
    if (document.getElementById('marketplaceListings')) {
      document.getElementById('marketplaceListings').innerHTML = html || '<p class="muted">No listings</p>';
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

    // Modal (safely check for elements)
    if (document.getElementById('closeModal')) {
      document.getElementById('closeModal').addEventListener('click', closeModal);
    }
    if (document.getElementById('modalOverlay')) {
      document.getElementById('modalOverlay').addEventListener('click', closeModal);
    }

    // Wallet buttons
    if (document.getElementById('createWalletBtn')) {
      document.getElementById('createWalletBtn').addEventListener('click', showCreateWalletModal);
    }
    if (document.getElementById('importWalletBtn')) {
      document.getElementById('importWalletBtn').addEventListener('click', showImportWalletModal);
    }

    // Mint form
    populateMintWalletSelect();
    if (document.getElementById('mintNftBtn')) {
      document.getElementById('mintNftBtn').addEventListener('click', submitMintForm);
    }

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
    document.getElementById('menuToggle').addEventListener('click', () => {
      const sidebar = document.getElementById('sidebar');
      sidebar.style.left = sidebar.style.left === '0px' ? '-280px' : '0px';
    });
  }

  function populateMintWalletSelect() {
    const select = document.getElementById('mintWalletSelect');
    if (!select) return;  // Exit if element doesn't exist
    
    if (!state.wallets.length) {
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
    
    const name = nameEl.value.trim();
    const desc = descEl.value.trim();
    const walletId = walletEl.value;

    if (!name || !desc || !walletId) {
      showStatus('Please fill in all required fields', 'error', false);
      return;
    }

    showStatus('Creating NFT...', 'info', true);
    try {
      const res = await fetch(`${API_BASE}/telegram/web-app/mint`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: state.user.id,
          wallet_id: walletId,
          nft_name: name,
          nft_description: desc
        })
      });
      const data = await res.json();
      if (data.success) {
        showStatus('NFT created successfully!', 'success', false);
        nameEl.value = '';
        descEl.value = '';
        // Clear cache and reload
        Object.keys(cache).forEach(k => delete cache[k]);
        await loadDashboardData();
      } else {
        throw new Error(data.error || 'Creation failed');
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
          ${chains.map(c => `<option value="${c}">${c.toUpperCase()}</option>`).join('')}
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
    const chain = document.getElementById('chainSelect').value;
    showStatus(`Creating ${chain} wallet...`, 'info', true);
    showModalSpinner();
    try {
      const res = await fetch(`${API_BASE}/wallets/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ user_id: state.user.id, blockchain: chain })
      });
      const data = await res.json();
      if (data.success) {
        showStatus('Wallet created!', 'success', false);
        closeModal();
        Object.keys(cache).forEach(k => delete cache[k]);
        await loadDashboardData();
      }
    } catch (err) {
      showStatus(`Error: ${err.message}`, 'error', false);
      hideModalSpinner();
    }
  };

  window.importWallet = async function() {
    const addr = document.getElementById('importAddr').value.trim();
    const chain = document.getElementById('importChain').value;
    if (!addr) {
      showStatus('Please enter an address', 'error', false);
      return;
    }
    showStatus('Importing wallet...', 'info', true);
    showModalSpinner();
    try {
      const res = await fetch(`${API_BASE}/wallets/import?user_id=${state.user.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ blockchain: chain, address: addr, name: `${chain} Imported` })
      });
      const data = await res.json();
      if (data.success) {
        showStatus('Wallet imported!', 'success', false);
        closeModal();
        Object.keys(cache).forEach(k => delete cache[k]);
        await loadDashboardData();
      }
    } catch (err) {
      showStatus(`Error: ${err.message}`, 'error', false);
      hideModalSpinner();
    }
  };

  window.showWalletDetails = function(id) {
    const w = state.wallets.find(x => x.id === id);
    if (!w) return;
    showModal('Wallet Details', `
      <div class="profile-section">
        <div class="profile-item"><span>Blockchain:</span><strong>${w.blockchain?.toUpperCase()}</strong></div>
        <div class="profile-item"><span>Address:</span><code style="word-break:break-all;">${w.address}</code></div>
        <div class="profile-item"><span>Primary:</span><strong>${w.is_primary ? 'Yes' : 'No'}</strong></div>
      </div>
    `);
  };

  window.viewListing = function(id) {
    const listing = state.listings.find(l => l.id === id);
    if (!listing) return;
    showModal('NFT Details', `
      <div class="profile-section">
        <div class="profile-item"><span>NFT:</span><strong>${listing.nft?.name || 'Unknown'}</strong></div>
        <div class="profile-item"><span>Price:</span><strong>$${listing.price}</strong></div>
        <div class="profile-item"><span>Status:</span><strong>${listing.active ? 'For Sale' : 'Inactive'}</strong></div>
      </div>
      <button class="btn btn-primary btn-block" onclick="window.closeModal()">Close</button>
    `);
  };

  window.closeModal = closeModal;

  // Initialize
  initApp();
})();

