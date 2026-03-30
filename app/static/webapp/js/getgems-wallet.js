/**
 * GetGems-style Wallet Connection
 * 
 * GetGems uses a sophisticated wallet detection + deep-linking system
 * This implementation follows GetGems patterns:
 * - Native wallet detection (TonHub, TonKeeper, Ledger)
 * - Fallback to TonConnect v2
 * - Deep linking for direct transactions
 * - Auto-reconnect on page load
 */

class GetGemsWallet {
  constructor() {
    this.wallet = null;
    this.account = null;
    this.walletType = null; // 'tonhub', 'tonkeeper', 'tonwallet', 'ledger', 'tonconnect'
    this.isConnected = false;
    this.requestId = null;
    this.bridge = null;
    this.listeners = {};
    
    // GetGems bridge detection
    this.TonHub = window.TonHub;
    this.TonKeeper = window.ton; // TonKeeper injects ton object
    this.isTMA = window.Telegram?.WebApp;
  }

  /**
   * Initialize and detect available wallets
   */
  async init() {
    console.log('[GetGemsWallet] Initializing wallet detection...');
    
    try {
      // Check for native wallets
      await this.detectNativeWallets();
      
      // Restore previous connection
      await this.restoreConnection();
      
      // Fallback to TonConnect
      if (!this.isConnected) {
        await this.initTonConnect();
      }
      
      this.emit('ready');
      return true;
    } catch (error) {
      console.error('[GetGemsWallet] Init error:', error);
      this.emit('error', error);
      return false;
    }
  }

  /**
   * Detect available native wallets (TonHub, TonKeeper, TON Wallet)
   */
  async detectNativeWallets() {
    console.log('[GetGemsWallet] Detecting native wallets...');
    
    // 1. Check for TonHub (popular bridge)
    if (window.TonHub) {
      console.log('[GetGemsWallet] TonHub detected');
      this.walletType = 'tonhub';
      this.bridge = window.TonHub;
      return;
    }
    
    // 2. Check for TonKeeper (injects ton object)
    if (window.ton?.isTonkeeper) {
      console.log('[GetGemsWallet] TonKeeper detected');
      this.walletType = 'tonkeeper';
      this.bridge = window.ton;
      return;
    }
    
    // 3. Check for generic TON wallet (Chrome extension)
    if (window.ton && typeof window.ton.send === 'function') {
      console.log('[GetGemsWallet] Generic TON wallet detected');
      this.walletType = 'tonwallet';
      this.bridge = window.ton;
      return;
    }

    // 4. Check for Ledger (hardened)
    if (this.isTMA && navigator.userAgent.includes('Ledger')) {
      console.log('[GetGemsWallet] Ledger wallet detected');
      this.walletType = 'ledger';
      return;
    }
    
    console.log('[GetGemsWallet] No native wallet detected, will use TonConnect');
  }

  /**
   * Restore previous wallet connection from localStorage
   */
  async restoreConnection() {
    try {
      const stored = localStorage.getItem('getgems_wallet_session');
      if (!stored) return;
      
      const session = JSON.parse(stored);
      const now = Date.now();
      
      // Check if session is still valid (24 hours)
      if (now - session.timestamp > 24 * 60 * 60 * 1000) {
        localStorage.removeItem('getgems_wallet_session');
        return;
      }
      
      console.log('[GetGemsWallet] Restoring session:', session.address);
      this.account = session.account;
      this.isConnected = true;
      this.walletType = session.walletType;
      this.emit('connected', session.account);
      
    } catch (error) {
      console.warn('[GetGemsWallet] Failed to restore session:', error);
      localStorage.removeItem('getgems_wallet_session');
    }
  }

  /**
   * Connect wallet - GetGems style
   * Tries native wallets first, then falls back to TonConnect
   */
  async connect() {
    console.log('[GetGemsWallet] Starting connection flow...');
    
    if (this.isConnected) {
      console.log('[GetGemsWallet] Already connected');
      return this.account;
    }

    try {
      // Try native wallet connection
      if (this.bridge) {
        return await this.connectNativeWallet();
      }
      
      // Fallback to TonConnect
      return await this.connectTonConnect();
      
    } catch (error) {
      console.error('[GetGemsWallet] Connection failed:', error);
      this.emit('error', error);
      throw error;
    }
  }

