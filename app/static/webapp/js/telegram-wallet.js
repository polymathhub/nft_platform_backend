/**
 * Telegram Wallet Connection Module
 * Handles Telegram Web App wallet authentication
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
   * Check if Telegram contextis available
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
   * Authenticate via Telegram
   */
  async authenticate() {
    try {
      if (!this.isReady()) {
        throw new Error('Telegram WebApp not available');
      }

      console.log('🔐 Authenticating with Telegram...');

      const response = await fetch('/api/v1/auth/telegram/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          init_data: this.tg.initData,
          user_id: this.tg.initDataUnsafe?.user?.id,
          username: this.tg.initDataUnsafe?.user?.username,
        })
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Authentication failed');
      }

      const data = await response.json();
      if (data.token) {
        localStorage.setItem('token', data.token);
        this.isConnected = true;
        this.user = data.user;
        console.log('✅ Connected to Telegram wallet');
        return { success: true, user: data.user, token: data.token };
      } else {
        throw new Error('No token received');
      }
    } catch (error) {
      console.error('Telegram wallet authentication error:', error);
      throw error;
    }
  }

  /**
   * Disconnect Telegram wallet
   */
  disconnect() {
    localStorage.removeItem('token');
    this.isConnected = false;
    this.user = null;
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
