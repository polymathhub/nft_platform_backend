

import { api, endpoints } from './api.js';
import { Toast } from './components.js';

/**
 * UNIFIED AUTH MANAGER - TELEGRAM-ONLY STATELESS AUTHENTICATION
 * ===============================================================
 * 
 * ✅ WHAT'S NEW:
 * - NO JWT tokens
 * - NO localStorage token storage
 * - NO refresh tokens
 * - Stateless: Uses session cookies only (sent automatically by browser)
 * - Every Telegram WebApp request includes window.Telegram.WebApp.initData
 * 
 * FLOW:
 * 1. Frontend reads window.Telegram.WebApp.initData
 * 2. Frontend sends initData to /api/v1/auth/telegram/login
 * 3. Backend verifies using HMAC-SHA256 with bot token
 * 4. Backend returns user object
 * 5. Frontend stores user in memory (NOT localStorage)
 * 6. All API calls include session cookie (automatic)
 */

export class UnifiedAuthManager {
  constructor() {
    this.tg = null;
    this.tonConnectUI = null;
    this.user = null;
    this.isAuthenticated = false;
    this.authMethod = null; // 'telegram' | 'ton_wallet'
    this.isLoading = false;
    
    // ❌ REMOVED: accessToken, refreshToken - no JWT anymore!
    
    this.initializeAll();
  }

  /**
   * Initialize all authentication systems
   */
  async initializeAll() {
    try {
      this.initTelegram();
      this.initTonConnect();
      this.setupEventListeners();
      await this.restoreSession();
      console.log('[Auth] ✅ Initialization complete (Telegram-only)');
    } catch (error) {
      console.error('[Auth] Initialization error:', error);
      this.dispatchEvent('auth:initialized', { user: null });
    }
  }

  /**
   * Initialize Telegram WebApp API
   */
  initTelegram() {
    try {
      if (typeof window !== 'undefined' && window.Telegram?.WebApp) {
        this.tg = window.Telegram.WebApp;
        this.tg.expand();
        this.tg.isClosingConfirmationEnabled = true;
        this.tg.setHeaderColor('#0f0f1a');
        this.tg.setBackgroundColor('#0f0f1a');
        console.log('[Auth] ✅ Telegram WebApp initialized');
      }
    } catch (error) {
      console.warn('[Auth] Telegram init failed (normal if not in Telegram):', error.message);
    }
  }

  /**
   * Initialize TonConnect UI
   */
  initTonConnect() {
    try {
      if (typeof TonConnectUI !== 'undefined') {
        const manifestUrl = (function(){ try { return new URL('/tonconnect-manifest.json', window.location.href).href } catch(e){ return (window.location && window.location.origin ? window.location.origin.replace(/\/+$/,'') : '') + '/tonconnect-manifest.json' } })();
        this.tonConnectUI = new TonConnectUI({ manifestUrl });
        console.log('[Auth] ✅ TonConnect UI initialized');
        
        if (this.tonConnectUI && typeof this.tonConnectUI.onStatusChange === 'function') {
          this.tonConnectUI.onStatusChange((wallet) => {
            this.handleTonConnectStatusChange(wallet);
          });
        }
      }
    } catch (error) {
      console.warn('[Auth] TonConnect init failed:', error.message);
    }
  }

  /**
   * Restore session from backend (NO localStorage token restoration)
   */
  async restoreSession() {
    try {
      // PRIMARY: Try Telegram authentication
      if (this.tg && this.tg.initData) {
        console.log('[Auth] 🔵 Attempting Telegram authentication (initData)...');
        try {
          const response = await api.post(endpoints.unifiedAuth.telegramLogin, {
            init_data: this.tg.initData
          });

          if (response.success && response.user) {
            this.setUser(response.user);
            this.authMethod = 'telegram';
            console.log('[Auth] ✅ Telegram authentication successful');
            this.dispatchEvent('auth:initialized', { user: this.user });
            return;
          }
        } catch (error) {
          console.warn('[Auth] Telegram authentication failed:', error.message);
        }
      }

      // FALLBACK: Check if user object exists in memory (not localStorage!)
      // This only works if the app is still loaded and hasn't been refreshed
      if (this.user && this.isAuthenticated) {
        console.log('[Auth] Using in-memory user session');
        this.dispatchEvent('auth:initialized', { user: this.user });
        return;
      }
      
      // NO FALLBACK: Don't restore from localStorage - use cookies/server-side sessions only
      console.log('[Auth] No active session found (requires Telegram authentication)');
      this.dispatchEvent('auth:initialized', { user: null });

    } catch (error) {
      console.error('[Auth] Session restoration error:', error);
      this.dispatchEvent('auth:initialized', { user: null });
    }
  }

  /**
   * Validate session when explicitly needed
   */
  async validateSessionOnDemand() {
    try {
      const profile = await api.get(endpoints.unifiedAuth.profile);
      this.setUser(profile);
      console.log('[Auth] ✅ Session validated (on-demand)');
      return true;
    } catch (error) {
      console.warn('[Auth] Session validation failed:', error.message);
      if (error.status === 401) {
        this.logout();
      }
      return false;
    }
  }

