/**

 * @module js/tonconnect.js
 */

class TonConnectManager {
  constructor() {
    this.tonConnectUI = null;
    this.isInitialized = false;
    this.isReady = false;
    this.wallet = null;
    this.listeners = new Map();
    this.initPromise = null;  // Track initialization promise for race condition handling
    this.modalQueue = [];      // Queue for modal reque
    this.initializationAborted = false;
  }

  getManifestUrl() {
    try {
      return new URL('/tonconnect-manifest.json', window.location.href).href;
    } catch (e) {
      const origin = window.location && window.location.origin ? window.location.origin : '';
      return (origin ? origin.replace(/\/+$/,'') : '') + '/tonconnect-manifest.json';
    }
  }

  /**
   * Initialize TonConnect UI independently
   * Can be called at any time without marketplace dependencies
   * Returns: Promise that resolves when initialization completes
   */
  initialize(options = {}) {
    // Return existing promise if already initializing/initialized
    if (this.initPromise) {
      console.log('TonConnect initialization already in progress, returning existing promise');
      return this.initPromise;
    }
    
    this.initPromise = this._performInitialization(options);
    return this.initPromise;
  }

  /**
   * Actual initialization logic (private)
   */
  async _performInitialization(options = {}) {
    try {
      // Check if TonConnect library is loaded
      if (typeof TonConnectUI === 'undefined') {
        console.error('TonConnect UI SDK NOT loaded. typeof TonConnectUI:', typeof TonConnectUI);
        console.log('Window keys containing "ton":', Object.keys(window).filter(k => k.toLowerCase().includes('ton')));
        this.isReady = false;
        return false;
      }

      console.log('TonConnectUI library found:', typeof TonConnectUI);
      console.log('Initializing TON Connect (Independent)...');

      // Create root element if needed
      let rootElement = document.getElementById('tonconnect-button');
      if (!rootElement) {
        rootElement = document.createElement('div');
        rootElement.id = 'tonconnect-button';
        document.body.appendChild(rootElement);
      }

      // Validate manifest is accessible
      const manifestValidation = await this.validateManifest();
      if (!manifestValidation.success) {
        console.error('Manifest validation failed:', manifestValidation.error);
        this.isReady = false;
        return false;
      }

      console.log('Manifest valid:', manifestValidation.url);

      // Initialize TonConnect UI
      const manifestUrl = this.getManifestUrl();
      console.log('Instantiating TonConnectUI with config:', {
        manifestUrl,
        buttonRootId: 'tonconnect-button'
      });
      
      this.tonConnectUI = new TonConnectUI({
        manifestUrl,
        buttonRootId: 'tonconnect-button'
      });
      
      console.log('TonConnectUI instance created:', this.tonConnectUI);

      // Setup event listeners
      this.setupEventListeners();

      this.isInitialized = true;
      this.isReady = true;
      console.log('TonConnect initialized successfully - isReady:', this.isReady);

      // Emit custom event for other modules
      window.dispatchEvent(new CustomEvent('tonconnect:initialized', {
        detail: { ready: true }
      }));

      // After successful initialization, process any queued modal requests
      this._processModalQueue();
      
      return true;
    } catch (error) {
      console.error(' TonConnect initialization failed:', error);
      this.isReady = false;
      this.initializationAborted = true;
      
      // Reject any queued modal requests
      this.modalQueue.forEach(({ reject }) => {
        reject(new Error('TonConnect initialization failed: ' + error.message));
      });
      this.modalQueue = [];
      
      // Emit error event
      window.dispatchEvent(new CustomEvent('tonconnect:error', {
        detail: { error: error.message }
      }));
      
      return false;
    }
  }