  /**
   * Connect using native wallet bridge
   */
  async connectNativeWallet() {
    console.log('[GetGemsWallet] Connecting to native wallet:', this.walletType);
    
    try {
      let account;
      
      switch (this.walletType) {
        case 'tonhub':
          account = await this.connectTonHub();
          break;
        case 'tonkeeper':
        case 'tonwallet':
          account = await this.connectTonBridge();
          break;
        case 'ledger':
          account = await this.connectLedger();
          break;
        default:
          throw new Error('Unknown wallet type');
      }
      
      if (account) {
        this.account = account;
        this.isConnected = true;
        this.saveSession();
        this.emit('connected', account);
        return account;
      }
      
    } catch (error) {
      console.error('[GetGemsWallet] Native wallet connection failed:', error);
      // Try fallback
      return await this.connectTonConnect();
    }
  }

  /**
   * TonHub connection
   */
  async connectTonHub() {
    console.log('[GetGemsWallet] Connecting TonHub...');
    
    try {
      const isAvailable = await this.TonHub.isAvailable();
      if (!isAvailable) {
        throw new Error('TonHub not available');
      }

      this.requestId = this.TonHub.getSessionId();
      
      // Get wallet address
      const wallet = await this.TonHub.getWalletInfo();
      
      return {
        address: wallet.address,
        chain: wallet.network === 0 ? 'mainnet' : 'testnet',
        publicKey: wallet.publicKey,
        walletType: 'tonhub'
      };
      
    } catch (error) {
      console.error('[GetGemsWallet] TonHub error:', error);
      throw error;
    }
  }

  /**
   * Generic TON bridge connection (TonKeeper, TON Wallet)
   */
  async connectTonBridge() {
    console.log('[GetGemsWallet] Connecting TON bridge...');
    
    try {
      // Request RPC contract address
      const result = await this.bridge.send('ton_requestAccounts');
      
      if (!result || result.length === 0) {
        throw new Error('No wallet selected');
      }

      const address = result[0];
      
      return {
        address: address,
        chain: this.isTMA ? 'mainnet' : 'testnet',
        walletType: this.walletType
      };
      
    } catch (error) {
      console.error('[GetGemsWallet] TON bridge error:', error);
      throw error;
    }
  }

  /**
   * Ledger connection (for TMA)
   */
  async connectLedger() {
    console.log('[GetGemsWallet] Connecting Ledger...');
    
    // Ledger flow is more complex, typically requires TonConnect
    throw new Error('Ledger requires TonConnect fallback');
  }

  /**
   * Fallback to TonConnect v2
   */
  async initTonConnect() {
    console.log('[GetGemsWallet] Initializing TonConnect fallback...');
    
    try {
      // Load TonConnect SDK if not already loaded
      if (!window.TonConnectUI) {
        await this.loadTonConnectSDK();
      }

      const manifestUrl = `${window.location.origin}/tonconnect-manifest.json`;
      
      this.ui = new window.TonConnectUI({
        manifestUrl: manifestUrl,
        actionsConfiguration: {
          twaReturnUrl: window.location.href,
        }
      });

      this.walletType = 'tonconnect';
      this.emit('fallback-to-tonconnect');
      
    } catch (error) {
      console.error('[GetGemsWallet] TonConnect init failed:', error);
      throw error;
    }
  }

  /**
   * Connect using TonConnect (fallback)
   */
  async connectTonConnect() {
    console.log('[GetGemsWallet] Connecting via TonConnect...');
    
    if (!this.ui) {
      await this.initTonConnect();
    }

    try {
      this.ui.openModal();
      
      // Wait for connection
      const unsubscribe = this.ui.onStatusChange((wallet) => {
        if (wallet) {
          this.account = {
            address: wallet.account.address,
            chain: wallet.account.chain,
            publicKey: wallet.account.publicKey,
            walletType: 'tonconnect'
          };
          this.isConnected = true;
          this.saveSession();
          this.emit('connected', this.account);
          unsubscribe();
        }
      });
      
      return this.account;
      
    } catch (error) {
      console.error('[GetGemsWallet] TonConnect connection failed:', error);
      throw error;
    }
  }

  /**
   * Send transaction - GetGems style
   * Optimized for NFT transfers and marketplace transactions
   */
  async sendTransaction(tx) {
    console.log('[GetGemsWallet] Sending transaction:', tx);
    
    if (!this.isConnected) {
      throw new Error('Wallet not connected');
    }

    try {
      let result;
      
      switch (this.walletType) {
        case 'tonhub':
          result = await this.sendTonHubTransaction(tx);
          break;
        case 'tonkeeper':
        case 'tonwallet':
          result = await this.sendBridgeTransaction(tx);
          break;
        case 'tonconnect':
          result = await this.sendTonConnectTransaction(tx);
          break;
        default:
          throw new Error('Unknown wallet type for transaction');
      }
      
      this.emit('transaction-sent', result);
      return result;
      
    } catch (error) {
      console.error('[GetGemsWallet] Transaction failed:', error);
      this.emit('error', error);
      throw error;
    }
  }

