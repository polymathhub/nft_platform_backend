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
  const modal = document.getElementById('modal');

  // ========== UTIL FUNCTIONS ==========
  function showStatus(msg, type = 'info') {
    status.textContent = msg;
    status.className = `status-alert ${type}`;
    if (type !== 'info') {
      setTimeout(() => status.classList.add('hidden'), 4000);
    }
  }

  function showModal(title, content) {
    document.getElementById('modalTitle').textContent = title;
    document.getElementById('modalBody').innerHTML = content;
    modal.style.display = 'flex';
  }

  function closeModal() {
    modal.style.display = 'none';
  }

  function truncate(str, len = 20) {
    return str && str.length > len ? str.slice(0, len - 3) + '...' : str;
  }

  function formatAddr(addr) {
    return addr ? addr.slice(0, 6) + '...' + addr.slice(-4) : '—';
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
    document.getElementById('pageTitle').textContent = titles[pageName] || 'NFT Platform';\n    state.currentPage = pageName;
  }

  // ========== INITIALIZE APP ==========
  async function initApp() {
    showStatus('Initializing NFT Platform...');

    if (!window.Telegram?.WebApp) {
      showStatus('Please open this app from Telegram using the \"Open App\" button.', 'error');
      return;
    }

    window.Telegram.WebApp.ready();
    showStatus('Authenticating with NFT Platform...');

    try {
      const initData = window.Telegram.WebApp.initData || window.Telegram.WebApp.initDataUnsafe;
      if (!initData) throw new Error('No init data');

      const res = await fetch(`${API_BASE}/telegram/web-app/init?init_data=${encodeURIComponent(initData)}`);
      const data = await res.json();

      if (!data.success) throw new Error(data.error || 'Auth failed');

      state.user = data.user;
      showStatus('Connected successfully!', 'success');
      updateUserInfo();
      setupEventListeners();
      await loadDashboardData();
      setTimeout(() => status.classList.add('hidden'), 2000);
    } catch (err) {
      showStatus(`Error: ${err.message}`, 'error');
    }
  }

  // ========== UPDATE UI ==========
  function updateUserInfo() {
    const name = state.user?.first_name || state.user?.telegram_username || 'User';
    document.getElementById('userInfo').innerHTML = `\n      <strong>${name}</strong>\n      <small>@${state.user?.telegram_username || 'user'}</small>\n    `;
  }

  async function loadDashboardData() {
    try {
      const [wallets, nfts, listings] = await Promise.all([\n        fetch(`${API_BASE}/wallets?user_id=${state.user.id}`).then(r => r.json()),\n        fetch(`${API_BASE}/telegram/web-app/nfts?user_id=${state.user.id}`).then(r => r.json()),\n        fetch(`${API_BASE}/telegram/web-app/marketplace/listings`).then(r => r.json())\n      ]);

      state.wallets = Array.isArray(wallets) ? wallets : [];
      state.nfts = Array.isArray(nfts) ? nfts : [];
      state.listings = Array.isArray(listings) ? listings : [];

      updateDashboard();
      updateWalletsList();
      updateNftsList();
      updateMarketplace();
    } catch (err) {
      console.error('Load data error:', err);
    }
  }

  function updateDashboard() {
    document.getElementById('portfolioValue').textContent = '$' + (state.nfts.length * 100).toFixed(2);
    document.getElementById('totalNfts').textContent = state.nfts.length;
    document.getElementById('totalWallets').textContent = state.wallets.length;
    document.getElementById('totalListings').textContent = state.listings.filter(l => l.active).length;

    const activity = `\n      <div class=\"activity-item\">\n        <span class=\"activity-type\">Connected</span>\n        <span class=\"activity-time\">Just now</span>\n      </div>\n    `;
    document.getElementById('recentActivity').innerHTML = activity;

    // Profile stats
    const profileInfo = `\n      <div class=\"profile-item\">\n        <span>Username:</span>\n        <strong>@${state.user?.telegram_username || 'user'}</strong>\n      </div>\n      <div class=\"profile-item\">\n        <span>Name:</span>\n        <strong>${state.user?.first_name || 'User'}</strong>\n      </div>\n      <div class=\"profile-item\">\n        <span>Member Since:</span>\n        <strong>February 2026</strong>\n      </div>\n    `;
    document.getElementById('profileInfo').innerHTML = profileInfo;

    const stats = `\n      <div class=\"stat-item\">\n        <div class=\"stat-value\">${state.nfts.length}</div>\n        <div class=\"stat-label\">Total NFTs</div>\n      </div>\n      <div class=\"stat-item\">\n        <div class=\"stat-value\">${state.wallets.length}</div>\n        <div class=\"stat-label\">Wallets</div>\n      </div>\n      <div class=\"stat-item\">\n        <div class=\"stat-value\">${state.listings.length}</div>\n        <div class=\"stat-label\">Listings</div>\n      </div>\n      <div class=\"stat-item\">\n        <div class=\"stat-value\">0</div>\n        <div class=\"stat-label\">Sales</div>\n      </div>\n    `;
    document.getElementById('profileStats').innerHTML = stats;
  }

  function updateWalletsList() {
    const html = state.wallets.map(w => `\n      <div class=\"card wallet-card\">\n        <div class=\"wallet-blockchain\">\n          <strong>${w.blockchain?.toUpperCase() || 'Wallet'}</strong>\n          ${w.is_primary ? '<span class=\"blockchain-badge\">Primary</span>' : ''}\n        </div>\n        <div class=\"wallet-address\">${formatAddr(w.address)}</div>\n        <div class=\"wallet-actions\">\n          <button class=\"btn btn-secondary\" onclick=\"window.showWalletDetails('${w.id}')\">Details</button>\n        </div>\n      </div>\n    `).join('');
    document.getElementById('walletsList').innerHTML = html || '<p class=\"muted\">No wallets yet</p>';
  }

  function updateNftsList() {
    const html = state.nfts.map(nft => `\n      <div class=\"card nft-card\">\n        <div class=\"nft-image\">${nft.image_url ? `<img src=\"${nft.image_url}\" alt=\"${nft.name}\">` : '🎨'}</div>\n        <div class=\"nft-content\">\n          <div class=\"nft-name\">${truncate(nft.name, 25)}</div>\n          <div class=\"nft-collection\">${nft.collection?.name || 'No Collection'}</div>\n          <div class=\"nft-price\">$${(Math.random() * 10000).toFixed(0)}</div>\n        </div>\n      </div>\n    `).join('');
    document.getElementById('nftList').innerHTML = html || '<p class=\"muted\">No NFTs yet</p>';
  }

  function updateMarketplace() {\n    const html = state.listings.map(l => `\n      <div class=\"card nft-card\">\n        <div class=\"nft-image\">💎</div>\n        <div class=\"nft-content\">\n          <div class=\"nft-name\">${truncate(l.nft?.name || 'NFT', 25)}</div>\n          <div class=\"nft-collection\">${l.nft?.collection?.name || 'Unknown'}</div>\n          <div class=\"nft-price\">$${l.price.toFixed(2)}</div>\n          <button class=\"btn btn-primary\" style=\"width:100%;margin-top:8px;\" onclick=\"window.viewListing('${l.id}')\">View</button>\n        </div>\n      </div>\n    `).join('');\n    document.getElementById('marketplaceListings').innerHTML = html || '<p class=\"muted\">No listings</p>';
  }

  // ========== EVENT LISTENERS ==========
  function setupEventListeners() {
    // Navigation
    document.querySelectorAll('.nav-item').forEach(item => {
      item.addEventListener('click', (e) => {\n        e.preventDefault();\n        switchPage(item.dataset.page);\n      });\n    });

    // Modal
    document.getElementById('closeModal').addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => e.target === modal && closeModal());

    // Wallet buttons
    document.getElementById('createWalletBtn').addEventListener('click', () => showCreateWalletModal());
    document.getElementById('importWalletBtn').addEventListener('click', () => showImportWalletModal());

    // Mint form
    populateMintWalletSelect();
    document.getElementById('mintNftBtn').addEventListener('click', () => submitMintForm());

    // Marketplace tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {\n        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));\n        btn.classList.add('active');\n        if (btn.dataset.tab === 'listings') {\n          document.getElementById('marketplaceListings').style.display = 'grid';\n          document.getElementById('myListings').style.display = 'none';\n        } else {\n          document.getElementById('marketplaceListings').style.display = 'none';\n          document.getElementById('myListings').style.display = 'grid';\n        }\n      });\n    });\n  }

  function populateMintWalletSelect() {\n    const select = document.getElementById('mintWalletSelect');\n    select.innerHTML = state.wallets.map(w => `\n      <option value=\"${w.id}\">${w.blockchain?.toUpperCase()} - ${formatAddr(w.address)}</option>\n    `).join('');\n  }

  async function submitMintForm() {\n    const name = document.getElementById('mintName').value.trim();\n    const desc = document.getElementById('mintDesc').value.trim();\n    const walletId = document.getElementById('mintWalletSelect').value;

    if (!name || !desc || !walletId) {\n      showStatus('Please fill in all required fields', 'error');\n      return;\n    }

    showStatus('Creating NFT...');\n    try {\n      const res = await fetch(`${API_BASE}/telegram/web-app/mint`, {\n        method: 'POST',\n        headers: { 'Content-Type': 'application/json' },\n        body: JSON.stringify({\n          user_id: state.user.id,\n          wallet_id: walletId,\n          nft_name: name,\n          nft_description: desc\n        })\n      });\n      const data = await res.json();\n      if (data.success) {\n        showStatus('NFT created successfully!', 'success');\n        document.getElementById('mintName').value = '';\n        document.getElementById('mintDesc').value = '';\n        await loadDashboardData();\n      } else {\n        throw new Error(data.error || 'Creation failed');\n      }\n    } catch (err) {\n      showStatus(`Error: ${err.message}`, 'error');\n    }\n  }

  function showCreateWalletModal() {\n    const chains = ['ethereum', 'polygon', 'solana', 'ton'];\n    const html = `\n      <div class=\"form-group\">\n        <label>Please select a blockchain</label>\n        <select id=\"chainSelect\" style=\"margin-bottom:16px;\" class=\"input-select\">\n          ${chains.map(c => `<option value=\"${c}\">${c.toUpperCase()}</option>`).join('')}\n        </select>\n      </div>\n      <button class=\"btn btn-primary btn-block\" onclick=\"window.createWallet()\">Create Wallet</button>\n    `;\n    showModal('Create New Wallet', html);\n  }

  function showImportWalletModal() {\n    const html = `\n      <div class=\"form-group\">\n        <label>Wallet Address</label>\n        <input type=\"text\" id=\"importAddr\" placeholder=\"Wallet address\" class=\"input-text\">\n      </div>\n      <div class=\"form-group\">\n        <label>Blockchain</label>\n        <select id=\"importChain\" class=\"input-select\">\n          <option value=\"ethereum\">Ethereum</option>\n          <option value=\"polygon\">Polygon</option>\n          <option value=\"solana\">Solana</option>\n          <option value=\"ton\">TON</option>\n        </select>\n      </div>\n      <button class=\"btn btn-primary btn-block\" onclick=\"window.importWallet()\">Import Wallet</button>\n    `;\n    showModal('Import Wallet', html);\n  }

  window.createWallet = async function() {\n    const chain = document.getElementById('chainSelect').value;\n    showStatus(`Creating ${chain} wallet...`);\n    try {\n      const res = await fetch(`${API_BASE}/wallets/create`, {\n        method: 'POST',\n        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },\n        body: new URLSearchParams({ user_id: state.user.id, blockchain: chain })\n      });\n      const data = await res.json();\n      if (data.success) {\n        showStatus('Wallet created!', 'success');\n        closeModal();\n        await loadDashboardData();\n      }\n    } catch (err) {\n      showStatus(`Error: ${err.message}`, 'error');\n    }\n  };

  window.importWallet = async function() {\n    const addr = document.getElementById('importAddr').value.trim();\n    const chain = document.getElementById('importChain').value;\n    if (!addr) {\n      showStatus('Please enter an address', 'error');\n      return;\n    }\n    showStatus('Importing wallet...');\n    try {\n      const res = await fetch(`${API_BASE}/wallets/import?user_id=${state.user.id}`, {\n        method: 'POST',\n        headers: { 'Content-Type': 'application/json' },\n        body: JSON.stringify({ blockchain: chain, address: addr, name: `${chain} Imported` })\n      });\n      const data = await res.json();\n      if (data.success) {\n        showStatus('Wallet imported!', 'success');\n        closeModal();\n        await loadDashboardData();\n      }\n    } catch (err) {\n      showStatus(`Error: ${err.message}`, 'error');\n    }\n  };

  window.showWalletDetails = function(id) {\n    const w = state.wallets.find(x => x.id === id);\n    if (!w) return;\n    showModal('Wallet Details', `\n      <div class=\"profile-section\">\n        <div class=\"profile-item\"><span>Blockchain:</span><strong>${w.blockchain?.toUpperCase()}</strong></div>\n        <div class=\"profile-item\"><span>Address:</span><code>${w.address}</code></div>\n        <div class=\"profile-item\"><span>Primary:</span><strong>${w.is_primary ? 'Yes' : 'No'}</strong></div>\n      </div>\n    `);\n  };

  window.viewListing = function(id) {\n    const listing = state.listings.find(l => l.id === id);\n    if (!listing) return;\n    showModal('NFT Details', `\n      <div class=\"profile-section\">\n        <div class=\"profile-item\"><span>NFT:</span><strong>${listing.nft?.name || 'Unknown'}</strong></div>\n        <div class=\"profile-item\"><span>Price:</span><strong>$${listing.price}</strong></div>\n        <div class=\"profile-item\"><span>Status:</span><strong>${listing.active ? 'For Sale' : 'Inactive'}</strong></div>\n      </div>\n      <button class=\"btn btn-primary btn-block\" onclick=\"closeModal()\">Make Offer</button>\n    `);\n  };

  // Initialize
  initApp();
})();
