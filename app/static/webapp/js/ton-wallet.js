/**
 * ═══════════════════════════════════════════════════════════════════════════
 * TON WALLET - Production Grade Connector
 * ═══════════════════════════════════════════════════════════════════════════
 * 
 * Simple, clean TON Connect implementation for Telegram Mini Apps
 * 
 * Features:
 * ✅ Single responsibility: connect/disconnect wallet
 * ✅ Auto-restore previous session
 * ✅ Event-driven (connected, disconnected, error)
 * ✅ Backend sync on connection
 * ✅ Clean error handling
 * ✅ Zero dependencies (except TonConnectUI)
 * 
 * Usage:
 *   const wallet = new TonWallet();
 *   await wallet.init();
 *   wallet.on('connected', (account) => console.log(account.address));
 * ═══════════════════════════════════════════════════════════════════════════
 */

class TonWallet {
  constructor() {
    this.ui = null;
    this.wallet = null;
    this.initialized = false;
    this.listeners = {};

    // Load TonConnect SDK
    this._loadSDK();
  }

  /**
   * Load TonConnect SDK from CDN
   * @private
   */
  _loadSDK() {
    // Load CSS
    if (!document.querySelector('link[href*="tonconnect"]')) {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = 'https://cdn.jsdelivr.net/npm/@tonconnect/ui@latest/dist/tonconnect-ui.css';
      document.head.appendChild(link);
    }

    // Load JS
    if (!window.TonConnectUI) {
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/@tonconnect/ui@latest/dist/tonconnect-ui.min.js';
      script.async = true;
      document.head.appendChild(script);
    }
  }

  /**
   * Initialize TonConnect UI
   * Waits for SDK to load and creates UI instance
   */
  async init() {
    if (this.initialized) return this.ui;

    // Wait for SDK to load
    let attempts = 0;
    while (!window.TonConnectUI && attempts < 50) {
      await new Promise(resolve => setTimeout(resolve, 100));
      attempts++;
    }

    if (!window.TonConnectUI) {
      throw new Error('TonConnect SDK failed to load');
    }

    try {
      const manifestUrl = this._getManifestUrl();
      
      // Create UI instance
      this.ui = new window.TonConnectUI({
        manifestUrl: manifestUrl,
      });

      // Restore previous session if available
      const status = this.ui.wallet;
      if (status) {
        this.wallet = status;
        this._emit('connected', status.account);
      }

      // Listen for connection changes
      this.ui.onStatusChange(
        (wallet) => {
          if (wallet) {
            this.wallet = wallet;
            this._emit('connected', wallet.account);
            // Sync with backend
            this._syncBackend(wallet.account.address);
          } else {
            this.wallet = null;
            this._emit('disconnected');
          }
        },
        (error) => {
          this._emit('error', error);
        }
      );

      this.initialized = true;
      return this.ui;
    } catch (error) {
      this._emit('error', error);
      throw error;
    }
  }

  /**
   * Open wallet selection modal and connect
   */
  async connect() {
    if (!this.ui) {
      throw new Error('TonWallet not initialized. Call init() first.');
    }

    try {
      const result = await this.ui.connectWallet();
      return result;
    } catch (error) {
      if (error.message === 'User declined') {
        this._emit('cancelled');
      } else {
        this._emit('error', error);
      }
      throw error;
    }
  }

  /**
   * Disconnect wallet
   */
  async disconnect() {
    if (!this.ui) return;

    try {
      await this.ui.disconnect();
      this.wallet = null;
      this._emit('disconnected');
    } catch (error) {
      this._emit('error', error);
      throw error;
    }
  }

  /**
   * Get current connected wallet address
   */
  getAddress() {
    if (!this.wallet?.account?.address) {
      return null;
    }
    return this.wallet.account.address;
  }

  /**
   * Check if wallet is connected
   */
  isConnected() {
    return !!this.wallet?.account?.address;
  }

  /**
   * Format address for display (shortened)
   */
  formatAddress(address) {
    if (!address) return '';
    return address.slice(0, 6) + '...' + address.slice(-6);
  }

  /**
   * Get manifest URL (full HTTPS required)
   * Priority: window.location.origin > fallback to known domain
   * @private
   */
  _getManifestUrl() {
    const origin = window.location.origin;
    
    // ⚠️ CRITICAL: Must be full HTTPS URL
    // Relative paths like /tonconnect-manifest.json fail silently
    // Wallets fetch manifest independently from outside app context
    if (origin && origin.startsWith('https://')) {
      return `${origin}/tonconnect-manifest.json`;
    }

    // Fallback only for localhost development
    if (origin?.includes('localhost') || origin?.includes('127.0.0.1')) {
      return `${origin}/tonconnect-manifest.json`;
    }

    // Production fallback (should never reach here)
    return 'https://nftplatformbackend-production-ee5f.up.railway.app/tonconnect-manifest.json';
  }

  /**
   * Sync wallet connection with backend
   * @private
   */
  async _syncBackend(address) {
    try {
      const initData = window.Telegram?.WebApp?.initData || '';
      
      const response = await fetch('/api/v1/walletconnect/connect', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(initData && { 'X-Telegram-Init-Data': initData })
        },
        body: JSON.stringify({
          wallet_address: address,
          blockchain: 'ton'
        })
      });

      if (!response.ok) {
        console.warn('[TonWallet] Backend sync failed:', response.status);
      }
    } catch (error) {
      console.warn('[TonWallet] Backend sync error:', error);
    }
  }

  /**
   * Event listener management
   */
  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }

  off(event, callback) {
    if (!this.listeners[event]) return;
    this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
  }

  /**
   * Emit event to listeners
   * @private
   */
  _emit(event, data) {
    if (!this.listeners[event]) return;
    this.listeners[event].forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        console.error(`[TonWallet] Event listener error (${event}):`, error);
      }
    });
  }
}

// Export as ES6 module
export default TonWallet;

