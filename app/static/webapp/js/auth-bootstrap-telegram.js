/**
 * AUTH BOOTSTRAP - Telegram-Only Stateless Authentication
 * ======================================================
 * 
 * Single entry point for authentication across the entire app.
 * 
 * ✅ NEW SYSTEM:
 * - NO tokens (no localStorage, no sessionStorage)
 * - NO refresh logic
 * - NO login forms
 * - Telegram WebApp.initData ONLY
 * - Completely stateless (session on every request)
 * 
 * FLOW:
 * 1. Extract window.Telegram.WebApp.initData
 * 2. Send to every API request via X-Telegram-Init-Data header
 * 3. Backend verifies HMAC-SHA256
 * 4. Backend returns user or 401
 */

import { telegramFetch, telegramApi } from './telegram-fetch.js';

// Global auth state
window.authManager = {
  user: null,
  isAuthenticated: false,
  isInitialized: false,
  isLoading: false,
  
  /**
   * Initialize authentication on app startup
   */
  async init() {
    console.log('[Auth] Initializing Telegram-only auth...');
    this.isLoading = true;
    
    try {
      // Wait for Telegram SDK
      if (!window.Telegram?.WebApp?.initData) {
        console.warn('[Auth] Not in Telegram WebApp - auth may not work');
        this.isInitialized = true;
        this.dispatchEvent('auth:initialized', { user: null });
        return;
      }
      
      console.log('[Auth] ✓ Telegram WebApp detected');
      
      // Try to fetch current user
      try {
        const response = await telegramApi.me();
        
        if (response && response.id) {
          console.log('[Auth] ✅ User authenticated:', {
            id: response.id,
            username: response.username,
            email: response.email,
          });
          
          this.user = response;
          this.isAuthenticated = true;
          
          this.dispatchEvent('auth:initialized', { user: this.user });
        } else {
          console.warn('[Auth] No user in response');
          this.dispatchEvent('auth:initialized', { user: null });
        }
      } catch (error) {
        // 401 is normal - just not authenticated yet
        if (error.status === 401) {
          console.log('[Auth] Not authenticated (401) - will work once in Telegram Mini App');
        } else {
          console.error('[Auth] Failed to fetch user:', error.message);
        }
        this.dispatchEvent('auth:initialized', { user: null });
      }
    } catch (error) {
      console.error('[Auth] Initialization error:', error);
      this.dispatchEvent('auth:initialized', { user: null });
    } finally {
      this.isLoading = false;
      this.isInitialized = true;
    }
  },
  
  /**
   * Get current user
   */
  getUser() {
    return this.user;
  },
  
  /**
   * Check if authenticated
   */
  isLoggedIn() {
    return this.isAuthenticated && !!this.user;
  },
  
  /**
   * Logout (client-side only - backend is stateless)
   */
  logout() {
    console.log('[Auth] Logging out (client-side only)');
    this.user = null;
    this.isAuthenticated = false;
    
    // No server-side logout needed - stateless system
    this.dispatchEvent('auth:logout', {});
  },
  
  /**
   * Dispatch custom event
   */
  dispatchEvent(eventName, detail) {
    window.dispatchEvent(new CustomEvent(eventName, { detail }));
  },
};

/**
 * Initialize on page load
 */
export async function initializeAuthSystem() {
  console.log('[Auth Bootstrap] Starting...');
  
  // Wait for DOM ready
  if (document.readyState === 'loading') {
    await new Promise(r => document.addEventListener('DOMContentLoaded', r));
  }
  
  // Wait for Telegram SDK
  if (typeof window.Telegram === 'undefined') {
    console.warn('[Auth Bootstrap] Waiting for Telegram SDK...');
    await new Promise(r => {
      const check = () => {
        if (window.Telegram?.WebApp) {
          r();
        } else {
          setTimeout(check, 100);
        }
      };
      check();
    });
  }
  
  // Initialize auth
  await window.authManager.init();
  
  console.log('[Auth Bootstrap] ✅ Complete');
  
  return window.authManager;
}

// Auto-initialize on import
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    initializeAuthSystem().catch(console.error);
  });
} else {
  initializeAuthSystem().catch(console.error);
}