  /**
   * Setup event listeners
   */
  setupEventListeners() {
    window.addEventListener('auth:login_telegram', (e) => this.onTelegramLogin(e.detail));
    window.addEventListener('auth:login_ton', (e) => this.onTonLogin(e.detail));
  }

  /**
   * Set user data (MEMORY ONLY - no storage!)
   */
  setUser(userData) {
    if (!userData) {
      console.warn('[Auth] Clearing user data');
      this.user = null;
      this.isAuthenticated = false;
      this.authMethod = null;
      return;
    }

    if (!userData.id || !userData.username || !userData.email) {
      console.error('[Auth] Invalid user data:', userData);
      throw new Error('Invalid user data - missing required fields');
    }

    this.user = {
      id: String(userData.id),
      email: String(userData.email || ''),
      username: String(userData.username || ''),
      full_name: userData.full_name ? String(userData.full_name) : null,
      avatar: userData.avatar_url ? String(userData.avatar_url) : (userData.avatar ? String(userData.avatar) : null),
      telegramId: userData.telegram_id ? String(userData.telegram_id) : null,
      telegram_username: userData.telegram_username || null,
      tonWalletAddress: userData.ton_wallet_address ? String(userData.ton_wallet_address) : null,
      role: String(userData.user_role || 'user'),
      createdAt: userData.created_at ? new Date(userData.created_at) : new Date(),
      ...userData,
    };

    console.log('[Auth] ✅ User set in memory:', {
      id: this.user.id,
      username: this.user.username,
      email: this.user.email
    });

    this.isAuthenticated = true;
    
    // ❌ REMOVED: localStorage.setItem('user', ...) - no client-side storage!
  }

  /**
   * Handle Telegram login
   */
  async onTelegramLogin(data) {
    try {
      this.setLoading(true);
      
      console.log('[Auth] 🔵 Starting Telegram login...');
      
      if (!this.tg || !this.tg.initData) {
        throw new Error('Telegram WebApp not initialized');
      }

      const response = await api.post(endpoints.unifiedAuth.telegramLogin, {
        init_data: this.tg.initData
      });

      if (!response || !response.user) {
        throw new Error('Invalid response from backend');
      }
      
      this.setUser(response.user);
      this.authMethod = 'telegram';
      
      Toast.success('✅ Logged in with Telegram!');
      console.log('[Auth] ✅ Telegram login successful');
      this.dispatchEvent('auth:login_telegram', { user: this.user });
      
      return this.user;
    } catch (error) {
      console.error('[Auth] ❌ Telegram login error:', error);
      Toast.error(`Login failed: ${error.message}`);
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

      const walletAddress = this.tonConnectUI.wallet.account?.address;
      if (!walletAddress) {
        throw new Error('Failed to get wallet address');
      }

      const response = await api.post(endpoints.unifiedAuth.tonLogin, {
        wallet_address: walletAddress,
        wallet_info: this.tonConnectUI.wallet,
      });
      
      this.setUser(response.user);
      this.authMethod = 'ton_wallet';
      
      Toast.success('✅ Logged in with TON Wallet!');
      this.dispatchEvent('auth:login_ton', { user: this.user });
      
      return this.user;
    } catch (error) {
      console.error('[Auth] TON login error:', error);
      Toast.error(`TON login failed: ${error.message}`);
      this.dispatchEvent('auth:error', { error: error.message, method: 'ton' });
      throw error;
    } finally {
      this.setLoading(false);
    }
  }

  /**
   * Handle TonConnect status changes
   */
  handleTonConnectStatusChange(wallet) {
    if (wallet) {
      console.log('[Auth] TonConnect wallet connected:', wallet.account?.address);
      this.dispatchEvent('tonconnect:connected', { wallet });
    } else {
      console.log('[Auth] TonConnect wallet disconnected');
      this.dispatchEvent('tonconnect:disconnected', {});
    }
  }

  /**
   * Logout - clear memory only (session cookie cleared by server)
   */
  async logout() {
    try {
      console.log('[Auth] Logging out...');
      
      // Call backend to clear server-side session
      try {
        await api.post(endpoints.unifiedAuth.logout, {});
      } catch (error) {
        console.warn('[Auth] Backend logout failed:', error.message);
        // Continue anyway - we'll clear client state
      }
      
      // Clear memory state
      this.user = null;
      this.isAuthenticated = false;
      this.authMethod = null;
      
      // ❌ REMOVED: localStorage.removeItem calls - no client storage!
      
      Toast.success('Logged out');
      this.dispatchEvent('auth:logout', {});
      
      console.log('[Auth] ✅ Logout complete');
    } catch (error) {
      console.error('[Auth] Logout error:', error);
      // Force local logout anyway
      this.user = null;
      this.isAuthenticated = false;
    }
  }

  /**
   * Get current user
   */
  getUser() {
    return this.user;
  }

  /**
   * Check if authenticated
   */
  isUserAuthenticated() {
    return this.isAuthenticated && !!this.user;
  }

  /**
   * Set loading state
   */
  setLoading(value) {
    this.isLoading = value;
    this.dispatchEvent('auth:loading', { loading: value });
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
