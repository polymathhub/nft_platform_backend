/**
 * GetGems Wallet Integration - Updated telegram-wallet.js
 * 
 * Drop-in replacement showing how to use GetGemsWallet instead of TonConnect
 */

class TelegramWalletIntegrator {
  constructor(walletUi) {
    this.walletUi = walletUi; // #wallet-balance-card or container
    this.connectBtn = null;
    this.walletAddressEl = null;
    this.statusEl = null;
    this.errorEl = null;
    this.loadingEl = null;
    this.walletTypeEl = null;
    
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
    this.walletTypeEl = this.walletUi.querySelector('#walletType');
  }

  bindEvents() {
    // GetGems Wallet events
    getGemsWallet.on('ready', () => this.updateUI());
    getGemsWallet.on('connected', (account) => this.handleConnect(account));
    getGemsWallet.on('disconnected', () => this.handleDisconnect());
    getGemsWallet.on('error', (error) => this.handleError(error));
    getGemsWallet.on('fallback-to-tonconnect', () => this.handleFallback());
    getGemsWallet.on('transaction-sent', (result) => this.handleTransactionSent(result));

    // Button click
    if (this.connectBtn) {
      this.connectBtn.addEventListener('click', () => this.connect());
    }
  }

  async initWalletState() {
    try {
      // Wait for GetGems Wallet ready
      await getGemsWallet.init();
      await this.updateUI();
    } catch (error) {
      console.error('[TelegramWallet] Init error:', error);
      this.setError('Wallet initialization failed');
    }
  }

