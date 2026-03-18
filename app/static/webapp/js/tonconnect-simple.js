/**
 * Minimal TonConnect Manager
 * Simplified for actual functionality
 */
class TonConnectManager {
  constructor() {
    this.tonConnectUI = null;
    this.isReady = false;
    this.wallet = null;
  }

  getManifestUrl() {
    try {
      return new URL('/tonconnect-manifest.json', window.location.href).href;
    } catch (e) {
      const origin = window.location && window.location.origin ? window.location.origin : '';
      return (origin ? origin.replace(/\/+$/,'') : '') + '/tonconnect-manifest.json';
    }
  }

  async initialize() {
    try {
      if (typeof TonConnectUI === 'undefined') {
        console.error('TonConnectUI not loaded');
        return false;
      }

      console.log('Initializing TonConnect...');
      
      this.tonConnectUI = new TonConnectUI({
        manifestUrl: this.getManifestUrl()
      });

      this.isReady = true;
      console.log('TonConnect ready');
      return true;
    } catch (error) {
      console.error('TonConnect init error:', error);
      return false;
    }
  }

  async openModal() {
    if (!this.isReady || !this.tonConnectUI) {
      throw new Error('TonConnect not initialized');
    }

    try {
    console.log('Opening wallet modal...');
      const result = await this.tonConnectUI.openModal();
      
      if (result?.account?.address) {
        this.wallet = result;
        console.log('Wallet connected:', result.account.address);
        return result;
      }
      
      console.log('No wallet selected');
      return null;
    } catch (error) {
      console.error('Modal error:', error);
      throw error;
    }
  }

  async waitForReady() {
    if (this.isReady) return true;
    
    for (let i = 0; i < 10; i++) {
      if (this.isReady) return true;
      await new Promise(r => setTimeout(r, 100));
    }
    
    return false;
  }

  getWallet() {
    return this.wallet;
  }

  isConnected() {
    return !!this.wallet?.account?.address;
  }
}

export const tonConnect = new TonConnectManager();
