/**
 * Telegram Wallet Connection Module (DEPRECATED - USE auth-bootstrap-telegram.js INSTEAD)
 * 
 * This is a compatibility facade for the new Web3/stateless auth system.
 * All authentication is now handled via Telegram WebApp initData (no tokens).
 * 
 * @deprecated Use window.authManager from auth-bootstrap-telegram.js instead
 * @module js/telegram-wallet.js
 */

class TelegramWalletManager {
  constructor() {
    this.tg = window.Telegram?.WebApp ?? null;
    this.isAvailable = !!this.tg;
    this.isConnected = false;
    this.user = null;
  }

  /**
   * Check if Telegram context is available
   */
  isReady() {
    return this.isAvailable && this.tg?.initData;
  }

  /**
   * Get Telegram user data
   */
  getTelegramUser() {
    if (!this.tg?.initDataUnsafe?.user) {
      return null;
    }
    return this.tg.initDataUnsafe.user;
  }

  /**
   * Authenticate via Telegram (stateless - uses initData only)
   * 
   * This uses the new Web3-based auth system.
   * No tokens are stored. User is identified via Telegram initData.
   */
  async authenticate() {
    try {
      if (!this.isReady()) {
        throw new Error('Telegram WebApp not available');
      }

      console.log('🔐 Authenticating with Telegram (stateless)...');

      // Use the global authManager from auth-bootstrap-telegram.js
      if (!window.authManager) {
        throw new Error('Auth system not initialized');
      }

      // Wait for auth to be ready
      if (!window.authManager.isInitialized) {
        // If not initialized yet, wait for auth:initialized event
        await new Promise((resolve, reject) => {
          const timeout = setTimeout(() => {
            window.removeEventListener('auth:initialized', handleInit);
            reject(new Error('Auth initialization timeout'));
          }, 5000);

          const handleInit = () => {
            clearTimeout(timeout);
            window.removeEventListener('auth:initialized', handleInit);
            resolve();
          };
          window.addEventListener('auth:initialized', handleInit);
        });
      }

      // Get authenticated user from authManager
      const user = window.authManager.getUser();
      if (user) {
        this.isConnected = true;
        this.user = user;
        console.log('✅ Connected to Telegram (stateless auth)');
        return { success: true, user: user };
      } else {
        throw new Error('Not authenticated');
      }
    } catch (error) {
      console.error('Telegram wallet authentication error:', error);
      throw error;
    }
  }

  /**
   * Disconnect Telegram wallet (stateless - just clears client state)
   */
  disconnect() {
    this.isConnected = false;
    this.user = null;
    if (window.authManager) {
      window.authManager.logout();
    }
    console.log('🔌 Disconnected from Telegram wallet');
  }

  /**
   * Get user display name
   */
  getUserName() {
    return this.user?.username || 
           this.tg?.initDataUnsafe?.user?.username ||
           'Telegram User';
  }

  /**
   * Get user ID
   */
  getUserId() {
    return this.user?.id || this.tg?.initDataUnsafe?.user?.id;
  }
}

export const telegramWallet = new TelegramWalletManager();
