/**
 * ═══════════════════════════════════════════════════════════════════════════
 * TON WALLET CONNECTION COMPREHENSIVE FLOW
 * ═══════════════════════════════════════════════════════════════════════════
 * 
 * Complete end-to-end flow for connecting Telegram's built-in TON wallet:
 * 1. User clicks "Connect Wallet" button
 * 2. TonConnect modal opens (Telegram Wallet, Tonkeeper, TonWallet)
 * 3. User selects wallet and approves connection
 * 4. Frontend receives wallet address
 * 5. Frontend CALLS BACKEND to register wallet in database
 * 6. Backend creates user account and TON wallet entry
 * 7. Backend returns token and user data
 * 8. Frontend redirects to dashboard with persistent session
 * ═══════════════════════════════════════════════════════════════════════════
 */

// ═══════════════════════════════════════════════════════════════════════════
// STEP 1: ENHANCED WALLET CONNECTION FLOW WITH LOGGING
// ═══════════════════════════════════════════════════════════════════════════

class TONWalletConnectionFlow {
  constructor() {
    this.logger = new WalletLogger('[TON-Wallet]');
    this.state = 'idle'; // idle, connecting, processing, connected, error
    this.connectionTimeout = 30000; // 30 seconds
  }

  /**
   * Main connect wallet handler - Called when user clicks "Connect Wallet" button
   */
  async connectWallet() {
    this.logger.info('🔵 [STEP 1] User clicked "Connect Wallet" button');
    
    if (this.state === 'connecting') {
      this.logger.warn('Connection already in progress, ignoring duplicate click');
      Toast.warning('Connection in progress, please wait...', 3000);
      return;
    }

    this.state = 'connecting';
    const uiController = new WalletUIController();
    uiController.showConnectingState();
    this.logger.debug('UI updated to "connecting" state');

    try {
      // ───────────────────────────────────────────────────────────────────
      // STEP 2: OPEN TONCONNECT MODAL
      // ───────────────────────────────────────────────────────────────────
      this.logger.info('🔵 [STEP 2] Opening TonConnect modal...');
      
      const result = await this.openModalWithTimeout();
      
      if (!result) {
        this.logger.warn('User dismissed wallet selection modal');
        Toast.info('Wallet connection cancelled', 2000);
        this.state = 'idle';
        uiController.showConnectButton();
        return;
      }

      if (!result.account?.address) {
        throw new Error('No wallet address received from TonConnect');
      }

      const walletAddress = result.account.address;
      this.logger.info(`✅ Wallet selected: ${walletAddress.slice(0, 10)}...`);
      this.logger.debug(`Full wallet address: ${walletAddress}`);

      // ───────────────────────────────────────────────────────────────────
      // STEP 3: VALIDATE WALLET ADDRESS FORMAT
      // ───────────────────────────────────────────────────────────────────
      this.logger.info('🔵 [STEP 3] Validating wallet address format...');
      
      if (!this.isValidTONAddress(walletAddress)) {
        throw new Error(`Invalid TON wallet address format: ${walletAddress}`);
      }
      this.logger.info('✅ Wallet address format valid');

      // ───────────────────────────────────────────────────────────────────
      // STEP 4: PREPARE CALLBACK DATA
      // ───────────────────────────────────────────────────────────────────
      this.logger.info('🔵 [STEP 4] Preparing backend callback data...');
      
      const callbackData = {
        wallet_address: walletAddress,
        tonconnect_session: result,
        init_data: window.Telegram?.WebApp?.initData || '',
        wallet_metadata: {
          connected_at: new Date().toISOString(),
          user_agent: navigator.userAgent,
          client_type: this.detectClientType()
        }
      };
      
      this.logger.debug('Callback data prepared:', {
        wallet: walletAddress.slice(0, 10) + '...',
        session_id: result.sessionId?.slice(0, 8) + '...',
        has_init_data: !!callbackData.init_data
      });

      // ───────────────────────────────────────────────────────────────────
      // STEP 5: CALL BACKEND CALLBACK ENDPOINT
      // ───────────────────────────────────────────────────────────────────
      this.logger.info('🔵 [STEP 5] Sending wallet registration to backend...');
      this.logger.debug('POST /api/v1/wallet/ton/callback');
      
      this.state = 'processing';
      uiController.showProcessingState('Registering wallet...');

      const response = await this.callBackendCallback(callbackData);
      
      this.logger.info('✅ Backend callback successful (200 OK)');
      this.logger.debug('Response:', {
        user_id: response.user_id?.slice(0, 8) + '...',
        wallet_address: response.wallet_address?.slice(0, 10) + '...',
        redirect_url: response.redirect_url
      });

      // ───────────────────────────────────────────────────────────────────
      // STEP 6: STORE TOKEN & USER DATA
      // ───────────────────────────────────────────────────────────────────
      this.logger.info('🔵 [STEP 6] Storing user session...');
      
      if (response.token) {
        sessionStorage.setItem('auth_token', response.token);
        this.logger.debug('Auth token stored in sessionStorage');
      }
      
      if (response.user_id) {
        sessionStorage.setItem('user_id', response.user_id);
        this.logger.debug('User ID stored in sessionStorage');
      }

      // ───────────────────────────────────────────────────────────────────
      // STEP 7: UPDATE UI & EMIT EVENTS
      // ───────────────────────────────────────────────────────────────────
      this.logger.info('🔵 [STEP 7] Updating UI with wallet info...');
      
      this.state = 'connected';
      uiController.showConnectedState({
        address: walletAddress,
        shortAddress: this.formatAddress(walletAddress)
      });
      this.logger.debug('UI updated to "connected" state');

      // Emit success event for other components
      window.dispatchEvent(new CustomEvent('wallet:connected', {
        detail: {
          address: walletAddress,
          userId: response.user_id,
          timestamp: new Date()
        }
      }));
      this.logger.debug('Event dispatched: wallet:connected');

      // ───────────────────────────────────────────────────────────────────
      // STEP 8: SUCCESS NOTIFICATION & REDIRECT
      // ───────────────────────────────────────────────────────────────────
      this.logger.info('✅ [STEP 8] Wallet connected successfully!');
      
      Toast.success(`Wallet connected: ${this.formatAddress(walletAddress)}`, 3000);
      
      // Redirect to dashboard after brief delay
      setTimeout(() => {
        this.logger.info(`🔴 Redirecting to: ${response.redirect_url || '/dashboard'}`);
        window.location.href = response.redirect_url || '/dashboard';
      }, 1500);

    } catch (error) {
      await this.handleConnectionError(error, uiController);
    }
  }

