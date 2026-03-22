/**
 * Wallet Utilities
 * Provides reusable functions for wallet connection checks and notifications
 */

import { Toast } from './components.js';

class WalletUtils {
  constructor() {
    this.tonConnect = null;
  }

  /**
   * Initialize with TonConnect manager
   */
  setTonConnect(tonConnectManager) {
    this.tonConnect = tonConnectManager;
  }

  /**
   * Check if wallet is connected, show notification if not
   * and optionally trigger connection modal
   */
  async ensureWalletConnected(options = {}) {
    const {
      showNotification = true,
      triggerConnect = true,
      actionName = 'perform this action'
    } = options;

    // Check if wallet is already connected
    if (this.tonConnect && this.tonConnect.isConnected()) {
      return true;
    }

    // Show notification about missing wallet
    if (showNotification) {
      Toast.show({
        title: 'Wallet Required',
        description: `Please connect your TON wallet to ${actionName}.`,
        type: 'warning',
        duration: 3000
      });
    }

    // Optionally trigger wallet connection modal
    if (triggerConnect && this.tonConnect) {
      try {
        console.log('Opening wallet connection modal...');
        const ready = await this.tonConnect.waitForReady();
        if (ready) {
          const result = await this.tonConnect.openModal();
          if (result && result.account) {
            Toast.show({
              title: 'Wallet Connected',
              description: 'Your TON wallet is now connected.',
              type: 'success',
              duration: 2000
            });
            return true;
          }
        }
      } catch (error) {
        console.error('Error connecting wallet:', error);
        Toast.show({
          title: 'Connection Failed',
          description: 'Failed to connect wallet. Please try again.',
          type: 'error',
          duration: 3000
        });
      }
    }

    return false;
  }

  /**
   * Get wallet address or trigger connection
   */
  async getWalletAddress(options = {}) {
    if (this.tonConnect && this.tonConnect.isConnected()) {
      return this.tonConnect.getWalletAddress();
    }

    const connected = await this.ensureWalletConnected({
      showNotification: true,
      triggerConnect: true,
      actionName: options.actionName || 'get your wallet address'
    });

    if (connected && this.tonConnect) {
      return this.tonConnect.getWalletAddress();
    }

    return null;
  }

  /**
   * Navigate to wallet page if not connected
   */
  navigateToWalletIfNeeded() {
    if (this.tonConnect && !this.tonConnect.isConnected()) {
      // Do not perform automatic redirect; prompt user via UI instead.
      Toast.show({
        title: 'Wallet Required',
        description: 'Please open the Wallet page to connect your TON wallet.',
        type: 'info',
        duration: 4000
      });
      return false;
    }
    return false;
  }
}

// Export singleton instance
export const walletUtils = new WalletUtils();
