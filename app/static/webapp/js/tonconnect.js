/**
 * TonConnectManager - Singleton TON wallet connection manager
 * 
 * CRITICAL SAFEGUARDS:
 * - Singleton pattern prevents multiple instances
 * - Modal queue prevents recursive openModal calls
 * - Guard flag prevents multiple listener attachments
 * - All async operations wrapped in try/catch
 * - No window.location or tg.close() at init
 * 
 * @module js/tonconnect.js
 */

class TonConnectManager {
  constructor() {
    // Prevent multiple instances
    if (TonConnectManager.instance) {
      return TonConnectManager.instance;
    }

    this.tonConnectUI = null;
    this.isInitialized = false;
    this.isReady = false;
    this.wallet = null;
    this.listeners = new Map();
    this.initPromise = null;
    this.modalQueue = [];
    this.modalInProgress = false; // Guard against recursive modal calls
    this.listenersAttached = false; // Guard against multiple listener attachments
    this.initializationAborted = false;

    // Mark this as the singleton instance
    TonConnectManager.instance = this;
  }

  /**
   * Get manifest URL for TonConnect
   * @private
   */
  getManifestUrl() {
    try {
      const url = new URL('/tonconnect-manifest.json', window.location.href).href;
      console.log('[TonConnect] Manifest URL:', url);
      return url;
    } catch (e) {
      const origin = window.location?.origin || '';
      const fallbackUrl = (origin ? origin.replace(/\/+$/, '') : '') + '/tonconnect-manifest.json';
      console.log('[TonConnect] Using fallback manifest URL:', fallbackUrl);
      return fallbackUrl;
    }
  }

  /**
   * Initialize TonConnect UI
   * Safe: Returns existing promise if already initializing
   * 
   * @param {Object} options - Initialization options
   * @returns {Promise<boolean>} true if ready, false if failed
   */
  initialize(options = {}) {
    // Return existing promise if already initializing
    if (this.initPromise) {
      console.log('[TonConnect] Already initializing, returning existing promise');
      return this.initPromise;
    }

    // Already initialized successfully
    if (this.isReady) {
      console.log('[TonConnect] Already initialized');
      return Promise.resolve(true);
    }

    // Start initialization
    this.initPromise = this._performInitialization(options);
    return this.initPromise;
  }

  /**
   * Actual initialization logic
   * @private
   */
  async _performInitialization(options = {}) {
    try {
      // ⚠️ CRITICAL: Ensure Telegram WebApp is ready before proceeding
      console.log('[TonConnect] Waiting for Telegram WebApp to be ready...');
      let telegramReady = false;
      let telegramAttempts = 0;
      
      while (!telegramReady && telegramAttempts < 20) {
        if (window.Telegram?.WebApp?.initData) {
          console.log('[TonConnect] ✅ Telegram WebApp is ready with initData');
          telegramReady = true;
          break;
        }
        telegramAttempts++;
        await new Promise(r => setTimeout(r, 100));
      }
      
      if (!telegramReady) {
        console.warn('[TonConnect] ⚠️ Telegram WebApp not ready yet, continuing anyway...');
      }

      // Check if TonConnect library is loaded
      if (typeof TonConnectUI === 'undefined') {
        console.error('[TonConnect] TonConnectUI library not loaded');
        this.isReady = false;
        return false;
      }

      console.log('[TonConnect] Starting initialization...');

      // Create root element for TonConnect button
      let rootElement = document.getElementById('tonconnect-button');
      if (!rootElement) {
        rootElement = document.createElement('div');
        rootElement.id = 'tonconnect-button';
        rootElement.style.display = 'none'; // Hidden by default
        document.body.appendChild(rootElement);
      }

      // Validate manifest endpoint
      const manifestValidation = await this.validateManifest();
      if (!manifestValidation.success) {
        console.error('[TonConnect] Manifest validation failed:', manifestValidation.error);
        this.isReady = false;
        return false;
      }

      console.log('[TonConnect] Manifest validated:', manifestValidation.url);

      // Initialize TonConnectUI
      const manifestUrl = this.getManifestUrl();
      try {
        this.tonConnectUI = new TonConnectUI({
          manifestUrl,
          buttonRootId: 'tonconnect-button'
        });
      } catch (error) {
        console.error('[TonConnect] Failed to instantiate TonConnectUI:', error);
        this.isReady = false;
        return false;
      }

      console.log('[TonConnect] TonConnectUI instance created');

      // Setup event listeners (only once)
      this.setupEventListeners();

      this.isInitialized = true;
      this.isReady = true;
      console.log('[TonConnect] Initialization successful');

      // Emit custom event
      try {
        window.dispatchEvent(new CustomEvent('tonconnect:initialized', {
          detail: { ready: true }
        }));
      } catch (error) {
        console.warn('[TonConnect] Event dispatch failed:', error);
      }

      // Process any queued modal requests
      this._processModalQueue();

      return true;

    } catch (error) {
      console.error('[TonConnect] Initialization failed:', error);
      this.isReady = false;
      this.initializationAborted = true;

      // Reject queued modal requests
      this.modalQueue.forEach(({ reject }) => {
        try {
          reject(new Error('TonConnect initialization failed: ' + error.message));
        } catch (e) {
          console.warn('[TonConnect] Failed to reject queued modal:', e);
        }
      });
      this.modalQueue = [];

      // Emit error event
      try {
        window.dispatchEvent(new CustomEvent('tonconnect:error', {
          detail: { error: error.message }
        }));
      } catch (error) {
        console.warn('[TonConnect] Error event dispatch failed:', error);
      }

      return false;
    }
  }