  /**
   * Open TonConnect modal with timeout protection
   */
  async openModalWithTimeout() {
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.logger.error('TonConnect modal timeout (30s)');
        reject(new Error('Wallet selection timed out'));
      }, this.connectionTimeout);

      try {
        window.tonWallet?.tonConnect?.openModal?.()
          .then(result => {
            clearTimeout(timer);
            resolve(result);
          })
          .catch(err => {
            clearTimeout(timer);
            reject(err);
          });
      } catch (err) {
        clearTimeout(timer);
        reject(err);
      }
    });
  }

  /**
   * Call backend callback endpoint with retry logic
   */
  async callBackendCallback(data, retryCount = 0) {
    const maxRetries = 3;
    
    try {
      this.logger.debug(`Backend request attempt ${retryCount + 1}/${maxRetries}`);
      
      const response = await fetch('/api/v1/wallet/ton/callback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Telegram-Init-Data': data.init_data
        },
        body: JSON.stringify(data),
        timeout: 15000
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new BackendError(
          response.status,
          errorData.detail || 'Backend callback failed'
        );
      }

      const result = await response.json();
      this.logger.debug('Backend response received:', {
        status: response.status,
        success: result.success,
        message: result.message
      });

      return result;

    } catch (error) {
      if (retryCount < maxRetries) {
        this.logger.warn(`Retry ${retryCount + 1}/${maxRetries} after error:`, error.message);
        await this.delay(Math.pow(2, retryCount) * 1000); // Exponential backoff
        return this.callBackendCallback(data, retryCount + 1);
      }
      throw error;
    }
  }

  /**
   * Comprehensive error handling
   */
  async handleConnectionError(error, uiController) {
    this.state = 'error';
    
    this.logger.error(`❌ Connection failed: ${error.message}`);
    this.logger.error('Full error:', error);

    const errorMessage = this.getErrorMessage(error);
    const errorCode = error.code || 'UNKNOWN';

    this.logger.error(`Error code: ${errorCode}`);

    // Show user-friendly error message
    Toast.error(errorMessage, 5000);
    
    // Update UI
    uiController.showErrorState(errorMessage);
    
    // Log error for analytics
    this.reportError({
      type: 'wallet_connection_failed',
      code: errorCode,
      message: error.message,
      timestamp: new Date().toISOString()
    });

    // Reset to allow retry
    setTimeout(() => {
      this.state = 'idle';
      uiController.showConnectButton();
      this.logger.info('Ready for retry');
    }, 3000);
  }

  /**
   * Utility: Validate TON wallet address format
   */
  isValidTONAddress(address) {
    // TON addresses start with 0: (testnet) or -1: (mainnet)
    const pattern = /^(0|EQAg|-1):[A-Fa-f0-9]{64}$/;
    const valid = pattern.test(address);
    this.logger.debug(`Address validation: ${valid ? '✅' : '❌'}`);
    return valid;
  }

  /**
   * Utility: Format address for display
   */
  formatAddress(address) {
    if (!address) return '';
    return `${address.slice(0, 10)}...${address.slice(-10)}`;
  }

  /**
   * Utility: Detect client type (Telegram, Browser, etc)
   */
  detectClientType() {
    if (window.Telegram?.WebApp) return 'telegram_webapp';
    if (navigator.userAgent.includes('TonKeeper')) return 'tonkeeper';
    if (navigator.userAgent.includes('Chrome')) return 'chrome';
    return 'unknown';
  }

  /**
   * Utility: Get user-friendly error message
   */
  getErrorMessage(error) {
    const messages = {
      'Network error': 'Network connection failed. Please check your internet.',
      'Timeout': 'Connection took too long. Please try again.',
      'Invalid TON wallet address': 'Invalid wallet address format.',
      'Not authenticated': 'Please verify your Telegram identity.',
      'Wallet already connected': 'This wallet is already connected to another account.',
      'Server error': 'Backend server error. Please try again later.',
    };

    for (const [key, message] of Object.entries(messages)) {
      if (error.message.includes(key)) return message;
    }

    return `Connection failed: ${error.message}`;
  }

  /**
   * Report error to logging service
   */
  reportError(errorData) {
    this.logger.error('Reporting to error tracking:', errorData);
    // TODO: Send to error tracking service (Sentry, etc)
  }

  /**
   * Utility: Promise delay
   */
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// UI CONTROLLER - Manages UI state transitions
// ═══════════════════════════════════════════════════════════════════════════