  async connect() {
    // Already connected
    if (getGemsWallet.getConnected()) {
      console.log('[TelegramWallet] Already connected to:', getGemsWallet.getAddress());
      return;
    }

    this.setLoading(true);
    this.clearError();

    try {
      console.log('[TelegramWallet] Connecting wallet...');
      const account = await getGemsWallet.connect();
      
      if (!account) {
        this.setError('No wallet selected');
        return;
      }

      console.log('[TelegramWallet] Connected to:', account.address);
      
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
    console.log('[TelegramWallet] Wallet type:', account.walletType);
    this.updateUI(account);
    await this.syncWithBackend(account.address);
  }

  async handleDisconnect() {
    console.log('[TelegramWallet] Disconnected');
    this.updateUI();
  }

  async handleError(error) {
    console.error('[TelegramWallet] Wallet error:', error);
    this.setError(error.message || 'Wallet error');
    this.updateUI();
  }

  handleFallback() {
    console.log('[TelegramWallet] Using TonConnect fallback (no native wallet)');
    this.setStatus('Using TonConnect (no native wallet detected)');
  }

  handleTransactionSent(result) {
    console.log('[TelegramWallet] Transaction sent:', result);
    this.setStatus('Transaction sent ✓');
    setTimeout(() => {
      if (getGemsWallet.getConnected()) {
        this.setStatus(`Connected via ${getGemsWallet.getWalletType()}`);
      }
    }, 3000);
  }

  async updateUI(account = null) {
    const conn = account || (getGemsWallet.getConnected() ? { address: getGemsWallet.getAddress() } : null);
    
    if (conn) {
      // Connected state
      if (this.connectBtn) {
        this.connectBtn.textContent = 'Disconnect';
        this.connectBtn.onclick = () => this.disconnect();
      }

      if (this.walletAddressEl) {
        this.walletAddressEl.textContent = this.shortenAddress(conn.address);
        this.walletAddressEl.style.cursor = 'pointer';
        this.walletAddressEl.onclick = () => this.copyAddress(conn.address);
      }

      if (this.walletTypeEl) {
        this.walletTypeEl.textContent = `[${getGemsWallet.getWalletType().toUpperCase()}]`;
      }

      this.setStatus('Connected to TON');
      this.clearError();
    } else {
      // Disconnected state
      if (this.connectBtn) {
        this.connectBtn.textContent = 'Connect Wallet';
        this.connectBtn.onclick = () => this.connect();
      }

      if (this.walletAddressEl) {
        this.walletAddressEl.textContent = 'Not connected';
      }

      if (this.walletTypeEl) {
        this.walletTypeEl.textContent = '';
      }

      this.setStatus('Ready to connect');
    }
  }

  async copyAddress(address) {
    try {
      await navigator.clipboard.writeText(address);
      this.setStatus('Address copied ✓');
      setTimeout(() => {
        this.setStatus(`Connected via ${getGemsWallet.getWalletType()}`);
      }, 2000);
    } catch (err) {
      this.setError('Copy failed');
    }
  }

  async disconnect() {
    try {
      await getGemsWallet.disconnect();
      this.updateUI();
      this.setStatus('Disconnected');
    } catch (error) {
      this.setError('Disconnect failed: ' + error.message);
    }
  }

  async syncWithBackend(walletAddress) {
    try {
      // Get Telegram auth if available
      const initData = window.Telegram?.WebApp?.initData;
      if (!initData) {
        console.warn('[TelegramWallet] No Telegram init data');
        return;
      }

      // Send to backend
      const response = await fetch('/api/wallet/connect', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Telegram-Init-Data': initData,
        },
        body: JSON.stringify({
          walletAddress: walletAddress,
          walletType: getGemsWallet.getWalletType(),
        })
      });

      if (!response.ok) {
        throw new Error(`Backend sync failed: ${response.status}`);
      }

      const data = await response.json();
      console.log('[TelegramWallet] Backend sync successful:', data);
      
    } catch (error) {
      console.error('[TelegramWallet] Backend sync error:', error);
      // Don't fail the connection if backend sync fails
    }
  }

  async sendNFTPurchaseTransaction(nftContract, amount) {
    if (!getGemsWallet.getConnected()) {
      this.setError('Wallet not connected');
      return;
    }

    this.setLoading(true);

    try {
      const tx = {
        to: nftContract,
        value: amount.toString(),  // in nanotons
        data: this.buildNFTTransactionBody(),
      };

      console.log('[TelegramWallet] Sending NFT purchase transaction...');
      const result = await getGemsWallet.sendTransaction(tx);
      console.log('[TelegramWallet] Transaction result:', result);

      this.setStatus('NFT purchase sent ✓');
      return result;

    } catch (error) {
      this.setError('NFT purchase failed: ' + error.message);
      console.error('[TelegramWallet] NFT purchase error:', error);
    } finally {
      this.setLoading(false);
    }
  }

  buildNFTTransactionBody() {
    // Build the transaction body for NFT purchase
    // This is a simplified example
    return 'te6ccgECHwEAA9gAAkWIAWV7Is01Syor7pn-AgEg4vHj9ABk-KFlKSXxVXxxGCfBIIIQF41VICLvdDAO9EHJST0DE8F0DkyDmAEUERKqElvHcUERKqElvHcUxwIIIQF41VICHG6MARAAAAAAAAAAZQAAAAA';
  }

  shortenAddress(address, chars = 6) {
    if (!address) return '';
    return `${address.slice(0, chars)}...${address.slice(-chars)}`;
  }

  setLoading(show) {
    if (this.loadingEl) {
      this.loadingEl.style.display = show ? 'block' : 'none';
    }
  }

  setStatus(message) {
    if (this.statusEl) {
      this.statusEl.textContent = message;
      this.statusEl.style.color = '#4CAF50';
    }
  }

  setError(message) {
    if (this.errorEl) {
      this.errorEl.textContent = message;
      this.errorEl.style.display = 'block';
    }
  }

  clearError() {
    if (this.errorEl) {
      this.errorEl.textContent = '';
      this.errorEl.style.display = 'none';
    }
  }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    const walletContainer = document.getElementById('wallet-balance-card');
    if (walletContainer) {
      window.telegramWalletIntegrator = new TelegramWalletIntegrator(walletContainer);
    }
  });
} else {
  const walletContainer = document.getElementById('wallet-balance-card');
  if (walletContainer) {
    window.telegramWalletIntegrator = new TelegramWalletIntegrator(walletContainer);
  }
}

// For backwards compatibility with existing code
async function connectWalletGetGems() {
  try {
    return await getGemsWallet.connect();
  } catch (error) {
    console.error('[GetGemsWallet] Connect failed:', error);
    throw error;
  }
}

async function disconnectWalletGetGems() {
  try {
    return await getGemsWallet.disconnect();
  } catch (error) {
    console.error('[GetGemsWallet] Disconnect failed:', error);
    throw error;
  }
}

function getWalletAddressGetGems() {
  return getGemsWallet.getAddress();
}

function getWalletTypeGetGems() {
  return getGemsWallet.getWalletType();
}

function isWalletConnectedGetGems() {
  return getGemsWallet.getConnected();
}
