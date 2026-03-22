/**
 * AUTH BOOTSTRAP - Telegram-Only Stateless Authentication
 * ======================================================
 * 
 * Single entry point for authentication across the entire app.
 * 
 * ✅ HYBRID SYSTEM:
 * - Stateless API authentication: X-Telegram-Init-Data header on every request
 * - Persistent UI state: User data cached in localStorage for fast restoration
 * - NO tokens stored (no JWT, refresh tokens, or session IDs)
 * - NO passwords, forms, or OAuth
 * - Telegram WebApp.initData verified on backend
 * 
 * FLOW:
 * 1. On page load: restore user from localStorage if available
 * 2. If no cached user: fetch from /api/v1/me using X-Telegram-Init-Data header
 * 3. Backend verifies HMAC-SHA256 and returns user
 * 4. Store user in localStorage for next navigation
 * 5. API requests always send X-Telegram-Init-Data header (stateless)
 */

import { telegramFetch, telegramApi } from './telegram-fetch.js';

// Storage keys
const STORAGE_KEYS = {
  USER: 'app_tg_user'  // Stores user data (NOT auth tokens)
};

// Global auth state
window.authManager = {
  user: null,
  isAuthenticated: false,
  isInitialized: false,
  isLoading: false,
  
  /**
   * Initialize authentication on app startup
   * TRY: localStorage → API → fallback to null
   */
  async init() {
    console.log('[Auth] Initializing Telegram-only auth...');
    this.isLoading = true;
    
    try {
      // STEP 1: Try to restore user from localStorage (fast path)
      try {
        const cachedUser = localStorage.getItem(STORAGE_KEYS.USER);
        if (cachedUser) {
          const user = JSON.parse(cachedUser);
          // Validate the cached user has required fields
          if (user && user.id && user.username) {
            console.log('[Auth] ✓ Restored user from localStorage:', {
              id: user.id,
              username: user.username,
            });
            
            this.user = user;
            this.isAuthenticated = true;
            this.dispatchEvent('auth:initialized', { user: this.user, source: 'cache' });
            return;  // Don't call API if we have cached user
          }
        }
      } catch (e) {
        console.warn('[Auth] Failed to restore from localStorage:', e);
      }
      
      // STEP 2: If not in localStorage, try to fetch from API
      if (!window.Telegram?.WebApp?.initData) {
        console.warn('[Auth] Not in Telegram WebApp - auth may not work');
        this.isInitialized = true;
        this.dispatchEvent('auth:initialized', { user: null });
        return;
      }
      
      console.log('[Auth] localStorage miss - fetching fresh user from API...');
      
      try {
        const response = await telegramApi.me();
        
        if (response && response.id) {
          console.log('[Auth] ✅ User authenticated via API:', {
            id: response.id,
            username: response.username,
            email: response.email,
          });
          
          this.user = response;
          this.isAuthenticated = true;
          
          // STEP 3: Store in localStorage for next page load
          try {
            localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(this.user));
            console.log('[Auth] ✓ User cached in localStorage');
          } catch (e) {
            console.warn('[Auth] Failed to cache user in localStorage:', e);
            // Continue anyway - user is authenticated, just not cached
          }
          
          this.dispatchEvent('auth:initialized', { user: this.user, source: 'api' });
        } else {
          console.warn('[Auth] No user in API response');
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
   * Clears cached user from localStorage
   */
  logout() {
    console.log('[Auth] Logging out...');
    this.user = null;
    this.isAuthenticated = false;
    
    // Clear cached user from localStorage
    try {
      localStorage.removeItem(STORAGE_KEYS.USER);
      console.log('[Auth] ✓ User cleared from localStorage');
    } catch (e) {
      console.warn('[Auth] Failed to clear localStorage:', e);
    }
    
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
}

// Auto-initialize on import
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    initializeAuthSystem().catch(console.error);
  });
} else {
  initializeAuthSystem().catch(console.error);
}
