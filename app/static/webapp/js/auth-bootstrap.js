/**
 * AUTH BOOTSTRAP - Single Centralized Authentication Entry Point
 * 
 * This module initializes authentication ONCE for the entire app.
 * All pages use the same auth instance, eliminating redundant checks.
 * 
 * Features:
 * - Initializes UnifiedAuthManager once at app startup
 * - Restores cached session instantly (no waiting)
 * - Handles auth events globally
 * - No per-page auth initialization needed
 * - Graceful degradation (no aggressive redirects)
 */

import { UnifiedAuthManager } from './unified-auth.js';

// Global auth instance - shared across all pages
window.authManager = null;
window.authInitialized = false;
window.authInitPromise = null;

/**
 * Initialize authentication system globally
 * Only runs once, subsequent calls return cached promise
 */
export async function initializeAuthSystem() {
  // Return existing promise if already initializing
  if (window.authInitPromise) {
    return window.authInitPromise;
  }

  // Return existing instance if already initialized
  if (window.authManager && window.authInitialized) {
    return window.authManager;
  }

  // Create initialization promise
  window.authInitPromise = (async () => {
    try {
      console.log('[AUTH] Initializing authentication system...');

      // Create global auth manager instance
      if (!window.authManager) {
        window.authManager = new UnifiedAuthManager();
      }

      const authManager = window.authManager;

      // Wait for initial session restoration (with max timeout)
      await Promise.race([
        new Promise(resolve => {
          // Listen for auth:initialized event
          const handler = () => {
            window.removeEventListener('auth:initialized', handler);
            resolve();
          };
          window.addEventListener('auth:initialized', handler);
          // Timeout in 5 seconds
          setTimeout(resolve, 5000);
        })
      ]);

      // Set flag that auth is initialized
      window.authInitialized = true;
      console.log('[AUTH] Authentication system initialized', {
        isAuthenticated: authManager.isAuthenticated,
        user: authManager.user?.username || 'Anonymous'
      });

      // Setup global auth event listeners
      setupGlobalAuthListeners(authManager);

      return authManager;
    } catch (error) {
      console.error('[AUTH] Initialization failed:', error);
      window.authInitialized = true; // Still mark as done even if error
      return window.authManager;
    }
  })();

  return window.authInitPromise;
}

/**
 * Setup global event listeners for auth changes
 */
function setupGlobalAuthListeners(authManager) {
  // Handle logout event - DON'T redirect, just clear state
  // Let pages handle logout gracefully via auth:logout event
  let logoutHandled = false;
  
  window.addEventListener('auth:logout', () => {
    // Only process once per app session
    if (logoutHandled) {
      console.log('[AUTH] Logout already handled');
      return;
    }
    
    logoutHandled = true;
    console.log('[AUTH] Logout event fired - pages will handle UI updates');
    // Do NOT redirect - let each page decide how to handle logout
    // This prevents aggressive redirects and refresh loops
  }, { once: true });

  // Handle auth errors
  window.addEventListener('auth:error', (e) => {
    console.warn('[AUTH] Authentication error:', e.detail);
    // Don't redirect on error - let page handle gracefully
  });

  // Handle successful login
  window.addEventListener('auth:login_telegram', (e) => {
    console.log('[AUTH] Telegram login successful');
    // Update any UI that depends on auth
    broadcastAuthChange();
  });

  window.addEventListener('auth:login_ton', (e) => {
    console.log('[AUTH] TON wallet login successful');
    // Update any UI that depends on auth
    broadcastAuthChange();
  });
}

/**
 * Broadcast auth state change to all pages
 */
function broadcastAuthChange() {
  if (window.authManager) {
    // Trigger custom event that pages can listen to
    window.dispatchEvent(new CustomEvent('auth:changed', {
      detail: {
        isAuthenticated: window.authManager.isAuthenticated,
        user: window.authManager.user
      }
    }));
  }
}

/**
 * Get auth status - ALWAYS use this instead of checking directly
 * Ensures auth is initialized before checking
 */
export async function getAuthStatus() {
  await initializeAuthSystem();
  if (window.authManager) {
    return {
      isAuthenticated: window.authManager.isAuthenticated,
      user: window.authManager.user,
      authMethod: window.authManager.authMethod
    };
  }
  return {
    isAuthenticated: false,
    user: null,
    authMethod: null
  };
}

/**
 * Wait for auth initialization to complete
 * Use this in page initialization functions
 */
export async function waitForAuth(maxWaitMs = 5000) {
  const start = Date.now();
  await initializeAuthSystem();
  
  // Wait for actual initialization with timeout
  while (!window.authInitialized && (Date.now() - start) < maxWaitMs) {
    await new Promise(r => setTimeout(r, 100));
  }
  
  return window.authManager;
}

/**
 * Auto-initialize on module load (if in browser)
 * Don't await - let it happen in background
 */
if (typeof window !== 'undefined' && typeof document !== 'undefined') {
  // Initialize auth as soon as possible
  initializeAuthSystem().catch(err => {
    console.warn('[AUTH] Background initialization error:', err);
  });
}

export default {
  initializeAuthSystem,
  getAuthStatus,
  waitForAuth
};
