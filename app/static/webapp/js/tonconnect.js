/**
 * TON Connect v2 - Production Module for Telegram Mini App
 * 
 * Features:
 * ✅ Latest @tonconnect/ui v2 
 * ✅ Session persistence/reconnect
 * ✅ Telegram Mini App compatible
 * ✅ Custom events
 * ✅ Error boundaries
 * ✅ Universal wallet support
 * ✅ Full API compatibility
 */

class TonConnectManager {
  constructor() {
    this.ui = null;
    this.isInitialized = false;
    this.isReady = false;
    this.currentAccount = null;
    this.isConnecting = false;
    this.readyPromise = null;
    this.readyResolve = null;
  }

  /**
   * Initialize TON Connect UI v2
   */
  async init() {
    if (this.isInitialized) {
      console.log('[TONConnect] Already initialized');
      return this.ui;
    }

    if (this.readyPromise) {
      return this.readyPromise;
    }

    this.readyPromise = this._doInit();
    return this.readyPromise;
  }

  async _doInit() {
    try {
      console.log('[TONConnect] Initializing v2 UI...');
      
      // Load TonConnect SDK and CSS
      await this.loadTonConnectSDK();
      
      // Verify SDK is available
      if (!window.TonConnectUI) {
        throw new Error('TonConnectUI SDK not loaded');
      }

      // Get manifest URL 
      const manifestUrl = `${window.location.origin}/tonconnect-manifest.json`;
      console.log('[TONConnect] Manifest URL:', manifestUrl);

      // Create a container for the button (required by TonConnectUI)
      let buttonContainer = document.getElementById('tonconnect-button-container');
      if (!buttonContainer) {
        buttonContainer = document.createElement('div');
        buttonContainer.id = 'tonconnect-button-container';
        buttonContainer.style.display = 'none';
        document.body.appendChild(buttonContainer);
      }

      // Initialize UI v2 with proper configuration
      try {
        this.ui = new window.TonConnectUI({
          manifestUrl: manifestUrl,
          buttonRootId: 'tonconnect-button-container',
          actionsConfiguration: {
            twaReturnUrl: window.location.href,
          },
          uiPreferences: {
            theme: this._getTheme(),
          },
        });
      } catch (e) {
        console.warn('[TONConnect] Standard UI init failed, trying alternative:', e);
        // Fallback: create UI without button
        this.ui = new window.TonConnectUI({
          manifestUrl: manifestUrl,
        });
      }

      // Listen for status changes
      this.ui.onStatusChange((wallet) => {
        console.log('[TONConnect] Status change:', wallet);
        if (wallet) {
          this.currentAccount = wallet.account;
          this.saveSession(wallet);
          this.emit('connected', wallet.account);
          console.log('[TONConnect] Connected to:', wallet.account.address);
        } else {
          this.currentAccount = null;
          this.clearSession();
          this.emit('disconnected');
          console.log('[TONConnect] Disconnected');
        }
      });

      // Try to restore previous session
      await this.restoreSession();

      this.isInitialized = true;
      this.isReady = true;
      console.log('[TONConnect] ✅ Initialized successfully');
      this.emit('ready');
      
      return this.ui;
    } catch (error) {
      console.error('[TONConnect] Init failed:', error);
      this.isReady = false;
      this.emit('error', { message: error.message || 'Initialization failed' });
      throw error;
    }
  }

  /**
   * Get current theme
   */
  _getTheme() {
    if (window.Telegram?.WebApp?.colorScheme) {
      return window.Telegram.WebApp.colorScheme === 'dark' ? 'dark' : 'light';
    }
    return 'light';
  }

