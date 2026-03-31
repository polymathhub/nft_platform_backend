/**
 * ═══════════════════════════════════════════════════════════════════════════
 * SIMPLE TON CONNECT - Straightforward Wallet Connection
 * ═══════════════════════════════════════════════════════════════════════════
 * 
 * Usage:
 *   const tonConnect = new SimpleTonConnect('tonconnect-button');
 *   await tonConnect.init();
 *   tonConnect.on('connected', (wallet) => console.log(wallet.address));
 * 
 * Features:
 * ✅ Simple, clean API
 * ✅ Telegram Mini App compatible
 * ✅ Triggers wallet selection modal
 * ✅ Event-based (connected, disconnected, error)
 * ✅ Auto-restore previous session
 * ✅ Backend synchronization
 * ═══════════════════════════════════════════════════════════════════════════
 */

class SimpleTonConnect {
  constructor(buttonId = 'tonconnect-button') {
    this.buttonId = buttonId;
    this.ui = null;
    this.isInitialized = false;
    this.currentWallet = null;
    this.listeners = {};
    
    // Load SDK
    this.loadSDK();
  }

  /**
   * Load TonConnect SDK and CSS
   */
  loadSDK() {
    // Load CSS
    if (!document.querySelector('link[href*="tonconnect"]')) {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = 'https://cdn.jsdelivr.net/npm/@tonconnect/ui@latest/dist/tonconnect-ui.css';
      document.head.appendChild(link);
    }

    // Load JS SDK
    if (!window.TonConnectUI) {
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/@tonconnect/ui@latest/dist/tonconnect-ui.min.js';
      script.async = true;
      script.onload = () => console.log('[TONConnect] SDK loaded');
      document.head.appendChild(script);
    }
  }

  /**
   * Initialize TON Connect UI
   */
  async init() {
    if (this.isInitialized) return this.ui;

    // Wait for SDK to load
    while (!window.TonConnectUI) {
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    const manifestUrl = this.getManifestUrl();
    console.log('[TONConnect] Initializing with manifest:', manifestUrl);

    try {
      // Initialize UI
      this.ui = new window.TonConnectUI({
        manifestUrl: manifestUrl,
        buttonRootId: this.buttonId,
      });

      // Check if wallet already connected
      const wallet = this.ui.wallet;
      if (wallet) {
        this.currentWallet = wallet;
        console.log('[TONConnect] Restored session:', wallet.account.address);
        this.emit('connected', wallet.account);
      }

      // Listen for status changes
      this.ui.onStatusChange((wallet) => {
        if (wallet) {
          this.currentWallet = wallet;
          console.log('[TONConnect] Wallet connected:', wallet.account.address);
          this.emit('connected', wallet.account);
          this.syncWithBackend(wallet.account.address);
        } else {
          this.currentWallet = null;
          console.log('[TONConnect] Wallet disconnected');
          this.emit('disconnected');
        }
      });

      this.isInitialized = true;
      console.log('[TONConnect] Initialized successfully');
      this.emit('ready');

      return this.ui;
    } catch (error) {
      console.error('[TONConnect] Initialization failed:', error);
      this.emit('error', error);
      throw error;
    }
  }

  /**
   * Get manifest URL (must be full HTTPS URL)
   */
  getManifestUrl() {
    const origin = window.location.origin;
    return `${origin}/tonconnect-manifest.json`;
  }

  /**
   * Manually trigger wallet selection (for custom button clicks)
   */
  async connectWallet() {
    if (!this.ui) {
      throw new Error('TON Connect not initialized. Call init() first.');
    }

    try {
      console.log('[TONConnect] Opening wallet selection...');
      await this.ui.connectWallet();
    } catch (error) {
      console.error('[TONConnect] Connection failed:', error);
      this.emit('error', error);
      throw error;
    }
  }

  /**
   * Disconnect current wallet
   */
  async disconnectWallet() {
    if (!this.ui) return;

    try {
      console.log('[TONConnect] Disconnecting wallet');
      await this.ui.disconnect();
      this.currentWallet = null;
    } catch (error) {
      console.error('[TONConnect] Disconnect failed:', error);
    }
  }

  /**
   * Get current wallet or null
   */
  getWallet() {
    return this.currentWallet;
  }

  /**
   * Check if wallet is connected
   */
  isConnected() {
    return !!this.currentWallet;
  }

  /**
   * Get wallet address
   */
  getAddress() {
    return this.currentWallet?.account?.address || null;
  }

  /**
   * Sync wallet connection with backend
   */
  async syncWithBackend(address) {
    try {
      const { telegramFetch } = await import('./telegram-fetch.js');
      
      const response = await telegramFetch('/api/v1/walletconnect/connect', {
        method: 'POST',
        body: JSON.stringify({
          wallet_address: address,
          blockchain: 'ton',
        }),
      });

      if (response.ok) {
        const data = await response.json();
        console.log('[TONConnect] Backend sync successful:', data);
        this.emit('synced', data);
      } else {
        console.warn('[TONConnect] Backend sync failed:', response.status);
      }
    } catch (error) {
      console.warn('[TONConnect] Backend sync error:', error);
      // Don't fail wallet connection if backend sync fails
    }
  }

  /**
   * Event listeners
   */
  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }

  emit(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(cb => cb(data));
    }
  }
}

// Export as ES6 module (default) and global
export default SimpleTonConnect;

// Also expose globally for direct access
if (typeof window !== 'undefined') {
  window.SimpleTonConnect = SimpleTonConnect;
}
