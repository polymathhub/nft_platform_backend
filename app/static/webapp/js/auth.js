import { api, endpoints } from './api.js';

/**
 * AuthManager - Handles user authentication
 * 
 * CRITICAL: Async initialization is deferred, not run in constructor.
 * This prevents unhandled promise rejections during app startup.
 */
class AuthManager {
  constructor() {
    this.user = null;
    this.isAuthenticated = false;
    this.userRole = null;
    this.tokenRefreshInterval = null;
    this.tg = null;
    this.initPromise = null;
    this.initCompleted = false;
    
    // SAFE: Initialize Telegram UI synchronously (no async operations)
    this.initTelegramUI();
    
    // Deferred: Auth restoration starts on-demand or via initializeAuth()
    // NOT in constructor to prevent unhandled rejections
  }

  /**
   * Initialize Telegram UI (synchronous, safe)
   * @private
   */
  initTelegramUI() {
    try {
      if (typeof window !== 'undefined' && window.Telegram?.WebApp) {
        this.tg = window.Telegram.WebApp;
        
        // Safe Telegram configuration
        if (this.tg.expand) this.tg.expand();
        if (this.tg.isClosingConfirmationEnabled !== undefined) {
          this.tg.isClosingConfirmationEnabled = true;
        }
        if (this.tg.setHeaderColor) this.tg.setHeaderColor('#0f0f1a');
        if (this.tg.setBackgroundColor) this.tg.setBackgroundColor('#0f0f1a');

        console.log('[Auth] Telegram UI initialized');
        this.dispatchEvent('telegram:ready', { tg: this.tg });
      }
    } catch (error) {
      console.warn('[Auth] Telegram initialization failed (non-critical):', error.message);
    }
  }

  /**
   * Initialize authentication (async, deferred from constructor)
   * Call this when you need to restore session from API
   * Safe: Errors are caught and don't cause redirects
   * 
   * @returns {Promise<boolean>} true if session restored, false otherwise
   */
  async initializeAuth() {
    // Prevent multiple concurrent initializations
    if (this.initPromise) {
      return this.initPromise;
    }

    if (this.initCompleted) {
      return true;
    }

    this.initPromise = this._performInit();
    return this.initPromise;
  }

  /**
   * Actual initialization logic (private)
   * @private
   */
  async _performInit() {
    try {
      console.log('[Auth] Starting Telegram Mini App authentication...');

      // For Telegram Mini App, authenticate via Telegram initData
      if (this.tg && this.tg.initData) {
        return await this._authenticateWithTelegram();
      }

      // Fallback: Try to restore session from existing token
      try {
        const token = localStorage.getItem('token');
        if (token) {
          const profile = await api.get(endpoints.unifiedAuth.profile);
          if (profile) {
            this.setUser(profile);
            console.log('[Auth] Session restored from existing token');
            this.dispatchEvent('auth:initialized', { user: this.user });
            this.initCompleted = true;
            return true;
          }
        }
      } catch (error) {
        console.warn('[Auth] Failed to restore session:', error.message);
      }

      // No session - that's OK for guest access
      this.user = null;
      this.isAuthenticated = false;
      this.dispatchEvent('auth:initialized', { user: null });
      this.initCompleted = true;
      return false;

    } catch (error) {
      console.error('[Auth] Unexpected error during initialization:', error);
      this.dispatchEvent('auth:initialized', { user: null });
      this.initCompleted = true;
      return false;
    }
  }

  /**
   * Authenticate using Telegram Mini App initData
   * This is the primary auth method for Telegram apps
   * @private
   */
  async _authenticateWithTelegram() {
    try {
      if (!this.tg?.initData) {
        console.warn('[Auth] No Telegram initData available');
        return false;
      }

      console.log('[Auth] Authenticating with Telegram initData...');

      // Send Telegram initData to backend for verification
      const response = await fetch(endpoints.unifiedAuth.telegramLogin, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ init_data: this.tg.initData })
      });

      if (!response.ok) {
        const error = await response.text();
        console.warn('[Auth] Telegram authentication failed:', error);
        return false;
      }

      const data = await response.json();
      
      if (!data.success || !data.user) {
        console.warn('[Auth] Invalid Telegram response:', data);
        return false;
      }

      // Store tokens
      if (data.tokens?.access) {
        localStorage.setItem('token', data.tokens.access);
        if (data.tokens.refresh) {
          localStorage.setItem('refresh_token', data.tokens.refresh);
        }
      }

      // Set user
      this.setUser(data.user);
      console.log('[Auth] Telegram authentication successful:', data.user.username);
      this.dispatchEvent('auth:initialized', { user: this.user });
      this.initCompleted = true;
      return true;

    } catch (error) {
      console.error('[Auth] Telegram authentication error:', error);
      return false;
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
    try {
      if (!this.tg) return null;

      return {
        initData: this.tg?.initData || null,
        initDataUnsafe: this.tg?.initDataUnsafe || null,
        user: this.tg?.initDataUnsafe?.user || null,
        isBot: this.tg?.initDataUnsafe?.user?.is_bot || false,
      };
    } catch (error) {
      console.warn('[Auth] Error getting Telegram data:', error);
      return null;
    }
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
   * Logout user
   * Safe: Never throws, always completes
   */
  async logout() {
    try {
      if (this.isAuthenticated) {
        try {
          await api.post(endpoints.auth.logout, {});
        } catch (error) {
          console.warn('[Auth] Logout API call failed (non-critical):', error);
          // Continue with local logout even if API fails
        }
      }
    } finally {
      // ALWAYS perform local cleanup
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
    try {
      if (!['light', 'dark', 'auto'].includes(theme)) return;
      localStorage.setItem('theme', theme);
      this.applyTheme(theme);
    } catch (error) {
      console.warn('[Auth] Theme setting failed:', error);
    }
  }

  /**
   * Apply theme to document
   */
  applyTheme(theme) {
    try {
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
    } catch (error) {
      console.warn('[Auth] Theme application failed:', error);
    }
  }

  /**
   * Dispatch auth events
   * @private
   */
  dispatchEvent(eventName, detail = {}) {
    try {
      window.dispatchEvent(new CustomEvent(eventName, { detail }));
    } catch (error) {
      console.warn('[Auth] Event dispatch failed:', eventName, error);
    }
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

  /**
   * Wait for initialization to complete
   * Useful for checking if session was restored
   */
  async waitForInit() {
    if (this.initCompleted) return true;
    return await this.initializeAuth();
  }
}

// Global auth instance
export const auth = new AuthManager();

export default auth;
