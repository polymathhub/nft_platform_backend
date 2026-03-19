import { api, endpoints } from './api.js';

class AuthManager {
  constructor() {
    this.user = null;
    this.isAuthenticated = false;
    this.userRole = null;
    this.tokenRefreshInterval = null;
    this.tg = null;
    this.initializeAuth();
  }

  async initializeAuth() {
    try {
      this.initTelegramUI();

      try {
        const profile = await api.get(endpoints.auth.profile);
        this.setUser(profile);
        this.dispatchEvent('auth:initialized', { user: this.user });
        console.log('Session restored');
        return;
      } catch (error) {
        console.log('No session found - this is normal on first load');
        // Do NOT call logout on init error - it causes unwanted redirects
        // Just mark as uninitialized and let app recover gracefully
      }
    } catch (error) {
      console.error('Auth initialization error (graceful fallback):', error);
      // Do NOT call logout() here - it causes forced redirects in Telegram
      // Instead, mark auth as initialized but not authenticated
      this.dispatchEvent('auth:initialized', { user: null });
    }
  }

  initTelegramUI() {
    if (typeof window !== 'undefined' && window.Telegram?.WebApp) {
      this.tg = window.Telegram.WebApp;
      
      this.tg.expand();
      this.tg.isClosingConfirmationEnabled = true;
      this.tg.setHeaderColor('#0f0f1a');
      this.tg.setBackgroundColor('#0f0f1a');

      console.log('Telegram UI initialized');
      this.dispatchEvent('telegram:ready', { tg: this.tg });
    }
  }
  /**
   * Populate the current user object
   * @param {Object|null} userData
   */
  setUser(userData) {
    if (!userData) {
      this.user = null;
      this.isAuthenticated = false;
      this.userRole = null;
      return;
    }

    if (typeof userData !== 'object' || !userData.id || !userData.email) {
      throw new Error('Invalid user data structure');
    }

    this.user = {
      id: String(userData.id),
      email: String(userData.email),
      username: String(userData.username || ''),
      avatar: userData.avatar ? String(userData.avatar) : null,
      role: String(userData.role || 'user'),
      createdAt: userData.createdAt ? new Date(userData.createdAt) : new Date(),
      ...userData,
    };

    this.isAuthenticated = true;
    this.userRole = this.user.role;

    if (userData.theme) {
      this.setTheme(userData.theme);
    }
  }

  async login(email, password) {
    try {
      if (!email || !password) {
        throw new Error('Email and password are required');
      }

      const response = await api.post(endpoints.auth.login, {
        email: email.toLowerCase().trim(),
        password,
      });

      if (!response.user) {
        throw new Error('Invalid login response');
      }

      this.setUser(response.user);
      
      // Store tokens (both access and refresh) if provided in response
      if (response.tokens) {
        localStorage.setItem('token', response.tokens.access_token);
        if (response.tokens.refresh_token) {
          localStorage.setItem('refresh_token', response.tokens.refresh_token);
        }
      }
      
      this.dispatchEvent('auth:login', { user: this.user });
      console.log(' Login successful');

      return this.user;
    } catch (error) {
      console.error('Login error:', error);
      this.dispatchEvent('auth:error', { error: error.message });
      throw error;
    }
  }

  /**
   * Register new user
   * @param {string} email - User email
   * @param {string} password - User password
   * @param {string} username - Username
   */
  async register(email, password, username) {
    try {
      if (!email || !password || !username) {
        throw new Error('Email, password, and username are required');
      }

      const response = await api.post(endpoints.auth.register, {
        email: email.toLowerCase().trim(),
        password,
        username: username.trim(),
      });

      if (!response.user) {
        throw new Error('Invalid registration response');
      }

      this.setUser(response.user);
      
      // Store tokens (both access and refresh) if provided in response
      if (response.tokens) {
        localStorage.setItem('token', response.tokens.access_token);
        if (response.tokens.refresh_token) {
          localStorage.setItem('refresh_token', response.tokens.refresh_token);
        }
      }
      
      this.dispatchEvent('auth:register', { user: this.user });
      console.log('Registration successful');

      return this.user;
    } catch (error) {
      console.error('Registration error:', error);
      this.dispatchEvent('auth:error', { error: error.message });
      throw error;
    }
  }

