/**
 * Unified Authentication Manager
 * Handles both TON Wallet (via TonConnect) and Telegram authentication
 * Provides consistent error handling, button state management, and validation
 */

import { api, endpoints } from './api.js';
import { Toast } from './components.js';

export class UnifiedAuthManager {
  constructor() {
    this.tg = null;
    this.tonConnectUI = null;
    this.user = null;
    this.isAuthenticated = false;
    this.authMethod = null; // 'telegram' | 'ton_wallet' | 'email'
    this.isLoading = false;
    
    this.initializeAll();
  }

  /**
   * Initialize all authentication systems
   */
  async initializeAll() {
    this.initTelegram();
    this.initTonConnect();
    this.setupEventListeners();
    await this.restoreSession();
  }

  /**
   * Initialize Telegram WebApp API
   */
  initTelegram() {
    if (typeof window !== 'undefined' && window.Telegram?.WebApp) {
      this.tg = window.Telegram.WebApp;
      this.tg.expand();
      this.tg.isClosingConfirmationEnabled = true;
      this.tg.setHeaderColor('#0f0f1a');
      this.tg.setBackgroundColor('#0f0f1a');
      console.log('Telegram WebApp initialized');
    }
  }

  /**
   * Initialize TonConnect UI for wallet connection
   */
  initTonConnect() {
    try {
      // Check if TonConnect UI library is available
      if (typeof TonConnectUI !== 'undefined') {
        this.tonConnectUI = new TonConnectUI({
          manifestUrl: '/tonconnect-manifest.json',
        });
        console.log('TonConnect UI initialized');
        
        // Setup TonConnect event listeners
        this.tonConnectUI.onStatusChange((wallet) => {
          this.handleTonConnectStatusChange(wallet);
        });
      } else {
        console.warn(' TonConnect UI SDK not loaded');
      }
    } catch (error) {
      console.error('Failed to initialize TonConnect:', error);
    }
  }

  /**
   * Restore session from backend
   */
  async restoreSession() {
    try {
      const profile = await api.get(endpoints.unifiedAuth.profile);
      this.setUser(profile);
      console.log('Session restored');
      this.dispatchEvent('auth:initialized', { user: this.user });
    } catch (error) {
      console.log('No active session');
    }
  }

  /**
   * Setup global event listeners
   */
  setupEventListeners() {
    // Listen for auth events
    window.addEventListener('auth:login_telegram', (e) => this.onTelegramLogin(e.detail));
    window.addEventListener('auth:login_ton', (e) => this.onTonLogin(e.detail));
  }

  /**
   * Set user data after authentication
   */
  setUser(userData) {
    if (!userData) {
      this.user = null;
      this.isAuthenticated = false;
      this.authMethod = null;
      return;
    }

    this.user = {
      id: String(userData.id),
      email: String(userData.email || ''),
      username: String(userData.username || ''),
      avatar: userData.avatar ? String(userData.avatar) : null,
      telegramId: userData.telegram_id ? String(userData.telegram_id) : null,
      tonWalletAddress: userData.ton_wallet_address ? String(userData.ton_wallet_address) : null,
      role: String(userData.user_role || 'user'),
      createdAt: userData.created_at ? new Date(userData.created_at) : new Date(),
      ...userData,
    };

    this.isAuthenticated = true;
  }

  /**
   * Handle Telegram login
   */
  async onTelegramLogin(data) {
    try {
      this.setLoading(true);
      
      // Validate Telegram data
      if (!this.tg || !this.tg.initData) {
        throw new Error('Telegram WebApp not properly initialized');
      }

      // Send to backend for verification
      const response = await api.post(endpoints.unifiedAuth.telegramLogin, {
        init_data: this.tg.initData,
        user_id: this.tg.initDataUnsafe?.user?.id,
        username: this.tg.initDataUnsafe?.user?.username,
      });

      this.setUser(response.user);
      this.authMethod = 'telegram';
      
      Toast.success('Logged in with Telegram!');
      this.dispatchEvent('auth:login_telegram', { user: this.user });
      
      // Redirect to dashboard after successful login
      setTimeout(() => {
        window.location.href = '/webapp/dashboard.html';
      }, 1000);
      
      return this.user;
    } catch (error) {
      console.error('Telegram login error:', error);
      Toast.error(`Telegram login failed: ${error.message}`);
      this.dispatchEvent('auth:error', { error: error.message, method: 'telegram' });
      throw error;
    } finally {
      this.setLoading(false);
    }
  }

