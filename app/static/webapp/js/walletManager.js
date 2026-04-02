/**
 * ═══════════════════════════════════════════════════════════════════════════
 * WALLET MANAGER - PRODUCTION-GRADE TON WALLET SYSTEM
 * ═══════════════════════════════════════════════════════════════════════════
 * 
 * Single source of truth for wallet management across the entire app
 * 
 * Features:
 * ✅ Singleton pattern - one instance across all pages
 * ✅ Persistent session - restores on reload
 * ✅ Global transaction engine
 * ✅ Event system for state changes
 * ✅ Production-error handling
 * ✅ Zero external dependencies (uses existing TON Connect UI)
 * 
 * Global API:
 * - window.walletManager.connect() - Connect wallet
 * - window.walletManager.disconnect() - Disconnect wallet
 * - window.walletManager.isConnected() - Check connection status
 * - window.walletManager.getAddress() - Get wallet address
 * - window.walletManager.getWallet() - Get full wallet object
 * - window.walletManager.sendTransaction(tx) - Send transaction
 */

class WalletManager {
  static #instance = null;

  #tonConnectUI = null;
  #wallet = null;
  #address = null;
  #isConnecting = false;
  #listeners = new Map();
  #initialized = false;

  // Storage keys
  #STORAGE_KEYS = {
    WALLET_SESSION: 'ton_wallet_manager_session',
    WALLET_ADDRESS: 'ton_wallet_address',
    MANIFEST_URL: 'ton_manifest_url',
  };

  // Constants
  #MANIFEST_URL = null;
  #CHECK_CONNECT_INTERVAL = 500;
  #MAX_RETRIES = 3;
  #RETRY_DELAY = 1000;

  /**
   * Get singleton instance
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
    this.#setupManifestURL();
    this.#setupEventSystem();
    console.log('[WalletManager] Initialized');
  }

  /**
   * Setup manifest URL - must be full HTTPS
   * @private
   */
  #setupManifestURL() {
    try {
      const origin = window.location.origin;
      this.#MANIFEST_URL = `${origin}/tonconnect-manifest.json`;
      console.log('[WalletManager] Manifest URL:', this.#MANIFEST_URL);
    } catch (e) {
      console.error('[WalletManager] Failed to setup manifest URL:', e);
      this.#MANIFEST_URL = 'https://nftplatformbackend-production-ee5f.up.railway.app/tonconnect-manifest.json';
    }
  }

  /**
   * Setup event listener system
   * @private
   */
  #setupEventSystem() {
    this.#listeners.set('connected', []);
    this.#listeners.set('disconnected', []);
    this.#listeners.set('error', []);
    this.#listeners.set('transaction-sent', []);
  }

  /**
   * Initialize wallet system
   * Restores previous session if available
   * @returns {Promise<boolean>} - true if wallet is connected
   */
  async initialize() {
    if (this.#initialized) {
      return this.isConnected();
    }

    console.log('[WalletManager] Initializing...');

    try {
      // Wait for TON Connect UI library to load
      await this.#waitForTonConnectUI();

      // Create TON Connect UI instance
      this.#tonConnectUI = new window.TON_CONNECT_UI.TonConnectUI({
        manifestUrl: this.#MANIFEST_URL,
      });

      // Setup status listener
      this.#tonConnectUI.onStatusChange(async (wallet) => {
        await this.#handleWalletStatusChange(wallet);
      });

      // Try to restore previous session
      await this.#restoreSession();

      this.#initialized = true;
      console.log('[WalletManager] Initialized successfully');
      
      return this.isConnected();
    } catch (error) {
      console.error('[WalletManager] Initialization failed:', error);
      this.#emit('error', error);
      throw error;
    }
  }

  /**
   * Wait for TON Connect UI to load from CDN
   * @private
   */
  async #waitForTonConnectUI() {
    return new Promise((resolve, reject) => {
      const maxAttempts = 50;
      let attempts = 0;

      const checkLoaded = () => {
        if (window.TON_CONNECT_UI) {
          resolve();
        } else if (attempts < maxAttempts) {
          attempts++;
          setTimeout(checkLoaded, 100);
        } else {
          reject(new Error('TON Connect UI failed to load'));
        }
      };

      checkLoaded();
    });
  }

  /**
   * Handle wallet status changes from TON Connect
   * @private
   */
  async #handleWalletStatusChange(wallet) {
    if (wallet) {
      const address = wallet.account.address;
      this.#wallet = wallet;
      this.#address = address;

      // Save session
      await this.#saveSession(address);

      // Sync with backend
      await this.#syncWithBackend(address);

      // Emit event
      this.#emit('connected', { address, wallet });

      console.log('[WalletManager] Wallet connected:', address);
    } else {
      // Wallet disconnected
      this.#wallet = null;
      this.#address = null;
      this.#clearSession();

      // Emit event
      this.#emit('disconnected', {});

      console.log('[WalletManager] Wallet disconnected');
    }
  }

  /**
   * Restore session from storage
   * @private
   */
  async #restoreSession() {
    try {
      const stored = sessionStorage.getItem(this.#STORAGE_KEYS.WALLET_SESSION);
      if (stored) {
        const session = JSON.parse(stored);
        console.log('[WalletManager] Session restored from storage');
        this.#address = session.address;
        // Note: Full wallet object restored by TON Connect UI automatically
      }
    } catch (error) {
      console.warn('[WalletManager] Failed to restore session:', error);
    }
  }

  /**
   * Save session to storage
   * @private
   */
  async #saveSession(address) {
    try {
      sessionStorage.setItem(
        this.#STORAGE_KEYS.WALLET_SESSION,
        JSON.stringify({
          address,
          timestamp: Date.now(),
        })
      );
    } catch (error) {
      console.warn('[WalletManager] Failed to save session:', error);
    }
  }

  /**
   * Clear session from storage
   * @private
   */
  #clearSession() {
    sessionStorage.removeItem(this.#STORAGE_KEYS.WALLET_SESSION);
    sessionStorage.removeItem(this.#STORAGE_KEYS.WALLET_ADDRESS);
  }

  /**
   * Sync wallet with backend
   * @private
   */
  async #syncWithBackend(address) {
    try {
      const initData = window.Telegram?.WebApp?.initData || '';

      const response = await fetch('/api/v1/walletconnect/connect', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(initData && { 'X-Telegram-Init-Data': initData }),
        },
        body: JSON.stringify({
          wallet_address: address,
          blockchain: 'ton',
        }),
      });

      if (response.ok) {
        console.log('[WalletManager] Backend sync successful');
      } else {
        console.warn('[WalletManager] Backend sync failed:', response.status);
      }
    } catch (error) {
      console.warn('[WalletManager] Backend sync error:', error);
    }
  }

  /**
   * Connect wallet via TON Connect modal
   * @returns {Promise<{address, publicKey, wallet}>}
   */
  async connect() {
    if (this.#isConnecting) {
      throw new Error('Connection in progress');
    }

    if (!this.#tonConnectUI) {
      throw new Error('Wallet manager not initialized. Call initialize() first');
    }

    this.#isConnecting = true;

    try {
      console.log('[WalletManager] Opening wallet modal...');
      const wallet = await this.#tonConnectUI.connectWallet();

      if (wallet) {
        this.#wallet = wallet;
        this.#address = wallet.account.address;
        await this.#saveSession(this.#address);
        await this.#syncWithBackend(this.#address);
        this.#emit('connected', { address: this.#address, wallet });
        console.log('[WalletManager] Connected:', this.#address);
      }

      return {
        address: this.#address,
        publicKey: wallet?.account?.publicKey,
        wallet: wallet,
      };
    } catch (error) {
      if (error.message !== 'User declined') {
        console.error('[WalletManager] Connection error:', error);
        this.#emit('error', error);
      }
      throw error;
    } finally {
      this.#isConnecting = false;
    }
  }

  /**
   * Disconnect wallet
   * @returns {Promise<void>}
   */
  async disconnect() {
    if (!this.#tonConnectUI) {
      throw new Error('Wallet manager not initialized');
    }

    try {
      console.log('[WalletManager] Disconnecting wallet...');
      await this.#tonConnectUI.disconnect();
      this.#wallet = null;
      this.#address = null;
      this.#clearSession();
      this.#emit('disconnected', {});
      console.log('[WalletManager] Disconnected');
    } catch (error) {
      console.error('[WalletManager] Disconnect error:', error);
      this.#emit('error', error);
      throw error;
    }
  }

  /**
   * Check if wallet is connected
   * @returns {boolean}
   */
  isConnected() {
    return !!this.#address;
  }

  /**
   * Get wallet address
   * @returns {string|null}
   */
  getAddress() {
    return this.#address;
  }

  /**
   * Get full wallet object
   * @returns {Object|null}
   */
  getWallet() {
    return this.#wallet;
  }

  /**
   * Get formatted address (shortened for UI)
   * @returns {string|null}
   */
  getFormattedAddress() {
    if (!this.#address) return null;
    return this.#address.slice(0, 10) + '...' + this.#address.slice(-6);
  }

  /**
   * ═══════════════════════════════════════════════════════════════════════════
   * TRANSACTION ENGINE - CRITICAL COMPONENT
   * ═══════════════════════════════════════════════════════════════════════════
   * 
   * Send transactions on TON blockchain
   * Handles all Web3 operations: transfers, minting, marketplace actions
   */

  /**
   * Send transaction to TON blockchain
   * 
   * @param {Object} params
   * @param {string} params.to - Destination address
   * @param {string|number} params.amount - Amount in TON (will convert to nanoTON)
   * @param {string} [params.payload] - Message payload (base64 or Uint8Array)
   * @param {string} [params.stateInit] - Contract state init (base64 or Uint8Array)
   * @param {Object} [params.metadata] - Optional metadata for tracking
   * 
   * @returns {Promise<{hash, boc, exitCode}>}
   */
  async sendTransaction(params) {
    if (!this.#tonConnectUI) {
      throw new Error('Wallet manager not initialized');
    }

    if (!this.isConnected()) {
      throw new Error('Wallet not connected. Call connect() first');
    }

    const { to, amount, payload, stateInit, metadata } = params;

    try {
      console.log('[WalletManager] Sending transaction...', { to, amount, metadata });

      // Validate required fields
      if (!to) throw new Error('Destination address required');
      if (amount === undefined && amount === null) throw new Error('Amount required');

      // Build transaction with nanoTON conversion
      const transaction = {
        validUntil: Math.floor(Date.now() / 1000) + 600, // 10 minutes
        messages: [
          {
            address: to,
            amount: this.#convertTONToNanoTON(amount),
            ...(payload && { payload }),
            ...(stateInit && { init: stateInit }),
          },
        ],
      };

      console.log('[WalletManager] Transaction payload:', transaction);

      // Send via TON Connect with retry logic
      const result = await this.#sendWithRetry(transaction);

      console.log('[WalletManager] Transaction successful:', result);

      // Emit event
      this.#emit('transaction-sent', {
        hash: result.boc,
        to,
        amount,
        metadata,
      });

      return result;
    } catch (error) {
      console.error('[WalletManager] Transaction failed:', error);
      this.#emit('error', error);
      throw error;
    }
  }

  /**
   * Send transaction with retry logic
   * @private
   */
  async #sendWithRetry(transaction) {
    let lastError;

    for (let attempt = 1; attempt <= this.#MAX_RETRIES; attempt++) {
      try {
        console.log(
          `[WalletManager] Transaction attempt ${attempt}/${this.#MAX_RETRIES}`
        );
        return await this.#tonConnectUI.sendTransaction(transaction);
      } catch (error) {
        lastError = error;
        console.warn(
          `[WalletManager] Attempt ${attempt} failed:`,
          error.message
        );

        if (attempt < this.#MAX_RETRIES) {
          await this.#delay(this.#RETRY_DELAY);
        }
      }
    }

    throw new Error(
      `Transaction failed after ${this.#MAX_RETRIES} attempts: ${lastError.message}`
    );
  }

  /**
   * Convert TON to nanoTON
   * @private
   */
  #convertTONToNanoTON(ton) {
    const nanoTonPerTon = BigInt(1000000000);
    const tonBigInt = BigInt(Math.floor(Number(ton) * 1000000000));
    return tonBigInt.toString();
  }

  /**
   * Delay helper for retry logic
   * @private
   */
  #delay(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * ═══════════════════════════════════════════════════════════════════════════
   * EVENT SYSTEM
   * ═══════════════════════════════════════════════════════════════════════════
   */

  /**
   * Listen to wallet events
   * @param {string} event - Event name: 'connected', 'disconnected', 'error', 'transaction-sent'
   * @param {Function} callback - Callback function
   */
  on(event, callback) {
    if (!this.#listeners.has(event)) {
      this.#listeners.set(event, []);
    }
    this.#listeners.get(event).push(callback);

    // Return unsubscribe function
    return () => {
      const callbacks = this.#listeners.get(event);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    };
  }

  /**
   * Emit event to all listeners
   * @private
   */
  #emit(event, data) {
    if (!this.#listeners.has(event)) return;

    const callbacks = this.#listeners.get(event);
    callbacks.forEach((callback) => {
      try {
        callback(data);
      } catch (error) {
        console.error(`[WalletManager] Event handler error (${event}):`, error);
      }
    });
  }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = WalletManager;
}
