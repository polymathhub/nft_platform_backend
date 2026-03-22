
class NavbarController {
  constructor() {
    // Guard against multiple initializations
    if (window.navbarControllerInstance) {
      console.warn('[Navbar] NavbarController already exists, returning existing instance');
      return window.navbarControllerInstance;
    }
    
    this.profileBtn = document.getElementById('profileBtn');
    this.notificationBtn = document.getElementById('notificationBtn');
    this.profileDropdown = document.getElementById('profileDropdown');
    this.notificationDropdown = document.getElementById('notificationDropdown');
    this.headerOverlay = document.getElementById('headerOverlay');
    
    this.profileAvatar = document.getElementById('profileAvatar');
    this.profileAvatarLarge = document.getElementById('profileAvatarLarge');
    this.userName = document.getElementById('userName');
    this.userEmail = document.getElementById('userEmail');
    this.notificationBadge = document.getElementById('notificationBadge');
    this.notificationList = document.getElementById('notificationList');
    this.logoutBtn = document.getElementById('logoutBtn');
    this.notificationClose = document.getElementById('notificationClose');
    
    this.navItems = document.querySelectorAll('.nav-item');
    this.currentPage = this.detectCurrentPage();

    // Mark that this instance has been set up
    this.setupComplete = false;
    
    this.init();
    
    // Store instance to prevent re-creation
    window.navbarControllerInstance = this;
  }

  init() {
    this.setupEventListeners();
    this.setActiveNavItem();
    
    // Initialize with "P" placeholder
    this.initializeProfilePlaceholder();
    // Try to initialize user from central auth module (non-blocking)
    this.initUserFromCore().catch(err => {
      console.warn('[Navbar] initUserFromCore failed', err);
    });
    
    // NOTE: All data loading is now on-demand, triggered by user interaction only
    // No automatic API calls on initialization - navbar is a passive UI component
  }

  initializeProfilePlaceholder() {
    if (this.profileAvatar) {
      this.profileAvatar.textContent = 'P';
      this.profileAvatar.style.backgroundImage = 'none';
    }
    if (this.profileAvatarLarge) {
      this.profileAvatarLarge.textContent = 'P';
      this.profileAvatarLarge.style.backgroundImage = 'none';
    }
  }

  startRealtimeSync() {
    console.log('[Navbar] Real-time sync disabled - using on-demand loading only');
  }

  syncTelegramProfile() {
    try {
      let user = null;

      // TRY 1: authManager (includes localStorage fallback)
      if (window.authManager?.user) {
        user = { ...window.authManager.user };
      }
      // TRY 2: Telegram WebApp
      else if (window.Telegram?.WebApp?.initDataUnsafe?.user) {
        user = { ...window.Telegram.WebApp.initDataUnsafe.user };
      }
      // TRY 3: localStorage fallback (direct)
      else {
        try {
          const cachedUser = localStorage.getItem('app_tg_user');
          if (cachedUser) {
            user = JSON.parse(cachedUser);
          }
        } catch (e) {
          console.warn('[Navbar] Failed to parse cached user:', e);
        }
      }

      if (!user || !user.id) {
        console.log('[Navbar] No user available for profile sync');
        return;
      }

      // Get photo_url from Telegram if available (always fresh from SDK)
      const tgUser = window.Telegram?.WebApp?.initDataUnsafe?.user;
      if (tgUser && tgUser.photo_url) {
        user.avatar_url = tgUser.photo_url;
      }

      // Ensure we have a display name
      user.username = user.first_name || user.username || 'User';

      this.updateUserUI(user);
      console.log('[Navbar] Profile synced:', user.username);
    } catch (error) {
      console.warn('[Navbar] Failed to sync profile:', error.message);
      // Silently fail - non-critical
    }
  }

  async initUserFromCore() {
    try {
      // Dynamically import core auth to avoid breaking non-module pages
      const mod = await import('./js/core/auth.js');
      if (!mod || !mod.getCurrentUser) return;
      const user = await mod.getCurrentUser();
      if (!user) {
        // still attempt to fill with Telegram SDK unsafe data
        const tg = window.Telegram?.WebApp?.initDataUnsafe?.user;
        if (tg) {
          this.updateUserUI({
            username: tg.first_name || tg.username || 'User',
            avatar_url: tg.photo_url || null,
          });
        }
        return;
      }

      // Map backend user shape to navbar expected fields
      const mapped = {
        username: user.first_name || user.username || user.full_name || 'User',
        email: user.email || '',
        avatar_url: user.photo_url || user.avatar_url || null,
      };

      this.updateUserUI(mapped);
    } catch (error) {
      console.warn('[Navbar] initUserFromCore error:', error);
    }
  }

