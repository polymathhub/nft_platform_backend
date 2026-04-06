/**
 * TON INTEGRATION EXAMPLES - Page Implementation Guide
 * ═══════════════════════════════════════════════════════════════
 * 
 * Copy these patterns to integrate TON wallet and transactions
 * into wallet.html, mint.html, and profile.html
 * 
 * This file serves as reference documentation.
 * Real implementations are in the HTML page <script> tags.
 */

// ═══════════════════════════════════════════════════════════════
// 1. WALLET PAGE INTEGRATION
// ═══════════════════════════════════════════════════════════════

class WalletPageIntegration {
  constructor() {
    this.walletAddress = null;
    this.isConnected = false;
  }

  /**
   * Initialize wallet page functionality
   * Add this to wallet.html <script> section
   */
  async initWalletPage() {
    // Wait for TON system to be ready
    await this._waitForTONSystem();

    // Setup wallet connection button
    const connectBtn = document.getElementById('connectWalletBtn');
    if (connectBtn) {
      connectBtn.addEventListener('click', () => this.connectWallet());
    }

    // Setup disconnect button
    const disconnectBtn = document.getElementById('disconnectWalletBtn');
    if (disconnectBtn) {
      disconnectBtn.addEventListener('click', () => this.disconnectWallet());
    }

    // Listen for wallet changes
    window.onTONWalletChange?.((wallet) => {
      this.onWalletConnected(wallet);
    });

    // Check if already connected
    const currentWallet = window.getTONWallet?.();
    if (currentWallet?.connected) {
      this.updateWalletDisplay(currentWallet);
    }

    // Listen for custom events
    document.addEventListener('tonconnect-wallet-connected', (e) => {
      console.log('[Wallet Page] Wallet connected via event:', e.detail);
      this.updateWalletDisplay(e.detail.wallet);
    });
  }

  /**
   * Connect wallet via TonConnect
   */
  async connectWallet() {
    try {
      const connectBtn = document.querySelector('[data-action="connect-wallet"]');
      if (connectBtn) {
        connectBtn.disabled = true;
        connectBtn.textContent = 'Connecting...';
      }

      // TonConnect UI opens dialog automatically
      // Manager handles the rest
      const wallet = window.getTONWallet?.();
      if (wallet?.connected) {
        this.updateWalletDisplay(wallet);
      }
    } catch (error) {
      console.error('[Wallet Page] Connection failed:', error);
      alert('Failed to connect wallet: ' + error.message);
    } finally {
      const connectBtn = document.querySelector('[data-action="connect-wallet"]');
      if (connectBtn) {
        connectBtn.disabled = false;
        connectBtn.textContent = 'Connect Wallet';
      }
    }
  }

  /**
   * Disconnect wallet
   */
  async disconnectWallet() {
    try {
      const manager = window.tonConnectManager;
      if (manager) {
        manager.clearWallet();
        this.updateWalletDisplay(null);
      }
    } catch (error) {
      console.error('[Wallet Page] Disconnect failed:', error);
    }
  }

  /**
   * Update wallet display on page
   */
  updateWalletDisplay(wallet) {
    const addressEl = document.getElementById('walletAddress');
    const statusEl = document.getElementById('walletStatus');
    const balanceEl = document.getElementById('walletBalance');

    if (wallet?.connected) {
      if (addressEl) addressEl.textContent = wallet.formatted;
      if (statusEl) statusEl.textContent = 'Connected';
      if (statusEl) statusEl.classList.add('status-connected');
      this.isConnected = true;
      this.walletAddress = wallet.address;
    } else {
      if (addressEl) addressEl.textContent = 'Not connected';
      if (statusEl) statusEl.textContent = 'Disconnected';
      if (statusEl) statusEl.classList.remove('status-connected');
      this.isConnected = false;
      this.walletAddress = null;
    }
  }