  /**
   * Send transaction via TonHub
   */
  async sendTonHubTransaction(tx) {
    try {
      const result = await this.TonHub.send(tx);
      return result;
    } catch (error) {
      throw new Error(`TonHub transaction failed: ${error.message}`);
    }
  }

  /**
   * Send transaction via TON bridge
   */
  async sendBridgeTransaction(tx) {
    try {
      const params = {
        to: tx.to,
        value: tx.value.toString(),
        data: tx.data,
        dataType: 'boc',
      };

      const result = await this.bridge.send('ton_sendTransaction', params);
      return result;
      
    } catch (error) {
      throw new Error(`Bridge transaction failed: ${error.message}`);
    }
  }

  /**
   * Send transaction via TonConnect
   */
  async sendTonConnectTransaction(tx) {
    try {
      const result = await this.ui.sendTransaction(tx);
      return result;
    } catch (error) {
      throw new Error(`TonConnect transaction failed: ${error.message}`);
    }
  }

  /**
   * Deep link for direct wallet interaction (GetGems style)
   * Used for quick transfers without modal
   */
  deepLink(action, params = {}) {
    console.log('[GetGemsWallet] Creating deep link for:', action);
    
    const baseUrl = 'ton://transfer/';
    
    const query = new URLSearchParams({
      destination: params.destination || this.account?.address,
      amount: params.amount || '0',
      text: params.text || '',
      init: params.init || '',
    });

    const deepLinkUrl = baseUrl + query.toString();
    console.log('[GetGemsWallet] Deep link:', deepLinkUrl);
    
    return deepLinkUrl;
  }

  /**
   * Disconnect wallet
   */
  async disconnect() {
    console.log('[GetGemsWallet] Disconnecting wallet...');
    
    try {
      if (this.ui) {
        await this.ui.disconnect();
      }
      
      if (this.bridge && typeof this.bridge.disconnect === 'function') {
        await this.bridge.disconnect();
      }
      
      this.wallet = null;
      this.account = null;
      this.isConnected = false;
      localStorage.removeItem('getgems_wallet_session');
      
      this.emit('disconnected');
      
    } catch (error) {
      console.error('[GetGemsWallet] Disconnect error:', error);
    }
  }

  /**
   * Get current wallet address
   */
  getAddress() {
    return this.account?.address;
  }

  /**
   * Get wallet type
   */
  getWalletType() {
    return this.walletType;
  }

  /**
   * Check if connected
   */
  getConnected() {
    return this.isConnected;
  }

  /**
   * Save session to localStorage
   */
  saveSession() {
    const session = {
      account: this.account,
      walletType: this.walletType,
      timestamp: Date.now()
    };
    localStorage.setItem('getgems_wallet_session', JSON.stringify(session));
  }

  /**
   * Event emitter
   */
  emit(event, data) {
    console.log(`[GetGemsWallet] Emit: ${event}`, data);
    
    if (this.listeners[event]) {
      this.listeners[event].forEach(cb => cb(data));
    }
  }

  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }

  /**
   * Load TonConnect SDK from CDN
   */
  async loadTonConnectSDK() {
    return new Promise((resolve, reject) => {
      if (window.TonConnectUI) {
        resolve();
        return;
      }

      const script = document.createElement('script');
      script.src = 'https://unpkg.com/@tonconnect/ui@latest/dist/tonconnect-ui.js';
      script.async = true;
      script.onload = resolve;
      script.onerror = () => {
        const fallbackScript = document.createElement('script');
        fallbackScript.src = 'https://cdn.jsdelivr.net/npm/@tonconnect/ui@latest/dist/tonconnect-ui.js';
        fallbackScript.async = true;
        fallbackScript.onload = resolve;
        fallbackScript.onerror = () => reject(new Error('Failed to load TonConnect'));
        document.head.appendChild(fallbackScript);
      };
      document.head.appendChild(script);
    });
  }
}

// Export as global and module
const getGemsWallet = new GetGemsWallet();

if (typeof module !== 'undefined' && module.exports) {
  module.exports = getGemsWallet;
}
