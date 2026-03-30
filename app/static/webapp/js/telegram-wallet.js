
import { tonConnect } from './tonconnect.js';
import { AuthSystem } from './auth-system.js';

class TelegramWalletIntegrator {
  constructor(walletUi) {
    this.walletUi = walletUi; // #wallet-balance-card or container
    this.connectBtn = null;
    this.walletAddressEl = null;
    this.statusEl = null;
    this.errorEl = null;
    this.loadingEl = null;
    
    this.initElements();
    this.bindEvents();
    this.initWalletState();
  }

  initElements() {
    this.connectBtn = this.walletUi.querySelector('#connectBtn');
    this.walletAddressEl = this.walletUi.querySelector('#walletAddress');
    this.statusEl = this.walletUi.querySelector('#status');
    this.errorEl = this.walletUi.querySelector('#error');
    this.loadingEl = this.walletUi.querySelector('#loading');
  }

  bindEvents() {
    // TON Connect events
    tonConnect.on('ready', () => this.updateUI());
    tonConnect.on('connected', (account) => this.handleConnect(account));
    tonConnect.on('disconnected', () => this.handleDisconnect());
    tonConnect.on('error', (error) => this.handleError(error));

    // Button click
    if (this.connectBtn) {
      this.connectBtn.addEventListener('click', () => this.connect());
    }
  }

  async initWalletState() {
    // Wait for TON Connect ready
    await tonConnect.init();
    await this.updateUI();
  }

  async connect() {
    if (tonConnect.isConnecting || tonConnect.getAccount()) return;

    this.setLoading(true);
    this.clearError();

    try {
      const account = await tonConnect.connectWallet();
      if (!account) {
        this.setError('No wallet selected');
        return;
      }

      // Auto-sync with backend
      await this.syncWithBackend(account.address);
      
    } catch (error) {
      this.setError(error.message || 'Connection failed');
    } finally {
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
      const initData = AuthSystem.getTelegramInitData();
      if (!initData) {
        throw new Error('Telegram auth required');
      }

      const response = await fetch('/api/v1/walletconnect/connect', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Telegram-Init-Data': initData,
        },
        body: JSON.stringify({
          wallet_address: walletAddress,
          blockchain: 'ton',
          wallet_name: 'TON Connect Wallet'  // Optional name
        }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || `Sync failed: ${response.status}`);
      }

      console.log('[TelegramWallet] Backend sync OK');
      this.setStatus('Synced with backend ✓');
      
    } catch (error) {
      console.error('[TelegramWallet] Backend sync failed:', error);
      this.setError(`Sync failed: ${error.message}`);
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
}

// Export for modules
export default TelegramWalletIntegrator;

// Auto-init on pages that include it
if (typeof window !== 'undefined') {
  window.TelegramWalletIntegrator = TelegramWalletIntegrator;
}

