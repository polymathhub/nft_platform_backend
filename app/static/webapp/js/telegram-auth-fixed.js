/**
 * TELEGRAM MINI APP AUTHENTICATION
 * Fixed version - Uses proper Telegram auth and API endpoints
 * 
 * Requirements:
 * - Must run ONLY inside Telegram Mini App
 * - Uses window.Telegram.WebApp for authentication
 * - Tokens stored in localStorage
 */

class TelegramAuthManager {
  constructor() {
    this.tg = window.Telegram?.WebApp;
    this.user = null;
    this.token = null;
    this.isInitialized = false;
    
    // Check if running inside Telegram
    if (!this.tg || !this.tg.initData) {
      this.showErrorPage('⛔ Open this app inside Telegram Mini App');
      return;
    }
    
    this.init();
  }

  /**
   * Initialize authentication
   */
  async init() {
    try {
      console.log('[TG AUTH] Starting Telegram Mini App authentication...');
      
      // Expand app to fullscreen
      if (this.tg.expand) this.tg.expand();
      
      // Check if already authenticated (token in storage)
      const savedToken = localStorage.getItem('auth_token');
      if (savedToken) {
        console.log('[TG AUTH] Token found in localStorage, verifying...');
        this.token = savedToken;
        return await this.verifyToken();
      }
      
      // No saved token, authenticate with Telegram initData
      console.log('[TG AUTH] No saved token, authenticating with Telegram initData...');
      return await this.authenticateWithTelegram();
    } catch (error) {
      console.error('[TG AUTH] Initialization failed:', error);
      this.showErrorPage('❌ Authentication failed. Try again.');
    }
  }

  /**
   * Authenticate using Telegram initData
   */
  async authenticateWithTelegram() {
    try {
      if (!this.tg.initData) {
        throw new Error('Telegram initData not available');
      }
      
      console.log('[TG AUTH] Sending initData to backend for verification...');
      
      const response = await fetch('/api/v1/auth/telegram/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          init_data: this.tg.initData,
        }),
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `HTTP ${response.status}`);
      }
      
      const data = await response.json();
      
      if (!data.success || !data.tokens?.access) {
        throw new Error('Invalid response from server');
      }
      
      // Save token
      this.token = data.tokens.access;
      localStorage.setItem('auth_token', this.token);
      
      // Save user data
      if (data.user) {
        this.user = data.user;
        localStorage.setItem('user', JSON.stringify(data.user));
      }
      
      console.log('[TG AUTH] ✅ Authentication successful!');
      console.log('[TG AUTH] User:', this.user?.username || this.user?.id);
      
      this.isInitialized = true;
      window.dispatchEvent(new CustomEvent('auth:ready', { detail: { user: this.user, token: this.token } }));
      
      return { user: this.user, token: this.token };
    } catch (error) {
      console.error('[TG AUTH] Authentication failed:', error);
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
      throw error;
    }
  }

  /**
   * Verify saved token is still valid
   */
  async verifyToken() {
    try {
      const response = await fetch('/api/user/me', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${this.token}`,
        },
      });
      
      if (!response.ok) {
        if (response.status === 401) {
          // Token expired, need to re-authenticate
          console.log('[TG AUTH] Token expired, re-authenticating...');
          localStorage.removeItem('auth_token');
          localStorage.removeItem('user');
          return await this.authenticateWithTelegram();
        }
        throw new Error(`HTTP ${response.status}`);
      }
      
      this.user = await response.json();
      localStorage.setItem('user', JSON.stringify(this.user));
      
      console.log('[TG AUTH] ✅ Token verified!');
      this.isInitialized = true;
      window.dispatchEvent(new CustomEvent('auth:ready', { detail: { user: this.user, token: this.token } }));
      
      return { user: this.user, token: this.token };
    } catch (error) {
      console.error('[TG AUTH] Token verification failed:', error);
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
      throw error;
    }
  }

  /**
   * Get current user
   */
  getUser() {
    return this.user || JSON.parse(localStorage.getItem('user') || 'null');
  }

  /**
   * Get auth token
   */
  getToken() {
    return this.token || localStorage.getItem('auth_token');
  }

  /**
   * Logout
   */
  logout() {
    this.user = null;
    this.token = null;
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
    console.log('[TG AUTH] Logged out');
    window.dispatchEvent(new CustomEvent('auth:logout'));
  }

  /**
   * Show error page
   */
  showErrorPage(message) {
    document.body.innerHTML = `
      <div style="
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100vh;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        color: white;
        text-align: center;
        padding: 20px;
      ">
        <div>
          <h1 style="font-size: 48px; margin-bottom: 20px;">${message}</h1>
          <p style="font-size: 18px; margin-bottom: 30px;">This app only works inside Telegram</p>
          <p style="font-size: 14px; opacity: 0.8;">
            Search for <strong>@YourBotName</strong> in Telegram to open this app.
          </p>
        </div>
      </div>
    `;
    document.body.style.margin = '0';
    document.body.style.padding = '0';
  }
}

// Initialize on page load
window.telegramAuth = null;
document.addEventListener('DOMContentLoaded', async () => {
  window.telegramAuth = new TelegramAuthManager();
});
