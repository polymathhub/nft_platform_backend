
import { telegramFetch, telegramApi } from './telegram-fetch.js';

// Global auth state (memory-only)
window.authManager = {
  user: null,
  initData: null,
  isInitialized: false,
  isLoading: false,

  async init() {
    this.isLoading = true;
    try {
      // Wait for DOM
      if (document.readyState === 'loading') {
        await new Promise(r => document.addEventListener('DOMContentLoaded', r));
      }

      // Wait for Telegram SDK to be available
      if (typeof window.Telegram === 'undefined' || !window.Telegram?.WebApp) {
        console.warn('[Auth] Telegram WebApp SDK not present');
        this.isInitialized = true;
        this.isLoading = false;
        window.dispatchEvent(new CustomEvent('auth:initialized', { detail: { user: null } }));
        return;
      }

      // Use raw initData from Telegram SDK (do NOT modify)
      const initData = window.Telegram.WebApp.initData || null;
      this.initData = initData;
      window.TELEGRAM_INIT_DATA = initData; // legacy alias

      // Try to fetch user profile from backend (optional) using tg header
      try {
        const profile = await telegramApi.me();
        if (profile && profile.id) {
          this.user = profile;
          this.isInitialized = true;
          this.isLoading = false;
          window.dispatchEvent(new CustomEvent('auth:initialized', { detail: { user: this.user } }));
          return;
        }
      } catch (e) {
        // telegramApi.me() returns null on 401 per fetch wrapper
        console.info('[Auth] No backend profile available; continuing as guest');
      }

      this.isInitialized = true;
      this.isLoading = false;
      window.dispatchEvent(new CustomEvent('auth:initialized', { detail: { user: null } }));
    } catch (err) {
      console.error('[Auth] init error', err);
      this.isInitialized = true;
      this.isLoading = false;
      window.dispatchEvent(new CustomEvent('auth:initialized', { detail: { user: null } }));
    }
  },
  getUser() { return this.user; },
  isLoggedIn() { return !!this.user; },
  logout() {
    this.user = null;
    window.dispatchEvent(new CustomEvent('auth:logout', {}));
  }
};

export async function initializeAuthSystem() {
  await window.authManager.init();
  return window.authManager;
}

// Auto-init
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => initializeAuthSystem().catch(console.error));
} else {
  initializeAuthSystem().catch(console.error);
}