  /**
   * Load TON Connect SDK and CSS dynamically
   */
  async loadTonConnectSDK() {
    // Check if already loaded
    if (window.TonConnectUI) {
      console.log('[TONConnect] SDK already loaded');
      return;
    }

    // Load CSS first
    await this._loadCSS();
    
    // Load JS
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = 'https://unpkg.com/@tonconnect/ui@latest/dist/tonconnect-ui.min.js';
      script.async = true;
      
      script.onload = () => {
        console.log('[TONConnect] SDK script loaded');
        // Give it a moment to initialize
        setTimeout(() => {
          if (window.TonConnectUI) {
            resolve();
          } else {
            reject(new Error('TonConnectUI not available after script load'));
          }
        }, 100);
      };
      
      script.onerror = () => {
        reject(new Error('Failed to load TON Connect SDK from CDN'));
      };
      
      document.head.appendChild(script);
    });
  }

  /**
   * Load TON Connect CSS
   */
  async _loadCSS() {
    return new Promise((resolve) => {
      if (document.querySelector('link[href*="tonconnect-ui.min.css"]')) {
        resolve();
        return;
      }

      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = 'https://unpkg.com/@tonconnect/ui@latest/dist/tonconnect-ui.min.css';
      link.onload = () => {
        console.log('[TONConnect] CSS loaded');
        resolve();
      };
      link.onerror = () => {
        console.warn('[TONConnect] CSS failed to load (non-critical)');
        resolve(); // Don't fail on CSS
      };
      document.head.appendChild(link);
    });
  }

  /**
   * Wait for TON Connect to be ready
   */
  async waitForReady() {
    if (this.isReady) {
      return true;
    }

    try {
      await this.init();
      return this.isReady;
    } catch (error) {
      console.error('[TONConnect] waitForReady failed:', error);
      return false;
    }
  }

  /**
   * Initialize (same as init, for compatibility)
   */
  async initialize() {
    return this.init();
  }

  /**
   * Check if wallet is connected
   */
  isConnected() {
    return this.currentAccount != null;
  }

  /**
   * Open wallet connection modal
   */
  async openModal() {
    if (!this.isInitialized || !this.ui) {
      const ready = await this.waitForReady();
      if (!ready) {
        throw new Error('TON Connect not ready');
      }
    }

    try {
      console.log('[TONConnect] Opening wallet modal...');
      const wallet = await this.ui.connectWallet();
      console.log('[TONConnect] Wallet connected:', wallet);
      return wallet;
    } catch (error) {
      if (error.message === 'Already connected') {
        console.log('[TONConnect] Already connected');
        return true;
      }
      console.error('[TONConnect] Modal error:', error);
      this.emit('error', { message: error.message || 'Connection cancelled' });
      return null;
    }
  }

  /**
   * Get wallet address
   */
  getWalletAddress() {
    if (this.currentAccount?.address) {
      return this.currentAccount.address;
    }
    return null;
  }

  /**
   * Connect wallet (programmatic)
   */
  async connectWallet() {
    if (this.isConnecting) {
      console.log('[TONConnect] Already connecting');
      return this.currentAccount;
    }

    if (this.currentAccount) {
      console.log('[TONConnect] Already connected');
      return this.currentAccount;
    }

    this.isConnecting = true;
    this.emit('connecting');

    try {
      const result = await this.openModal();
      if (result) {
        return this.currentAccount;
      }
      return null;
    } catch (error) {
      console.error('[TONConnect] Connect failed:', error);
      this.emit('error', { message: error.message || 'Connection failed' });
      return null;
    } finally {
      this.isConnecting = false;
    }
  }

  /**
   * Send transaction
   */
  async sendTransaction(transaction) {
    if (!this.isConnected()) {
      throw new Error('Wallet not connected');
    }

    if (!this.ui) {
      throw new Error('TON Connect not initialized');
    }

    try {
      console.log('[TONConnect] Sending transaction:', transaction);
      
      // Use the TonConnectUI's sendTransaction method
      const result = await this.ui.sendTransaction(transaction);
      
      console.log('[TONConnect] Transaction sent:', result);
      this.emit('transaction-sent', result);
      
      return result;
    } catch (error) {
      console.error('[TONConnect] Send transaction failed:', error);
      this.emit('error', { message: error.message || 'Transaction failed' });
      throw error;
    }
  }

  /**
   * Disconnect wallet
   */
  async disconnect() {
    try {
      if (this.ui) {
        await this.ui.disconnect();
      }
      this.currentAccount = null;
      this.clearSession();
      console.log('[TONConnect] Disconnected');
      this.emit('disconnected');
    } catch (error) {
      console.error('[TONConnect] Disconnect failed:', error);
    }
  }

  /**
   * Get current account
   */
  getAccount() {
    return this.currentAccount;
  }

  /**
   * Restore session from localStorage
   */
  async restoreSession() {
    const session = localStorage.getItem('tonconnect_session');
    if (session && this.ui) {
      try {
        const parsed = JSON.parse(session);
        console.log('[TONConnect] Attempting to restore session...');
        
        // Try to restore the connection
        const restored = await this.ui.getWallets?.() || await this.ui.connectWallet?.();
        if (restored) {
          console.log('[TONConnect] Session restored');
          return true;
        }
      } catch (error) {
        console.warn('[TONConnect] Session restore failed:', error);
        this.clearSession();
      }
    }
    return false;
  }

  /**
   * Save session to localStorage
   */
  saveSession(wallet) {
    try {
      localStorage.setItem('tonconnect_session', JSON.stringify({
        account: wallet.account,
        wallet: wallet.jsBridgeKey,
      }));
      console.log('[TONConnect] Session saved');
    } catch (error) {
      console.warn('[TONConnect] Failed to save session:', error);
    }
  }

  /**
   * Clear session
   */
  clearSession() {
    localStorage.removeItem('tonconnect_session');
    console.log('[TONConnect] Session cleared');
  }

  /**
   * Custom event emitter
   */
  emit(event, data) {
    const customEvent = new CustomEvent(`tonconnect:${event}`, { detail: data });
    window.dispatchEvent(customEvent);
    console.log(`[TONConnect] Event: tonconnect:${event}`, data);
  }

  /**
   * Event listener
   */
  on(event, callback) {
    window.addEventListener(`tonconnect:${event}`, (e) => callback(e.detail));
  }
}

// Singleton instance
export const tonConnect = new TonConnectManager();

// Auto-init when DOM ready
function autoInitTonConnect() {
  console.log('[TONConnect] Setting up auto-init...');
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      console.log('[TONConnect] Initializing on DOMContentLoaded');
      tonConnect.init().catch(e => console.error('[TONConnect] Auto-init error:', e));
    });
  } else {
    console.log('[TONConnect] Initializing immediately');
    tonConnect.init().catch(e => console.error('[TONConnect] Auto-init error:', e));
  }
}

// Start auto-init
autoInitTonConnect();

// Global access
window.tonConnect = tonConnect;

console.log('[TONConnect] Module loaded and ready');

