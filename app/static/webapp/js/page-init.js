/**
 * Page Initialization Module
 * Handles consistent page setup across all pages (welcome greeting, auth checks, etc.)
 * @module js/page-init
 */

import { auth } from '/webapp/js/auth.js';

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
      // Ensure user is authenticated
      if (!auth.isLoggedIn()) {
        console.warn('User not authenticated, redirecting to login');
        window.location.href = '/';
        return false;
      }

      // Update user name in welcome section
      this.updateWelcomeGreeting();
      
      // Setup navigation active states
      this.setupNavigation();
      
      return true;
    } catch (error) {
      console.error('Page initialization error:', error);
      window.location.href = '/';
      return false;
    }
  }

  /**
   * Update welcome greeting with user's first name
   * Handles both single and multiple user name elements
   * @private
   */
  static updateWelcomeGreeting() {
    const user = auth.getUser();
    
    // Get first name from various possible fields
    let firstName = 'Guest';
    
    if (user) {
      // Try different name field variations
      firstName = user.firstName 
        || user.first_name 
        || (user.name && user.name.split(' ')[0])
        || user.username
        || 'Guest';
    }

    // Update all elements with id="user-name" (supports multiple on same page)
    const userNameElements = document.querySelectorAll('#user-name');
    userNameElements.forEach(element => {
      element.textContent = firstName;
    });

    console.log(`✅ Welcome greeting updated: Hello ${firstName}`);
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
      item.classList.remove('active');

      // Get href or data-page attribute
      const href = item.getAttribute('href') || item.getAttribute('data-page');
      
      // Compare with current path
      if (href && currentPath.includes(href.replace('/', ''))) {
        item.classList.add('active');
      }

      // Also handle click events for manual navigation
      item.addEventListener('click', function() {
        // Don't prevent default, just update active state
        if (!this.href) return; // Links will naturally navigate
        
        navItems.forEach(i => i.classList.remove('active'));
        this.classList.add('active');
      });
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

    // Redirect on logout
    window.addEventListener('auth:logout', () => {
      console.log('User logged out, redirecting to login');
      window.location.href = '/';
    });

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
  });
} else {
  // DOM already loaded
  PageInitializer.rewriteWebappAnchors();
  PageInitializer.initializePage();
  PageInitializer.setupNavigateFunction();
  PageInitializer.setupAuthListeners();
}

export default PageInitializer;
