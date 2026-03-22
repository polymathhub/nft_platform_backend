/**
 * Telegram WebApp Utility Functions
 * Provides safe checks and helpers for Telegram integration
 */

export const TelegramUtils = {
  /**
   * Check if Telegram WebApp is available and initialized
   * @returns {boolean} true if Telegram is ready
   */
  isTelegramReady() {
    return !!(
      window.Telegram &&
      window.Telegram.WebApp &&
      window.Telegram.WebApp.initDataUnsafe &&
      window.Telegram.WebApp.initDataUnsafe.user
    );
  },

  /**
   * Get Telegram user safely
   * @returns {object|null} User object or null if not ready
   */
  getTelegramUser() {
    try {
      return window.Telegram?.WebApp?.initDataUnsafe?.user || null;
    } catch (e) {
      console.warn('[TelegramUtils] Failed to get user:', e);
      return null;
    }
  },

  /**
   * Get Telegram initData safely
   * @returns {string|null} initData string or null if not ready
   */
  getInitData() {
    try {
      return window.Telegram?.WebApp?.initData || null;
    } catch (e) {
      console.warn('[TelegramUtils] Failed to get initData:', e);
      return null;
    }
  },

  /**
   * Wait for Telegram to be ready with timeout
   * @param {number} timeout - Max time to wait in milliseconds (default 5000)
   * @returns {Promise<boolean>} true if ready, false if timeout
   */
  async waitForTelegram(timeout = 5000) {
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeout) {
      if (this.isTelegramReady()) {
        console.log('[TelegramUtils] Telegram is ready');
        return true;
      }
      
      // Wait 100ms before checking again
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    console.warn('[TelegramUtils] Telegram initialization timeout');
    return false;
  },

  /**
   * DEPRECATED: Safe page redirect with Telegram readiness check
   * ⚠️ DO NOT USE - Causes aggressive redirect loops
   * 
   * This function is dangerous because it redirects the user when Telegram
   * is not immediately available, but Telegram often takes time to initialize.
   * 
   * Instead:
   * - Use window.AuthSystem.isInitialized for auth checks
   * - Wait for AuthSystem in your page initialization
   * - Never force redirects during auth loading phase
   * 
   * Only redirects if Telegram is ready or timeout is reached
   * @param {string} path - Path to redirect to
   * @param {number} timeout - Max time to wait for Telegram (default 3000)
   * @deprecated - Use AuthSystem instead
   */
  async safeNavigateIfNotReady(path, timeout = 3000) {
    console.warn('[TelegramUtils] DEPRECATED: safeNavigateIfNotReady() should not be used - use AuthSystem instead');

    // If already ready, nothing to do
    if (this.isTelegramReady()) {
      console.log('[TelegramUtils] Telegram ready, no navigation required');
      return true;
    }

    console.log('[TelegramUtils] Waiting for Telegram before deciding navigation...');
    const ready = await this.waitForTelegram(timeout);

    if (!ready) {
      // Suppress automatic redirect to avoid aggressive loops.
      // Return false so callers can decide how to handle navigation (UI prompt, modal, or manual click).
      console.warn(`[TelegramUtils] Telegram not ready after ${timeout}ms — automatic redirect suppressed for ${path}`);
      return false;
    } else {
      console.log('[TelegramUtils] Telegram became ready, no redirect needed');
      return true;
    }
  },

  /**
   * Check if user is authenticated
   * @returns {boolean} true if user has valid Telegram data
   */
  isAuthenticated() {
    const user = this.getTelegramUser();
    return !!(user && user.id);
  },

  /**
   * Get base path for webapp
   * @returns {string} '/webapp' or ''
   */
  getBasePath() {
    return window.location.pathname.includes('/webapp') ? '/webapp' : '';
  }
};

export default TelegramUtils;
