/**
 * TON Connect Module
 * Independent TON wallet connection authentication
 * Does NOT require or depend on marketplace
 * @module js/tonconnect.js
 */

class TonConnectManager {
  constructor() {
    this.tonConnectUI = null;
    this.isInitialized = false;
    this.isReady = false;
    this.wallet = null;
    this.listeners = new Map();
  }

  /**
   * Initialize TonConnect UI independently
   * Can be called at any time without marketplace dependencies
   */
  async initialize(options = {}) {
    try {
      // Check if TonConnect library is loaded
      if (typeof TonConnectUI === 'undefined') {
        console.warn('⚠️  TonConnect UI SDK not loaded. Skipping initialization.');
        this.isReady = false;
        return false;
      }

      console.log('🔌 Initializing TON Connect (Independent)...');

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
        console.error('❌ Manifest validation failed:', manifestValidation.error);
        this.isReady = false;
        return false;
      }

      console.log('✓ Manifest valid:', manifestValidation.url);

      // Initialize TonConnect UI
      this.tonConnectUI = new TonConnectUI({
        manifestUrl: '/tonconnect-manifest.json',
        buttonRootId: 'tonconnect-button'
      });

      // Setup event listeners
      this.setupEventListeners();

      this.isInitialized = true;
      this.isReady = true;
      console.log('✅ TonConnect initialized successfully');

      // Emit custom event for other modules
      window.dispatchEvent(new CustomEvent('tonconnect:initialized', {
        detail: { ready: true }
      }));

      return true;
    } catch (error) {
      console.error('❌ TonConnect initialization failed:', error);
      this.isReady = false;
      
      // Emit error event
      window.dispatchEvent(new CustomEvent('tonconnect:error', {
        detail: { error: error.message }
      }));
      
      return false;
    }
  }

  /**
   * Validate manifest endpoint
   * @private
   */
  async validateManifest(retries = 3) {
    const manifestUrl = '/tonconnect-manifest.json';
    
    for (let attempt = 1; attempt <= retries; attempt++) {
      try {
        const response = await fetch(manifestUrl, { 
          method: 'GET',
          cache: 'no-cache'
        });
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const manifest = await response.json();
        
        if (!manifest.url) {
          throw new Error('Manifest missing "url" field');
        }
        
        console.log('✓ TonConnect manifest valid:', manifest.url);
        return { success: true, url: manifest.url };
      } catch (error) {
        console.warn(`Manifest validation attempt ${attempt}/${retries} failed:`, error.message);
        
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
        console.log('✅ Wallet connected:', wallet.account?.address);
        this.emit('wallet:connected', { wallet });
      } else {
        this.wallet = null;
        console.log('🔌 Wallet disconnected');
        this.emit('wallet:disconnected', {});
      }
    });
  }

  /**
   * Open TON Connect modal for wallet selection
   */
  async openModal() {
    if (!this.isReady || !this.tonConnectUI) {
      throw new Error('TonConnect is not ready');
    }

    try {
      console.log('🔓 Opening TonConnect modal...');
      const result = await this.tonConnectUI.openModal();
      
      if (!result || !result.account || !result.account.address) {
        console.log('❌ User cancelled connection');
        return null;
      }

      console.log('✓ Wallet selected:', result.account.address);
      this.wallet = result;
      return result;
    } catch (error) {
      console.error('Error opening modal:', error);
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
      console.log('🔌 Wallet disconnected');
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

      console.log('💸 Sending transaction...');
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