class WalletUIController {
  showConnectingState() {
    const btn = document.querySelector('[data-wallet-action="connect"]');
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '⏳ Opening wallet...';
      btn.classList.add('btn-loading');
    }
  }

  showProcessingState(message = 'Processing...') {
    const btn = document.querySelector('[data-wallet-action="connect"]');
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = `⏳ ${message}`;
      btn.classList.add('btn-loading');
    }
  }

  showConnectedState(walletInfo) {
    const btn = document.querySelector('[data-wallet-action="connect"]');
    const addressDisplay = document.querySelector('[data-wallet-address]');
    
    if (btn) {
      btn.innerHTML = '✅ Connected';
      btn.disabled = true;
      btn.classList.remove('btn-loading');
    }
    
    if (addressDisplay) {
      addressDisplay.textContent = walletInfo.shortAddress;
      addressDisplay.title = walletInfo.address;
    }

    // Show disconnect button
    const disconnectBtn = document.querySelector('[data-wallet-action="disconnect"]');
    if (disconnectBtn) {
      disconnectBtn.style.display = 'inline-block';
    }
  }

  showErrorState(errorMessage) {
    const btn = document.querySelector('[data-wallet-action="connect"]');
    if (btn) {
      btn.innerHTML = '❌ Try Again';
      btn.disabled = false;
      btn.classList.remove('btn-loading');
    }

    const errorDisplay = document.querySelector('[data-wallet-error]');
    if (errorDisplay) {
      errorDisplay.textContent = errorMessage;
      errorDisplay.style.display = 'block';
    }
  }

  showConnectButton() {
    const btn = document.querySelector('[data-wallet-action="connect"]');
    if (btn) {
      btn.innerHTML = '🔗 Connect Wallet';
      btn.disabled = false;
      btn.classList.remove('btn-loading');
    }
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// WALLET LOGGER - Comprehensive logging system
// ═══════════════════════════════════════════════════════════════════════════

class WalletLogger {
  constructor(prefix = '[Wallet]') {
    this.prefix = prefix;
    this.logs = [];
    this.maxLogs = 100;
  }

  _log(level, message, data = null) {
    const timestamp = new Date().toISOString();
    const logEntry = {
      timestamp,
      level,
      message,
      data,
      prefix: this.prefix
    };

    this.logs.push(logEntry);
    if (this.logs.length > this.maxLogs) {
      this.logs.shift();
    }

    const icon = {
      'INFO': 'ℹ️',
      'DEBUG': '🔍',
      'WARN': '⚠️',
      'ERROR': '❌'
    }[level] || '•';

    const output = data 
      ? `${icon} ${this.prefix} [${level}] ${message}`, data
      : `${icon} ${this.prefix} [${level}] ${message}`;

    console[level.toLowerCase()](output);
  }

  info(message, data) { this._log('INFO', message, data); }
  debug(message, data) { this._log('DEBUG', message, data); }
  warn(message, data) { this._log('WARN', message, data); }
  error(message, data) { this._log('ERROR', message, data); }

  getLogs() {
    return this.logs;
  }

  exportLogs() {
    return JSON.stringify(this.logs, null, 2);
  }

  downloadLogs() {
    const data = this.exportLogs();
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `wallet-logs-${Date.now()}.json`;
    link.click();
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// ERROR CLASSES
// ═══════════════════════════════════════════════════════════════════════════

class BackendError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
    this.code = `HTTP_${status}`;
    this.name = 'BackendError';
  }
}

class ValidationError extends Error {
  constructor(message, field = null) {
    super(message);
    this.field = field;
    this.name = 'ValidationError';
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// INITIALIZATION
// ═══════════════════════════════════════════════════════════════════════════

// Create global instance
const walletConnectionFlow = new TONWalletConnectionFlow();

// Attach to window for button click handler
window.connectTONWallet = () => {
  walletConnectionFlow.connectWallet();
};

// Add button event listener
document.addEventListener('DOMContentLoaded', () => {
  const connectBtn = document.querySelector('[data-wallet-action="connect"]');
  if (connectBtn) {
    connectBtn.addEventListener('click', window.connectTONWallet);
    console.log('✅ Wallet connect button initialized');
  }
});

// ═══════════════════════════════════════════════════════════════════════════
// EXPORT FOR USE IN HTML
// ═══════════════════════════════════════════════════════════════════════════

// Usage in HTML:
// <button onclick="connectTONWallet()" data-wallet-action="connect">
//   🔗 Connect Wallet
// </button>

// Debug: Export logger for console inspection
window.walletLogs = () => walletConnectionFlow.logger.downloadLogs();
window.walletDebug = () => console.table(walletConnectionFlow.logger.getLogs());
