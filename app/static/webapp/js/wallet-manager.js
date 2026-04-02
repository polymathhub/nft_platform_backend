/**
 * ═══════════════════════════════════════════════════════════════════════════════
 * WALLET MANAGER - Production-Grade TON Connect Session & Transaction Management
 * ═══════════════════════════════════════════════════════════════════════════════
 * 
 * Senior-level implementation providing:
 * ✅ Persistent wallet session (survives page reloads)
 * ✅ Auto-restore on app load
 * ✅ Global transaction execution API
 * ✅ Real blockchain operations
 * ✅ Comprehensive error handling
 * ✅ Type-safe state management
 * ✅ Telegram Mini App integration
 * 
 * Architecture:
 * - Singleton pattern for global access
 * - Event-driven for reactive UI
 * - Session storage for persistence
 * - TonConnectUI integration for signing
 * 
 * PUBLIC API:
 *   WalletManager.getInstance()
 *   .getWallet() → { address, publicKey }
 *   .isConnected() → boolean
 *   .sendTransaction(tx) → { hash, boc, exitCode }
 *   .disconnect()
 *   .on('connected', callback)
 *   .on('disconnected', callback)
 *   .on('transaction', callback)
 * ═══════════════════════════════════════════════════════════════════════════════
 */

class WalletManager {
  // Singleton instance
  static #instance = null;

  // Private properties
  #tonConnectUI = null;
  #walletState = null;
  #isConnecting = false;
  #listeners = new Map();
  #initialized = false;

