/**
 * Modal & Form Management System
 * Handles all modal dialogs, forms, and user interactions
 */

class ModalManager {
  constructor() {
    this.modals = {};
    this.currentModal = null;
    this.setupModals();
  }

  setupModals() {
    // Modal definitions
    this.modals = {
      'create-wallet': {
        title: 'Create New Wallet',
        template: this.createWalletForm,
        handlers: this.setupCreateWalletHandlers,
      },
      'import-wallet': {
        title: 'Import Wallet',
        template: this.importWalletForm,
        handlers: this.setupImportWalletHandlers,
      },
      'mint-nft': {
        title: 'Mint New NFT',
        template: this.mintNFTForm,
        handlers: this.setupMintNFTHandlers,
      },
      'create-listing': {
        title: 'List Your NFT',
        template: this.createListingForm,
        handlers: this.setupCreateListingHandlers,
      },
      'user-profile': {
        title: 'Profile Settings',
        template: this.userProfileForm,
        handlers: this.setupProfileHandlers,
      },
      'notifications': {
        title: 'Notifications',
        template: this.notificationsView,
        handlers: this.setupNotificationHandlers,
      },
      'transaction-detail': {
        title: 'Transaction Details',
        template: this.transactionDetailView,
        handlers: this.setupTransactionHandlers,
      },
    };
  }

  async show(modalName, data = null) {
    const modalDef = this.modals[modalName];
    if (!modalDef) {
      console.warn(`Modal "${modalName}" not found`);
      return;
    }

    this.currentModal = modalName;
    const modalEl = document.getElementById('modal');
    const overlay = document.getElementById('modalOverlay');

    if (!modalEl || !overlay) return;

    // Generate modal HTML
    const content = await modalDef.template.call(this, data);
    modalEl.innerHTML = content;

    // Show overlay
    overlay.style.display = 'flex';

    // Setup close handlers
    this.setupCloseHandlers(modalEl, overlay);

    // Run modal-specific handlers
    await modalDef.handlers.call(this, data);
  }