  /**
   * Login with Telegram (removed - use standard login instead)
   * Deprecated: Use login() method with email/password
   */
  async loginWithTelegram() {
    throw new Error('Telegram authentication is disabled. Please use standard email/password login.');
  }

  /**
   * Get Telegram data if available (for UI purposes only)
   * Returns null if not in Telegram context
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
   * Require specific role - show access denied if insufficient permissions
   */
  requireRole(role) {
    if (!this.hasRole(role)) {
      this.dispatchEvent('auth:access-denied', { requiredRole: role, userRole: this.userRole });
      throw new Error('Insufficient permissions');
    }
    return true;
  }

  /**
   * Logout user and close Telegram app
   */
  async logout() {
    try {
      if (this.isAuthenticated) {
        await api.post(endpoints.auth.logout, {});
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      this.user = null;
      this.isAuthenticated = false;
      this.userRole = null;

      // Clear all stored auth data
      localStorage.removeItem('token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');

      if (this.tokenRefreshInterval) {
        clearInterval(this.tokenRefreshInterval);
      }

      // Close Telegram app if available
      if (this.tg && this.tg.close) {
        this.tg.close();
      }

      this.dispatchEvent('auth:logout');
    }
  }

  /**
   * Check if user has required role
   */
  hasRole(requiredRole) {
    if (!this.isAuthenticated) return false;
    if (!requiredRole) return true;

    // Admin has access to everything
    if (this.userRole === 'admin') return true;

    return this.userRole === requiredRole;
  }

  /**
   * Check if user has any of the required roles
   */
  hasAnyRole(roles) {
    if (!Array.isArray(roles)) return false;
    return roles.some(role => this.hasRole(role));
  }

  /**
   * Require authentication - throw error if not authenticated
   * Pages handle the error gracefully, WITHOUT redirects
   */
  async requireAuth() {
    if (!this.isAuthenticated) {
      // Don't redirect - let pages handle gracefully
      throw new Error('Authentication required');
    }
    return true;
  }

  /**
   * Get authentication headers for requests (if needed)
   */
  getAuthHeaders() {
    // JWT is in httpOnly cookie, fetch handles it automatically
    return {};
  }

  /**
   * Set user theme preference
   */
  setTheme(theme) {
    if (!['light', 'dark', 'auto'].includes(theme)) return;
    localStorage.setItem('theme', theme);
    this.applyTheme(theme);
  }

  /**
   * Apply theme to document
   */
  applyTheme(theme) {
    const html = document.documentElement;
    if (theme === 'dark') {
      html.setAttribute('data-theme', 'dark');
    } else if (theme === 'light') {
      html.setAttribute('data-theme', 'light');
    } else {
      // Auto - respect system preference
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      html.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
    }
  }

  /**
   * Dispatch auth events
   * @private
   */
  dispatchEvent(eventName, detail = {}) {
    window.dispatchEvent(new CustomEvent(eventName, { detail }));
  }

  /**
   * Get base URL for OAuth
   * @private
   */
  getBaseURL() {
    return window.location.origin;
  }

  /**
   * Get current user
   */
  getUser() {
    return this.user;
  }

  /**
   * Get user ID
   */
  getUserId() {
    return this.user?.id || null;
  }

  /**
   * Check if authenticated
   */
  isLoggedIn() {
    return this.isAuthenticated;
  }

  /**
   * Get user role
   */
  getRole() {
    return this.userRole || 'guest';
  }
}

// Global auth instance
export const auth = new AuthManager();

export default auth;