  // Storage keys
  #STORAGE_KEYS = {
    WALLET: 'ton_wallet_session',
    ADDRESS: 'ton_wallet_address',
    PUBLIC_KEY: 'ton_wallet_pubkey',
    LAST_SYNC: 'ton_wallet_sync',
  };

  // Constants
  #MANIFEST_URL = null;
  #RETRY_CONFIG = { attempts: 3, delay: 1000, backoff: 1.5 };

  /**
   * Get singleton instance
   * @static
   * @returns {WalletManager}
   */
  static getInstance() {
    if (!WalletManager.#instance) {
      WalletManager.#instance = new WalletManager();
    }
    return WalletManager.#instance;
  }

  constructor() {
    if (WalletManager.#instance) {
      return WalletManager.#instance;
    }
    this._setupManifestURL();
    this._restoreSessionFromStorage();
  }

  /**
   * Setup manifest URL from current deployment
   * @private
   */
  _setupManifestURL() {
    const protocol = window.location.protocol;
    const host = window.location.host;
    this.#MANIFEST_URL = `${protocol}//${host}/tonconnect-manifest.json`;
    console.log('[WalletManager] Manifest URL:', this.#MANIFEST_URL);
  }

  /**
   * Restore wallet session from storage if exists
   * @private
   */
  _restoreSessionFromStorage() {
    try {
      const stored = sessionStorage.getItem(this.#STORAGE_KEYS.WALLET);
      if (stored) {
        this.#walletState = JSON.parse(stored);
        console.log('[WalletManager] Restored session:', this.#walletState.address);
      }
    } catch (e) {
      console.warn('[WalletManager] Failed to restore session:', e);
      this.#walletState = null;
    }
  }

  /**
   * Persist wallet state to storage
   * @private
   */
  _persistSession() {
    try {
      if (this.#walletState) {
        sessionStorage.setItem(
          this.#STORAGE_KEYS.WALLET,
          JSON.stringify(this.#walletState)
        );
        sessionStorage.setItem(
          this.#STORAGE_KEYS.LAST_SYNC,
          new Date().toISOString()
        );
      } else {
        sessionStorage.removeItem(this.#STORAGE_KEYS.WALLET);
      }
    } catch (e) {
      console.error('[WalletManager] Failed to persist session:', e);
    }
  }

  /**
   * Initialize wallet manager - must call on app startup
   * @async
   * @returns {Promise<boolean>} true if already connected, false if not
   */
  async initialize() {
    if (this.#initialized) {
      console.log('[WalletManager] Already initialized');
      return this.isConnected();
    }

    try {
      console.log('[WalletManager] Initializing...');

      // Initialize TonConnectUI
      this.#tonConnectUI = new window.TonConnectUI.TonConnectUI({
        manifestUrl: this.#MANIFEST_URL,
        buttons: {
          root: '#tonconnect-button',
        },
      });

      // Restore previous wallet connection if available
      const wallet = this.#tonConnectUI.wallet;
      if (wallet) {
        console.log('[WalletManager] Found existing connection:', wallet.account?.address);
        await this._onWalletConnected(wallet);
      }

      // Listen for wallet status changes
      this.#tonConnectUI.onStatusChange(async (wallet) => {
        if (wallet) {
          await this._onWalletConnected(wallet);
        } else {
          await this._onWalletDisconnected();
        }
      });

      this.#initialized = true;
      console.log('[WalletManager] Initialization complete');
      return this.isConnected();
    } catch (error) {
      console.error('[WalletManager] Initialization failed:', error);
      throw error;
    }
  }

  /**
   * Handle wallet connection
   * @private
   * @async
   */
  async _onWalletConnected(wallet) {
    try {
      const address = wallet.account?.address;
      const publicKey = wallet.account?.publicKey;

      if (!address) {
        throw new Error('Invalid wallet: missing address');
      }

      this.#walletState = {
        address,
        publicKey,
        chainId: wallet.account?.chain,
        walletInfo: {
          name: wallet.name,
          appName: wallet.appName,
          image: wallet.image,
        },
        connectedAt: new Date().toISOString(),
      };

      this._persistSession();

      // Emit event
      this._emit('connected', {
        address,
        publicKey,
        chainId: wallet.account?.chain,
      });

      // Sync with backend
      await this._syncWithBackend(address);

      console.log('[WalletManager] Wallet connected:', address);
    } catch (error) {
      console.error('[WalletManager] Connection error:', error);
      this._emit('error', { code: 'CONNECT_ERROR', message: error.message });
    }
  }

  /**
   * Handle wallet disconnection
   * @private
   * @async
   */
  async _onWalletDisconnected() {
    try {
      const wasConnected = this.#walletState !== null;
      const previousAddress = this.#walletState?.address;

      this.#walletState = null;
      this._persistSession();

      if (wasConnected) {
        this._emit('disconnected', { address: previousAddress });
        console.log('[WalletManager] Wallet disconnected');
      }
    } catch (error) {
      console.error('[WalletManager] Disconnection error:', error);
    }
  }

  /**
   * Sync wallet with backend
   * @private
   * @async
   */
  async _syncWithBackend(address) {
    try {
      const { telegramFetch } = await import('./telegram-fetch.js');
      const response = await telegramFetch('/api/v1/walletconnect/connect', {
        method: 'POST',
        body: JSON.stringify({
          wallet_address: address,
          blockchain: 'ton',
          wallet_name: this.#walletState?.walletInfo?.name || 'TON Connect',
        }),
      });

      console.log('[WalletManager] Backend sync successful:', response);
    } catch (error) {
      console.warn('[WalletManager] Backend sync failed (non-critical):', error);
      // Non-critical, don't throw
    }
  }

  /**
   * Connect wallet via TonConnectUI
   * @async
   * @returns {Promise<{address, publicKey}>}
   */
  async connect() {
    if (!this.#tonConnectUI) {
      throw new Error('WalletManager not initialized. Call initialize() first.');
    }

    if (this.#isConnecting) {
      throw new Error('Connection already in progress');
    }

    try {
      this.#isConnecting = true;
      console.log('[WalletManager] Opening wallet connection modal...');

      const wallet = await this.#tonConnectUI.connectWallet();

      if (wallet) {
        console.log('[WalletManager] Wallet connection accepted');
        return {
          address: wallet.account?.address,
          publicKey: wallet.account?.publicKey,
        };
      } else {
        throw new Error('User rejected wallet connection');
      }
    } finally {
      this.#isConnecting = false;
    }
  }

  /**
   * Disconnect wallet
   * @async
   */
  async disconnect() {
    if (!this.#tonConnectUI) {
      throw new Error('WalletManager not initialized');
    }

    try {
      console.log('[WalletManager] Disconnecting wallet...');
      await this.#tonConnectUI.disconnect();
      console.log('[WalletManager] Wallet disconnected');
    } catch (error) {
      console.error('[WalletManager] Disconnect failed:', error);
      // Force local state update even if TonConnectUI fails
      this.#walletState = null;
      this._persistSession();
    }
  }

  /**
   * Send transaction  with automatic retry
   * @async
   * @param {Object} transaction - Transaction object
   * @param {string} transaction.to - Destination address
   * @param {string} transaction.value - Amount in TON
   * @param {string} [transaction.payload] - Message payload (base64 or BOC)
   * @param {string} [transaction.stateInit] - Contract state init (base64 or BOC)
   * @returns {Promise<{hash, boc, exitCode}>}
   */
  async sendTransaction(transaction) {
    if (!this.isConnected()) {
      const error = new Error('Wallet not connected');
      this._emit('error', { code: 'NOT_CONNECTED', message: error.message });
      throw error;
    }

    if (!this.#tonConnectUI) {
      throw new Error('WalletManager not initialized');
    }

    return this._sendTransactionWithRetry(transaction, 0);
  }

  /**
   * Send transaction with retry logic
   * @private
   * @async
   */
  async _sendTransactionWithRetry(transaction, attemptNumber) {
    try {
      console.log(`[WalletManager] Sending transaction (attempt ${attemptNumber + 1}):`, transaction);

      // Validate and normalize transaction
      const normalizedTx = this._normalizeTransaction(transaction);

      // Show to user for approval
      const result = await this.#tonConnectUI.sendTransaction(normalizedTx);

      if (!result || !result.boc) {
        throw new Error('Invalid transaction result: missing boc');
      }

      console.log('[WalletManager] Transaction sent successfully:', result);

      // Emit event
      this._emit('transaction', {
        hash: result.hash,
        boc: result.boc,
        exitCode: result.exitCode,
        status: 'sent',
      });

      return {
        hash: result.hash,
        boc: result.boc,
        exitCode: result.exitCode,
      };
    } catch (error) {
      console.error('[WalletManager] Transaction error:', error);

      // Retry logic
      if (attemptNumber < this.#RETRY_CONFIG.attempts) {
        const delay = this.#RETRY_CONFIG.delay * Math.pow(this.#RETRY_CONFIG.backoff, attemptNumber);
        console.log(`[WalletManager] Retrying after ${delay}ms...`);
        await new Promise((resolve) => setTimeout(resolve, delay));
        return this._sendTransactionWithRetry(transaction, attemptNumber + 1);
      }

      // User rejected or other non-retryable error
      if (error.message?.includes('user rejected')) {
        this._emit('error', {
          code: 'USER_REJECTED',
          message: 'User rejected the transaction',
        });
      } else {
        this._emit('error', {
          code: 'TRANSACTION_FAILED',
          message: error.message,
        });
      }

      throw error;
    }
  }

  /**
   * Normalize and validate transaction
   * @private
   */
  _normalizeTransaction(tx) {
    if (!tx.to) throw new Error('Transaction missing "to" field');
    if (!tx.value) throw new Error('Transaction missing "value" field');

    // Convert TON to nanoTON if needed
    let value = tx.value;
    if (typeof value === 'string') {
      value = parseFloat(value);
    }
    // Check if value is in TON (not nanoTON)
    if (value < 1000000) {
      // Likely in TON, convert to nanoTON
      value = Math.floor(value * 1e9).toString();
    } else {
      value = Math.floor(value).toString();
    }

    return {
      to: tx.to,
      value: value,
      payload: tx.payload || undefined,
      stateInit: tx.stateInit || undefined,
    };
  }

  /**
   * Get connected wallet info
   * @returns {Object|null}
   */
  getWallet() {
    return this.#walletState
      ? {
          address: this.#walletState.address,
          publicKey: this.#walletState.publicKey,
          chainId: this.#walletState.chainId,
        }
      : null;
  }

  /**
   * Check if wallet is connected
   * @returns {boolean}
   */
  isConnected() {
    return this.#walletState !== null && this.#walletState.address !== undefined;
  }

  /**
   * Get full wallet state (for advanced users)
   * @returns {Object|null}
   */
  getFullState() {
    return this.#walletState ? { ...this.#walletState } : null;
  }

  /**
   * Register event listener
   * @param {string} event - Event name (connected, disconnected, transaction, error)
   * @param {Function} callback
   */
  on(event, callback) {
    if (!this.#listeners.has(event)) {
      this.#listeners.set(event, []);
    }
    this.#listeners.get(event).push(callback);
    console.log(`[WalletManager] Registered listener for event: ${event}`);
  }

  /**
   * Unregister event listener
   * @param {string} event
   * @param {Function} callback
   */
  off(event, callback) {
    if (this.#listeners.has(event)) {
      const listeners = this.#listeners.get(event);
      const index = listeners.indexOf(callback);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
  }

  /**
   * Emit event to listeners
   * @private
   */
  _emit(event, data) {
    if (this.#listeners.has(event)) {
      this.#listeners.get(event).forEach((callback) => {
        try {
          callback(data);
        } catch (error) {
          console.error(`[WalletManager] Listener error for "${event}":`, error);
        }
      });
    }
  }

  /**
   * Get connection status string (for UI)
   * @returns {string}
   */
  getStatusString() {
    if (this.#isConnecting) return 'Connecting...';
    if (this.isConnected()) return `Connected - ${this.#walletState.address.slice(0, 6)}...${this.#walletState.address.slice(-6)}`;
    return 'Not Connected';
  }
}

// Export as module and attach to window
if (typeof module !== 'undefined' && module.exports) {
  module.exports = WalletManager;
}
window.WalletManager = WalletManager;