  /**
   * Handle wallet connection event
   */
  onWalletConnected(wallet) {
    console.log('[Wallet Page] Wallet connected:', wallet);
    this.updateWalletDisplay(wallet);

    // Enable transaction buttons
    document.querySelectorAll('[data-require-wallet]').forEach(btn => {
      btn.disabled = false;
    });
  }

  /**
   * Wait for TON system to be ready
   */
  async _waitForTONSystem() {
    return new Promise((resolve) => {
      if (window.isTONConnected !== undefined) {
        resolve();
        return;
      }

      const checkInterval = setInterval(() => {
        if (window.isTONConnected !== undefined) {
          clearInterval(checkInterval);
          resolve();
        }
      }, 100);

      // Timeout after 10 seconds
      setTimeout(() => {
        clearInterval(checkInterval);
        resolve();
      }, 10000);
    });
  }
}

// ═══════════════════════════════════════════════════════════════
// 2. MINT PAGE INTEGRATION (NFT Creation)
// ═══════════════════════════════════════════════════════════════

class MintPageIntegration {
  constructor() {
    this.nftMetadata = {
      name: '',
      description: '',
      image: '',
      attributes: []
    };
    this.isMinting = false;
  }

  /**
   * Initialize mint page functionality
   * Add this to mint.html <script> section
   */
  async initMintPage() {
    // Wait for TON system
    await this._waitForTONSystem();

    // Setup form submission
    const mintForm = document.getElementById('mintForm');
    if (mintForm) {
      mintForm.addEventListener('submit', (e) => this.handleMintSubmit(e));
    }

    // Setup image upload
    const imageInput = document.getElementById('nftImage');
    if (imageInput) {
      imageInput.addEventListener('change', (e) => this.handleImageUpload(e));
    }

    // Check wallet connection
    if (!window.isTONConnected?.()) {
      this.showMintBlocker('Please connect your wallet to mint NFTs');
    }

    // Listen for wallet changes
    document.addEventListener('tonconnect-wallet-connected', () => {
      this.enableMinting();
    });

    document.addEventListener('tonconnect-wallet-disconnected', () => {
      this.disableMinting('Wallet disconnected');
    });
  }

