
import { tonConnect } from './tonconnect.js';

class TelegramWalletIntegrator {
  constructor(walletUi) {
    this.walletUi = walletUi; // #wallet-balance-card or container
    this.connectBtn = null;
    this.walletAddressEl = null;
    this.statusEl = null;
    this.errorEl = null;
    this.loadingEl = null;
    this.authSystem = null;
    this.isConnecting = false;
    
    this.initElements();
    this.initAuth();
    this.bindEvents();
    this.initWalletState();
  }

  /**
   * Initialize authentication system
   * Ensures AuthSystem is initialized before wallet operations
   */
  async initAuth() {
    try {
      // Wait for AuthSystem to be available (set in auth-system.js)
      let retries = 0;
      while (!window.AuthSystem && retries < 10) {
        await new Promise(r => setTimeout(r, 100));
        retries++;
      }
      
      if (!window.AuthSystem) {
        console.warn('[TelegramWallet] AuthSystem not available, proceeding without cached auth');
        return;
      }
      
      this.authSystem = window.AuthSystem;
      console.log('[TelegramWallet] AuthSystem initialized');
      
      // If not authenticated yet, initialize auth
      if (!this.authSystem.isInitialized && !this.authSystem.isInitializing) {
        console.log('[TelegramWallet] Initializing authentication...');
        await this.authSystem.initialize();
      }
      
    } catch (error) {
      console.error('[TelegramWallet] Auth initialization error:', error);
    }
  }

  initElements() {
    this.connectBtn = this.walletUi.querySelector('#connectBtn');
    this.walletAddressEl = this.walletUi.querySelector('#walletAddress');
    this.statusEl = this.walletUi.querySelector('#status');
    this.errorEl = this.walletUi.querySelector('#error');
    this.loadingEl = this.walletUi.querySelector('#loading');
    
    if (!this.connectBtn) {
      console.error('[TelegramWallet] Critical: connectBtn not found in DOM');
    }
  }

