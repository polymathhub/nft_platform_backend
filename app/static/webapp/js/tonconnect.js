/**
 * TON Connect v2 - Production Module for Telegram Mini App
 * 
 * Features:
 * ✅ GetGems-style native wallet detection
 * ✅ Priority: TonHub → TonKeeper → TON Wallet → TonConnect
 * ✅ Session persistence/reconnect (24h auto-restore)
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
    
    // GetGems connection mode
    this.walletType = null; // 'tonhub', 'tonkeeper', 'tonwallet', 'tonconnect'
    this.nativeWalletBridge = null; // Reference to native wallet if available
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
      console.log('[TONConnect] Initializing with GetGems-style detection...');
      
      // 1. Detect native wallets 
      this._detectNativeWallets();
      console.log('[TONConnect] Wallet type detected:', this.walletType);

      // 2. Try to restore previous session first
      const restored = await this.restoreSession();
      if (restored) {
        console.log('[TONConnect] Session restored, skipping modal');
        this.isInitialized = true;
        this.isReady = true;
        this.emit('ready');
        return this.ui || true;
      }

      // 3. Load TonConnect SDK and CSS (for fallback or native bridge)
      await this.loadTonConnectSDK();
      
      // Verify SDK is available
      if (!window.TonConnectUI) {
        throw new Error('TonConnectUI SDK not loaded');
      }

      // Get manifest URL 
      const manifestUrl = `${window.location.origin}/tonconnect-manifest.json`;
      console.log('[TONConnect] Manifest URL:', manifestUrl);

      // Verify manifest is accessible before creating UI
      await this.verifyManifest(manifestUrl);

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
        console.log('[TONConnect] UI initialized with button container');
      } catch (e) {
        console.warn('[TONConnect] Standard UI init failed, trying alternative:', e);
        // Fallback: create UI without button
        this.ui = new window.TonConnectUI({
          manifestUrl: manifestUrl,
        });
        console.log('[TONConnect] UI initialized without button container');
      }

      // Listen for status changes
      this.ui.onStatusChange((wallet) => {
        console.log('[TONConnect] Status change:', wallet);
        if (wallet) {
          this.currentAccount = wallet.account;
          this.walletType = 'tonconnect';
          this.saveSession(wallet);
          this.emit('connected', wallet.account);
          console.log('[TONConnect] Connected to:', wallet.account.address);
        } else {
          this.currentAccount = null;
          this.walletType = null;
          this.clearSession();
          this.emit('disconnected');
          console.log('[TONConnect] Disconnected');
        }
      });

      this.isInitialized = true;
      this.isReady = true;
      console.log('[TONConnect] Initialized successfully');
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
   * GetGems-style native wallet detection
   * Check in priority order: TonHub → TonKeeper → TON Wallet → TonConnect
   */
  _detectNativeWallets() {
    console.log('[TONConnect] Detecting native wallets...');
    
    // 1. Check for TonHub (popular bridge)
    if (window.TonHub) {
      console.log('[TONConnect] ✓ TonHub detected');
      this.walletType = 'tonhub';
      this.nativeWalletBridge = window.TonHub;
      return;
    }
    
    // 2. Check for TonKeeper (injects ton object with isTonkeeper flag)
    if (window.ton?.isTonkeeper) {
      console.log('[TONConnect] ✓ TonKeeper detected');
      this.walletType = 'tonkeeper';
      this.nativeWalletBridge = window.ton;
      return;
    }
    
    // 3. Check for generic TON wallet (Chrome extension)
    if (window.ton && typeof window.ton.send === 'function') {
      console.log('[TONConnect] ✓ Generic TON Wallet detected');
      this.walletType = 'tonwallet';
      this.nativeWalletBridge = window.ton;
      return;
    }

    console.log('[TONConnect] No native wallet detected, will use TonConnect');
    this.walletType = 'tonconnect';
  }

  /**
   * Connect via native wallet bridge
   */
  async connectNativeWallet() {
    if (!this.nativeWalletBridge) {
      throw new Error('No native wallet bridge available');
    }

    try {
      console.log('[TONConnect] Connecting via', this.walletType, '...');

      let account;
      
      switch (this.walletType) {
        case 'tonhub':
          account = await this._connectTonHub();
          break;
        case 'tonkeeper':
        case 'tonwallet':
          account = await this._connectViaRpcBridge();
          break;
        default:
          throw new Error('Unknown wallet type: ' + this.walletType);
      }

      if (account) {
        this.currentAccount = account;
        this.saveSession({ account, walletType: this.walletType });
        this.emit('connected', account);
        console.log('[TONConnect] Connected via', this.walletType);
        return account;
      }
      
      throw new Error('Failed to get account from native wallet');

    } catch (error) {
      console.error('[TONConnect] Native wallet connection failed:', error);
      throw error;
    }
  }

  /**
   * Connect via TonHub
   */
  async _connectTonHub() {
    try {
      const isAvailable = await this.TonHub?.isAvailable?.();
      if (!isAvailable) {
        throw new Error('TonHub not available');
      }

      const wallet = await this.TonHub.getWalletInfo?.();
      if (!wallet) {
        throw new Error('Could not get wallet info from TonHub');
      }

      return {
        address: wallet.address,
        publicKey: wallet.publicKey,
        chain: wallet.network === 0 ? 'mainnet' : 'testnet'
      };
    } catch (error) {
      console.error('[TONConnect] TonHub connection error:', error);
      throw error;
    }
  }

  /**
   * Connect via RPC bridge (TonKeeper, TON Wallet)
   */
  async _connectViaRpcBridge() {
    try {
      const result = await this.nativeWalletBridge.send('ton_requestAccounts');
      
      if (!result || !result[0]) {
        throw new Error('No account selected');
      }

      return {
        address: result[0],
        chain: this.walletType === 'tonkeeper' ? 'mainnet' : 'testnet'
      };
    } catch (error) {
      console.error('[TONConnect] RPC bridge connection error:', error);
      throw error;
    }
  }

  /**
   * Verify manifest is accessible
   */
  async verifyManifest(manifestUrl) {
    try {
      console.log('[TONConnect] Verifying manifest at:', manifestUrl);
      const response = await fetch(manifestUrl, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
        cache: 'no-cache'
      });

      if (!response.ok) {
        throw new Error(`Manifest returned ${response.status}`);
      }

      const manifest = await response.json();
      console.log('[TONConnect] Manifest verified:', manifest);

      // Verify manifest has required fields
      if (!manifest.url || !manifest.name) {
        throw new Error('Manifest missing required fields (url, name)');
      }

      return manifest;
    } catch (error) {
      console.error('[TONConnect] Manifest verification failed:', error);
      throw new Error(`Failed to load manifest: ${error.message}`);
    }
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

    // Load CSS first (non-blocking)
    await this._loadCSS();
    
    // Load JS with retry logic
    return this._loadSDKWithRetry();
  }

  /**
   * Load SDK with retry logic
   */
  async _loadSDKWithRetry(attempt = 1, maxAttempts = 3) {
    try {
      return await this._loadSDKScript();
    } catch (error) {
      if (attempt < maxAttempts) {
        console.warn(`[TONConnect] SDK load attempt ${attempt} failed, retrying...`);
        await new Promise(r => setTimeout(r, 1000 * attempt)); // Exponential backoff
        return this._loadSDKWithRetry(attempt + 1, maxAttempts);
      }
      throw error;
    }
  }

  /**
   * Load SDK script from CDN
   */
  async _loadSDKScript() {
    return new Promise((resolve, reject) => {
      // Try primary CDN
      const cdnUrls = [
        'https://unpkg.com/@tonconnect/ui@latest/dist/tonconnect-ui.min.js',
        'https://cdn.jsdelivr.net/npm/@tonconnect/ui@latest/dist/tonconnect-ui.min.js'
      ];

      let attemptedUrls = 0;

      const tryLoadFromCDN = (index) => {
        if (index >= cdnUrls.length) {
          reject(new Error('Failed to load TON Connect SDK from all CDN sources'));
          return;
        }

        const script = document.createElement('script');
        script.src = cdnUrls[index];
        script.async = true;
        script.crossOrigin = 'anonymous';
        
        script.onload = () => {
          console.log(`[TONConnect] SDK loaded from: ${cdnUrls[index]}`);
          // Give it a moment to initialize
          setTimeout(() => {
            if (window.TonConnectUI) {
              console.log('[TONConnect] TonConnectUI is available');
              resolve();
            } else {
              console.warn('[TONConnect] TonConnectUI not available after load, trying next CDN');
              tryLoadFromCDN(index + 1);
            }
          }, 100);
        };
        
        script.onerror = () => {
          console.warn(`[TONConnect] Failed to load from ${cdnUrls[index]}, trying next...`);
          tryLoadFromCDN(index + 1);
        };
        
        document.head.appendChild(script);
      };

      tryLoadFromCDN(0);
    });
  }

  /**
   * Load TON Connect CSS
   */
  async _loadCSS() {
    return new Promise((resolve) => {
      // Check if already loaded
      if (document.querySelector('link[href*="tonconnect"]')) {
        console.log('[TONConnect] CSS already loaded');
        resolve();
        return;
      }

      const cssUrls = [
        'https://unpkg.com/@tonconnect/ui@latest/dist/tonconnect-ui.min.css',
        'https://cdn.jsdelivr.net/npm/@tonconnect/ui@latest/dist/tonconnect-ui.min.css'
      ];

      const tryLoadCSS = (index) => {
        if (index >= cssUrls.length) {
          console.warn('[TONConnect] Could not load CSS from any CDN (will continue without styles)');
          resolve();
          return;
        }

        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = cssUrls[index];
        link.crossOrigin = 'anonymous';
        
        link.onload = () => {
          console.log(`[TONConnect] CSS loaded from: ${cssUrls[index]}`);
          resolve();
        };
        
        link.onerror = () => {
          console.warn(`[TONConnect] CSS load failed from ${cssUrls[index]}, trying next...`);
          tryLoadCSS(index + 1);
        };
        
        document.head.appendChild(link);
      };

      tryLoadCSS(0);
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
   * Show wallet connection modal (Telegram popup)
   * This is the GATEWAY - triggered when user clicks "Connect Wallet" button
   */
  async showWalletModal() {
    console.log('[TONConnect] ==== WALLET MODAL GATEWAY TRIGGERED ====');
    
    if (!this.isInitialized || !this.ui) {
      console.log('[TONConnect] UI not initialized, initializing now...');
      const ready = await this.waitForReady();
      if (!ready) {
        throw new Error('TON Connect not ready');
      }
    }

    try {
      console.log('[TONConnect] Opening wallet selection modal...');
      console.log('[TONConnect] UI instance:', this.ui);
      console.log('[TONConnect] UI available methods:', Object.getOwnPropertyNames(Object.getPrototypeOf(this.ui || {})));
      
      if (!this.ui) {
        throw new Error('UI instance not available');
      }

      if (typeof this.ui.connectWallet !== 'function') {
        console.warn('[TONConnect] connectWallet method not available, trying openModal...');
        if (typeof this.ui.openModal === 'function') {
          await this.ui.openModal();
        } else {
          throw new Error('No modal method available on TonConnectUI');
        }
      } else {
        // Trigger the TonConnect wallet selection modal
        console.log('[TONConnect] Calling ui.connectWallet()...');
        const wallet = await this.ui.connectWallet();
        console.log('[TONConnect] Modal returned wallet:', wallet);
        return wallet;
      }

    } catch (error) {
      if (error.message.includes('Already connected')) {
        console.log('[TONConnect] Already connected');
        return { success: true, alreadyConnected: true };
      }
      console.error('[TONConnect] Modal error:', error);
      this.emit('error', { message: error.message || 'Connection cancelled' });
      throw error;
    }
  }

  /**
   * Open wallet connection modal (alias for backward compatibility)
   */
  async openModal() {
    return this.showWalletModal();
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
   * Connect wallet - GetGems style
   * Tries native wallet first, then falls back to TonConnect modal
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
      // Try native wallet first (GetGems priority)
      if (this.walletType && this.walletType !== 'tonconnect' && this.nativeWalletBridge) {
        try {
          console.log('[TONConnect] Attempting native wallet connection...');
          const account = await this.connectNativeWallet();
          return account;
        } catch (error) {
          console.warn('[TONConnect] Native wallet connection failed, falling back to TonConnect:', error.message);
          this.walletType = 'tonconnect';
        }
      }

      // Fallback: use TonConnect modal
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
   * Send transaction - GetGems style
   * Routes to native wallet or TonConnect based on connection type
   */
  async sendTransaction(transaction) {
    if (!this.isConnected()) {
      throw new Error('Wallet not connected');
    }

    try {
      console.log('[TONConnect] Sending transaction via', this.walletType);
      
      // Send via native wallet if available
      if (this.walletType !== 'tonconnect' && this.nativeWalletBridge) {
        return await this._sendViaNativeWallet(transaction);
      }

      // Fallback to TonConnect
      if (!this.ui) {
        throw new Error('TON Connect not initialized');
      }

      console.log('[TONConnect] Sending transaction via TonConnect UI');
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
   * Send transaction via native wallet bridge
   */
  async _sendViaNativeWallet(tx) {
    try {
      switch (this.walletType) {
        case 'tonhub':
          return await this.nativeWalletBridge.send(tx);
        
        case 'tonkeeper':
        case 'tonwallet':
          const params = {
            to: tx.to,
            value: tx.value?.toString() || '0',
            data: tx.data,
            dataType: 'boc',
          };
          return await this.nativeWalletBridge.send('ton_sendTransaction', params);
        
        default:
          throw new Error('Unknown wallet type for transaction: ' + this.walletType);
      }
    } catch (error) {
      console.error('[TONConnect] Native wallet transaction error:', error);
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
      this.walletType = 'tonconnect';
      this.nativeWalletBridge = null;
      this.clearSession();
      console.log('[TONConnect] Disconnected');
      this.emit('disconnected');
    } catch (error) {
      console.error('[TONConnect] Disconnect failed:', error);
    }
  }

  /**
   * Deep link for direct transfer (GetGems style)
   * Usage: window.location.href = tonConnect.createDeepLink(...)
   */
  createDeepLink(params) {
    const query = new URLSearchParams({
      destination: params.destination || this.getWalletAddress() || '',
      amount: params.amount || '0',
      text: params.text || '',
      init: params.init || '',
    });

    const deepLink = `ton://transfer/${query.toString()}`;
    console.log('[TONConnect] Created deep link');
    return deepLink;
  }

  /**
   * Get current account
   */
  getAccount() {
    return this.currentAccount;
  }

  /**
   * Restore session from localStorage with 24-hour TTL
   * GetGems-style auto-reconnect
   */
  async restoreSession() {
    const session = localStorage.getItem('tonconnect_session');
    if (!session) {
      console.log('[TONConnect] No session to restore');
      return false;
    }

    try {
      const parsed = JSON.parse(session);
      const now = Date.now();

      // Check if session is still valid (24 hours = 86400000 ms)
      if (now - parsed.timestamp > 24 * 60 * 60 * 1000) {
        console.log('[TONConnect] Session expired');
        this.clearSession();
        return false;
      }

      console.log('[TONConnect] Restoring session with wallet type:', parsed.walletType);
      this.currentAccount = parsed.account;
      this.walletType = parsed.walletType;
      
      this.emit('connected', parsed.account);
      console.log('[TONConnect] Session restored successfully');
      return true;

    } catch (error) {
      console.warn('[TONConnect] Session restore error:', error);
      this.clearSession();
      return false;
    }
  }

  /**
   * Save session to localStorage with timestamp
   */
  saveSession(wallet) {
    try {
      const session = {
        account: wallet.account || this.currentAccount,
        walletType: this.walletType,
        timestamp: Date.now()
      };
      localStorage.setItem('tonconnect_session', JSON.stringify(session));
      console.log('[TONConnect] Session saved (', this.walletType, ')');
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
   * Get wallet type (GetGems info)
   */
  getWalletType() {
    return this.walletType;
  }

  /**
   * Get native wallet info
   */
  getNativeWalletInfo() {
    return {
      type: this.walletType,
      isNative: this.walletType !== 'tonconnect' && this.walletType !== null,
      bridge: this.nativeWalletBridge ? 'available' : 'none'
    };
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

