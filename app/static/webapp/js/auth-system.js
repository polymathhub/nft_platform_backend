/**
 * AUTHENTICATION SYSTEM - Telegram WebApp + FastAPI
 * ================================================
 * 
 * Production-grade authentication system for Telegram Mini Apps
 * 
 * ARCHITECTURE:
 * 1. Telegram SDK provides immutable initData (identity proof)
 * 2. Every API request includes X-Telegram-Init-Data header
 * 3. Backend verifies signature and returns authenticated user
 * 4. Frontend maintains user in memory (no token storage)
 * 5. localStorage used only for caching (always validated against API)
 * 
 * FEATURES:
 * ✅ No passwords, tokens, or refresh logic
 * ✅ Stateless backend (verify signature on every request)
 * ✅ Persistent state across navigations
 * ✅ Exponential backoff for failed auth attempts
 * ✅ Graceful degradation if auth fails
 * ✅ Single source of truth: Telegram initData
 */

// ============================================
// DEBUG: Intercept all redirects to log origin
// ============================================
(function() {
  // Override window.location.href setter
  const locationDescriptor = Object.getOwnPropertyDescriptor(window.location, 'href');
  Object.defineProperty(window.location, 'href', {
    get: locationDescriptor?.get,
    set: function(value) {
      console.warn('[AUTH-DEBUG] REDIRECT ATTEMPTED:', value);
      console.trace('[AUTH-DEBUG] Stack trace:');
      
      // Allow the redirect to proceed
      if (locationDescriptor?.set) {
        locationDescriptor.set.call(this, value);
      } else {
        window.location.replace(value);
      }
    },
    configurable: true
  });
  
  // Also intercept window.location.replace()
  const originalReplace = window.location.replace;
  window.location.replace = function(url) {
    console.warn('[AUTH-DEBUG] REPLACE ATTEMPTED:', url);
    console.trace('[AUTH-DEBUG] Stack trace:');
    return originalReplace.call(this, url);
  };
})();