  bindEvents() {
    // TON Connect events
    tonConnect.on('ready', () => {
      console.log('[TelegramWallet] TON Connect is ready for wallet connections');
      this.updateUI();
    });
    tonConnect.on('connected', (account) => {
      console.log('[TelegramWallet] Connection event fired:', account);
      this.handleConnect(account);
    });
    tonConnect.on('disconnected', () => {
      console.log('[TelegramWallet] Disconnection event fired');
      this.handleDisconnect();
    });
    tonConnect.on('error', (error) => {
      console.log('[TelegramWallet] Error event fired:', error);
      this.handleError(error);
    });

    // ═══════════════════════════════════════════════════════════════════
    // BUTTON CLICK - GATEWAY ENTRY POINT FOR TON CONNECT
    // ═══════════════════════════════════════════════════════════════════
    // This is the entry point that initiates TON Connect from Telegram
    // When user clicks button on line 883 of wallet.html:
    // 1. This handler fires
    // 2. Calls this.connect()
    // 3. Shows TonConnectUI wallet selection modal
    // 4. User selects wallet
    // 5. Auto-syncs with backend
    // ═══════════════════════════════════════════════════════════════════
    if (this.connectBtn) {
      this.connectBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        console.log('[TelegramWallet] Connect button clicked - gateway entry point');
        
        // Check current state
        if (tonConnect.getAccount()) {
          console.log('[TelegramWallet] Already connected, showing disconnect option');
          this.handleDisconnect();
        } else {
          console.log('[TelegramWallet] Not connected, initiating connect gateway');
          this.connect();
        }
      });
    }
  }

  async initWalletState() {
    // Wait for TON Connect ready
    console.log('[TelegramWallet] Initializing wallet state...');
    try {
      // Wait for Telegram SDK
      let retries = 0;
      while (!window.Telegram?.WebApp?.initData && retries < 10) {
        await new Promise(r => setTimeout(r, 100));
        retries++;
      }
      
      if (!window.Telegram?.WebApp?.initData) {
        console.warn('[TelegramWallet] Telegram SDK not ready, proceeding anyway');
      }

      // Initialize TON Connect
      console.log('[TelegramWallet] Initializing TON Connect...');
      await tonConnect.init();
      console.log('[TelegramWallet] TON Connect initialized successfully');
      
      // ✨ RESTORE WALLET STATE FROM SESSIONSTROAGE IF AVAILABLE
      try {
        const savedState = sessionStorage.getItem('ton_wallet_state');
        if (savedState) {
          const state = JSON.parse(savedState);
          console.log('[TelegramWallet] Restored wallet state from sessionStorage:', state.address);
          
          // Restore to globals for immediate access
          window.walletConnected = {
            address: state.address,
            isTONConnect: true,
            chain: state.chain,
            publicKey: state.publicKey,
            formatted: `${state.address.slice(0, 10)}...${state.address.slice(-10)}`
          };
          
          window.currentMintWalletAddress = state.address;
          console.log('[TelegramWallet] Wallet restored and available globally');
        }
      } catch (e) {
        console.warn('[TelegramWallet] Could not restore from sessionStorage:', e);
      }
      
      // Check current wallet state
      const walletType = tonConnect.getWalletType();
      console.log('[TelegramWallet] Current wallet type:', walletType);
      
      // Update UI with current state
      await this.updateUI();
      console.log('[TelegramWallet] Wallet state initialization complete - GATEWAY READY');
      
    } catch (error) {
      console.error('[TelegramWallet] Wallet initialization error:', error);
      this.setError(`Initialization error: ${error.message}`);
      // Still allow user to try connecting
    }
  }

  async connect() {
    console.log('[TelegramWallet] ==== WALLET CONNECT GATEWAY INITIATED ====');
    
    // Check if already connecting or connected
    if (this.isConnecting) {
      console.log('[TelegramWallet] Already connecting, skipping duplicate request');
      this.setError('Connection already in progress');
      return;
    }

    if (tonConnect.getAccount()) {
      console.log('[TelegramWallet] Already connected');
      this.setConnected(tonConnect.getAccount().address);
      return;
    }

    this.isConnecting = true;
    this.setLoading(true);
    this.clearError();

    try {
      console.log('[TelegramWallet] Triggering TON Connect modal...');
      
      // This is the GATEWAY: shows the wallet selection modal (popup)
      const account = await tonConnect.connectWallet();
      
      if (!account) {
        this.setError('No wallet selected - modal cancelled');
        console.warn('[TelegramWallet] User cancelled wallet selection');
        return;
      }

      console.log('[TelegramWallet] Wallet selected via modal:', account.address);
      
      // Auto-sync with backend
      await this.syncWithBackend(account.address);
      console.log('[TelegramWallet] Gateway flow completed successfully');
      
    } catch (error) {
      console.error('[TelegramWallet] Gateway error:', error);
      this.setError(error.message || 'Connection failed - check console');
    } finally {
      this.isConnecting = false;
      this.setLoading(false);
    }
  }

  async handleConnect(account) {
    console.log('[TelegramWallet] Connected:', account.address);
    this.updateUI(account);
    await this.syncWithBackend(account.address);
  }

  async handleDisconnect() {
    console.log('[TelegramWallet] Disconnected');
    this.updateUI();
  }

  async handleError(error) {
    console.error('[TelegramWallet] Error:', error);
    this.setError(error.message);
    this.updateUI();
  }

  async copyAddress(address) {
    try {
      await navigator.clipboard.writeText(address);
      this.setStatus('Address copied ✓');
      setTimeout(() => this.setStatus('Connected to TON'), 2000);
    } catch (err) {
      this.setError('Copy failed');
    }
  }

  async syncWithBackend(walletAddress) {
    try {
      // Get Telegram initData with multiple fallback strategies
      let initData = null;
      
      // Strategy 1: Use AuthSystem if available
      if (this.authSystem && typeof this.authSystem.getTelegramInitData === 'function') {
        initData = this.authSystem.getTelegramInitData();
      }
      
      // Strategy 2: Get directly from Telegram SDK
      if (!initData) {
        initData = window.Telegram?.WebApp?.initData;
      }
      
      if (!initData) {
        const errorMsg = 'Telegram authentication required - initData not available. Please ensure you\'re using a valid Telegram Mini App URL.';
        console.error('[TelegramWallet] Authentication error:', errorMsg);
        this.setError(errorMsg);
        throw new Error(errorMsg);
      }

      console.log('[TelegramWallet] Syncing wallet with backend:', {
        walletAddress: walletAddress.slice(0, 10) + '...',
        authAvailable: !!initData,
        timestamp: new Date().toISOString()
      });

      const response = await fetch('/api/v1/walletconnect/connect', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Telegram-Init-Data': initData,
        },
        body: JSON.stringify({
          wallet_address: walletAddress,
          blockchain: 'ton',
          wallet_name: 'TON Connect Wallet'
        }),
      });

      if (!response.ok) {
        let errorDetail = `HTTP ${response.status}`;
        try {
          const data = await response.json();
          errorDetail = data.detail || data.message || errorDetail;
        } catch (e) {
          // Response is not JSON
        }
        throw new Error(`Backend sync failed: ${errorDetail}`);
      }

      const result = await response.json();
      console.log('[TelegramWallet] Backend sync successful:', result);
      this.setStatus('Synced with backend ✓');
      
    } catch (error) {
      console.error('[TelegramWallet] Backend sync failed:', error);
      const userMessage = error.message.includes('initData') 
        ? 'Authentication error - please reload the app'
        : `Sync failed: ${error.message}`;
      this.setError(userMessage);
      console.error('[TelegramWallet] Full error:', error);
      // Don't disconnect wallet on sync error - it's frontend state
    }
  }

  async updateUI(account = tonConnect.getAccount()) {
    if (account) {
      this.setConnected(account.address);
    } else {
      this.setDisconnected();
    }
  }

  setConnected(address) {
    if (this.connectBtn) {
      this.connectBtn.textContent = '✓ Connected';
      this.connectBtn.disabled = true;
      this.connectBtn.classList.add('connected');
    }
    
    if (this.walletAddressEl) {
      const short = `${address.slice(0,6)}...${address.slice(-6)}`;
      this.walletAddressEl.textContent = short;
      this.walletAddressEl.dataset.full = address;
      this.walletAddressEl.style.display = 'inline';
    }
    
    this.setStatus('Connected to TON');
    this.clearError();
    
    // ✨ PERSIST WALLET STATE FOR CROSS-PAGE DETECTION
    // Store in sessionStorage for page reloads
    const walletState = {
      address: address,
      chain: tonConnect.getAccount()?.chain || '-3',
      publicKey: tonConnect.getAccount()?.publicKey,
      timestamp: new Date().toISOString()
    };
    
    try {
      sessionStorage.setItem('ton_wallet_state', JSON.stringify(walletState));
      console.log('[TelegramWallet] Wallet state persisted to sessionStorage:', address);
    } catch (e) {
      console.error('[TelegramWallet] Failed to persist to sessionStorage:', e);
    }
    
    // Store in window global for immediate access
    window.walletConnected = {
      address: address,
      isTONConnect: true,
      chain: walletState.chain,
      publicKey: walletState.publicKey,
      formatted: `${address.slice(0, 10)}...${address.slice(-10)}`
    };
    
    console.log('[TelegramWallet] Wallet connected and available globally:', window.walletConnected);
    
    // ✨ DISPATCH CUSTOM EVENT FOR CROSS-PAGE NOTIFICATION
    // This allows mint.html and other pages to listen for wallet connection
    const event = new CustomEvent('wallet-connected-tonconnect', {
      detail: {
        address: address,
        chain: walletState.chain,
        publicKey: walletState.publicKey,
        timestamp: walletState.timestamp
      },
      bubbles: true,
      cancelable: true
    });
    
    window.dispatchEvent(event);
    console.log('[TelegramWallet] Dispatched wallet-connected-tonconnect event');
  }

  setDisconnected() {
    if (this.connectBtn) {
      this.connectBtn.textContent = 'Connect TON Wallet';
      this.connectBtn.disabled = false;
      this.connectBtn.classList.remove('connected');
    }
    
    if (this.walletAddressEl) {
      this.walletAddressEl.style.display = 'none';
    }
    
    this.setStatus('No wallet connected');
    this.clearError();
    
    // ✨ CLEAR WALLET STATE
    try {
      sessionStorage.removeItem('ton_wallet_state');
      console.log('[TelegramWallet] Wallet state cleared from sessionStorage');
    } catch (e) {
      console.error('[TelegramWallet] Failed to clear sessionStorage:', e);
    }
    
    window.walletConnected = null;
    window.currentMintWalletAddress = null;
    console.log('[TelegramWallet] Wallet state cleared from globals');
    
    // ✨ DISPATCH DISCONNECT EVENT FOR CROSS-PAGE NOTIFICATION
    const event = new CustomEvent('wallet-disconnected-tonconnect', {
      bubbles: true,
      cancelable: true
    });
    
    window.dispatchEvent(event);
    console.log('[TelegramWallet] Dispatched wallet-disconnected-tonconnect event');
  }

  setLoading(show) {
    if (this.loadingEl) {
      this.loadingEl.style.display = show ? 'inline-block' : 'none';
    }
    if (this.connectBtn) {
      this.connectBtn.disabled = show;
    }
  }

  setStatus(message) {
    if (this.statusEl) {
      this.statusEl.textContent = message;
      this.statusEl.style.display = 'inline';
    }
  }

  setError(message) {
    if (this.errorEl) {
      this.errorEl.textContent = message;
      this.errorEl.style.display = 'inline';
      this.errorEl.style.color = '#ef4444';
    }
    console.error('[TelegramWallet] Error:', message);
  }

  clearError() {
    if (this.errorEl) {
      this.errorEl.textContent = '';
      this.errorEl.style.display = 'none';
    }
  }

  /**
   * Disconnect current wallet
   */
  async disconnect() {
    console.log('[TelegramWallet] Disconnecting wallet...');
    this.setLoading(true);
    
    try {
      await tonConnect.disconnect();
      this.setDisconnected();
      this.setStatus('Wallet disconnected');
      console.log('[TelegramWallet] Wallet disconnected successfully');
    } catch (error) {
      console.error('[TelegramWallet] Disconnect error:', error);
      this.setError('Disconnect failed: ' + error.message);
    } finally {
      this.setLoading(false);
    }
  }

  /**
   * Handle disconnect action
   */
  handleDisconnect() {
    console.log('[TelegramWallet] Disconnect handler triggered');
    this.setDisconnected();
    console.log('[TelegramWallet] UI updated for disconnected state');
  }
}

// Export for modules
export default TelegramWalletIntegrator;

// Auto-init on pages that include it
if (typeof window !== 'undefined') {
  window.TelegramWalletIntegrator = TelegramWalletIntegrator;
}

