/**
 * TON CONNECT INITIALIZATION - Global Setup
 * ═══════════════════════════════════════════════════════════════
 * 
 * Entry point for TON Connect system initialization.
 * Sets up global instances and makes them available across all pages.
 * 
 * Global API:
 * - window.tonConnectManager - Wallet state management
 * - window.tonTransactionHandler - NFT transaction handler
 * - window.getTONWallet() - Get connected wallet
 * - window.isTONConnected() - Check wallet status
 */

// Import modules
import TonWallet from './ton-wallet.js';
import TONConnectManager from './tonconnect-manager.js';
import TONTransactionHandler from './ton-transaction-handler.js';

class TONConnectInitializer {
  constructor() {
    this.tonWallet = null;
    this.tonConnectManager = null;
    this.tonTransactionHandler = null;
    this.initialized = false;
  }

  /**
   * Initialize TON Connect system globally
   */
  async initialize() {
    if (this.initialized) {
      return {
        manager: this.tonConnectManager,
        handler: this.tonTransactionHandler,
        wallet: this.tonWallet
      };
    }

    try {
      console.log('[TONConnect Init] Starting initialization...');

      // 1. Initialize TonWallet (SDK wrapper)
      this.tonWallet = new TonWallet();
      await this.tonWallet.init();
      console.log('[TONConnect Init] TonWallet initialized');

      // 2. Initialize TONConnectManager (global state)
      this.tonConnectManager = TONConnectManager.getInstance();
      await this.tonConnectManager.initialize(this.tonWallet);
      console.log('[TONConnect Init] TONConnectManager initialized');

      // 3. Initialize TONTransactionHandler (transaction operations)
      this.tonTransactionHandler = new TONTransactionHandler(
        this.tonConnectManager,
        this.tonWallet
      );
      console.log('[TONConnect Init] TONTransactionHandler initialized');

      // 4. Setup global API
      this._setupGlobalAPI();
      console.log('[TONConnect Init] Global API set up');

      // 5. Setup cross-page synchronization
      this._setupCrossPagesync();
      console.log('[TONConnect Init] Cross-page sync set up');

      // 6. Setup event notifications
      this._setupEventNotifications();
      console.log('[TONConnect Init] Event notifications set up');

      this.initialized = true;
      window.dispatchEvent(new CustomEvent('tonconnect-ready', {
        detail: {
          manager: this.tonConnectManager,
          handler: this.tonTransactionHandler
        }
      }));

      console.log('[TONConnect Init] ✅ Fully initialized');
      return {
        manager: this.tonConnectManager,
        handler: this.tonTransactionHandler,
        wallet: this.tonWallet
      };
    } catch (error) {
      console.error('[TONConnect Init] Initialization failed:', error);
      window.dispatchEvent(new CustomEvent('tonconnect-error', {
        detail: { error }
      }));
      throw error;
    }
  }

  /**
   * Setup global window API
   * @private
   */
  _setupGlobalAPI() {
    // Wallet state access
    window.getTONWallet = () => this.tonConnectManager.getWallet();
    window.getTONAddress = () => this.tonConnectManager.getAddress();
    window.getTONFormattedAddress = () => this.tonConnectManager.getFormattedAddress();
    window.isTONConnected = () => this.tonConnectManager.isConnected();

    // Transaction operations
    window.mintNFT = async (collectionAddress, metadata, options) => {
      if (!this.tonTransactionHandler) {
        throw new Error('Transaction handler not initialized');
      }
      return this.tonTransactionHandler.mintNFT(collectionAddress, metadata, options);
    };

    window.transferNFT = async (itemAddress, newOwner, options) => {
      if (!this.tonTransactionHandler) {
        throw new Error('Transaction handler not initialized');
      }
      return this.tonTransactionHandler.transferNFT(itemAddress, newOwner, options);
    };

    // Event subscription
    window.onTONWalletChange = (handler) => {
      return this.tonConnectManager.on('wallet-connected', handler);
    };

    window.onTONTransaction = (handler) => {
      return this.tonConnectManager.on('transaction-added', handler);
    };

    window.onTONError = (handler) => {
      return this.tonConnectManager.on('error', handler);
    };
  }

  /**
   * Setup cross-page synchronization
   * @private
   */
  _setupCrossPagesync() {
    // Listen for broadcast events from other pages
    window.addEventListener('tonconnect-broadcast', (event) => {
      console.log('[TONConnect Init] Cross-page sync event:', event.detail);
      window.dispatchEvent(new CustomEvent('tonconnect-synced', {
        detail: event.detail
      }));
    });

    // Listen for storage changes from other tabs
    window.addEventListener('storage', (event) => {
      if (event.key && event.key.includes('tonconnect')) {
        console.log('[TONConnect Init] Storage sync from another tab');
      }
    });
  }

  /**
   * Setup event notifications
   * @private
   */
  _setupEventNotifications() {
    // Wallet connection changes
    this.tonConnectManager.on('wallet-connected', (data) => {
      console.log('[TONConnect Init] Wallet connected:', data.wallet.formatted);
      window.dispatchEvent(new CustomEvent('tonconnect-wallet-connected', {
        detail: data
      }));

      // Show toast/notification
      this._notifyUser(`Wallet connected: ${data.wallet.formatted}`, 'success');
    });

    this.tonConnectManager.on('wallet-disconnected', () => {
      console.log('[TONConnect Init] Wallet disconnected');
      window.dispatchEvent(new CustomEvent('tonconnect-wallet-disconnected'));
      this._notifyUser('Wallet disconnected', 'info');
    });

    // Transaction tracking
    this.tonConnectManager.on('transaction-added', (data) => {
      console.log('[TONConnect Init] Transaction recorded:', data.transaction.type);
      window.dispatchEvent(new CustomEvent('tonconnect-transaction', {
        detail: data
      }));
    });

    // Error handling
    this.tonConnectManager.on('error', (data) => {
      console.error('[TONConnect Init] Error:', data.error);
      window.dispatchEvent(new CustomEvent('tonconnect-error', {
        detail: data
      }));
      this._notifyUser(`Error: ${data.error.message}`, 'error');
    });
  }

  /**
   * Show user notification
   * @private
   */
  _notifyUser(message, type = 'info') {
    try {
      // Try to use existing notification system if available
      if (window.Notification) {
        console.log(`[TONConnect Init] [${type.toUpperCase()}] ${message}`);
      }
    } catch (error) {
      console.warn('[TONConnect Init] Notification failed:', error);
    }
  }

  /**
   * Get initialization status
   */
  isInitialized() {
    return this.initialized;
  }

  /**
   * Reset system (for testing)
   */
  reset() {
    if (this.tonConnectManager) {
      this.tonConnectManager.reset();
    }
    this.initialized = false;
    console.log('[TONConnect Init] System reset');
  }
}

// Create singleton instance
const tonConnectInit = new TONConnectInitializer();

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', async () => {
    try {
      await tonConnectInit.initialize();
    } catch (error) {
      console.error('[TONConnect Init] Auto-initialization failed:', error);
    }
  }, { once: true });
} else {
  // DOM already loaded
  tonConnectInit.initialize().catch(error => {
    console.error('[TONConnect Init] Auto-initialization failed:', error);
  });
}

// Export for testing
export default tonConnectInit;
export { TONConnectInitializer };