  stopRealtimeSync() {
    // No-op: All polling intervals have been disabled
    console.log('[Navbar] Real-time sync already stopped (no intervals)');
  }

  detectCurrentPage() {
    const path = window.location.pathname.toLowerCase();
    if (path.includes('dashboard')) return 'dashboard';
    if (path.includes('wallet')) return 'wallet';
    if (path.includes('marketplace')) return 'marketplace';
    if (path.includes('mint')) return 'mint';
    if (path.includes('profile')) return 'profile';
    return 'dashboard';
  }

  setActiveNavItem() {
    this.navItems.forEach(item => {
      const page = item.getAttribute('data-page');
      if (page === this.currentPage) {
        item.classList.add('active');
      } else {
        item.classList.remove('active');
      }
    });
  }

  setupEventListeners() {
    // Guard against multiple listener attachments
    if (this.listenersAttached) {
      console.log('[Navbar] Event listeners already attached, skipping');
      return;
    }
    this.listenersAttached = true;

    // Profile dropdown
    if (this.profileBtn) {
      this.profileBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.toggleDropdown(this.profileDropdown);
        if (this.notificationDropdown) {
          this.notificationDropdown.classList.remove('active');
        }
        // Load user data only when profile dropdown is opened (on-demand)
        if (this.profileDropdown?.classList.contains('active')) {
          this.loadUserData();
        }
      });
    }

    // Notification dropdown
    if (this.notificationBtn) {
      this.notificationBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.toggleDropdown(this.notificationDropdown);
        if (this.profileDropdown) {
          this.profileDropdown.classList.remove('active');
        }
        this.loadNotifications();
      });
    }

    // Header overlay to close dropdowns
    if (this.headerOverlay) {
      this.headerOverlay.addEventListener('click', () => {
        if (this.profileDropdown) {
          this.profileDropdown.classList.remove('active');
        }
        if (this.notificationDropdown) {
          this.notificationDropdown.classList.remove('active');
        }
      });
    }

    // Close dropdowns when clicking outside - use event delegation
    const closeDropdownsHandler = (e) => {
      if (!e.target.closest('.profile-btn') && !e.target.closest('#profileDropdown')) {
        if (this.profileDropdown) {
          this.profileDropdown.classList.remove('active');
        }
      }
      if (!e.target.closest('.notifications-btn') && !e.target.closest('#notificationDropdown')) {
        if (this.notificationDropdown) {
          this.notificationDropdown.classList.remove('active');
        }
      }
    };
    
    // Store handler for cleanup
    this.closeDropdownsHandler = closeDropdownsHandler;
    document.addEventListener('click', closeDropdownsHandler);

    // Logout button
    if (this.logoutBtn) {
      this.logoutBtn.addEventListener('click', () => this.handleLogout());
    }

    // Notification close button
    if (this.notificationClose) {
      this.notificationClose.addEventListener('click', () => {
        if (this.notificationDropdown) {
          this.notificationDropdown.classList.remove('active');
        }
      });
    }

    // Nav items click handler - store for potential cleanup
    const navItemHandler = (item, e) => {
      this.navItems.forEach(navItem => navItem.classList.remove('active'));
      item.classList.add('active');
    };
    
    this.navItemHandlers = [];
    this.navItems.forEach(item => {
      const handler = (e) => navItemHandler(item, e);
      item.addEventListener('click', handler);
      this.navItemHandlers.push({ item, handler });
    });
  }

  toggleDropdown(dropdown) {
    if (!dropdown) return;
    dropdown.classList.toggle('active');
  }

  loadUserData() {
    try {
      // Check if authManager is already initialized
      if (window.authManager?.user) {
        this.updateUserUIFromAuthManager();
        this.syncTelegramProfile();
        return;
      }

      // If authManager still initializing, wait for auth:initialized event
      if (window.addEventListener) {
        const handleAuthInit = () => {
          this.updateUserUIFromAuthManager();
          this.syncTelegramProfile();
          window.removeEventListener('auth:initialized', handleAuthInit);
        };
        window.addEventListener('auth:initialized', handleAuthInit);
      }

      // Fallback: Read directly from Telegram WebApp for avatar and display name
      if (window.Telegram && window.Telegram.WebApp) {
        const tgUser = window.Telegram.WebApp.initDataUnsafe?.user;
        if (tgUser && tgUser.photo_url) {
          this.updateUserUI({
            avatar_url: tgUser.photo_url,
            username: tgUser.first_name || 'User'
          });
        }
      }
    } catch (error) {
      console.error('Error loading user data:', error);
    }
  }

  updateUserUIFromAuthManager() {
    try {
      const user = window.authManager?.user;
      if (user) {
        this.updateUserUI(user);
      }
    } catch (error) {
      console.error('[Navbar] Error updating UI from authManager:', error);
    }
  }

  updateUserUI(user) {
    if (this.userName) this.userName.textContent = user.username || user.name || 'User';
    if (this.userEmail) this.userEmail.textContent = user.email || '';
    
    // Handle profile avatar - check multiple sources
    const avatarUrl = user.avatar_url || user.avatar || user.photo_url || user.telegram_photo_url;
    
    if (avatarUrl) {
      // Display actual profile picture
      if (this.profileAvatar) {
        this.profileAvatar.style.backgroundImage = `url('${avatarUrl}')`;
        this.profileAvatar.style.backgroundSize = 'cover';
        this.profileAvatar.style.backgroundPosition = 'center';
        this.profileAvatar.textContent = '';
      }
      if (this.profileAvatarLarge) {
        this.profileAvatarLarge.style.backgroundImage = `url('${avatarUrl}')`;
        this.profileAvatarLarge.style.backgroundSize = 'cover';
        this.profileAvatarLarge.style.backgroundPosition = 'center';
        this.profileAvatarLarge.textContent = '';
      }
    } else {
      // Show initial "P" if no profile picture
      const initial = 'P';
      if (this.profileAvatar) {
        this.profileAvatar.textContent = initial;
        this.profileAvatar.style.backgroundImage = 'none';
      }
      if (this.profileAvatarLarge) {
        this.profileAvatarLarge.textContent = initial;
        this.profileAvatarLarge.style.backgroundImage = 'none';
      }
    }
  }

  loadNotifications(silent = false) {
    try {
      // Get initData safely
      const getInitData = () => window.Telegram?.WebApp?.initData || null;
      const initData = getInitData();
      
      if (!initData) {
        console.log('[Navbar] No Telegram initData - using local notifications');
        this.displayLocalNotifications();
        return;
      }

      this.fetchNotificationsFromAPI();
    } catch (error) {
      console.error('Error loading notifications:', error);
      this.displayLocalNotifications();
    }
  }

  async fetchNotificationsFromAPI() {
    try {
      // Get initData safely
      const getInitData = () => window.Telegram?.WebApp?.initData || null;
      const initData = getInitData();
      
      if (!initData) return;

      // Use centralized apiFetch
      const api = await import('./js/core/api.js');
      const response = await api.apiFetch('/api/v1/notifications', { method: 'GET' });

      // If 404, endpoint doesn't exist - fall back to local
      if (response.status === 404) {
        console.warn('[Navbar] Notifications endpoint not found, using local cache');
        this.displayLocalNotifications();
        return;
      }

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      if (data && (data.data || data.notifications)) {
        const notifications = data.data || data.notifications || [];
        
        // Cache in memory (session-only, not persistent)
        window.notificationCache = notifications;
        
        this.displayNotifications(notifications);
      }
    } catch (err) {
      console.warn('[Navbar] Error fetching notifications, using local cache:', err.message);
      // Fall back to localStorage
      this.displayLocalNotifications();
    }
  }

  displayNotifications(notifications) {
    const unreadCount = notifications.filter(n => !n.read && !n.is_read).length;

    // Update badge
    if (this.notificationBadge) {
      this.notificationBadge.textContent = unreadCount;
      this.notificationBadge.style.display = unreadCount > 0 ? 'flex' : 'none';
    }

    // Update notification list
    if (this.notificationList) {
      this.notificationList.innerHTML = '';
      
      if (notifications.length === 0) {
        const empty = document.createElement('div');
        empty.className = 'empty-notification';
        empty.textContent = 'No notifications';
        this.notificationList.appendChild(empty);
      } else {
        notifications.forEach((notif, index) => {
          const item = document.createElement('div');
          item.className = `notification-item ${(notif.read || notif.is_read) ? 'read' : 'unread'}`;
          item.id = `notif-${notif.id || index}`;
          item.setAttribute('data-id', notif.id || index);
          
          const title = notif.title || notif.subject || 'Notification';
          const description = notif.description || notif.message || notif.body || '';
          const timestamp = notif.timestamp || notif.created_at || new Date().toISOString();
          const isRead = notif.read || notif.is_read;
          
          // Build using createElement to prevent XSS
          const icon = document.createElement('div');
          icon.className = 'notification-icon';
          const dot = document.createElement('div');
          dot.className = `notification-dot ${isRead ? 'read' : 'unread'}`;
          icon.appendChild(dot);
          
          const content = document.createElement('div');
          content.className = 'notification-content';
          const titleEl = document.createElement('div');
          titleEl.className = 'notification-title';
          titleEl.textContent = title;
          const descEl = document.createElement('div');
          descEl.className = 'notification-description';
          descEl.textContent = description;
          const timeEl = document.createElement('div');
          timeEl.className = 'notification-time';
          timeEl.textContent = this.formatTime(timestamp);
          
          content.appendChild(titleEl);
          content.appendChild(descEl);
          content.appendChild(timeEl);
          
          const deleteBtn = document.createElement('button');
          deleteBtn.className = 'notification-delete-btn';
          deleteBtn.textContent = '×';
          deleteBtn.setAttribute('data-id', notif.id || index);
          deleteBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.deleteNotification(notif.id || index);
          });
          
          item.appendChild(icon);
          item.appendChild(content);
          item.appendChild(deleteBtn);
          this.notificationList.appendChild(item);
        });
      }
    }
  }

  displayLocalNotifications() {
    try {
      // Use in-memory cache instead of localStorage
      const notifications = window.notificationCache || [];
      this.displayNotifications(notifications);
    } catch (error) {
      console.error('Error displaying local notifications:', error);
    }
  }

  escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  deleteNotification(id) {
    try {
      const initData = window.Telegram?.WebApp?.initData;
      if (!initData) {
        console.log('[Navbar] No Telegram initData - cannot delete notification');
        return;
      }

      this.deleteNotificationFromAPI(id);
    } catch (error) {
      console.error('Error deleting notification:', error);
    }
  }

  async deleteNotificationFromAPI(id) {
    try {
      const api = await import('./js/core/api.js');
      const response = await api.apiFetch(`/api/v1/notifications/${id}`, { method: 'DELETE' });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      // Reload notifications to sync state
      this.loadNotifications(true);
    } catch (err) {
      console.error('[Navbar] Error deleting notification:', err);
      // Try to reload from API to sync state
      this.loadNotifications(true);
    }
  }

  /**
   * Format time
   */
  formatTime(timestamp) {
    if (!timestamp) return 'Just now';

    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diff = now - date;

      const mins = Math.floor(diff / 60000);
      const hours = Math.floor(diff / 3600000);
      const days = Math.floor(diff / 86400000);

      if (mins < 1) return 'Just now';
      if (mins < 60) return `${mins}m ago`;
      if (hours < 24) return `${hours}h ago`;
      if (days < 7) return `${days}d ago`;

      return date.toLocaleDateString();
    } catch (error) {
      return 'Recently';
    }
  }

  /**
   * Cleanup method - remove all event listeners
   */
  cleanup() {
    if (this.closeDropdownsHandler) {
      document.removeEventListener('click', this.closeDropdownsHandler);
    }
    
    if (this.navItemHandlers) {
      this.navItemHandlers.forEach(({ item, handler }) => {
        item.removeEventListener('click', handler);
      });
    }
  }

  /**
   * Handle logout (stateless - just clear client state and redirect)
   */
  handleLogout() {
    if (confirm('Are you sure you want to logout?')) {
      // Clear in-memory auth state
      if (window.authManager) {
        window.authManager.logout();
      }
      // Do NOT force navigation — keep logout passive so pages don't get redirected automatically.
      if (window.AuthSystem && typeof window.AuthSystem.logout === 'function') {
        try { window.AuthSystem.logout(); } catch (e) { /* ignore */ }
      }
      alert('You have been logged out. Use the Home button to return to Dashboard when ready.');
    }
  }
}

