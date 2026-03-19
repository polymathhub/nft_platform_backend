/**
 * NAVBAR CONTROLLER
 * Handles header dropdowns, notifications, and bottom navigation
 */

class NavbarController {
  constructor() {
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
    
    // Real-time polling intervals
    this.notificationPollInterval = null;
    this.userDataPollInterval = null;
    this.telegramSyncInterval = null;
    
    this.init();
  }

  init() {
    this.setupEventListeners();
    this.setActiveNavItem();
    
    // Initialize with "P" placeholder
    this.initializeProfilePlaceholder();
    
    // Then load actual data
    this.loadUserData();
    this.loadNotifications();
    
    // Start real-time polling
    this.startRealtimeSync();
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
    // Only load notifications on-demand, no aggressive polling
    // Refresh notifications every 30 seconds (much less aggressive)
    this.notificationPollInterval = setInterval(() => {
      this.loadNotifications(true);
    }, 30000);

    // Refresh user data every 60 seconds (was 10s, too aggressive for mini app)
    this.userDataPollInterval = setInterval(() => {
      this.loadUserData();
    }, 60000);

    // Remove aggressive Telegram sync (was 3s, causing constant updates)
    // Only sync when needed, not continuously
    // this.telegramSyncInterval removed - too aggressive
  }

  syncTelegramProfile() {
    try {
      if (window.Telegram && window.Telegram.WebApp) {
        const tgUser = window.Telegram.WebApp.initDataUnsafe?.user;
        if (tgUser) {
          const user = JSON.parse(localStorage.getItem('user')) || {};
          
          // Update if Telegram photo exists
          if (tgUser.photo_url) {
            this.updateUserUI({
              ...user,
              avatar_url: tgUser.photo_url,
              username: tgUser.first_name || user.username || 'User'
            });
          }
        }
      }
    } catch (error) {
      // Silently fail - Telegram might not be available
    }
  }

  stopRealtimeSync() {
    if (this.notificationPollInterval) clearInterval(this.notificationPollInterval);
    if (this.userDataPollInterval) clearInterval(this.userDataPollInterval);
    // Telegram sync removed - no longer used
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
    // Profile dropdown
    if (this.profileBtn) {
      this.profileBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.toggleDropdown(this.profileDropdown);
        if (this.notificationDropdown) {
          this.notificationDropdown.classList.remove('active');
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

    // Close dropdowns when clicking outside
    document.addEventListener('click', (e) => {
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
    });

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

    // Nav items click handler
    this.navItems.forEach(item => {
      item.addEventListener('click', (e) => {
        this.navItems.forEach(navItem => navItem.classList.remove('active'));
        item.classList.add('active');
      });
    });
  }

  toggleDropdown(dropdown) {
    if (!dropdown) return;
    dropdown.classList.toggle('active');
  }

  loadUserData() {
    try {
      // First try to get from localStorage
      const user = JSON.parse(localStorage.getItem('user'));
      if (user) {
        this.updateUserUI(user);
      }

      // Then fetch latest from API
      const token = localStorage.getItem('token');
      if (token) {
        fetch('/api/user/profile', {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        .then(res => res.json())
        .then(data => {
          if (data.data) {
            const user = data.data;
            localStorage.setItem('user', JSON.stringify(user));
            this.updateUserUI(user);
          }
        })
        .catch(err => console.error('Error fetching user profile:', err));
      }

      // Check for Telegram WebApp user
      if (window.Telegram && window.Telegram.WebApp) {
        const tgUser = window.Telegram.WebApp.initDataUnsafe.user;
        if (tgUser && tgUser.photo_url) {
          this.updateUserUI({
            ...user,
            avatar_url: tgUser.photo_url,
            username: tgUser.first_name || user?.username || 'User'
          });
        }
      }
    } catch (error) {
      console.error('Error loading user data:', error);
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
      const token = localStorage.getItem('token');
      if (!token) {
        this.displayLocalNotifications();
        return;
      }

      // Fetch from API
      fetch('/api/notifications', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      .then(res => res.json())
      .then(data => {
        const notifications = data.data || data.notifications || [];
        
        // Store in localStorage for offline access
        localStorage.setItem('notifications', JSON.stringify(notifications));
        
        this.displayNotifications(notifications);
      })
      .catch(err => {
        console.error('Error fetching notifications from API:', err);
        // Fall back to localStorage
        this.displayLocalNotifications();
      });
    } catch (error) {
      console.error('Error loading notifications:', error);
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
      if (notifications.length === 0) {
        this.notificationList.innerHTML = '<div class="empty-notification">No notifications</div>';
      } else {
        this.notificationList.innerHTML = notifications.map((notif, index) => {
          const isRead = notif.read || notif.is_read;
          const title = notif.title || notif.subject || 'Notification';
          const description = notif.description || notif.message || notif.body || '';
          const timestamp = notif.timestamp || notif.created_at || new Date().toISOString();
          
          return `
            <div class="notification-item ${isRead ? 'read' : 'unread'}" data-id="${notif.id || index}">
              <div class="notification-icon">
                <div class="notification-dot ${isRead ? 'read' : 'unread'}"></div>
              </div>
              <div class="notification-content">
                <div class="notification-title">${this.escapeHtml(title)}</div>
                <div class="notification-description">${this.escapeHtml(description)}</div>
                <div class="notification-time">${this.formatTime(timestamp)}</div>
              </div>
              <button class="notification-delete-btn" data-id="${notif.id || index}" onclick="event.stopPropagation(); window.navbarController && window.navbarController.deleteNotification('${notif.id || index}')">×</button>
            </div>
          `;
        }).join('');
      }
    }
  }

  displayLocalNotifications() {
    try {
      const notifications = JSON.parse(localStorage.getItem('notifications')) || [];
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
      const token = localStorage.getItem('token');
      if (token) {
        fetch(`/api/notifications/${id}`, {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${token}` }
        })
        .then(() => this.loadNotifications(true))
        .catch(err => console.error('Error deleting notification:', err));
      }
    } catch (error) {
      console.error('Error deleting notification:', error);
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
   * Handle logout
   */
  handleLogout() {
    if (confirm('Are you sure you want to logout?')) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      localStorage.removeItem('notifications');
      const basePath = window.location.pathname.startsWith('/webapp') ? '/webapp' : '';
      window.location.href = basePath + '/dashboard.html';
    }
  }
}

/**
 * Initialize when DOM is ready
 */
document.addEventListener('DOMContentLoaded', () => {
  // Ensure navbar exists
  const header = document.querySelector('.app-header');
  if (header) {
    window.navbarController = new NavbarController();
  }
});

/**
 * Add notification
 * Usage: addNotification({ title: 'NFT Sale', description: 'Your NFT sold for 5 ETH' })
 */
function addNotification(notification) {
  try {
    const notifications = JSON.parse(localStorage.getItem('notifications')) || [];
    notifications.unshift({
      ...notification,
      timestamp: new Date().toISOString(),
      read: false
    });

    // Keep only last 50 notifications
    notifications.splice(50);

    localStorage.setItem('notifications', JSON.stringify(notifications));

    if (window.navbarController) {
      window.navbarController.loadNotifications();
    }
  } catch (error) {
    console.error('Error adding notification:', error);
  }
}

/**
 * Clear all notifications
 */
function clearAllNotifications() {
  try {
    localStorage.removeItem('notifications');
    if (window.navbarController) {
      window.navbarController.loadNotifications();
    }
  } catch (error) {
    console.error('Error clearing notifications:', error);
  }
}