  /**
   * Process modal requests queued during initialization
   * @private
   */
  _processModalQueue() {
    if (this.modalQueue.length === 0) return;

    console.log(`[TonConnect] Processing ${this.modalQueue.length} queued modal requests`);
    const queue = [...this.modalQueue];
    this.modalQueue = [];

    queue.forEach(({ resolve, reject }) => {
      this._openModalSafe()
        .then(resolve)
        .catch(reject);
    });
  }

  /**
   * Validate manifest endpoint
   * @private
   */
  async validateManifest(retries = 2) {
    const manifestUrl = this.getManifestUrl();

    for (let attempt = 1; attempt <= retries; attempt++) {
      try {
        console.log(`[TonConnect] Validating manifest (${attempt}/${retries}): ${manifestUrl}`);
        const response = await fetch(manifestUrl, {
          method: 'GET',
          cache: 'no-cache',
          signal: AbortSignal.timeout?.(5000), // 5 second timeout
        });

        console.log(`[TonConnect] Manifest response status: ${response.status}`);
        if (!response.ok) {
          throw new Error(`HTTP ${response.status} ${response.statusText}`);
        }

        const manifest = await response.json();
        console.log('[TonConnect] Manifest loaded, checking url field...');
        if (!manifest.url) {
          throw new Error('Manifest missing "url" field');
        }

        console.log('[TonConnect] ✅ Manifest valid, app URL:', manifest.url);
        return { success: true, url: manifest.url };

      } catch (error) {
        console.warn(`[TonConnect] Validation attempt ${attempt}/${retries} failed:`, error.message);

        // Exponential backoff before retry
        if (attempt < retries) {
          const delay = Math.pow(2, attempt) * 100;
          console.log(`[TonConnect] Retrying in ${delay}ms...`);
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }

    console.error('[TonConnect] ❌ Manifest validation failed after all retries');
    return {
      success: false,
      error: 'Manifest validation failed after retries. Manifest URL may be incorrect or server unreachable.'
    };
  }

  /**
   * Setup TonConnect event listeners (only once)
   * @private
   */
  setupEventListeners() {
    // Guard against multiple listener attachments
    if (this.listenersAttached || !this.tonConnectUI) {
      return;
    }
    this.listenersAttached = true;

    try {
      // Listen for wallet status changes (only attach once)
      if (typeof this.tonConnectUI.onStatusChange === 'function') {
        this.tonConnectUI.onStatusChange((wallet) => {
          try {
            if (wallet) {
              this.wallet = wallet;
              console.log('[TonConnect] Wallet connected:', wallet.account?.address);
              this.emit('wallet:connected', { wallet });
            } else {
              this.wallet = null;
              console.log('[TonConnect] Wallet disconnected');
              this.emit('wallet:disconnected', {});
            }
          } catch (error) {
            console.error('[TonConnect] Error in wallet status handler:', error);
          }
        });
      }
    } catch (error) {
      console.error('[TonConnect] Failed to setup event listeners:', error);
      this.listenersAttached = false;
    }
  }

  /**
   * Safe internal modal opening (no recursion guard)
   * @private
   */
  async _openModalSafe() {
    if (!this.isReady || !this.tonConnectUI) {
      throw new Error('TonConnect is not ready');
    }

    try {
      console.log('[TonConnect] Opening wallet selection modal...');
      const result = await this.tonConnectUI.openModal();

      if (!result || !result.account?.address) {
        console.log('[TonConnect] Modal closed or no wallet selected');
        return null;
      }

      console.log('[TonConnect] Wallet selected:', result.account.address);
      this.wallet = result;
      return result;

    } catch (error) {
      console.error('[TonConnect] Modal error:', error);
      throw error;
    }
  }

  /**
   * Open TON Connect modal for wallet selection
   * Safe: Prevents recursive calls via guard flag
   * 
   * @returns {Promise} Resolves with wallet selection result or null if cancelled
   */
  async openModal() {
    // Guard against recursive calls
    if (this.modalInProgress) {
      console.log('[TonConnect] Modal already opening, queuing request');
      return new Promise((resolve, reject) => {
        this.modalQueue.push({ resolve, reject });
      });
    }

    try {
      // If still initializing, queue the request
      if (this.initPromise && !this.isReady) {
        console.log('[TonConnect] Still initializing, queuing modal request');
        return new Promise((resolve, reject) => {
          this.modalQueue.push({ resolve, reject });
          this.initPromise
            .then((success) => {
              if (success && this.isReady) {
                // Initialization complete, open modal
                this._openModalSafe()
                  .then(result => {
                    // Find and resolve this specific request
                    const index = this.modalQueue.findIndex(q => {
                      return q.resolve === resolve;
                    });
                    if (index !== -1) {
                      resolve(result);
                      this.modalQueue.splice(index, 1);
                    }
                  })
                  .catch(reject);
              } else {
                reject(new Error('TonConnect initialization failed'));
              }
            })
            .catch(reject);
        });
      }

      // If not initialized, initialize first
      if (!this.isReady) {
        console.log('[TonConnect] Not initialized, starting initialization...');
        const initialized = await this.initialize();
        if (!initialized) {
          throw new Error('Failed to initialize TonConnect');
        }
      }

      // Now open the modal
      this.modalInProgress = true;
      return await this._openModalSafe();

    } catch (error) {
      console.error('[TonConnect] Error opening modal:', error);
      throw error;
    } finally {
      this.modalInProgress = false;
    }
  }

  /**
   * Get current connected wallet
   * @returns {Object|null} Wallet object or null
   */
  getWallet() {
    return this.wallet;
  }

  /**
   * Check if wallet is connected
   * @returns {boolean}
   */
  isConnected() {
    return !!(this.wallet && this.wallet.account?.address);
  }

  /**
   * Get connected wallet address
   * @returns {string|null} Wallet address or null
   */
  getWalletAddress() {
    return this.wallet?.account?.address || null;
  }

  /**
   * Disconnect wallet
   * Safe error handling
   */
  async disconnect() {
    if (!this.tonConnectUI) {
      console.log('[TonConnect] Not initialized, nothing to disconnect');
      return;
    }

    try {
      await this.tonConnectUI.disconnect();
      this.wallet = null;
      console.log('[TonConnect] Wallet disconnected');
      this.emit('wallet:disconnected', {});
    } catch (error) {
      console.error('[TonConnect] Error disconnecting:', error);
      // Continue anyway - clear local state
      this.wallet = null;
      this.emit('wallet:disconnected', {});
    }
  }

  /**
   * Send transaction (requires connected wallet)
   * Safe error handling
   */
  async sendTransaction(transaction) {
    if (!this.isConnected()) {
      throw new Error('Wallet not connected');
    }

    try {
      if (!this.tonConnectUI?.connector) {
        throw new Error('TonConnect connector not available');
      }

      console.log('[TonConnect] Sending transaction...');
      const result = await this.tonConnectUI.connector.sendTransaction(transaction, {
        modals: 'all',
        notifications: ['in-app']
      });

      console.log('[TonConnect] Transaction sent successfully');
      return result;

    } catch (error) {
      console.error('[TonConnect] Transaction error:', error);
      throw error;
    }
  }

  /**
   * Wait for initialization to complete
   * Useful for other modules waiting on TonConnect
   * 
   * @returns {Promise<boolean>} true if ready, false if failed
   */
  async waitForReady() {
    if (this.isReady) return true;
    if (this.initializationAborted) return false;

    if (this.initPromise) {
      return await this.initPromise;
    }

    // No initialization in progress, start one
    return await this.initialize();
  }

  /**
   * Custom event system for other modules
   * @param {string} event - Event name
   * @param {Function} callback - Callback function
   */
  on(event, callback) {
    if (typeof callback !== 'function') return;
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  /**
   * Remove event listener
   * @param {string} event - Event name
   * @param {Function} callback - Callback function to remove
   */
  off(event, callback) {
    if (!this.listeners.has(event)) return;
    const callbacks = this.listeners.get(event);
    const index = callbacks.indexOf(callback);
    if (index > -1) {
      callbacks.splice(index, 1);
    }
  }

  /**
   * Emit custom event
   * Safe: Catches exceptions in listeners
   * @private
   */
  emit(event, data) {
    if (!this.listeners.has(event)) return;
    this.listeners.get(event).forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        console.error(`[TonConnect] Error in listener for '${event}':`, error);
      }
    });
  }

  /**
   * Destroy manager (cleanup)
   */
  destroy() {
    try {
      this.modalQueue = [];
      this.listeners.clear();
      this.wallet = null;
      this.tonConnectUI = null;
      this.isReady = false;
      this.isInitialized = false;
      TonConnectManager.instance = null;
      console.log('[TonConnect] Manager destroyed');
    } catch (error) {
      console.error('[TonConnect] Error during cleanup:', error);
    }
  }
}

// Create singleton instance
export const tonConnect = new TonConnectManager();

export default tonConnect;
