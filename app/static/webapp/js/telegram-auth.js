/**
 * Telegram WebApp Authentication Manager - REWRITTEN
 * 
 * NEW DESIGN: Session-based authentication using Telegram initData
 * - No localStorage tokens
 * - No Bearer headers
 * - Uses httpOnly cookies for session management
 * - Backend validates initData using HMAC-SHA256
 * 
 * Flow:
 * 1. App loads → script auto-initializes
 * 2. Reads window.Telegram.WebApp.initData
 * 3. POSTs initData to /api/auth/telegram
 * 4. Backend validates + sets session cookie
 * 5. All requests use credentials: 'include' for cookie-based auth
 */

class TelegramAuthManager {
  constructor() {
    this.user = null;
    this.isAuthenticated = false;
    this.isInitializing = false;
    this.initPromise = null;
  }

  /**
   * Main initialization: Get Telegram initData and authenticate with backend
   */
  async init() {
    // Prevent multiple simultaneous init attempts
    if (this.isInitializing) {
      return this.initPromise;
    }

    if (this.isAuthenticated) {
      console.log('[TelegramAuth] Already authenticated, skipping init');
      return this.user;
    }

    this.isInitializing = true;
    this.initPromise = this._performInit();

    try {
      const user = await this.initPromise;
      return user;
    } finally {
      this.isInitializing = false;
    }
  }

  async _performInit() {
    console.log('[TelegramAuth] Initializing Telegram authentication...');

    // Step 1: Ensure Telegram WebApp SDK is available
    if (!window.Telegram?.WebApp) {
      console.error('[TelegramAuth] Telegram WebApp SDK not available');
      this._showErrorPage(
        'Telegram WebApp Not Available',
        'This application must be opened from Telegram. Please open it via the bot.',
        'ERROR_NO_TELEGRAM'
      );
      throw new Error('Telegram WebApp SDK not available');
    }

    // Step 2: Get initData from Telegram
    const initData = window.Telegram.WebApp.initData;

    if (!initData) {
      console.error('[TelegramAuth] No initData from Telegram WebApp');
      this._showErrorPage(
        'Authentication Failed',
        'Could not obtain Telegram authentication data. Please try reopening the app.',
        'ERROR_NO_INIT_DATA'
      );
      throw new Error('No initData from Telegram WebApp');
    }

    console.log('[TelegramAuth] Got initData from Telegram WebApp, authenticating with server...');

    // Step 3: Send initData to backend for validation
    try {
      const response = await fetch('/api/auth/telegram', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ init_data: initData }),
        credentials: 'include', // IMPORTANT: Include cookies for session
      });

      if (!response.ok) {
        const bodyText = await response.text().catch(() => '');
        console.error(
          `[TelegramAuth] Backend returned ${response.status}: ${bodyText}`
        );
        this._showErrorPage(
          'Authentication Failed',
          `Server validation failed (${response.status}). Please try again.`,
          `ERROR_SERVER_${response.status}`
        );
        throw new Error(
          `Server returned ${response.status}: ${bodyText}`
        );
      }

      const data = await response.json();

      if (!data.success || !data.user) {
        console.error('[TelegramAuth] Server response missing user data');
        this._showErrorPage(
          'Authentication Failed',
          'Server returned invalid response. Please try again.',
          'ERROR_INVALID_RESPONSE'
        );
        throw new Error('Server response missing user data');
      }

      // Step 4: Store user data in memory only (NO localStorage)
      this.user = data.user;
      this.isAuthenticated = true;

      console.log(
        `[TelegramAuth] ✓ Authenticated | id=${this.user.id} | username=${this.user.username}`
      );

      // Step 5: Dispatch ready event for app initialization
      window.dispatchEvent(
        new CustomEvent('auth:ready', {
          detail: { user: this.user },
        })
      );

      return this.user;
    } catch (error) {
      console.error('[TelegramAuth] Authentication error:', error);

      // Only show error page if not already shown
      if (!document.getElementById('error-page')) {
        this._showErrorPage(
          'Authentication Error',
          error.message || 'An unexpected error occurred.',
          'ERROR_UNEXPECTED'
        );
      }

      throw error;
    }
  }

  /**
   * Get currently authenticated user
   */
  getUser() {
    return this.user;
  }

  /**
   * Check if user is logged in
   */
  isLoggedIn() {
    return this.isAuthenticated && !!this.user;
  }

  /**
   * Logout: Clear session on server and local state
   */
  async logout() {
    try {
      const response = await fetch('/api/auth/logout', {
        method: 'POST',
        credentials: 'include',
      });

      if (!response.ok) {
        console.warn(`[TelegramAuth] Logout response: ${response.status}`);
      } else {
        console.log('[TelegramAuth] Logout successful');
      }
    } catch (error) {
      console.error('[TelegramAuth] Logout error:', error);
    } finally {
      // Clear local state (server already cleared httpOnly cookie)
      this.user = null;
      this.isAuthenticated = false;
      window.dispatchEvent(new CustomEvent('auth:logged-out'));
    }
  }

  /**
   * Show error overlay page (blocks further interaction)
   * This prevents any interaction if auth fails
   */
  _showErrorPage(title, message, errorCode) {
    const html = `
      <div id="error-page" style="
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 999999;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      ">
        <div style="
          text-align: center;
          color: white;
          padding: 40px 20px;
          max-width: 500px;
        ">
          <div style="
            font-size: 48px;
            margin-bottom: 20px;
          ">⚠️</div>
          <h1 style="
            font-size: 24px;
            margin: 0 0 15px 0;
            font-weight: 600;
          ">${title}</h1>
          <p style="
            font-size: 16px;
            margin: 0 0 30px 0;
            opacity: 0.9;
            line-height: 1.6;
          ">${message}</p>
          <button onclick="location.reload()" style="
            background: white;
            color: #667eea;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
          " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
            Reload App
          </button>
          <p style="
            font-size: 12px;
            margin-top: 30px;
            opacity: 0.6;
          ">Error Code: <code style="
            background: rgba(255,255,255,0.1);
            padding: 2px 6px;
            border-radius: 3px;
          ">${errorCode}</code></p>
        </div>
      </div>
    `;

    document.body.innerHTML = html;
    document.body.style.overflow = 'hidden';
    document.body.style.margin = '0';
  }
}

// Create global singleton instance
window.telegramAuth = new TelegramAuthManager();

// Auto-initialize when DOM is ready
console.log('[TelegramAuth] Script loaded');

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    // Small delay to ensure all resources are loaded
    setTimeout(() => {
      window.telegramAuth
        .init()
        .catch((error) => {
          console.error('[TelegramAuth] Auto-init failed:', error);
        });
    }, 100);
  });
} else {
  // DOM already ready
  setTimeout(() => {
    window.telegramAuth
      .init()
      .catch((error) => {
        console.error('[TelegramAuth] Auto-init failed:', error);
      });
  }, 100);
}