  setupCloseHandlers(modalEl, overlay) {
    // Close on overlay click
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) {
        this.close();
      }
    });

    // Close on close button
    const closeBtn = modalEl.querySelector('[data-modal-close]');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.close());
    }

    // Close on escape key
    const closeOnEscape = (e) => {
      if (e.key === 'Escape') {
        this.close();
        document.removeEventListener('keydown', closeOnEscape);
      }
    };
    document.addEventListener('keydown', closeOnEscape);
  }

  close() {
    const overlay = document.getElementById('modalOverlay');
    if (overlay) {
      overlay.style.display = 'none';
    }
    this.currentModal = null;
  }

  // ============================================================
  // FORM TEMPLATES
  // ============================================================

  createWalletForm() {
    return `
      <div class="modal-header">
        <h2>Create New Wallet</h2>
        <button data-modal-close class="btn-close">✕</button>
      </div>
      <form id="createWalletForm" class="modal-form">
        <div class="form-group">
          <label for="blockchain">Blockchain</label>
          <select id="blockchain" name="blockchain" required>
            <option value="">Select blockchain...</option>
            <option value="ETH">Ethereum</option>
            <option value="SOL">Solana</option>
            <option value="POLYGON">Polygon</option>
          </select>
        </div>
        <div class="form-group">
          <label for="walletType">Wallet Type</label>
          <div class="radio-group">
            <label class="radio-label">
              <input type="radio" name="walletType" value="SEED" checked>
              <span>Generate New (Seed)</span>
            </label>
            <label class="radio-label">
              <input type="radio" name="walletType" value="IMPORT">
              <span>Import Existing</span>
            </label>
          </div>
        </div>
        <div class="form-group">
          <label class="checkbox-label">
            <input type="checkbox" id="setPrimary" name="isPrimary">
            <span>Set as primary wallet</span>
          </label>
        </div>
        <div class="form-actions">
          <button type="button" class="btn-secondary" data-modal-close>Cancel</button>
          <button type="submit" class="btn-primary">Create Wallet</button>
        </div>
      </form>
    `;
  }

  importWalletForm() {
    return `
      <div class="modal-header">
        <h2>Import Wallet</h2>
        <button data-modal-close class="btn-close">✕</button>
      </div>
      <form id="importWalletForm" class="modal-form">
        <div class="form-group">
          <label for="importBlockchain">Blockchain</label>
          <select id="importBlockchain" name="blockchain" required>
            <option value="">Select blockchain...</option>
            <option value="ETH">Ethereum</option>
            <option value="SOL">Solana</option>
            <option value="POLYGON">Polygon</option>
          </select>
        </div>
        <div class="form-group">
          <label for="walletAddress">Wallet Address</label>
          <input 
            type="text" 
            id="walletAddress" 
            name="address" 
            placeholder="0x... or wallet address"
            required
          >
          <p class="form-help">Enter your existing wallet address</p>
        </div>
        <div class="form-group">
          <label class="checkbox-label">
            <input type="checkbox" id="setImportPrimary" name="isPrimary">
            <span>Set as primary wallet</span>
          </label>
        </div>
        <div class="form-actions">
          <button type="button" class="btn-secondary" data-modal-close>Cancel</button>
          <button type="submit" class="btn-primary">Import Wallet</button>
        </div>
      </form>
    `;
  }

  mintNFTForm() {
    return `
      <div class="modal-header">
        <h2>Mint New NFT</h2>
        <button data-modal-close class="btn-close">✕</button>
      </div>
      <form id="mintNFTForm" class="modal-form">
        <div class="form-group">
          <label for="mintWallet">Select Wallet</label>
          <select id="mintWallet" name="walletId" required>
            <option value="">Loading wallets...</option>
          </select>
        </div>
        <div class="form-group">
          <label for="nftName">NFT Name *</label>
          <input 
            type="text" 
            id="nftName" 
            name="name" 
            placeholder="e.g., Cosmic Cube #1"
            maxlength="100"
            required
          >
        </div>
        <div class="form-group">
          <label for="nftDescription">Description</label>
          <textarea 
            id="nftDescription" 
            name="description" 
            placeholder="Describe your NFT..."
            maxlength="500"
            rows="3"
          ></textarea>
        </div>
        <div class="form-group">
          <label for="nftImage">Image URL</label>
          <input 
            type="url" 
            id="nftImage" 
            name="imageUrl" 
            placeholder="https://..."
          >
          <p class="form-help">IPFS or HTTP(S) image URL</p>
        </div>
        <div class="form-group">
          <label for="royalty">Royalty Percentage</label>
          <input 
            type="number" 
            id="royalty" 
            name="royaltyPercentage" 
            min="0" 
            max="50" 
            value="5"
            step="0.1"
          >
          <p class="form-help">0-50%: Percentage you earn from future sales</p>
        </div>
        <div class="form-actions">
          <button type="button" class="btn-secondary" data-modal-close>Cancel</button>
          <button type="submit" class="btn-primary">Mint NFT</button>
        </div>
      </form>
    `;
  }

  createListingForm(data = {}) {
    const nft = data.nft || {};
    return `
      <div class="modal-header">
        <h2>List Your NFT</h2>
        <button data-modal-close class="btn-close">✕</button>
      </div>
      <form id="createListingForm" class="modal-form">
        ${nft.id ? `<input type="hidden" name="nftId" value="${nft.id}">` : ''}
        
        ${!nft.id ? `
          <div class="form-group">
            <label for="listingNFT">Select NFT</label>
            <select id="listingNFT" name="nftId" required>
              <option value="">Loading your NFTs...</option>
            </select>
          </div>
        ` : `
          <div class="form-group">
            <div class="nft-preview">
              <div class="preview-image">${nft.image_url ? `<img src="${nft.image_url}" alt="${nft.name}">` : '🖼️'}</div>
              <div class="preview-info">
                <h3>${nft.name}</h3>
                <p>${nft.description}</p>
              </div>
            </div>
          </div>
        `}
        
        <div class="form-group">
          <label for="listingPrice">Price *</label>
          <div class="input-group">
            <input 
              type="number" 
              id="listingPrice" 
              name="price" 
              placeholder="0.00" 
              min="0" 
              step="0.01"
              required
            >
            <select name="currency" class="currency-select">
              <option value="USD">USD</option>
              <option value="USDT">USDT</option>
              <option value="ETH">ETH</option>
              <option value="SOL">SOL</option>
            </select>
          </div>
        </div>
        
        <div class="form-group">
          <label for="listingExpires">Listing Duration</label>
          <select id="listingExpires" name="duration">
            <option value="7">7 days</option>
            <option value="14">14 days</option>
            <option value="30">30 days</option>
            <option value="0">No expiration</option>
          </select>
        </div>
        
        <div class="form-actions">
          <button type="button" class="btn-secondary" data-modal-close>Cancel</button>
          <button type="submit" class="btn-primary">Create Listing</button>
        </div>
      </form>
    `;
  }

  userProfileForm(data = {}) {
    const user = appState.currentUser || {};
    return `
      <div class="modal-header">
        <h2>Profile Settings</h2>
        <button data-modal-close class="btn-close">✕</button>
      </div>
      <form id="profileForm" class="modal-form">
        <div class="form-group">
          <label for="firstName">First Name</label>
          <input 
            type="text" 
            id="firstName" 
            name="firstName" 
            value="${user.first_name || ''}"
            placeholder="First name"
          >
        </div>
        <div class="form-group">
          <label for="lastName">Last Name</label>
          <input 
            type="text" 
            id="lastName" 
            name="lastName" 
            value="${user.last_name || ''}"
            placeholder="Last name"
          >
        </div>
        <div class="form-group">
          <label for="email">Email</label>
          <input 
            type="email" 
            id="email" 
            name="email" 
            value="${user.email || ''}"
            placeholder="email@example.com"
            disabled
          >
          <p class="form-help">Email cannot be changed</p>
        </div>
        <div class="form-group">
          <label for="bio">Bio</label>
          <textarea 
            id="bio" 
            name="bio" 
            placeholder="Tell us about yourself"
            maxlength="200"
            rows="2"
          >${user.bio || ''}</textarea>
        </div>
        <div class="form-divider">
          <h3>Security</h3>
        </div>
        <div class="form-group">
          <button type="button" class="btn-secondary" id="changePasswordBtn">Change Password</button>
        </div>
        <div class="form-actions">
          <button type="button" class="btn-secondary" data-modal-close>Cancel</button>
          <button type="submit" class="btn-primary">Save Changes</button>
        </div>
      </form>
    `;
  }

  notificationsView() {
    const notifications = appState.notifications || [];
    return `
      <div class="modal-header">
        <h2>Notifications</h2>
        <button data-modal-close class="btn-close">✕</button>
      </div>
      <div class="modal-body notifications-list">
        ${notifications.length === 0 ? `
          <div class="empty-state" style="padding: 40px 20px;">
            <div style="font-size: 40px; margin-bottom: 12px;">🔔</div>
            <p>No notifications yet</p>
          </div>
        ` : `
          ${notifications.map((notif, idx) => `
            <div class="notification-item ${notif.read ? 'read' : 'unread'}" data-notif-id="${notif.id}">
              <div class="notif-icon">${this.getNotificationIcon(notif.type)}</div>
              <div class="notif-content">
                <h4>${notif.title}</h4>
                <p>${notif.message}</p>
                <span class="notif-time">${this.formatTime(notif.created_at)}</span>
              </div>
              ${!notif.read ? `<span class="unread-dot"></span>` : ''}
            </div>
          `).join('')}
        `}
      </div>
    `;
  }

  transactionDetailView(data = {}) {
    const tx = data.transaction || {};
    return `
      <div class="modal-header">
        <h2>Transaction Details</h2>
        <button data-modal-close class="btn-close">✕</button>
      </div>
      <div class="modal-body transaction-detail">
        <div class="detail-row">
          <label>Type</label>
          <span class="badge">${tx.type || 'Unknown'}</span>
        </div>
        <div class="detail-row">
          <label>Status</label>
          <span class="status-badge ${tx.status || 'pending'}">${tx.status || 'Pending'}</span>
        </div>
        <div class="detail-row">
          <label>Amount</label>
          <span>${UIUtils.formatCurrency(tx.amount)}</span>
        </div>
        <div class="detail-row">
          <label>From</label>
          <span class="address" title="${tx.from_address}">${UIUtils.formatAddress(tx.from_address)}</span>
        </div>
        <div class="detail-row">
          <label>To</label>
          <span class="address" title="${tx.to_address}">${UIUtils.formatAddress(tx.to_address)}</span>
        </div>
        ${tx.transaction_hash ? `
          <div class="detail-row">
            <label>Hash</label>
            <span class="address" title="${tx.transaction_hash}" onclick="navigator.clipboard.writeText('${tx.transaction_hash}')">${UIUtils.formatAddress(tx.transaction_hash)}</span>
          </div>
        ` : ''}
        <div class="detail-row">
          <label>Date</label>
          <span>${new Date(tx.created_at).toLocaleString()}</span>
        </div>
        <div class="detail-actions">
          <a href="https://etherscan.io/tx/${tx.transaction_hash}" target="_blank" class="btn-secondary">
            View on Explorer →
          </a>
        </div>
      </div>
    `;
  }

  // ============================================================
  // FORM HANDLERS
  // ============================================================

  async setupCreateWalletHandlers() {
    const form = document.getElementById('createWalletForm');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(form);
      const blockchain = formData.get('blockchain');
      const walletType = formData.get('walletType');
      const isPrimary = formData.get('isPrimary') === 'on';

      try {
        UIUtils.setButtonLoading(form.querySelector('button[type="submit"]'), true);
        const wallet = await window.api.createWallet(blockchain, walletType, isPrimary);
        appState.addWallet(wallet);
        UIUtils.showToast(`${blockchain} wallet created successfully!`, 'success');
        this.close();
      } catch (error) {
        UIUtils.showToast(`Error: ${error.message}`, 'error');
      } finally {
        UIUtils.setButtonLoading(form.querySelector('button[type="submit"]'), false);
      }
    });
  }

  async setupImportWalletHandlers() {
    const form = document.getElementById('importWalletForm');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(form);
      const blockchain = formData.get('blockchain');
      const address = formData.get('address');
      const isPrimary = formData.get('isPrimary') === 'on';

      // Validate address
      if (!UIUtils.isValidBlockchainAddress(address, blockchain)) {
        UIUtils.showToast('Invalid wallet address', 'error');
        return;
      }

      try {
        UIUtils.setButtonLoading(form.querySelector('button[type="submit"]'), true);
        const wallet = await window.api.importWallet(blockchain, address, isPrimary);
        appState.addWallet(wallet);
        UIUtils.showToast(`${blockchain} wallet imported successfully!`, 'success');
        this.close();
      } catch (error) {
        UIUtils.showToast(`Error: ${error.message}`, 'error');
      } finally {
        UIUtils.setButtonLoading(form.querySelector('button[type="submit"]'), false);
      }
    });
  }

  async setupMintNFTHandlers() {
    const form = document.getElementById('mintNFTForm');
    if (!form) return;

    // Populate wallets dropdown
    const walletSelect = form.querySelector('#mintWallet');
    if (walletSelect && appState.wallets.length > 0) {
      walletSelect.innerHTML = appState.wallets
        .map((w) => `<option value="${w.id}">${w.blockchain} - ${UIUtils.formatAddress(w.address)}</option>`)
        .join('');
    }

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(form);

      const walletId = formData.get('walletId');
      const name = formData.get('name');
      const description = formData.get('description');
      const imageUrl = formData.get('imageUrl');
      const royaltyPercentage = parseFloat(formData.get('royaltyPercentage')) || 0;

      if (!name.trim()) {
        UIUtils.showToast('NFT name is required', 'error');
        return;
      }

      try {
        UIUtils.setButtonLoading(form.querySelector('button[type="submit"]'), true);
        const nft = await window.api.mintNFT(walletId, name, description, imageUrl, royaltyPercentage, {});
        appState.userNFTs.push(nft);
        UIUtils.showToast('NFT minted successfully!', 'success');
        this.close();
      } catch (error) {
        UIUtils.showToast(`Error: ${error.message}`, 'error');
      } finally {
        UIUtils.setButtonLoading(form.querySelector('button[type="submit"]'), false);
      }
    });
  }

  async setupCreateListingHandlers(data = {}) {
    const form = document.getElementById('createListingForm');
    if (!form) return;

    // Populate NFTs if not pre-selected
    if (!data.nft) {
      const nftSelect = form.querySelector('#listingNFT');
      if (nftSelect && appState.userNFTs.length > 0) {
        nftSelect.innerHTML = appState.userNFTs
          .map((n) => `<option value="${n.id}">${n.name}</option>`)
          .join('');
      }
    }

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(form);
      const nftId = formData.get('nftId');
      const price = parseFloat(formData.get('price'));
      const currency = formData.get('currency');
      const duration = parseInt(formData.get('duration'));

      if (!price || price <= 0) {
        UIUtils.showToast('Please enter a valid price', 'error');
        return;
      }

      try {
        UIUtils.setButtonLoading(form.querySelector('button[type="submit"]'), true);
        const listing = await window.api.createListing(nftId, price, currency, duration > 0 ? Date.now() + duration * 24 * 60 * 60 * 1000 : null);
        appState.userListings.push(listing);
        UIUtils.showToast('NFT listed successfully!', 'success');
        this.close();
      } catch (error) {
        UIUtils.showToast(`Error: ${error.message}`, 'error');
      } finally {
        UIUtils.setButtonLoading(form.querySelector('button[type="submit"]'), false);
      }
    });
  }

  async setupProfileHandlers() {
    const form = document.getElementById('profileForm');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      // TODO: Implement profile update API call
      UIUtils.showToast('Profile update coming soon', 'info');
    });
  }

  async setupNotificationHandlers() {
    const notifItems = document.querySelectorAll('.notification-item');
    notifItems.forEach((item) => {
      item.addEventListener('click', async () => {
        const notifId = item.dataset.notifId;
        try {
          await window.api.markNotificationAsRead(notifId);
          item.classList.add('read');
        } catch (error) {
          console.error('Failed to mark notification as read:', error);
        }
      });
    });
  }

  async setupTransactionHandlers() {
    // Setup blockchain explorer link
  }

  // ============================================================
  // UTILITIES
  // ============================================================

  getNotificationIcon(type) {
    const icons = {
      transaction: '💳',
      listing: '🛒',
      offer: '🎁',
      sale: '✅',
      mint: '✨',
      transfer: '➡️',
      alert: '⚠️',
    };
    return icons[type] || '📬';
  }

  formatTime(timestamp) {
    const now = new Date();
    const date = new Date(timestamp);
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  }
}

// Create global instance
if (!window.modalManager) {
  window.modalManager = new ModalManager();
}
