// Keeps wallet connection state synced across all pages
// Uses sessionStorage + storage events so other tabs know when you connect

window.WalletStateManager = {
  currentWallet: null,
  isMonitoring: false,
  checkInterval: null,
  CHECK_INTERVAL: 500, // Check every 500ms
  MAX_CHECK_ATTEMPTS: 200, // Max 100 seconds of checking
  checkAttempts: 0,

  // ════════════════════════════════════════════════════════════════
  // INITIALIZATION
  // ════════════════════════════════════════════════════════════════

  /**
   * Initialize wallet state manager
   * Must be called on every page that might use wallet
   */
  initialize() {
    console.log('[WalletStateManager] Initializing...');
    
    // Check for existing wallet in sessionStorage (from another page)
    this.loadStateFromStorage();
    
    // Start monitoring for wallet connections
    this.startMonitoring();
    
    // Listen for storage events (from other pages/tabs)
    window.addEventListener('storage', (e) => {
      if (e.key === 'wallet-state') {
        console.log('[WalletStateManager] Storage event received from another page/tab');
        this.loadStateFromStorage();
      }
    });
    
    // Listen for cross-tab messages
    window.addEventListener('message', (e) => {
      if (e.data && e.data.type === 'wallet-state-sync') {
        console.log('[WalletStateManager] Cross-tab wallet update received');
        this.handleWalletUpdate(e.data.wallet);
      }
    });
    
    console.log('[WalletStateManager] ✅ Initialized');
  },

  // ════════════════════════════════════════════════════════════════
  // STORAGE MANAGEMENT
  // ════════════════════════════════════════════════════════════════

  /**
   * Save wallet state to sessionStorage for cross-page access
   */
  saveToStorage() {
    try {
      if (this.currentWallet) {
        sessionStorage.setItem('wallet-state', JSON.stringify({
          address: this.currentWallet.address,
          wallet: this.currentWallet.wallet,
          isTONConnect: true,
          timestamp: Date.now()
        }));
        console.log('[WalletStateManager] ✅ State saved to sessionStorage');
      } else {
        sessionStorage.removeItem('wallet-state');
      }
    } catch (e) {
      console.warn('[WalletStateManager] Failed to save to storage:', e.message);
    }
  },

  // Check if another page saved wallet info
  loadStateFromStorage() {
    try {
      const stored = sessionStorage.getItem('wallet-state');
      if (stored) {
        const state = JSON.parse(stored);
        if (state && state.address) {
          this.currentWallet = {
            address: state.address,
            wallet: state.wallet,
            isTONConnect: true
          };
          console.log('[WalletStateManager] ✅ State loaded from sessionStorage:', state.address);
          this.notifyWalletChanged();
          return true;
        }
      }
      this.currentWallet = null;
      return false;
    } catch (e) {
      console.warn('[WalletStateManager] Failed to load from storage:', e.message);
      return false;
    }
  },

  // ════════════════════════════════════════════════════════════════
  // WALLET DETECTION
  // ════════════════════════════════════════════════════════════════

  /**
   * Check if wallet is connected via connectBtn (wallet.html)
   * Includes retry logic for pages that load before wallet.html
   */
  async detectConnectedWallet() {
    // First check: Is window.connectBtn available?
    if (window.connectBtn && typeof window.connectBtn.getWalletData === 'function') {
      try {
        const walletData = window.connectBtn.getWalletData();
        if (walletData && walletData.isConnected && walletData.address) {
          console.log('[WalletStateManager] ✅ Wallet detected via connectBtn:', walletData.address);
          return {
            address: walletData.address,
            wallet: walletData.wallet,
            isTONConnect: true
          };
        }
      } catch (e) {
        console.warn('[WalletStateManager] Error reading connectBtn:', e.message);
      }
    }

    // Fallback: Is window.TonConnectUI available and connected?
    if (window.TonConnectUI) {
      try {
        const wallet = window.TonConnectUI.wallet;
        if (wallet && wallet.account && wallet.account.address) {
          console.log('[WalletStateManager] ✅ Wallet detected via TonConnectUI:', wallet.account.address);
          return {
            address: wallet.account.address,
            wallet: wallet,
            isTONConnect: true
          };
        }
      } catch (e) {
        console.warn('[WalletStateManager] Error reading TonConnectUI:', e.message);
      }
    }

    // Fallback: Check sessionStorage from another page
    try {
      const stored = sessionStorage.getItem('wallet-state');
      if (stored) {
        const state = JSON.parse(stored);
        if (state && state.address && Date.now() - state.timestamp < 5 * 60 * 1000) {
          console.log('[WalletStateManager] ✅ Wallet loaded from sessionStorage:', state.address);
          return {
            address: state.address,
            wallet: state.wallet,
            isTONConnect: true
          };
        }
      }
    } catch (e) {
      // Ignore
    }

    return null;
  },

  // ════════════════════════════════════════════════════════════════
  // MONITORING
  // ════════════════════════════════════════════════════════════════

  /**
   * Start continuous monitoring for wallet connections
   * Polls every 500ms with retry logic for pages that load before wallet.html
   */
  startMonitoring() {
    if (this.isMonitoring) {
      console.log('[WalletStateManager] Already monitoring');
      return;
    }

    this.isMonitoring = true;
    this.checkAttempts = 0;

    this.checkInterval = setInterval(async () => {
      this.checkAttempts++;

      const detected = await this.detectConnectedWallet();

      // Check if wallet state changed
      const wasConnected = !!this.currentWallet;
      const isNowConnected = !!detected;

      if (!wasConnected && isNowConnected) {
        // Wallet just connected!
        console.log('[WalletStateManager] 🎉 Wallet connected!');
        this.currentWallet = detected;
        this.saveToStorage();
        this.notifyWalletChanged();
      } else if (wasConnected && !isNowConnected) {
        // Wallet disconnected
        console.log('[WalletStateManager] 👋 Wallet disconnected');
        this.currentWallet = null;
        this.saveToStorage();
        this.notifyWalletChanged();
      } else if (wasConnected && isNowConnected && this.currentWallet.address !== detected.address) {
        // Wallet switched
        console.log('[WalletStateManager] 🔄 Wallet switched to:', detected.address);
        this.currentWallet = detected;
        this.saveToStorage();
        this.notifyWalletChanged();
      }

      // Stop checking after max attempts to conserve resources
      if (this.checkAttempts > this.MAX_CHECK_ATTEMPTS) {
        console.log('[WalletStateManager] Max check attempts reached, slowing down monitoring');
        clearInterval(this.checkInterval);
        
        // Switch to slower 5-second checks
        this.checkInterval = setInterval(async () => {
          const detected = await this.detectConnectedWallet();
          if (detected && (!this.currentWallet || this.currentWallet.address !== detected.address)) {
            this.currentWallet = detected;
            this.saveToStorage();
            this.notifyWalletChanged();
          }
        }, 5000);
      }
    }, this.CHECK_INTERVAL);

    console.log('[WalletStateManager] ✅ Monitoring started (checking every 500ms)');
  },

  /**
   * Stop monitoring
   */
  stopMonitoring() {
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
      this.checkInterval = null;
      this.isMonitoring = false;
      console.log('[WalletStateManager] ✅ Monitoring stopped');
    }
  },

  // ════════════════════════════════════════════════════════════════
  // WALLET UPDATES
  // ════════════════════════════════════════════════════════════════

  /**
   * Handle wallet update (called when wallet connects/disconnects)
   */
  async handleWalletUpdate(wallet) {
    if (wallet && wallet.address) {
      console.log('[WalletStateManager] 📝 Handling wallet update:', wallet.address);
      this.currentWallet = wallet;
    } else {
      console.log('[WalletStateManager] 📝 Clearing wallet state');
      this.currentWallet = null;
    }
    
    this.saveToStorage();
    this.notifyWalletChanged();
  },

  /**
   * Notify all listeners of wallet state change
   */
  notifyWalletChanged() {
    // Dispatch custom event
    const event = new CustomEvent('wallet-state-changed', {
      detail: {
        wallet: this.currentWallet,
        isConnected: !!this.currentWallet,
        address: this.currentWallet?.address || null
      }
    });
    window.dispatchEvent(event);
    
    console.log('[WalletStateManager] 📢 Dispatched wallet-state-changed event');

    // Broadcast to other tabs
    try {
      window.localStorage.setItem('__wallet_state_sync', JSON.stringify({
        type: 'wallet-state-sync',
        wallet: this.currentWallet,
        timestamp: Date.now()
      }));
    } catch (e) {
      // Ignore localStorage errors
    }
  },

  // ════════════════════════════════════════════════════════════════
  // PUBLIC API
  // ════════════════════════════════════════════════════════════════

  /**
   * Get current wallet state
   * @returns {object|null}
   */
  getWallet() {
    return this.currentWallet;
  },

  /**
   * Check if wallet is connected
   * @returns {boolean}
   */
  isConnected() {
    return !!this.currentWallet && !!this.currentWallet.address;
  },

  /**
   * Get wallet address
   * @returns {string|null}
   */
  getAddress() {
    return this.currentWallet?.address || null;
  },

  /**
   * Get full wallet data
   * @returns {object|null}
   */
  getWalletData() {
    if (!this.currentWallet) return null;
    
    return {
      address: this.currentWallet.address,
      wallet: this.currentWallet.wallet,
      isConnected: true,
      isTONConnect: true,
      formatted: this.getFormattedAddress()
    };
  },

  /**
   * Get formatted wallet address (shortened)
   * @returns {string}
   */
  getFormattedAddress() {
    if (!this.currentWallet || !this.currentWallet.address) {
      return 'Not Connected';
    }
    const addr = this.currentWallet.address;
    return addr.length > 20 ? addr.slice(0, 10) + '...' + addr.slice(-10) : addr;
  },

  /**
   * Listen for wallet changes
   * @param {function} callback
   */
  onChange(callback) {
    window.addEventListener('wallet-state-changed', (e) => {
      callback(e.detail);
    });
  }
};

// Auto-initialize on document ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.WalletStateManager.initialize();
  });
} else {
  window.WalletStateManager.initialize();
}