  /**
   * Handle mint form submission
   */
  async handleMintSubmit(e) {
    e.preventDefault();

    if (this.isMinting) return;
    if (!window.isTONConnected?.()) {
      alert('Wallet not connected');
      return;
    }

    this.isMinting = true;
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalText = submitBtn?.textContent;

    try {
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Minting...';
      }

      // Collect form data
      this.nftMetadata = {
        name: document.getElementById('nftName')?.value || '',
        description: document.getElementById('nftDescription')?.value || '',
        image: document.getElementById('nftImage')?.value || '',
        attributes: this._parseAttributes()
      };

      // Validate
      if (!this.nftMetadata.name || !this.nftMetadata.image) {
        throw new Error('Name and image are required');
      }

      // Get collection address from form or config
      const collectionAddress = document.getElementById('collectionAddress')?.value;
      if (!collectionAddress) {
        throw new Error('Collection address not configured');
      }

      // Call global mint function
      const result = await window.mintNFT(collectionAddress, this.nftMetadata);

      if (result.success) {
        this.showSuccess('NFT minted successfully!', result.txHash);
        document.getElementById('mintForm')?.reset();
      } else {
        throw new Error(result.error || 'Mint failed');
      }
    } catch (error) {
      console.error('[Mint Page] Mint failed:', error);
      this.showError('Mint failed: ' + error.message);
    } finally {
      this.isMinting = false;
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
      }
    }
  }

  /**
   * Handle image upload and preview
   */
  handleImageUpload(e) {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      alert('Image too large (max 5MB)');
      return;
    }

    // Read and preview
    const reader = new FileReader();
    reader.onload = (event) => {
      const preview = document.getElementById('imagePreview');
      if (preview) {
        preview.src = event.target?.result;
      }
      this.nftMetadata.image = event.target?.result;
    };
    reader.readAsDataURL(file);
  }

  /**
   * Parse attributes from form
   */
  _parseAttributes() {
    const attrInputs = document.querySelectorAll('[data-attribute-name]');
    const attributes = [];

    attrInputs.forEach((input) => {
      const name = input.getAttribute('data-attribute-name');
      const value = input.value;
      if (name && value) {
        attributes.push({ trait_type: name, value });
      }
    });

    return attributes;
  }

  /**
   * Enable minting UI
   */
  enableMinting() {
    const submitBtn = document.querySelector('#mintForm button[type="submit"]');
    if (submitBtn) submitBtn.disabled = false;

    const blocker = document.getElementById('mintBlocker');
    if (blocker) blocker.remove();
  }

  /**
   * Disable minting UI
   */
  disableMinting(reason) {
    const submitBtn = document.querySelector('#mintForm button[type="submit"]');
    if (submitBtn) submitBtn.disabled = true;
    this.showMintBlocker(reason);
  }

  /**
   * Show mint blocker message
   */
  showMintBlocker(message) {
    let blocker = document.getElementById('mintBlocker');
    if (!blocker) {
      blocker = document.createElement('div');
      blocker.id = 'mintBlocker';
      blocker.className = 'mint-blocker';
      document.getElementById('mintForm')?.parentElement?.insertBefore(blocker, document.getElementById('mintForm'));
    }
    blocker.textContent = message;
  }

  /**
   * Show success notification
   */
  showSuccess(message, txHash) {
    console.log('[Mint Page] Success:', message, txHash);
    alert(`${message}\nTransaction: ${txHash}`);
  }

  /**
   * Show error notification
   */
  showError(message) {
    console.error('[Mint Page] Error:', message);
    alert(message);
  }

  /**
   * Wait for TON system
   */
  async _waitForTONSystem() {
    return new Promise((resolve) => {
      if (window.mintNFT !== undefined) {
        resolve();
        return;
      }

      const checkInterval = setInterval(() => {
        if (window.mintNFT !== undefined) {
          clearInterval(checkInterval);
          resolve();
        }
      }, 100);

      setTimeout(() => {
        clearInterval(checkInterval);
        console.warn('[Mint Page] TON system not ready');
        resolve();
      }, 10000);
    });
  }
}

// ═══════════════════════════════════════════════════════════════
// 3. PROFILE PAGE INTEGRATION
// ═══════════════════════════════════════════════════════════════

class ProfilePageIntegration {
  constructor() {
    this.walletAddress = null;
    this.userNFTs = [];
  }

  /**
   * Initialize profile page functionality
   * Add this to profile.html <script> section
   */
  async initProfilePage() {
    // Wait for TON system
    await this._waitForTONSystem();

    // Display connected wallet
    const wallet = window.getTONWallet?.();
    if (wallet?.connected) {
      this.displayWalletInfo(wallet);
      await this.loadUserNFTs(wallet.address);
    }

    // Listen for wallet changes
    document.addEventListener('tonconnect-wallet-connected', (e) => {
      this.displayWalletInfo(e.detail.wallet);
      this.loadUserNFTs(e.detail.wallet.address);
    });

    // Listen for new transactions
    window.onTONTransaction?.((tx) => {
      console.log('[Profile Page] New transaction:', tx.transaction);
      this.onTransactionAdded(tx.transaction);
    });

    // Load transaction history
    this.displayTransactionHistory();
  }

  /**
   * Display wallet information
   */
  displayWalletInfo(wallet) {
    const walletEl = document.getElementById('profileWallet');
    if (walletEl) {
      walletEl.innerHTML = `
        <div class="wallet-info">
          <div class="wallet-address">${wallet.formatted}</div>
          <div class="wallet-status connected">Connected</div>
          <div class="wallet-network">${wallet.network || 'mainnet'}</div>
        </div>
      `;
    }
    this.walletAddress = wallet.address;
  }

