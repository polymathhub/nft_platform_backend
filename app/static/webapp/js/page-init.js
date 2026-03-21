/**
 * Page Initialization Module
 * Handles consistent page setup across all pages (welcome greeting, auth checks, etc.)
 * Uses Telegram WebApp initData for authentication (stateless, no JWT tokens)
 * @module js/page-init
 */

class PageInitializer {
  /**
   * Initialize page with authentication and user data
   * Handles:
   * - Authentication checks
   * - User name display (welcome section)
   * - Navigation active states
   */
  static async initializePage() {
    try {
      // Allow graceful fallback - no aggressive redirects
      // Pages should degrade gracefully, not redirect
      console.log('Page initialization started (graceful auth)');

      // Update user name in welcome section (uses Telegram initData)
      await this.updateWelcomeGreeting();
      
      // Setup navigation active states
      this.setupNavigation();
      
      return true;
    } catch (error) {
      console.error('Page initialization error:', error);
      // Graceful error handling - do not redirect
      return false;
    }
  }

  /**
   * Update welcome greeting with user's first name
   * Uses in-memory authManager user data (no API call)
   * Falls back to Telegram WebApp data if needed
   * @private
   */
  static async updateWelcomeGreeting() {
    try {
      let firstName = 'Guest';

      // First priority: Use authManager user (already loaded in memory)
      if (window.authManager?.isAuthenticated && window.authManager?.user) {
        const user = window.authManager.user;
        firstName = user.first_name 
          || user.firstName 
          || (user.name && user.name.split(' ')[0])
          || user.username
          || user.telegram_id
          || 'Guest';
      }
      // Fallback: Use Telegram WebApp data directly
      else if (window.Telegram?.WebApp?.initDataUnsafe?.user) {
        const tgUser = window.Telegram.WebApp.initDataUnsafe.user;
        firstName = tgUser.first_name || tgUser.username || 'Guest';
      }

      // Update all elements with id="user-name" (supports multiple on same page)
      const userNameElements = document.querySelectorAll('#user-name');
      userNameElements.forEach(element => {
        element.textContent = firstName;
      });

      console.log(`✅ Welcome greeting updated: Hello ${firstName}`);
    } catch (error) {
      console.warn('updateWelcomeGreeting error:', error);
      // Fallback to Guest if anything goes wrong
      const userNameElements = document.querySelectorAll('#user-name');
      userNameElements.forEach(element => {
        element.textContent = 'Guest';
      });
    }
  }
    }
  }

  /**
   * Setup navigation active state tracking
   * Marks current page's nav item as active
   * @private
   */
  static setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    
    if (navItems.length === 0) {
      console.warn('No navigation items found');
      return;
    }

    // Get current page path
    const currentPath = window.location.pathname;

    // Set active nav item based on current page
    navItems.forEach(item => {
      // Remove previous active state
      item.classList.remove('active');

      // Get href or data-page attribute
      const href = item.getAttribute('href') || item.getAttribute('data-page');
      
      // Compare with current path
      if (href && currentPath.includes(href.replace('/', ''))) {
        item.classList.add('active');
      }

      // Only add listener if haven't already (use data-listener-attached flag)
      if (!item.hasAttribute('data-listener-attached')) {
        item.addEventListener('click', function(e) {
          // Don't prevent default, just update active state
          if (!this.href) return; // Links will naturally navigate
          
          navItems.forEach(i => i.classList.remove('active'));
          this.classList.add('active');
        });
        
        // Mark as already having listener attached
        item.setAttribute('data-listener-attached', 'true');
      }
    });
  }

  /**
   * Rewrite any anchors that use absolute `/webapp/` paths to be basePath-aware at runtime
   * This avoids 404s when the app is served at root (static preview) or mounted at `/webapp`.
   */
  static rewriteWebappAnchors() {
    try {
      const basePath = window.location.pathname.startsWith('/webapp') ? '/webapp' : '';
      const anchors = document.querySelectorAll('a[href^="/webapp/"]');
      anchors.forEach(a => {
        const href = a.getAttribute('href');
        if (!href) return;
        const newHref = href.replace(/^\/webapp/, basePath);
        a.setAttribute('href', newHref);
      });
    } catch (err) {
      console.warn('rewriteWebappAnchors failed', err);
    }
  }

  /**
   * Global navigate function for onclick handlers
   * Can be called from HTML onclick="navigate('/path')"
   */
  static setupNavigateFunction() {
    window.navigate = function(path) {
      // Update nav active state before navigating
      PageInitializer.markNavActive(path);
      window.location.href = path;
    };
  }

  /**
   * Mark navigation item as active based on path
   * @private
   */
  static markNavActive(path) {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
      item.classList.remove('active');
      const href = item.getAttribute('href') || item.getAttribute('data-page');
      if (href && path.includes(href.replace('/', ''))) {
        item.classList.add('active');
      }
    });
  }

  /**
   * Listen for authentication changes and update UI
   * @private
   */
  static setupAuthListeners() {
    // Update greeting when user changes
    window.addEventListener('auth:login', () => {
      this.updateWelcomeGreeting();
    });

    // NOTE: auth:logout is handled globally in auth-bootstrap.js
    // Do NOT add duplicate listener here to avoid double-redirects

    // Handle auth errors
    window.addEventListener('auth:error', (event) => {
      console.error('Auth error:', event.detail);
    });
  }
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    PageInitializer.rewriteWebappAnchors();
    PageInitializer.initializePage();
    PageInitializer.setupNavigateFunction();
    PageInitializer.setupAuthListeners();
    // Safety net: ensure body is always visible
    if (document.body) document.body.style.display = '';
  });
} else {
  // DOM already loaded
  PageInitializer.rewriteWebappAnchors();
  PageInitializer.initializePage();
  PageInitializer.setupNavigateFunction();
  PageInitializer.setupAuthListeners();
  // Safety net: ensure body is always visible
  if (document.body) document.body.style.display = '';
}

export default PageInitializer;
