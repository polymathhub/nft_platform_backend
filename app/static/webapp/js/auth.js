/**
 * ENHANCED AUTH - Telegram Mini App Authentication
 * ═══════════════════════════════════════════════════════════════
 * 
 * Production-grade authentication system with:
 * ✅ User data caching (5-minute TTL)
 * ✅ Avatar initials generation with consistent colors
 * ✅ Retry logic with exponential backoff (3 attempts)
 * ✅ Concurrent request prevention
 * ✅ DOM updates across all pages
 * ✅ Page visibility auto-refresh
 * 
 * Usage:
 *   const user = window.getUser();        // Get cached user
 *   window.refreshAuth();                 // Force refresh
 *   window.getDisplayName();              // Get user name
 *   const initials = auth.getAvatarInitials();  // Get initials
 */

class EnhancedAuth {
  constructor() {
    this.user = null;
    this.isAuthenticated = false;
    this.cacheExpiry = null;
    this.isFetching = false;  // Prevent concurrent fetches
    this.cacheTTL = 5 * 60 * 1000;  // 5 minutes in ms
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
   * Generate avatar initials from user data
   * @returns {string} 2-letter initials
   */
  getAvatarInitials() {
    if (!this.user) return 'GU';
    
    const fullName = this.user.full_name?.trim();
    if (fullName) {
      const parts = fullName.split(' ');
      if (parts.length > 1) {
        return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
      }
      return fullName.substring(0, 2).toUpperCase();
    }
    
    const firstName = this.user.first_name?.trim();
    const lastName = this.user.last_name?.trim();
    if (firstName && lastName) {
      return (firstName[0] + lastName[0]).toUpperCase();
    }
    if (firstName) {
      return firstName.substring(0, 2).toUpperCase();
    }
    
    const username = this.user.username?.trim();
    if (username) {
      return username.substring(0, 2).toUpperCase();
    }
    
    return 'GU';
  }

  /**
   * Generate consistent avatar color from initials (hash-based HSL)
   * @returns {string} HSL color
   */
  generateAvatarColor() {
    const initials = this.getAvatarInitials();
    let hash = 0;
    
    for (let i = 0; i < initials.length; i++) {
      hash = initials.charCodeAt(i) + ((hash << 5) - hash);
    }
    
    // Convert hash to HSL
    const hue = Math.abs(hash % 360);
    const saturation = 65 + (Math.abs(hash % 20));  // 65-85%
    const lightness = 50;  // 50% for nice contrast
    
    return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
  }

  /**
   * Get user from cache if valid, otherwise return null
   * @returns {object|null}
   */
  getCachedUser() {
    if (this.user && this.cacheExpiry && Date.now() < this.cacheExpiry) {
      console.log('[Auth] Returning cached user');
      return this.user;
    }
    this.user = null;
    this.cacheExpiry = null;
    return null;
  }

  /**
   * Fetch user from backend with caching and retry logic
   * @param {boolean} skipCache - Force fetch even if cached
   * @returns {Promise<object|null>}
   */
  async fetchUser(skipCache = false) {
    // Prevent concurrent fetches
    if (this.isFetching) {
      console.log('[Auth] Fetch already in progress, waiting...');
      // Wait for current fetch to complete
      await new Promise(resolve => {
        const checkInterval = setInterval(() => {
          if (!this.isFetching) {
            clearInterval(checkInterval);
            resolve();
          }
        }, 100);
      });
      return this.user;
    }

    // Use cache if available and not skipped
    if (!skipCache) {
      const cached = this.getCachedUser();
      if (cached) return cached;
    }

    this.isFetching = true;

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
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      this.user = data.data || data;
      this.isAuthenticated = !!this.user;
      this.cacheExpiry = Date.now() + this.cacheTTL;
      
      console.log('[Auth] User loaded:', this.user?.username || this.user?.email);
      return this.user;
    } catch (error) {
      console.error('[Auth] Error fetching user:', error);
      return null;
    } finally {
      this.isFetching = false;
    }
  }

  /**
   * Get current user from cache
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
    
    // Priority: full_name → first_name + last_name → username → email
    if (this.user.full_name?.trim()) return this.user.full_name;
    
    const firstName = this.user.first_name?.trim() || '';
    const lastName = this.user.last_name?.trim() || '';
    if (firstName || lastName) {
      return `${firstName} ${lastName}`.trim();
    }
    
    if (this.user.username) return `@${this.user.username}`;
    if (this.user.email) return this.user.email.split('@')[0];
    
    return 'User';
  }

  /**
   * Update DOM with user information across all pages
   */
  updateDOM() {
    const displayName = this.getDisplayName();
    const initials = this.getAvatarInitials();
    const avatarColor = this.generateAvatarColor();

    // Update user name in all elements
    document.querySelectorAll('#user-name, #userName').forEach(el => {
      el.textContent = displayName;
    });

    // Update user email/handle
    document.querySelectorAll('#userEmail').forEach(el => {
      el.textContent = this.user?.username || this.user?.email || 'No email';
    });

    // Update avatar initials and color
    document.querySelectorAll('#profileAvatar, #profileAvatarLarge').forEach(el => {
      // If user has photo_url, use it as background
      if (this.user?.photo_url) {
        el.style.backgroundImage = `url('${this.user.photo_url}')`;
        el.style.backgroundSize = 'cover';
        el.style.backgroundPosition = 'center';
        el.textContent = '';
      } else {
        // Otherwise show initials with generated color
        el.style.backgroundImage = 'none';
        el.style.backgroundColor = avatarColor;
        el.textContent = initials;
        el.style.display = 'flex';
        el.style.alignItems = 'center';
        el.style.justifyContent = 'center';
        el.style.fontSize = '14px';
        el.style.fontWeight = '600';
        el.style.color = '#fff';
      }
    });

    console.log('[Auth] DOM updated with user data');
  }

  /**
   * Initialize authentication with retry logic
   * @param {number} retries - Number of retry attempts
   * @param {number} retryDelay - Delay between retries in ms
   */
  async init(retries = 3, retryDelay = 100) {
    for (let attempt = 1; attempt <= retries; attempt++) {
      const user = await this.fetchUser();
      
      if (user) {
        this.updateDOM();
        console.log('[Auth] Init successful');
        return;
      }
      
      if (attempt < retries) {
        console.warn(`[Auth] Init attempt ${attempt} failed, retrying in ${retryDelay}ms...`);
        await new Promise(resolve => setTimeout(resolve, retryDelay));
        retryDelay *= 2;  // Exponential backoff
      }
    }
    
    console.error('[Auth] Init failed after', retries, 'attempts');
  }
}

// Initialize auth globally
const auth = new EnhancedAuth();

// Expose to window for global access
window.getUser = () => auth.getUser();
window.getDisplayName = () => auth.getDisplayName();
window.refreshAuth = async () => {
  await auth.fetchUser(true);  // Force refresh
  auth.updateDOM();
};

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    auth.init();
  });
} else {
  auth.init();
}

// Refresh auth when page becomes visible (handles backgrounding)
document.addEventListener('visibilitychange', () => {
  if (!document.hidden) {
    console.log('[Auth] Page visible, refreshing auth...');
    auth.init();
  }
});

export default auth;