  /**
   * Load user's NFTs
   */
  async loadUserNFTs(walletAddress) {
    try {
      const initData = window.Telegram?.WebApp?.initData || '';

      const response = await fetch(`/api/v1/nfts/owned?owner=${walletAddress}`, {
        headers: {
          'Content-Type': 'application/json',
          ...(initData && { 'X-Telegram-Init-Data': initData })
        }
      });

      if (!response.ok) throw new Error('Failed to load NFTs');

      const data = await response.json();
      this.userNFTs = data.nfts || [];
      this.displayUserNFTs();
    } catch (error) {
      console.error('[Profile Page] Failed to load NFTs:', error);
    }
  }

  /**
   * Display user's NFT collection
   */
  displayUserNFTs() {
    const container = document.getElementById('userNFTsContainer');
    if (!container) return;

    if (this.userNFTs.length === 0) {
      container.innerHTML = '<div class="empty-state">No NFTs yet. Start minting!</div>';
      return;
    }

    container.innerHTML = this.userNFTs.map(nft => `
      <div class="nft-card">
        <img src="${nft.image}" alt="${nft.name}">
        <div class="nft-info">
          <h3>${nft.name}</h3>
          <p>${nft.description || 'No description'}</p>
          <button data-action="transfer-nft" data-nft-id="${nft.id}">Transfer</button>
        </div>
      </div>
    `).join('');

    // Setup transfer buttons
    container.querySelectorAll('[data-action="transfer-nft"]').forEach(btn => {
      btn.addEventListener('click', (e) => this.transferNFT(e.currentTarget.getAttribute('data-nft-id')));
    });
  }

  /**
   * Transfer NFT
   */
  async transferNFT(nftId) {
    const recipientAddress = prompt('Enter recipient wallet address:');
    if (!recipientAddress) return;

    try {
      const nft = this.userNFTs.find(n => n.id === nftId);
      if (!nft) throw new Error('NFT not found');

      const result = await window.transferNFT(nft.item_address, recipientAddress);

      if (result.success) {
        alert(`NFT transferred! Transaction: ${result.txHash}`);
        await this.loadUserNFTs(this.walletAddress);
      } else {
        throw new Error(result.error);
      }
    } catch (error) {
      alert('Transfer failed: ' + error.message);
    }
  }

  /**
   * Display transaction history
   */
  displayTransactionHistory() {
    const manager = window.tonConnectManager;
    if (!manager) return;

    const txHistory = manager.getTransactionHistory?.() || [];
    const container = document.getElementById('transactionHistory');

    if (!container || txHistory.length === 0) return;

    container.innerHTML = txHistory.slice(0, 10).map(tx => `
      <div class="tx-item">
        <div class="tx-type">${tx.type}</div>
        <div class="tx-status">${tx.status}</div>
        <div class="tx-time">${new Date(tx.timestamp).toLocaleString()}</div>
      </div>
    `).join('');
  }

  /**
   * Handle new transaction
   */
  onTransactionAdded(tx) {
    console.log('[Profile Page] Transaction added:', tx);
    this.displayTransactionHistory();
  }

  /**
   * Wait for TON system
   */
  async _waitForTONSystem() {
    return new Promise((resolve) => {
      if (window.getTONWallet !== undefined) {
        resolve();
        return;
      }

      const checkInterval = setInterval(() => {
        if (window.getTONWallet !== undefined) {
          clearInterval(checkInterval);
          resolve();
        }
      }, 100);

      setTimeout(() => {
        clearInterval(checkInterval);
        resolve();
      }, 10000);
    });
  }
}

// Auto-initialize based on page
if (document.body.id.includes('wallet')) {
  const walletPage = new WalletPageIntegration();
  document.addEventListener('DOMContentLoaded', () => walletPage.initWalletPage());
} else if (document.body.id.includes('mint')) {
  const mintPage = new MintPageIntegration();
  document.addEventListener('DOMContentLoaded', () => mintPage.initMintPage());
} else if (document.body.id.includes('profile')) {
  const profilePage = new ProfilePageIntegration();
  document.addEventListener('DOMContentLoaded', () => profilePage.initProfilePage());
}

export { WalletPageIntegration, MintPageIntegration, ProfilePageIntegration };