  /**
   * Handle TON wallet connection
   */
  async onTonLogin(data) {
    try {
      this.setLoading(true);

      if (!this.tonConnectUI || !this.tonConnectUI.wallet) {
        throw new Error('TON wallet not connected');
      }

      const walletInfo = this.tonConnectUI.wallet;
      const walletAddress = walletInfo.account?.address;

      if (!walletAddress) {
        throw new Error('Failed to get wallet address from TonConnect');
      }

      // Send to backend for verification and user creation
      const response = await api.post(endpoints.unifiedAuth.tonLogin, {
        wallet_address: walletAddress,
        wallet_info: walletInfo,
      });

      this.setUser(response.user);
      this.authMethod = 'ton_wallet';
      
      Toast.success('Connected TON wallet!');
      this.dispatchEvent('auth:login_ton', { user: this.user });
      
      // Redirect to dashboard
      setTimeout(() => {
        window.location.href = '/webapp/dashboard.html';
      }, 1000);
      
      return this.user;
    } catch (error) {
      console.error('TON wallet login error:', error);
      Toast.error(`TON wallet connection failed: ${error.message}`);
      this.dispatchEvent('auth:error', { error: error.message, method: 'ton' });
      throw error;
    } finally {
      this.setLoading(false);
    }
  }

  /**
   * Handle TON Connect status changes
   */
  async handleTonConnectStatusChange(wallet) {
    if (wallet) {
      console.log(' TON wallet connected:', wallet);
      this.dispatchEvent('ton:connected', { wallet });
    } else {
      console.log('TON wallet disconnected');
      this.dispatchEvent('ton:disconnected');
    }
  }

  /**
   * Get Telegram data (read-only)
   */
  getTelegramData() {
    if (!this.tg) return null;

    return {
      initData: this.tg?.initData || null,
      initDataUnsafe: this.tg?.initDataUnsafe || null,
      user: this.tg?.initDataUnsafe?.user || null,
      isBot: this.tg?.initDataUnsafe?.user?.is_bot || false,
    };
  }

  /**
   * Disconnect TON wallet
   */
  async disconnectTon() {
    try {
      if (this.tonConnectUI) {
        await this.tonConnectUI.disconnect();
        console.log('TON wallet disconnected');
        this.dispatchEvent('ton:disconnected');
      }
    } catch (error) {
      console.error('Failed to disconnect TON wallet:', error);
      Toast.error('Failed to disconnect wallet');
    }
  }

  /**
   * Logout user
   */
  async logout() {
    try {
      // Disconnect TON wallet if connected
      if (this.tonConnectUI?.wallet) {
        await this.disconnectTon();
      }

      // Call logout endpoint
      try {
        await api.post(endpoints.auth.logout, {});
      } catch (error) {
        console.warn('Logout endpoint error:', error);
      }

      // Clear local state
      this.user = null;
      this.isAuthenticated = false;
      this.authMethod = null;

      Toast.success('Logged out');
      this.dispatchEvent('auth:logout');

      // Redirect to login
      setTimeout(() => {
        window.location.href = '/';
      }, 500);
    } catch (error) {
      console.error('Logout error:', error);
      Toast.error('Failed to logout');
    }
  }

  /**
   * Set loading state and dispatch event
   */
  setLoading(state) {
    this.isLoading = state;
    this.dispatchEvent('auth:loading', { isLoading: state });
  }

  /**
   * Check if user is authenticated
   */
  isLoggedIn() {
    return this.isAuthenticated && this.user;
  }

  /**
   * Get current user
   */
  getUser() {
    return this.user;
  }

  /**
   * Check user role
   */
  hasRole(role) {
    if (!this.isAuthenticated) return false;
    if (!role) return true;
    if (this.user.role === 'admin') return true;
    return this.user.role === role;
  }

  /**
   * Dispatch custom event
   */
  dispatchEvent(eventName, detail = {}) {
    window.dispatchEvent(new CustomEvent(eventName, { detail }));
  }
}

// Export singleton instance
export const authManager = new UnifiedAuthManager();