/**
 * Initialize when DOM is ready
 */
document.addEventListener('DOMContentLoaded', () => {
  // Prevent multiple initializations of navbar
  if (window.navbarControllerInitialized) {
    console.log('[Navbar] Already initialized, skipping');
    return;
  }
  window.navbarControllerInitialized = true;

  // Ensure navbar exists
  const header = document.querySelector('.app-header');
  if (header) {
    window.navbarController = new NavbarController();
  }
}, { once: true });

/**
 * In-memory notification cache (session-only, not persistent)
 */
window.notificationCache = [];

/**
 * Add notification (stores in session memory, not localStorage)
 * Usage: addNotification({ title: 'NFT Sale', description: 'Your NFT sold for 5 ETH' })
 */
function addNotification(notification) {
  try {
    // Add to in-memory cache only
    window.notificationCache.unshift({
      ...notification,
      timestamp: new Date().toISOString(),
      read: false
    });

    // Keep only last 50 notifications in memory
    window.notificationCache.splice(50);

    // Trigger UI update if navbar is initialized
    if (window.navbarController) {
      window.navbarController.loadNotifications();
    }
  } catch (error) {
    console.error('Error adding notification:', error);
  }
}

/**
 * Clear all notifications (session memory only)
 */
function clearAllNotifications() {
  try {
    window.notificationCache = [];
    if (window.navbarController) {
      window.navbarController.loadNotifications();
    }
  } catch (error) {
    console.error('Error clearing notifications:', error);
  }
}

