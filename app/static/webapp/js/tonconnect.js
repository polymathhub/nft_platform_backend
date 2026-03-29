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
 */

class TonConnectManager {
  constructor() {
    this.ui = null;
    this.isInitialized = false;
    this.currentAccount = null;
    this.isConnecting = false;
  }

  /**
   * Initialize TON Connect UI v2
   */
  async init() {
    if (this.isInitialized) {
      console.log('[TONConnect] Already initialized');
      return this.ui;
    }

    try {
      console.log('[TONConnect] Initializing v2 UI...');
      
      // Dynamically load v2 SDK (latest)
      await this.loadTonConnectSDK();
      
      // Get manifest URL (works with proxy/railway)
      const manifestUrl = `${window.location.origin}/tonconnect-manifest.json`;
      console.log('[TONConnect] Manifest:', manifestUrl);

      // Init UI v2
      this.ui = new window.TonConnectUI({
        manifestUrl,
        buttonRootId: null, // Programmatic control
        actionsConfiguration: {
          twaReturnUrl: window.location.href,
        },
        uiPreferences: {
          theme: window.Telegram?.WebApp?.colorScheme === 'dark' ? 'dark' : 'light',
        },
      });

      // Event listeners
      this.ui.onStatusChange((wallet) => {
        console.log('[TONConnect] Status change:', wallet);
        this.currentAccount = wallet?.account || null;
        
        if (wallet) {
          this.saveSession(wallet);
          this.emit('connected', wallet.account);
        } else {
          this.clearSession();
          this.emit('disconnected');
        }
      });

      // Try auto-reconnect
      await this.restoreSession();

      this.isInitialized = true;
      console.log('[TONConnect] ✅ Initialized');
      this.emit('ready');
      
      return this.ui;
    } catch (error) {
      console.error('[TONConnect] Init failed:', error);
      this.emit('error', { message: error.message });
      throw error;
    }
  }

  /**
   * Load TON Connect SDK dynamically
   */
  async loadTonConnectSDK() {
    if (window.TonConnectUI) {
      return;
    }

    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = 'https://unpkg.com/@tonconnect/ui@latest/dist/tonconnect-ui.min.js';
      script.onload = () => {
        console.log('[TONConnect] SDK loaded');
        resolve();
      };
      script.onerror = () => {
        reject(new Error('Failed to load TON Connect SDK'));
      };
      document.head.appendChild(script);
    });
  }

  /**
   * Connect wallet (user-initiated)
   */
  async connectWallet() {
    if (this.isConnecting || this.currentAccount) {
      console.log('[TONConnect] Already connecting or connected');
      return this.currentAccount;
    }

    this.isConnecting = true;
    this.emit('connecting');

    try {
      const wallet = await this.ui.connectWallet();
      console.log('[TONConnect] Connected:', wallet.account);
      return wallet.account;
    } catch (error) {
      console.error('[TONConnect] Connect failed:', error);
      this.emit('error', { message: error.message || 'Connection cancelled' });
      return null;
    } finally {
      this.isConnecting = false;
    }
  }

  /**
   * Disconnect wallet
   */
  async disconnect() {
    try {
      await this.ui.disconnect();
      console.log('[TONConnect] Disconnected');
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
        console.log('[TONConnect] Restoring session:', parsed);
        await this.ui.restoreConnection(parsed);
      } catch (error) {
        console.error('[TONConnect] Session restore failed:', error);
        localStorage.removeItem('tonconnect_session');
      }
    }
  }

  /**
   * Save session to localStorage
   */
  saveSession(wallet) {
    try {
      localStorage.setItem('tonconnect_session', JSON.stringify(wallet));
    } catch (error) {
      console.warn('[TONConnect] Failed to save session:', error);
    }
  }

  /**
   * Clear session
   */
  clearSession() {
    localStorage.removeItem('tonconnect_session');
  }

  /**
   * Custom event emitter
   */
  emit(event, data) {
    const customEvent = new CustomEvent(`tonconnect:${event}`, { detail: data });
    window.dispatchEvent(customEvent);
    console.log(`[TONConnect] Event: ${event}`, data);
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
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => tonConnect.init().catch(console.error));
} else {
  tonConnect.init().catch(console.error);
}

// Global access
window.tonConnect = tonConnect;

console.log('[TONConnect] Module loaded');

