(function() {
  'use strict';
  
  /* ========== STATE MANAGEMENT ========== */
  const state = {
    // Auth & User
    auth: {
      token: localStorage.getItem('auth_token') || null,
      user: null,
      ready: false,
    },
    
    // Wallet
    wallet: {
      connected: JSON.parse(localStorage.getItem('wallet_connected') || 'false'),
      address: localStorage.getItem('wallet_address') || null,
      method: null,
      popupDismissed: JSON.parse(localStorage.getItem('wallet_popup_dismissed') || 'false'),
    },
    
    // UI
    ui: {
      view: 'market',
      loading: false,
      error: null,
      modal: null,
      viewMode: localStorage.getItem('view_mode') || 'grid',
    },
    
    // Marketplace
    marketplace: {
      sort: localStorage.getItem('marketplace_sort') || 'created_at_desc',
      filters: {
        priceMin: null,
        priceMax: null,
        availability: true,
      },
      filterModalOpen: false,
    },
    
    // Data
    data: {
      listings: [],
      myItems: [],
      transactions: [],
      referrals: [],
      userStats: {},
    },
    
    // Cart & Payment
    cart: {
      items: [],
      total: 0,
    },
    
    payment: {
      pending: false,
      invoiceId: null,
      status: null,
    },
  };
  
  const config = {
    API_BASE: '/api/v1',
    CACHE_TTL: 300000, // 5 min
    PAYMENT_POLL_INTERVAL: 1000,
    PAYMENT_POLL_MAX: 30,
    COMMISSION_RATE: 0.02,
    REFERRAL_RATE: 0.1,
  };

  /* ========== SVG ICON MANAGEMENT ========== */
  const iconManager = {
    /**
     * Set button loading state with animated icon
     */
    setButtonLoading(button, isLoading = true) {
      if (!button) return;
      
      button.disabled = isLoading;
      const labels = button.querySelectorAll('span');
      
      if (isLoading) {
        // Fade out text
        labels.forEach(label => label.style.opacity = '0.6');
      } else {
        // Restore text opacity
        labels.forEach(label => label.style.opacity = '1');
      }
    },

    /**
     * Update icon to show status
     */
    setIconStatus(iconElement, status) {
      if (!iconElement) return;

      // Remove existing state classes
      iconElement.classList.remove('svg-icon-animate', 'icon--success', 'icon--error', 'icon--warning');

      // Add new status class
      const statusClassMap = {
        loading: 'svg-icon-animate',
        success: 'icon--success',
        error: 'icon--error',
        warning: 'icon--warning',
      };

      const className = statusClassMap[status];
      if (className) {
        iconElement.classList.add(className);
      }
    },

    /**
     * Replace icon with different one for status display
     */
    async replaceIcon(container, newIconId) {
      if (!container || !window.svgIcons) return;

      const existingIcon = container.querySelector('svg');
      if (existingIcon) {
        const newIcon = window.svgIcons.createIcon(newIconId, {
          size: '24',
          className: 'icon icon--md',
          ariaHidden: true,
        });
        existingIcon.replaceWith(newIcon);
      }
    },

    /**
     * Show loading spinner on button
     */
    showLoadingSpinner(button) {
      this.setButtonLoading(button, true);
      const icon = button.querySelector('svg');
      if (icon) {
        this.setIconStatus(icon, 'loading');
      }
    },

    /**
     * Show success icon on button
     */
    showSuccessIcon(button) {
      this.setButtonLoading(button, false);
      const icon = button.querySelector('svg');
      if (icon) {
        this.setIconStatus(icon, 'success');
      }
    },

    /**
     * Show error icon on button
     */
    showErrorIcon(button) {
      this.setButtonLoading(button, false);
      const icon = button.querySelector('svg');
      if (icon) {
        this.setIconStatus(icon, 'error');
      }
    },
  };
  
  /* ========== API LAYER ========== */
  const api = {
    cache: {},
    
    getCacheKey(endpoint) {
      return `cache_${endpoint}_${state.auth.token}`;
    },
    
    async call(endpoint, options = {}) {
      const { method = 'GET', body = null, skipCache = false } = options;
      
      // Check cache for GET
      if (method === 'GET' && !skipCache) {
        const cached = sessionStorage.getItem(this.getCacheKey(endpoint));
        if (cached) {
          const { data, timestamp } = JSON.parse(cached);
          if (Date.now() - timestamp < config.CACHE_TTL) {
            return data;
          }
          sessionStorage.removeItem(this.getCacheKey(endpoint));
        }
      }
      
      const url = endpoint.startsWith('/') ? endpoint : `${config.API_BASE}${endpoint}`;
      
      const init = {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...(state.auth.token && { 'Authorization': `Bearer ${state.auth.token}` }),
        },
      };
      
      if (body) init.body = JSON.stringify(body);
      
      try {
        const response = await fetch(url, init);
        
        if (!response.ok) {
          const error = await response.json().catch(() => ({}));
          throw new Error(error.detail || `HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        // Cache GET responses
        if (method === 'GET') {
          sessionStorage.setItem(
            this.getCacheKey(endpoint),
            JSON.stringify({ data, timestamp: Date.now() })
          );
        }
        
        return data;
      } catch (err) {
        console.error(`API Error [${endpoint}]:`, err);
        throw err;
      }
    },
    
    clearCache() {
      Object.keys(sessionStorage).forEach(key => {
        if (key.startsWith('cache_')) sessionStorage.removeItem(key);
      });
    },
  };
  
  /* ========== NOTIFICATIONS ========== */
  const notify = {
    toasts: [],
    
    show(message, type = 'info', duration = 3000) {
      const id = Math.random().toString(36).substr(2, 9);
      const toast = document.createElement('div');
      toast.style.cssText = `
        position: fixed;
        bottom: 80px;
        right: 16px;
        max-width: 300px;
        padding: 12px 16px;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 500;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
        animation: slideInRight 200ms ease-out;
        z-index: 3000;
        margin-bottom: ${this.toasts.length * 12}px;
      `;
      toast.textContent = message;
      document.body.appendChild(toast);
      
      this.toasts.push({ id, element: toast });
      
      setTimeout(() => {
        toast.style.animation = 'slideOutRight 200ms ease-out';
        setTimeout(() => {
          toast.remove();
          this.toasts = this.toasts.filter(t => t.id !== id);
        }, 200);
      }, duration);
      
      // Add animation styles if not exists
      if (!document.querySelector('style[data-toasts]')) {
        const style = document.createElement('style');
        style.setAttribute('data-toasts', 'true');
        style.textContent = `
          @keyframes slideInRight {
            from { transform: translateX(400px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
          }
          @keyframes slideOutRight {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(400px); opacity: 0; }
          }
        `;
        document.head.appendChild(style);
      }
    },
    
    success(message) { this.show(message, 'success'); },
    error(message) { this.show(message, 'error', 4000); },
    info(message) { this.show(message, 'info'); },
  };
  
  /* ========== UI LAYER ========== */
  const ui = {
    setView(viewName) {
      document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));
      const view = document.querySelector(`#view-${viewName}`);
      if (view) view.classList.remove('hidden');
      
      document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.view === viewName);
      });
      
      state.ui.view = viewName;
      this.updateHeader();
    },
    
    updateHeader() {
      const titles = {
        market: { title: 'Marketplace', subtitle: 'Browse and trade' },
        create: { title: 'Create', subtitle: 'Mint & list items' },
        wallet: { title: 'Wallet', subtitle: 'Manage funds' },
        referrals: { title: 'Referrals', subtitle: 'Earn rewards' },
        profile: { title: 'Profile', subtitle: 'Your account' },
      };
      
      const info = titles[state.ui.view] || {};
      document.querySelector('#pageTitle').textContent = info.title;
      document.querySelector('#pageSubtitle').textContent = info.subtitle;
      
      // Show/hide marketplace controls
      const controls = document.querySelector('#marketplaceHeaderControls');
      if (state.ui.view === 'market') {
        controls.classList.remove('hidden');
      } else {
        controls.classList.add('hidden');
      }
    },
    
    loading(show = true) {
      state.ui.loading = show;
    },
    
    error(message) {
      state.ui.error = message;
      console.error('UI Error:', message);
    },
    
    showToast(message, type = 'info') {
      notify.show(message, type);
    },
    
    openModal(content) {
      const overlay = document.querySelector('#modalOverlay');
      const existing = overlay.querySelector('.modal');
      if (existing) existing.remove();
      
      overlay.innerHTML = `
        <div class="modal">
          ${content}
        </div>
      `;
      overlay.classList.add('active');
      
      overlay.querySelector('.modal-close')?.addEventListener('click', () => {
        ui.closeModal();
      });
    },
    
    closeModal() {
      document.querySelector('#modalOverlay').classList.remove('active');
    },
  };
  
  /* ========== AUTH FLOWS ========== */
  const auth = {
    async initTelegram() {
      // Initialize Telegram WebApp
      if (typeof window.Telegram !== 'undefined' && window.Telegram.WebApp) {
        const tg = window.Telegram.WebApp;
        tg.ready();
        
        // Expand to full height
        if (tg.expand) tg.expand();
        
        // Get user data
        const initData = tg.initData;
        const user = tg.initDataUnsafe?.user;
        
        if (user && initData) {
          try {
            // Sign in with Telegram data
            const response = await api.call('/auth/telegram', {
              method: 'POST',
              body: { initData },
            });
            
            state.auth.token = response.token;
            state.auth.user = response.user;
            localStorage.setItem('auth_token', response.token);
            
            this.isReady = true;
            return true;
          } catch (err) {
            notify.error('Authentication failed');
            console.error(err);
          }
        }
      }
      
      return false;
    },
    
    async walletSignIn() {
      try {
        if (!window.ethereum) {
          throw new Error('MetaMask not installed');
        }
        
        // Request accounts
        const accounts = await window.ethereum.request({
          method: 'eth_requestAccounts',
        });
        
        const address = accounts[0];
        
        // Get message to sign
        const msgResponse = await api.call('/stars/wallet/message', {
          method: 'GET',
        });
        
        const message = msgResponse.message;
        
        // Sign message
        const signature = await window.ethereum.request({
          method: 'personal_sign',
          params: [message, address],
        });
        
        // Sign in
        const response = await api.call('/stars/wallet/signin', {
          method: 'POST',
          body: { address, message, signature },
        });
        
        state.auth.token = response.auth_token;
        state.auth.user = response.user;
        state.wallet.connected = true;
        state.wallet.address = address;
        state.wallet.method = 'metamask';
        
        localStorage.setItem('auth_token', response.auth_token);
        notify.success('Wallet connected');
        ui.setView('market');
        
        return true;
      } catch (err) {
        notify.error(`Wallet login failed: ${err.message}`);
        return false;
      }
    },
    
    logout() {
      state.auth.token = null;
      state.auth.user = null;
      state.wallet.connected = false;
      state.wallet.address = null;
      localStorage.removeItem('auth_token');
      sessionStorage.clear();
      api.clearCache();
      
      notify.info('Logged out');
      location.reload();
    },
  };
  
  /* ========== DATA FETCHING ========== */
  const data = {
    async loadMarketplace() {
      ui.loading(true);
      try {
        const listings = await api.call('/nft/marketplace', { method: 'GET' });
        state.data.listings = listings;
        render.marketplace();
      } catch (err) {
        notify.error('Failed to load marketplace');
        console.error('Marketplace error:', err);
      } finally {
        ui.loading(false);
      }
    },
    
    async loadUserProfile() {
      try {
        const user = await api.call('/auth/me', { method: 'GET' });
        state.auth.user = user;
        render.profile();
      } catch (err) {
        console.error('Failed to load profile:', err);
      }
    },
    
    async loadUserItems() {
      try {
        const items = await api.call('/nft/user/collection', { method: 'GET' });
        state.data.myItems = items;
      } catch (err) {
        console.error('Failed to load user items:', err);
      }
    },
    
    async loadTransactions() {
      ui.loading(true);
      try {
        const transactions = await api.call('/payments/history', { method: 'GET' });
        state.data.transactions = transactions;
        render.activity();
        render.walletHistory();
      } catch (err) {
        notify.error('Failed to load transaction history');
        console.error('Failed to load transactions:', err);
      } finally {
        ui.loading(false);
      }
    },
    
    async loadReferrals() {
      ui.loading(true);
      try {
        const referrals = await api.call('/referrals', { method: 'GET' });
        state.data.referrals = referrals;
        render.referrals();
      } catch (err) {
        notify.error('Failed to load referral data');
        console.error('Failed to load referrals:', err);
      } finally {
        ui.loading(false);
      }
    },
  };
  
  /* ========== RENDERING ========== */
  const render = {
    marketplace() {
      const grid = document.querySelector('#market-grid');
      
      if (!state.data.listings.length) {
        grid.innerHTML = '<div class="empty"><div class="empty-text">No listings</div></div>';
        return;
      }
      
      // Apply grid or list styling
      if (state.ui.viewMode === 'list') {
        grid.className = ''; // List view doesn't need grid class
        grid.style.display = 'flex';
        grid.style.flexDirection = 'column';
        grid.style.gap = '12px';
        
        grid.innerHTML = state.data.listings.map(item => `
          <div class="nft-card" data-id="${item.id}" style="display: flex; gap: var(--space-4); align-items: flex-start; overflow: visible;">
            <img src="${item.image_url || 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22100%22 height=%22100%22%3E%3Crect fill=%2223252d%22 width=%22100%22 height=%22100%22/%3E%3C/svg%3E'}" class="nft-image" alt="${item.name}" style="width: 100px; height: 100px; border-radius: var(--radius-md); flex-shrink: 0;">
            <div style="flex: 1; display: flex; flex-direction: column; justify-content: space-between; padding: 0;">
              <div>
                <div class="nft-name">${item.name}</div>
                <div class="nft-price">${item.price || 0} Stars</div>
              </div>
              <div style="font-size: var(--font-size-xs); color: var(--color-text-tertiary);">
                ${item.sales_count ? item.sales_count + ' sales' : 'New'}
              </div>
            </div>
          </div>
        `).join('');
      } else {
        // Grid view (default)
        grid.className = 'nft-grid';
        grid.style.display = '';
        grid.style.flexDirection = '';
        grid.style.gap = '';
        
        grid.innerHTML = state.data.listings.map(item => `
          <div class="nft-card" data-id="${item.id}">
            <img src="${item.image_url || 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22140%22 height=%22140%22%3E%3Crect fill=%2323252d%22 width=%22140%22 height=%22140%22/%3E%3C/svg%3E'}" class="nft-image" alt="${item.name}">
            <div class="nft-info">
              <div class="nft-name">${item.name}</div>
              <div class="nft-price">${item.price || 0} Stars</div>
            </div>
          </div>
        `).join('');
      }
      
      grid.querySelectorAll('.nft-card').forEach(card => {
        card.addEventListener('click', () => {
          const itemId = card.dataset.id;
          const item = state.data.listings.find(i => i.id === itemId);
          payment.showCheckout(item);
        });
      });
    },
    
    activity() {
      const table = document.querySelector('#activityTable tbody');
      const empty = document.querySelector('#activityEmpty');
      
      if (!state.data.transactions.length) {
        table.innerHTML = '';
        empty.classList.remove('hidden');
        return;
      }
      
      empty.classList.add('hidden');
      table.innerHTML = state.data.transactions.map(tx => `
        <tr>
          <td><div class="table-cell-label">${tx.type || 'Transfer'}</div></td>
          <td><div class="table-cell-value">${tx.amount_xtr || 0}</div></td>
          <td><span class="badge ${tx.status === 'confirmed' ? 'status-active' : ''}">${tx.status}</span></td>
          <td><div class="table-cell-label">${new Date(tx.created_at).toLocaleDateString()}</div></td>
        </tr>
      `).join('');
    },
    
    referrals() {
      const table = document.querySelector('#referralTable tbody');
      const empty = document.querySelector('#referralEmpty');
      
      if (!state.data.referrals.length) {
        table.innerHTML = '';
        empty.classList.remove('hidden');
        return;
      }
      
      empty.classList.add('hidden');
      table.innerHTML = state.data.referrals.map(ref => `
        <tr>
          <td><div class="table-cell-label">${ref.referred_user_name || 'User'}</div></td>
          <td><div class="table-cell-value positive">${ref.total_earned}</div></td>
        </tr>
      `).join('');
      
      // Update summary
      const totalEarned = state.data.referrals.reduce((sum, r) => sum + (r.total_earned || 0), 0);
      document.querySelector('#refEarnings').textContent = totalEarned.toFixed(2);
      document.querySelector('#refCount').textContent = state.data.referrals.length;
    },
    
    walletHistory() {
      const table = document.querySelector('#walletHistory tbody');
      table.innerHTML = state.data.transactions.slice(0, 5).map(tx => `
        <tr>
          <td><div class="table-cell-label">${tx.type === 'purchase' ? 'Purchase' : 'Earned'}</div></td>
          <td><div class="table-cell-value">${tx.amount_xtr}</div></td>
          <td><div class="table-cell-label">${new Date(tx.created_at).toLocaleDateString()}</div></td>
        </tr>
      `).join('');
    },
    
    profile() {
      const user = state.auth.user || {};
      document.querySelector('#profileUsername').textContent = user.telegram_username || user.wallet_address?.slice(0, 6) + '...';
      document.querySelector('#starBalance').textContent = (user.stars_balance || 0).toFixed(2);
      
      if (user.creator_name) {
        document.querySelector('#creatorName').value = user.creator_name;
      }
      if (user.creator_bio) {
        document.querySelector('#creatorBio').value = user.creator_bio;
      }
      
      // Show referral code
      if (user.referral_code) {
        document.querySelector('#refCode').value = user.referral_code;
      }
    },
  };
  
  /* ========== PAYMENT SYSTEM ========== */
  const payment = {
    showCheckout(item) {
      const breakdown = this.calculateBreakdown(item.price || 0);
      
      ui.openModal(`
        <div class="modal-header">
          <span class="modal-title">Confirm Purchase</span>
          <button class="modal-close">✕</button>
        </div>
        
        <div style="background: var(--color-bg-surface); border-radius: var(--radius-md); padding: var(--space-4); margin-bottom: var(--space-4);">
          <div class="row">
            <span class="row-label">Item Price</span>
            <span class="row-value">${item.price || 0} Stars</span>
          </div>
          <div class="row">
            <span class="row-label">Platform Fee</span>
            <span class="row-value negative">${breakdown.platformFee.toFixed(2)} Stars</span>
          </div>
          ${breakdown.referralBonus > 0 ? `
            <div class="row">
              <span class="row-label">Your Referral Bonus</span>
              <span class="row-value positive">+${breakdown.referralBonus.toFixed(2)} Stars</span>
            </div>
          ` : ''}
          <div style="border-top: 1px solid var(--color-border); margin: var(--space-3) 0; padding-top: var(--space-3);">
            <div class="row">
              <span class="row-label">You Pay</span>
              <span class="row-value">${breakdown.total.toFixed(2)} Stars</span>
            </div>
          </div>
        </div>
        
        <button id="confirmPurchaseBtn" class="btn btn-primary btn-block">Pay Now</button>
        <button id="cancelPurchaseBtn" class="btn btn-ghost btn-block" style="margin-top: var(--space-3);">Cancel</button>
      `);
      
      document.querySelector('#confirmPurchaseBtn').addEventListener('click', () => {
        this.initiate(item);
      });
      
      document.querySelector('#cancelPurchaseBtn').addEventListener('click', () => {
        ui.closeModal();
      });
    },
    
    calculateBreakdown(totalStars) {
      const platformFee = totalStars * config.COMMISSION_RATE;
      const referralBonus = platformFee * config.REFERRAL_RATE;
      
      return {
        total: totalStars,
        platformFee,
        referralBonus,
      };
    },
    
    async initiate(item) {
      try {
        state.payment.pending = true;
        
        const invoiceId = `inv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        state.payment.invoiceId = invoiceId;
        
        const response = await api.call('/stars/invoice/create', {
          method: 'POST',
          body: {
            invoice_id: invoiceId,
            item_id: item.id,
            amount_xtr: item.price || 0,
            currency: 'XTR',
          },
        });
        
        if (typeof window.Telegram !== 'undefined' && window.Telegram.WebApp) {
          // Use Telegram payment
          window.Telegram.WebApp.openInvoice(response.invoice_link, (status) => {
            if (status === 'paid') {
              this.pollConfirmation();
            } else if (status === 'failed') {
              notify.error('Payment failed');
              state.payment.pending = false;
            } else if (status === 'cancelled') {
              notify.info('Payment cancelled');
              state.payment.pending = false;
            }
          });
        } else {
          // Fallback: manual polling
          notify.info('Opening payment...');
          this.pollConfirmation();
        }
      } catch (err) {
        notify.error(`Payment initiation failed: ${err.message}`);
        state.payment.pending = false;
      }
    },
    
    async pollConfirmation() {
      let attempts = 0;
      const maxAttempts = config.PAYMENT_POLL_MAX;
      const pollInterval = setInterval(async () => {
        attempts++;
        
        try {
          const user = await api.call('/auth/me', { method: 'GET', skipCache: true });
          
          // If balance increased, payment confirmed
          if (user.stars_balance > (state.auth.user?.stars_balance || 0)) {
            clearInterval(pollInterval);
            state.auth.user = user;
            state.payment.pending = false;
            ui.closeModal();
            notify.success('Payment confirmed');
            render.profile();
            await data.loadTransactions();
          }
        } catch (err) {
          console.error('Poll error:', err);
        }
        
        if (attempts >= maxAttempts) {
          clearInterval(pollInterval);
          state.payment.pending = false;
          notify.error('Payment confirmation timeout - check your balance');
        }
      }, config.PAYMENT_POLL_INTERVAL);
    },
  };
  
  /* ========== EVENT HANDLERS ========== */
  function bindEvents() {
    // Navigation
    document.querySelectorAll('.nav-item').forEach(btn => {
      btn.addEventListener('click', () => {
        const view = btn.dataset.view;
        ui.setView(view);
        
        // Load data for view
        if (view === 'referrals') data.loadReferrals();
        if (view === 'activity') data.loadTransactions();
        if (view === 'wallet') data.loadUserProfile();
        if (view === 'profile') data.loadUserProfile();
      });
    });
    
    // Marketplace filters
    document.querySelectorAll('.tab').forEach(tab => {
      tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        // In production: filter listings by tab.dataset.filter
      });
    });
    
    // Create form
    const createForm = document.querySelector('#createForm');
    if (createForm) {
      createForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const name = document.querySelector('#itemName').value;
        const desc = document.querySelector('#itemDesc').value;
        const supply = parseInt(document.querySelector('#itemSupply').value);
        const price = parseFloat(document.querySelector('#itemPrice').value);
        
        try {
          await api.call('/nft/create', {
            method: 'POST',
            body: { name, description: desc, supply, price },
          });
          
          notify.success('Item created');
          createForm.reset();
          data.loadUserItems();
        } catch (err) {
          notify.error(`Creation failed: ${err.message}`);
        }
      });
    }
    
    // Image upload
    const imageInput = document.querySelector('#imageInput');
    if (imageInput) {
      imageInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
          const reader = new FileReader();
          reader.onload = (event) => {
            const preview = document.querySelector('#imagePreview');
            preview.innerHTML = `<img src="${event.target.result}" style="width: 100%; height: 100%; object-fit: cover;">`;
          };
          reader.readAsDataURL(file);
        }
      });
      
      document.querySelector('#imagePreview').addEventListener('click', () => {
        imageInput.click();
      });
    }
    
    // Wallet connect
    const walletConnectBtn = document.querySelector('#walletConnectBtn');
    if (walletConnectBtn) {
      walletConnectBtn.addEventListener('click', async () => {
        await auth.walletSignIn();
      });
    }
    
    // Referral copy
    const copyRefBtn = document.querySelector('#copyRefBtn');
    if (copyRefBtn) {
      copyRefBtn.addEventListener('click', () => {
        const code = document.querySelector('#refCode').value;
        navigator.clipboard.writeText(code).then(() => {
          notify.success('Copied to clipboard');
        });
      });
    }
    
    // Profile save
    const saveProfileBtn = document.querySelector('#saveProfileBtn');
    if (saveProfileBtn) {
      saveProfileBtn.addEventListener('click', async () => {
        const name = document.querySelector('#creatorName').value;
        const bio = document.querySelector('#creatorBio').value;
        
        try {
          await api.call('/users/me/creator-profile', {
            method: 'POST',
            body: { creator_name: name, creator_bio: bio },
          });
          notify.success('Profile saved');
        } catch (err) {
          notify.error(`Save failed: ${err.message}`);
        }
      });
    }
    
    // Logout
    const logoutBtn = document.querySelector('#logoutBtn');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', () => {
        auth.logout();
      });
    }
    
    // Marketplace Sort
    const sortSelect = document.querySelector('#sortSelect');
    if (sortSelect) {
      sortSelect.value = state.marketplace.sort;
      sortSelect.addEventListener('change', (e) => {
        state.marketplace.sort = e.target.value;
        localStorage.setItem('marketplace_sort', state.marketplace.sort);
        data.loadMarketplace();
      });
    }
    
    // Marketplace Filter Button
    const filterBtn = document.querySelector('#filterBtn');
    if (filterBtn) {
      filterBtn.addEventListener('click', () => {
        state.marketplace.filterModalOpen = true;
        document.querySelector('#filterOverlay').classList.add('active');
      });
    }
    
    // Filter Close
    const filterCloseBtn = document.querySelector('#filterCloseBtn');
    if (filterCloseBtn) {
      filterCloseBtn.addEventListener('click', () => {
        state.marketplace.filterModalOpen = false;
        document.querySelector('#filterOverlay').classList.remove('active');
      });
    }
    
    // Filter Reset
    const filterResetBtn = document.querySelector('#filterResetBtn');
    if (filterResetBtn) {
      filterResetBtn.addEventListener('click', () => {
        document.querySelector('#priceMin').value = '';
        document.querySelector('#priceMax').value = '';
        document.querySelector('#filterAvailable').checked = true;
        state.marketplace.filters = { priceMin: null, priceMax: null, availability: true };
      });
    }
    
    // Filter Apply
    const filterApplyBtn = document.querySelector('#filterApplyBtn');
    if (filterApplyBtn) {
      filterApplyBtn.addEventListener('click', () => {
        state.marketplace.filters.priceMin = document.querySelector('#priceMin').value ? parseFloat(document.querySelector('#priceMin').value) : null;
        state.marketplace.filters.priceMax = document.querySelector('#priceMax').value ? parseFloat(document.querySelector('#priceMax').value) : null;
        state.marketplace.filters.availability = document.querySelector('#filterAvailable').checked;
        state.marketplace.filterModalOpen = false;
        document.querySelector('#filterOverlay').classList.remove('active');
        data.loadMarketplace();
      });
    }
    
    // Grid/List Toggle
    const gridToggle = document.querySelector('#gridToggle');
    const listToggle = document.querySelector('#listToggle');
    if (gridToggle && listToggle) {
      gridToggle.addEventListener('click', () => {
        state.ui.viewMode = 'grid';
        localStorage.setItem('view_mode', 'grid');
        gridToggle.classList.add('active');
        listToggle.classList.remove('active');
        render.marketplace();
      });
      
      listToggle.addEventListener('click', () => {
        state.ui.viewMode = 'list';
        localStorage.setItem('view_mode', 'list');
        listToggle.classList.add('active');
        gridToggle.classList.remove('active');
        render.marketplace();
      });
    }
    
    // Wallet Popup
    const connectTelegramBtn = document.querySelector('#connectTelegramWalletBtn');
    const continueWithoutBtn = document.querySelector('#continuewithoutWalletBtn');
    
    if (connectTelegramBtn) {
      connectTelegramBtn.addEventListener('click', async () => {
        await auth.walletSignIn();
        state.wallet.popupDismissed = true;
        localStorage.setItem('wallet_popup_dismissed', 'true');
        document.querySelector('#walletPopup').classList.remove('active');
      });
    }
    
    if (continueWithoutBtn) {
      continueWithoutBtn.addEventListener('click', () => {
        state.wallet.popupDismissed = true;
        localStorage.setItem('wallet_popup_dismissed', 'true');
        document.querySelector('#walletPopup').classList.remove('active');
      });
    }
    
    // Modal close button
    document.querySelector('#modalOverlay').addEventListener('click', (e) => {
      if (e.target.id === 'modalOverlay') {
        ui.closeModal();
      }
    });
    
    // Filter modal close on overlay click
    document.querySelector('#filterOverlay').addEventListener('click', (e) => {
      if (e.target.id === 'filterOverlay') {
        state.marketplace.filterModalOpen = false;
        document.querySelector('#filterOverlay').classList.remove('active');
      }
    });
  }
  
  /* ========== INITIALIZATION ========== */
  async function init() {
    // Set initial view
    ui.setView('market');
    
    // Bind all events
    bindEvents();
    
    // Initialize auth
    const telegramReady = await auth.initTelegram();
    
    if (telegramReady || state.auth.token) {
      try {
        // Load user data
        await data.loadUserProfile();
        
        // Load marketplace
        await data.loadMarketplace();
        
        notify.info('Ready');
      } catch (err) {
        notify.error('Failed to initialize app');
        console.error(err);
      }
    } else {
      // Show wallet connect option
      ui.setView('wallet');
    }
    
    // Show wallet popup if not connected and not dismissed
    if (!state.wallet.connected && !state.wallet.popupDismissed) {
      setTimeout(() => {
        document.querySelector('#walletPopup').classList.add('active');
      }, 500);
    }
    
    state.auth.ready = true;
  }
  
  // Start app when DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
  
  // Expose only what's necessary
  window.app = { state, ui, auth, payment, data };
})();
