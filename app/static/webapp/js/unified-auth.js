

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
    this.accessToken = null;
    this.refreshToken = null;
    
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
      console.log('[Auth] Initialization complete');
    } catch (error) {
      console.error('[Auth] Critical initialization error:', error);
      // Continue anyway - app should work even with partial auth
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
        console.log('[Auth] Telegram WebApp initialized');
      }
    } catch (error) {
      console.warn('[Auth] Telegram initialization failed (not in Telegram?):', error.message);
    }
  }

  /**
   * Initialize TonConnect UI for wallet connection
   */
  initTonConnect() {
    try {
      // Check if TonConnect UI library is available
      if (typeof TonConnectUI !== 'undefined') {
        const manifestUrl = (function(){ try { return new URL('/tonconnect-manifest.json', window.location.href).href } catch(e){ return (window.location && window.location.origin ? window.location.origin.replace(/\/+$/,'') : '') + '/tonconnect-manifest.json' } })();
        this.tonConnectUI = new TonConnectUI({
          manifestUrl,
        });
        console.log('[Auth] TonConnect UI initialized at:', manifestUrl);
        
        // Setup TonConnect event listeners
        if (this.tonConnectUI && typeof this.tonConnectUI.onStatusChange === 'function') {
          this.tonConnectUI.onStatusChange((wallet) => {
            this.handleTonConnectStatusChange(wallet);
          });
        }
      } else {
        console.log('[Auth] TonConnect UI SDK not available (optional)');
      }
    } catch (error) {
      console.warn('[Auth] TonConnect initialization failed (optional):', error.message);
    }
  }

  /**
   * Restore session from backend and localStorage
   */
  async restoreSession() {
    try {
      // First check localStorage for cached user and token (fastest)
      const cachedUser = localStorage.getItem('user');
      const cachedToken = localStorage.getItem('token');
      
      if (cachedUser && cachedToken) {
        try {
          this.user = JSON.parse(cachedUser);
          this.isAuthenticated = true;
          console.log('[Auth] Session restored from localStorage (cached)');
          this.dispatchEvent('auth:initialized', { user: this.user });
          
          // Validate token in background (non-blocking)
          // This is CRITICAL: refresh the session from backend to ensure it's still valid
          setTimeout(() => this.validateSessionInBackground(), 500);
          return;
        } catch (e) {
          console.log('[Auth] Failed to parse cached user');
        }
      }
      
      // If no cache, try to restore from backend (slower)
      // But use Promise.race with a short timeout to avoid hanging
      try {
        const profile = await Promise.race([
          api.get(endpoints.unifiedAuth.profile),
          new Promise((_, reject) => 
            setTimeout(() => reject(new Error('Session restore timeout')), 5000)
          )
        ]);
        this.setUser(profile);
        console.log('[Auth] Session restored from backend');
        this.dispatchEvent('auth:initialized', { user: this.user });
      } catch (error) {
        // Backend call failed or timed out, that's OK
        console.log('[Auth] No active session found:', error.message);
        this.dispatchEvent('auth:initialized', { user: null });
      }
    } catch (error) {
      console.error('[Auth] Session restoration error:', error);
      // Clear invalid session data
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      this.dispatchEvent('auth:initialized', { user: null });
    }
  }

  /**
   * Validate session in background without blocking
   */
  async validateSessionInBackground() {
    try {
      const profile = await api.get(endpoints.unifiedAuth.profile);
      this.setUser(profile);
      console.log('[Auth] Session validated successfully in background');
    } catch (error) {
      // If validation fails, clear cache for next time
      console.warn('[Auth] Session validation failed in background:', error.message);
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      this.user = null;
      this.isAuthenticated = false;
      this.dispatchEvent('auth:invalid');
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
   * Set user data after authentication with validation
   */
  setUser(userData) {
    if (!userData) {
      console.warn('[Auth] Clearing user data (userData is null/undefined)');
      this.user = null;
      this.isAuthenticated = false;
      this.authMethod = null;
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      return;
    }

    // Validate required fields
    if (!userData.id || !userData.username || !userData.email) {
      console.error('[Auth] Invalid user data - missing required fields:', {
        hasId: !!userData.id,
        hasUsername: !!userData.username,
        hasEmail: !!userData.email,
        userData
      });
      throw new Error('Invalid user data structure - missing required fields (id, username, email)');
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

    console.log('[Auth] User data set:', {
      id: this.user.id,
      username: this.user.username,
      email: this.user.email,
      full_name: this.user.full_name
    });

    this.isAuthenticated = true;
    
    // Store user in localStorage for persistence across page reloads
    localStorage.setItem('user', JSON.stringify(this.user));
  }

  /**
   * Store authentication tokens (access and refresh)
   */
  setTokens(accessToken, refreshToken = null) {
    if (accessToken) {
      localStorage.setItem('token', accessToken);
      this.accessToken = accessToken;
    } else {
      localStorage.removeItem('token');
      this.accessToken = null;
    }
    
    if (refreshToken) {
      localStorage.setItem('refresh_token', refreshToken);
      this.refreshToken = refreshToken;
    } else {
      localStorage.removeItem('refresh_token');
      this.refreshToken = null;
    }
  }

  /**
   * Store authentication token (legacy - stores only access token)
   */
  setToken(token) {
    if (token) {
      localStorage.setItem('token', token);
      this.accessToken = token;
    } else {
      localStorage.removeItem('token');
      this.accessToken = null;
    }
  }

  /**
   * Get stored access token
   */
  getToken() {
    return localStorage.getItem('token');
  }

  /**
   * Get stored refresh token
   */
  getRefreshToken() {
    return localStorage.getItem('refresh_token');
  }

  /**
   * Handle Telegram login with complete error handling
   */
  async onTelegramLogin(data) {
    try {
      this.setLoading(true);
      
      console.log('[Telegram] Starting login process');
      
      // Validate Telegram data
      if (!this.tg || !this.tg.initData) {
        throw new Error('Telegram WebApp not properly initialized');
      }

      // Send to backend for verification
      console.log('[Telegram] Sending initData to backend for verification');
      const response = await api.post(endpoints.unifiedAuth.telegramLogin, {
        init_data: this.tg.initData,
        user_id: this.tg.initDataUnsafe?.user?.id,
        username: this.tg.initDataUnsafe?.user?.username,
      });

      console.log('[Telegram] Backend response received:', {
        success: response.success,
        hasUser: !!response.user,
        userId: response.user?.id,
        username: response.user?.username,
        email: response.user?.email,
        full_name: response.user?.full_name,
        hasTokens: !!response.tokens,
      });
      
      // Validate response structure
      if (!response || !response.user) {
        throw new Error('Invalid response from backend - missing user data');
      }
      
      if (!response.user.id || !response.user.username || !response.user.email) {
        console.error('[Telegram] ✗ Backend returned INCOMPLETE user data:', response.user);
        throw new Error('Backend returned incomplete user data');
      }

      // Store user and tokens (both access and refresh)
      console.log('[Telegram] ✓ Setting user data in auth manager:', {
        id: response.user.id,
        username: response.user.username,
        email: response.user.email,
        full_name: response.user.full_name,
      });
      this.setUser(response.user);
      
      if (response.tokens) {
        this.setTokens(response.tokens.access_token, response.tokens.refresh_token);
        console.log('[Telegram] ✓ Tokens stored successfully');
      } else {
        throw new Error('No tokens in authentication response');
      }
      
      this.authMethod = 'telegram';
      
      Toast.success('Logged in with Telegram!');
      console.log('[Telegram] ✓ Authentication successful, user:', {
        id: this.user.id,
        username: this.user.username,
        in_localStorage: localStorage.getItem('user') ? 'YES' : 'NO',
      });
      this.dispatchEvent('auth:login_telegram', { user: this.user });
      
      return this.user;
    } catch (error) {
      console.error('[Telegram] ✗ Login error:', error);
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

      // Store user and tokens (both access and refresh)
      this.setUser(response.user);
      if (response.tokens) {
        this.setTokens(response.tokens.access_token, response.tokens.refresh_token);
      }
      this.authMethod = 'ton_wallet';
      
      Toast.success('Connected TON wallet!');
      this.dispatchEvent('auth:login_ton', { user: this.user });
      
      // Don't force redirect - let the app handle navigation
      // Pages will update UI based on auth:login_ton event
      
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
      this.accessToken = null;
      this.refreshToken = null;
      localStorage.removeItem('user');
      localStorage.removeItem('token');
      localStorage.removeItem('refresh_token');

      Toast.success('Logged out');
      this.dispatchEvent('auth:logout');

      // Don't force redirect - let pages handle logout gracefully
      // Pages can listen to auth:logout event to update UI
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
