/**
 * PAGE INITIALIZER - Universal Page Setup
 * ═══════════════════════════════════════════════════════════════
 * 
 * Handles all page initialization:
 * ✅ Theme setup (dark/light from Telegram WebApp)
 * ✅ Navigation highlighting by current page
 * ✅ Auth system integration and lifecycle
 * ✅ Page visibility handlers for background refresh
 * ✅ Back button and window.navigate() global function
 */

class PageInitializer {
  constructor() {
    this.authReady = false;
    this.init();
  }

  /**
   * Initialize theme from Telegram WebApp
   */
  initTheme() {
    try {
      const colorScheme = window.Telegram?.WebApp?.colorScheme;
      if (colorScheme === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
      } else {
        document.documentElement.removeAttribute('data-theme');
      }
      console.log('[PageInit] Theme initialized:', colorScheme);
    } catch (e) {
      console.warn('[PageInit] Failed to initialize theme:', e.message);
    }
  }

  /**
   * Initialize navigation highlighting
   */
  initNavigation() {
    try {
      // Get current page from URL
      const pathname = window.location.pathname;
      const currentPage = pathname.split('/').pop()?.replace('.html', '') || 'dashboard';

      // Highlight active nav item
      document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        
        // Check if this nav item matches current page
        const itemPage = item.dataset.page || item.getAttribute('href')?.replace('.html', '').split('/').pop();
        if (itemPage === currentPage) {
          item.classList.add('active');
        }
      });

      // Add click handlers to nav items
      document.querySelectorAll('.nav-item a, .nav-item').forEach(link => {
        link.addEventListener('click', (e) => {
          const href = link.getAttribute('href') || `/webapp/${link.dataset.page}.html`;
          window.location.href = href;
        });
      });

      console.log('[PageInit] Navigation initialized for page:', currentPage);
    } catch (e) {
      console.warn('[PageInit] Failed to initialize navigation:', e.message);
    }
  }

  /**
   * Setup Telegram back button
   */
  initBackButton() {
    try {
      if (window.Telegram?.WebApp?.BackButton) {
        window.Telegram.WebApp.BackButton.onClick(() => {
          window.history.back();
        });
        window.Telegram.WebApp.BackButton.show();
        console.log('[PageInit] Back button initialized');
      }
    } catch (e) {
      console.warn('[PageInit] Failed to initialize back button:', e.message);
    }
  }

  /**
   * Initialize auth system and wait for it to be ready
   */
  async initAuth() {
    try {
      // Wait for auth.js to be loaded as a module
      let retries = 0;
      const maxRetries = 10;

      while (!window.getUser && retries < maxRetries) {
        console.log('[PageInit] Waiting for auth.js to load...');
        await new Promise(resolve => setTimeout(resolve, 100));
        retries++;
      }

      if (!window.getUser) {
        console.warn('[PageInit] Auth.js did not load within timeout');
        return;
      }

      console.log('[PageInit] Auth system ready, initializing user data...');
      
      // The auth module auto-initializes, but we can wait a bit for it to complete
      await new Promise(resolve => setTimeout(resolve, 200));
      
      const user = window.getUser();
      if (user) {
        console.log('[PageInit] User authenticated:', user.username || user.email);
      } else {
        console.log('[PageInit] User not yet loaded, will retry on visibility change');
      }

      this.authReady = true;
    } catch (e) {
      console.error('[PageInit] Failed to initialize auth:', e);
    }
  }

  /**
   * Setup handlers for page visibility changes (background/foreground)
   */
  setupVisibilityHandler() {
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) {
        console.log('[PageInit] Page became visible, refreshing auth state...');
        if (window.refreshAuth) {
          window.refreshAuth();
        }
      }
    });
    console.log('[PageInit] Visibility handler registered');
  }

  /**
   * Main initialization flow
   */
  async init() {
    // Run initialization steps
    this.initTheme();
    this.initNavigation();
    this.initBackButton();
    await this.initAuth();
    this.setupVisibilityHandler();

    console.log('[PageInit] Page initialization complete');
  }
}

/**
 * Global navigate function - handles both relative and absolute paths
 */
window.navigate = (path) => {
  if (path.startsWith('http')) {
    // Absolute URL
    window.location.href = path;
  } else if (path.startsWith('/webapp/')) {
    // Already has /webapp prefix
    window.location.href = path;
  } else if (path.startsWith('/')) {
    // Absolute path without /webapp - add it
    const filename = path.split('/').pop();
    const hasExtension = filename.includes('.');
    window.location.href = hasExtension ? `/webapp${path}` : `/webapp${path}.html`;
  } else {
    // Relative path - add .html if needed
    const hasExtension = path.includes('.');
    window.location.href = `/webapp/${path}${hasExtension ? '' : '.html'}`;
  }
};

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => new PageInitializer(), { once: true });
} else {
  new PageInitializer();
}

export default PageInitializer;

