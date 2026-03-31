/**
 * SIMPLE AUTH - Telegram Mini App Authentication
 * ═══════════════════════════════════════════════════════════════
 * 
 * Single, clean authentication system
 * - Fetches user from /api/v1/me
 * - Automatically includes X-Telegram-Init-Data header
 * - Displays user name on page load
 * - Provides window.getUser() for other scripts
 * 
 * Usage:
 *   const user = window.getUser();  // Get current user
 *   auth.fetchUser();                // Refresh user data
 */

class SimpleAuth {
  constructor() {
    this.user = null;
    this.isAuthenticated = false;
  }

  /**
   * Get Telegram initData
   * @returns {string}
   */
  getInitData() {
    try {
      return window.Telegram?.WebApp?.initData || '';
    } catch (e) {
      console.warn('[Auth] Failed to get Telegram data:', e.message);
      return '';
    }
  }

  /**
   * Fetch user from backend
   * @returns {Promise<object>}
   */
  async fetchUser() {
    try {
      const initData = this.getInitData();
      
      const response = await fetch('/api/v1/me', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...(initData && { 'X-Telegram-Init-Data': initData })
        }
      });

      if (!response.ok) {
        console.warn(`[Auth] Failed to fetch user: ${response.status}`);
        return null;
      }

      const data = await response.json();
      
      // Handle both direct user object and wrapped response
      this.user = data.data || data;
      this.isAuthenticated = !!this.user;
      
      console.log('[Auth] User loaded:', this.user?.username || this.user?.email);
      return this.user;
    } catch (error) {
      console.error('[Auth] Error fetching user:', error);
      return null;
    }
  }

  /**
   * Get current user
   * @returns {object|null}
   */
  getUser() {
    return this.user;
  }

  /**
   * Get display name for user
   * @returns {string}
   */
  getDisplayName() {
    if (!this.user) return 'Guest';
    
    // Try different name fields
    if (this.user.full_name?.trim()) return this.user.full_name;
    if (this.user.first_name) return this.user.first_name;
    if (this.user.username) return `@${this.user.username}`;
    if (this.user.email) return this.user.email.split('@')[0];
    
    return 'User';
  }

  /**
   * Initialize auth on page load
   */
  async init() {
    // Fetch user data
    await this.fetchUser();
    
    // Update DOM with user name
    this.updateDOM();
  }

  /**
   * Update DOM with user information
   */
  updateDOM() {
    // Update user name spans
    document.querySelectorAll('#user-name').forEach(el => {
      el.textContent = this.getDisplayName();
    });

    // Update user name divs
    document.querySelectorAll('#userName').forEach(el => {
      el.textContent = this.getDisplayName();
    });

    // Update avatar if available
    if (this.user?.photo_url) {
      document.querySelectorAll('#profileAvatar, #profileAvatarLarge').forEach(el => {
        el.style.backgroundImage = `url('${this.user.photo_url}')`;
        el.style.backgroundSize = 'cover';
        el.style.backgroundPosition = 'center';
      });
    }
  }
}

// Initialize auth globally
const auth = new SimpleAuth();

// Expose to window
window.getUser = () => auth.getUser();
window.getDisplayName = () => auth.getDisplayName();

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    auth.init();
  });
} else {
  auth.init();
}

export default auth;