  /**
   * Process any modal requests that were queued during initialization
   * @private
   */
  _processModalQueue() {
    if (this.modalQueue.length === 0) return;
    
    console.log(`Processing ${this.modalQueue.length} queued modal requests...`);
    const queue = [...this.modalQueue];
    this.modalQueue = [];
    
    queue.forEach(async ({ resolve, reject }) => {
      try {
        const result = await this.openModal();
        resolve(result);
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Validate manifest endpoint
   * @private
   */
  async validateManifest(retries = 3) {
    const manifestUrl = this.getManifestUrl();
    
    for (let attempt = 1; attempt <= retries; attempt++) {
      try {
        console.log(`Manifest validation attempt ${attempt}/${retries}...`);
        const response = await fetch(manifestUrl, { 
          method: 'GET',
          cache: 'no-cache'
        });
        
        console.log(`Manifest response status: ${response.status}`);
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const manifest = await response.json();
        console.log('Manifest parsed:', manifest);
        
        if (!manifest.url) {
          throw new Error('Manifest missing "url" field');
        }
        
        console.log('TonConnect manifest valid:', manifest.url);
        return { success: true, url: manifest.url };
      } catch (error) {
        console.error(`Manifest validation attempt ${attempt}/${retries} failed:`, error.message, error);
        
        if (attempt < retries) {
          await new Promise(r => setTimeout(r, Math.pow(2, attempt) * 100)); // exponential backoff
        }
      }
    }
    
    return { 
      success: false, 
      error: 'Failed to validate manifest after retries'
    };
  }

  /**
   * Setup TonConnect event listeners
   * @private
   */
  setupEventListeners() {
    if (!this.tonConnectUI) return;

    // Listen for wallet status changes
        this.tonConnectUI.onStatusChange((wallet) => {
      if (wallet) {
        this.wallet = wallet;
            console.log('Wallet connected:', wallet.account?.address);
        this.emit('wallet:connected', { wallet });
      } else {
        this.wallet = null;
            console.log('Wallet disconnected');
        this.emit('wallet:disconnected', {});
      }
    });
  }

  /**
   * Open TON Connect modal for wallet selection
   * Handles race condition by queuing requests if still initializing
   */
  async openModal() {
    // If still initializing, queue the request
    if (this.initPromise && !this.isReady) {
      console.log(' TonConnect still initializing... Queueing modal request');
      return new Promise((resolve, reject) => {
        this.modalQueue.push({ resolve, reject });
        // Wait for initialization to complete before retrying
        this.initPromise.then(() => {
          if (this.isReady) {
            console.log('Initialization complete, opening queued modal...');
            this.openModal().then(resolve).catch(reject);
          } else {
            reject(new Error('TonConnect initialization failed'));
          }
        }).catch(reject);
      });
    }
    
    // If not initialized at all, try initializing first
    if (!this.isReady && !this.tonConnectUI) {
      console.log('TonConnect not initialized, attempting initialization...');
      const initialized = await this.initialize();
      if (!initialized) {
        throw new Error('Failed to initialize TonConnect');
      }
    }
    
    // Now open the modal
    if (!this.isReady || !this.tonConnectUI) {
      throw new Error('TonConnect is not ready - initialization may have failed');
    }

    try {
      console.log('About to call tonConnectUI.openModal()...');
      console.log('tonConnectUI state:', {
        exists: !!this.tonConnectUI,
        hasOpenModal: !!this.tonConnectUI?.openModal,
        type: typeof this.tonConnectUI
      });
      
      const result = await this.tonConnectUI.openModal();
      
      console.log('openModal returned, result:', result);
      
      if (!result || !result.account || !result.account.address) {
        console.log('User cancelled connection or no wallet selected');
        return null;
      }

      console.log('Wallet selected:', result.account.address);
      this.wallet = result;
      return result;
    } catch (error) {
      console.error('Error opening modal:', error, error.stack);
      throw error;
    }
  }

  /**
   * Get current connected wallet
   */
  getWallet() {
    return this.wallet;
  }

  /**
   * Check if wallet is connected
   */
  isConnected() {
    return !!this.wallet && !!this.wallet.account?.address;
  }

  /**
   * Get connected wallet address
   */
  getWalletAddress() {
    return this.wallet?.account?.address || null;
  }

  /**
   * Disconnect wallet
   */
  async disconnect() {
    if (!this.tonConnectUI) return;

    try {
      await this.tonConnectUI.disconnect();
      this.wallet = null;
      console.log('Wallet disconnected');
      this.emit('wallet:disconnected', {});
    } catch (error) {
      console.error('Error disconnecting wallet:', error);
    }
  }

  /**
   * Send transaction (requires connected wallet)
   */
  async sendTransaction(transaction) {
    if (!this.isConnected()) {
      throw new Error('Wallet not connected');
    }

    try {
      if (!this.tonConnectUI.connector) {
        throw new Error('TonConnect connector not available');
      }

      console.log(' Sending transaction...');
      const result = await this.tonConnectUI.connector.sendTransaction(transaction, {
        modals: 'all',
        notifications: ['in-app']
      });

      console.log('✓ Transaction sent:', result);
      return result;
    } catch (error) {
      console.error('Error sending transaction:', error);
      throw error;
    }
  }

  /**
   * Wait for initialization to complete (helper for other modules)
   */
  async waitForReady() {
    if (this.isReady) return true;
    if (this.initializationAborted) return false;
    
    if (this.initPromise) {
      return await this.initPromise;
    }
    
    // No initialization in progress, try initializing
    return await this.initialize();
  }

  /**
   * Event system for other modules
   */
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  off(event, callback) {
    if (!this.listeners.has(event)) return;
    const callbacks = this.listeners.get(event);
    const index = callbacks.indexOf(callback);
    if (index > -1) callbacks.splice(index, 1);
  }

  emit(event, data) {
    if (!this.listeners.has(event)) return;
    this.listeners.get(event).forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        console.error(`Error in listener for event '${event}':`, error);
      }
    });
  }
}

export const tonConnect = new TonConnectManager();