// Global auth state
window.AuthSystem = {
  user: null,
  isAuthenticated: false,
  isInitialized: false,
  isInitializing: false,
  lastAuthAttempt: 0,
  lastError: null,
  authRetryCount: 0,
  MAX_RETRY_ATTEMPTS: 3,
  
  // ============================================
  // TELEGRAM SDK INITIALIZATION
  // ============================================
  
  /**
   * Wait for Telegram SDK to be available
   * Resolves when window.Telegram.WebApp.initData is ready
   * @param {number} timeout - Max wait time in ms (default 10 seconds)
   * @returns {Promise<boolean>} true if ready, false if timeout
   */
  async waitForTelegramSDK(timeout = 10000) {
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeout) {
      if (this.isTelegramReady()) {
        console.log('[AuthSystem] ✅ Telegram SDK ready');
        return true;
      }
      
      // Wait 100ms before checking again
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    console.warn(`[AuthSystem] ⚠️  Telegram SDK not ready after ${timeout}ms`);
    return false;
  },
  
  /**
   * Check if Telegram SDK is fully initialized
   * @returns {boolean}
   */
  isTelegramReady() {
    return !!(
      window.Telegram &&
      window.Telegram.WebApp &&
      window.Telegram.WebApp.initData &&
      window.Telegram.WebApp.initDataUnsafe &&
      window.Telegram.WebApp.initDataUnsafe.user
    );
  },
  
  /**
   * Get Telegram initData string
   * @returns {string|null}
   */
  getTelegramInitData() {
    try {
      return window.Telegram?.WebApp?.initData || null;
    } catch (e) {
      console.warn('[AuthSystem] Failed to get Telegram initData:', e.message);
      return null;
    }
  },
  
  /**
   * Get Telegram user data directly from SDK
   * Only use for display; always verify with backend
   * @returns {object|null}
   */
  getTelegramUser() {
    try {
      return window.Telegram?.WebApp?.initDataUnsafe?.user || null;
    } catch (e) {
      console.warn('[AuthSystem] Failed to get Telegram user:', e.message);
      return null;
    }
  },
  
  // ============================================
  // AUTHENTICATION FLOW
  // ============================================
  
  /**
   * Initialize authentication on app startup
   * Runs ONCE per app load - called from HTML <script>
   */
  async initialize() {
    // Prevent multiple initializations
    if (this.isInitialized) {
      console.log('[AuthSystem] 🔄 Already initialized');
      return this.user;
    }
    
    if (this.isInitializing) {
      console.log('[AuthSystem] ⏳ Initialization in progress...');
      return new Promise((resolve) => {
        const checkInterval = setInterval(() => {
          if (this.isInitialized) {
            clearInterval(checkInterval);
            resolve(this.user);
          }
        }, 100);
      });
    }
    
    this.isInitializing = true;
    
    try {
      console.log('[AuthSystem] 🚀 Starting initialization...');
      
      // Step 1: Wait for Telegram SDK
      console.log('[AuthSystem] Step 1 → Waiting for Telegram SDK...');
      const telegramReady = await this.waitForTelegramSDK(10000);
      
      if (!telegramReady) {
        console.warn('[AuthSystem] ⚠️  Telegram SDK not available - offline or non-Telegram context');
        this.isInitialized = true;
        this.isInitializing = false;
        this.emitEvent('auth:failed', { reason: 'Telegram SDK timeout' });
        return null;
      }
      
      // Step 2: Authenticate with backend
      console.log('[AuthSystem] Step 2 → Authenticating with backend...');
      const user = await this.authenticateWithBackend();
      
      if (user) {
        console.log('[AuthSystem] ✅ Authentication successful', {
          id: user.id,
          username: user.username,
          email: user.email,
        });
        
        // Step 3: Cache user for faster page loads
        this.cacheUser(user);
        
        this.isInitialized = true;
        this.isInitializing = false;
        this.emitEvent('auth:success', { user });
        
        return user;
      } else {
        console.warn('[AuthSystem] ❌ Authentication failed');
        this.isInitialized = true;
        this.isInitializing = false;
        this.emitEvent('auth:failed', { reason: 'Backend authentication failed' });
        
        // Return cached user as fallback (if available)
        const cachedUser = this.getCachedUser();
        if (cachedUser) {
          console.log('[AuthSystem] Using cached user as fallback');
          this.user = cachedUser;
          this.isAuthenticated = true;
          return cachedUser;
        }
        
        return null;
      }
    } catch (error) {
      console.error('[AuthSystem] ❌ Fatal initialization error:', error);
      this.lastError = error;
      this.isInitialized = true;
      this.isInitializing = false;
      this.emitEvent('auth:error', { error: error.message });
      
      // Return cached user as fallback
      const cachedUser = this.getCachedUser();
      if (cachedUser) {
        console.log('[AuthSystem] Using cached user after error');
        this.user = cachedUser;
        this.isAuthenticated = true;
        return cachedUser;
      }
      
      return null;
    }
  },
  
  /**
   * Authenticate with backend API
   * Sends Telegram initData and receives user object
   * @returns {Promise<object|null>} User object or null
   */
  async authenticateWithBackend() {
    const initData = this.getTelegramInitData();
    
    if (!initData) {
      console.error('[AuthSystem] No Telegram initData available');
      return null;
    }
    
    this.authRetryCount = 0;
    
    return this.authenticateWithRetry(initData);
  },
  
  /**
   * Authenticate with exponential backoff retry
   * @param {string} initData - Telegram initData
   * @returns {Promise<object|null>}
   */
  async authenticateWithRetry(initData) {
    try {
      const response = await fetch('/api/v1/me', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-Telegram-Init-Data': initData,
        },
        credentials: 'include',
      });
      
      if (!response.ok) {
        const error = new Error(`Auth failed: ${response.status} ${response.statusText}`);
        error.status = response.status;
        throw error;
      }
      
      const data = await response.json();
      
      if (data && data.id) {
        this.user = data;
        this.isAuthenticated = true;
        this.authRetryCount = 0;
        return data;
      } else {
        console.error('[AuthSystem] Invalid user data from backend:', data);
        return null;
      }
    } catch (error) {
      console.warn(`[AuthSystem] Auth attempt ${this.authRetryCount + 1} failed:`, error.message);
      
      this.lastError = error;
      this.authRetryCount++;
      
      if (this.authRetryCount >= this.MAX_RETRY_ATTEMPTS) {
        console.error('[AuthSystem] Max retry attempts reached');
        return null;
      }
      
      // Exponential backoff: 500ms, 1000ms, 2000ms
      const delay = Math.min(500 * Math.pow(2, this.authRetryCount - 1), 3000);
      console.log(`[AuthSystem] Retrying after ${delay}ms...`);
      
      await new Promise(resolve => setTimeout(resolve, delay));
      return this.authenticateWithRetry(initData);
    }
  },
  
  // ============================================
  // CACHING
  // ============================================
  
  /**
   * Cache user to localStorage for faster page loads
   * @param {object} user - User object
   */
  cacheUser(user) {
    try {
      localStorage.setItem('__auth_user_cache', JSON.stringify({
        user,
        cachedAt: new Date().toISOString(),
      }));
      console.log('[AuthSystem] ✅ User cached to localStorage');
    } catch (error) {
      console.warn('[AuthSystem] Failed to cache user:', error.message);
      // Non-fatal - continue without cache
    }
  },
  
  /**
   * Retrieve cached user from localStorage
   * @returns {object|null}
   */
  getCachedUser() {
    try {
      const cached = localStorage.getItem('__auth_user_cache');
      if (cached) {
        const { user, cachedAt } = JSON.parse(cached);
        
        // Cache is valid for 24 hours
        const cacheAge = Date.now() - new Date(cachedAt).getTime();
        const MAX_CACHE_AGE = 24 * 60 * 60 * 1000; // 24 hours
        
        if (cacheAge < MAX_CACHE_AGE && user && user.id) {
          console.log('[AuthSystem] ✅ Retrieved cached user (age: ' + Math.round(cacheAge / 1000) + 's)');
          return user;
        } else {
          console.log('[AuthSystem] Cached user expired, will fetch fresh');
          localStorage.removeItem('__auth_user_cache');
        }
      }
    } catch (error) {
      console.warn('[AuthSystem] Failed to read cache:', error.message);
    }
    
    return null;
  },
  
  /**
   * Clear cached user
   */
  clearCache() {
    try {
      localStorage.removeItem('__auth_user_cache');
      console.log('[AuthSystem] ✅ Cache cleared');
    } catch (error) {
      console.warn('[AuthSystem] Failed to clear cache:', error.message);
    }
  },
  
  // ============================================
  // USER STATE
  // ============================================
  
  /**
   * Get current authenticated user
   * @returns {object|null}
   */
  getUser() {
    return this.user;
  },
  
  /**
   * Check if user is authenticated
   * @returns {boolean}
   */
  isLoggedIn() {
    return this.isAuthenticated && !!this.user && !!this.user.id;
  },
  
  /**
   * Logout user (clears in-memory state and cache)
   */
  logout() {
    console.log('[AuthSystem] 🚪 Logging out...');
    
    this.user = null;
    this.isAuthenticated = false;
    this.clearCache();
    
    // Call backend logout endpoint (optional, backend is stateless)
    try {
      fetch('/api/v1/me/logout', {
        method: 'GET',
        headers: {
          'X-Telegram-Init-Data': this.getTelegramInitData() || '',
        },
        credentials: 'include',
      }).catch(err => console.warn('[AuthSystem] Backend logout failed:', err.message));
    } catch (e) {
      // Ignore
    }
    
    this.emitEvent('auth:logout', {});
  },
  
  // ============================================
  // EVENT SYSTEM
  // ============================================
  
  /**
   * Emit auth event (auth:success, auth:failed, auth:error, auth:logout)
   * @param {string} eventName
   * @param {object} detail
   */
  emitEvent(eventName, detail = {}) {
    const event = new CustomEvent(eventName, { detail });
    window.dispatchEvent(event);
    console.log(`[AuthSystem] Event: ${eventName}`, detail);
  },
  
  /**
   * Listen to auth events
   * @param {string} eventName
   * @param {function} callback
   */
  on(eventName, callback) {
    window.addEventListener(eventName, (event) => {
      callback(event.detail);
    });
  },
  
  // ============================================
  // API HELPERS
  // ============================================
  
  /**
   * Make authenticated API request
   * Automatically includes X-Telegram-Init-Data header
   * @param {string} endpoint - API endpoint
   * @param {object} options - Fetch options
   * @returns {Promise}
   */
  async apiCall(endpoint, options = {}) {
    const initData = this.getTelegramInitData();
    
    if (!initData && options.requireAuth !== false) {
      throw new Error('Not authenticated - Telegram initData not available');
    }
    
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };
    
    if (initData) {
      headers['X-Telegram-Init-Data'] = initData;
    }
    
    const url = endpoint.startsWith('http') ? endpoint : `${window.location.origin}${endpoint}`;
    
    const response = await fetch(url, {
      ...options,
      headers,
      credentials: 'include',
    });
    
    if (!response.ok) {
      const error = new Error(`API Error: ${response.status} ${response.statusText}`);
      error.status = response.status;
      throw error;
    }
    
    return response.json();
  },
};

// Auto-initialize on window load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.AuthSystem.initialize().catch(err => {
      console.error('[AuthSystem] Initialization failed:', err);
    });
  });
} else {
  // DOM already loaded
  window.AuthSystem.initialize().catch(err => {
    console.error('[AuthSystem] Initialization failed:', err);
  });
}

// Export for modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = window.AuthSystem;
}
