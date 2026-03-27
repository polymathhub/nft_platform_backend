/**
 * Real-time Notifications System using Socket.io
 * Provides centralized notification management across all pages
 */

class NotificationManager {
  constructor() {
    this.socket = null;
    this.notificationCount = 0;
    this.listeners = {};
    this.isConnected = false;
  }

  /**
   * Initialize Socket.io connection
   * @param {string} userId - User ID or Telegram ID
   * @param {Object} options - Additional connection options
   */
  initialize(userId, options = {}) {
    if (!userId) {
      console.warn('NotificationManager: userId is required');
      return;
    }

    if (typeof io === 'undefined') {
      console.warn('NotificationManager: Socket.io library not loaded');
      return;
    }

    const defaultOptions = {
      auth: {
        userId: userId,
        telegramInitData: window.Telegram?.WebApp?.initData || ''
      },
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 5,
      transports: ['websocket', 'polling']
    };

    const connectionOptions = { ...defaultOptions, ...options };

    try {
      this.socket = io(window.location.origin, connectionOptions);
      this.setupEventListeners();
      console.log('NotificationManager: Socket initialized');
    } catch (error) {
      console.error('NotificationManager: Failed to initialize socket', error);
    }
  }

  /**
   * Setup core socket event listeners
   */
  setupEventListeners() {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      this.isConnected = true;
      console.log('Notification socket connected');
      this.emit('connected');
    });

    this.socket.on('disconnect', (reason) => {
      this.isConnected = false;
      console.log('Notification socket disconnected:', reason);
      this.emit('disconnected', reason);
    });

    // Generic notification event
    this.socket.on('notification', (data) => {
      this.handleNotification(data);
    });

    // NFT-related events
    this.socket.on('nft:minted', (data) => {
      this.showNotification('NFT Minted', `Your NFT "${data.nft_name}" has been successfully minted!`, 'success');
      this.emit('nft:minted', data);
    });

    this.socket.on('nft:listed', (data) => {
      this.showNotification('NFT Listed', `Your NFT has been listed for ${data.price}`, 'info');
      this.emit('nft:listed', data);
    });

    this.socket.on('nft:sold', (data) => {
      this.showNotification('Sale Confirmed', `Your NFT sold for ${data.price}!`, 'success');
      this.emit('nft:sold', data);
    });

    // Referral events
    this.socket.on('referral:earned', (data) => {
      this.showNotification('Referral Earnings', `You earned ${data.amount} from a referral!`, 'success');
      this.emit('referral:earned', data);
    });

    // Wallet events
    this.socket.on('wallet:connected', (data) => {
      this.showNotification('Wallet Connected', `${data.wallet_address.slice(0, 10)}... connected`, 'info');
      this.emit('wallet:connected', data);
    });

    // Error handling
    this.socket.on('error', (error) => {
      console.error('Socket.io error:', error);
      this.emit('error', error);
    });
  }

  /**
   * Handle incoming notification
   * @param {Object} data - Notification data
   */
  handleNotification(data) {
    const { type, title, message, action_url } = data;
    this.showNotification(title || 'Notification', message, type || 'info', action_url);
    this.emit('notification', data);
  }

  /**
   * Display notification toast
   * @param {string} title - Notification title
   * @param {string} message - Notification message
   * @param {string} type - Notification type (success, error, warning, info)
   * @param {string} actionUrl - Optional action URL
   */
  showNotification(title, message, type = 'info', actionUrl = null) {
    this.notificationCount++;
    this.updateBadge();

    const notification = document.createElement('div');
    notification.style.cssText = `
      position: fixed;
      top: 70px;
      right: 16px;
      background: white;
      border-radius: 12px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
      padding: 16px;
      max-width: 360px;
      z-index: 9999;
      animation: slideInRight 0.3s ease-out;
      border-left: 4px solid;
    `;

    const colors = {
      success: '#10b981',
      error: '#ef4444',
      warning: '#f59e0b',
      info: '#3b82f6'
    };

    notification.style.borderLeftColor = colors[type] || colors.info;

    const titleEl = document.createElement('div');
    titleEl.style.cssText = 'font-weight: 600; color: #1a202c; margin-bottom: 4px; font-size: 14px;';
    titleEl.textContent = title;

    const messageEl = document.createElement('div');
    messageEl.style.cssText = 'color: #5a6370; font-size: 13px; line-height: 1.5;';
    messageEl.textContent = message;

    notification.appendChild(titleEl);
    notification.appendChild(messageEl);

    if (actionUrl) {
      const linkEl = document.createElement('a');
      linkEl.href = actionUrl;
      linkEl.style.cssText = 'display: inline-block; color: #5856d6; text-decoration: none; font-size: 12px; margin-top: 8px; font-weight: 600;';
      linkEl.textContent = 'View';
      notification.appendChild(linkEl);
    }

    document.body.appendChild(notification);

    setTimeout(() => {
      notification.style.animation = 'slideOutRight 0.3s ease-in';
      setTimeout(() => notification.remove(), 300);
    }, 5000);
  }

  /**
   * Update notification badge
   */
  updateBadge() {
    const badge = document.querySelector('.notification-badge');
    if (badge) {
      if (this.notificationCount > 0) {
        badge.style.display = 'block';
      }
    }
  }

  /**
   * Emit custom event
   * @param {string} eventName - Event name
   * @param {*} data - Event data
   */
  emit(eventName, data = null) {
    if (this.listeners[eventName]) {
      this.listeners[eventName].forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in listener for ${eventName}:`, error);
        }
      });
    }
  }

  /**
   * Register event listener
   * @param {string} eventName - Event name
   * @param {Function} callback - Callback function
   */
  on(eventName, callback) {
    if (!this.listeners[eventName]) {
      this.listeners[eventName] = [];
    }
    this.listeners[eventName].push(callback);
  }

  /**
   * Remove event listener
   * @param {string} eventName - Event name
   * @param {Function} callback - Callback function to remove
   */
  off(eventName, callback) {
    if (this.listeners[eventName]) {
      this.listeners[eventName] = this.listeners[eventName].filter(cb => cb !== callback);
    }
  }

  /**
   * Disconnect socket
   */
  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.isConnected = false;
    }
  }

  /**
   * Check if notification is connected
   */
  isConnectedTo() {
    return this.isConnected;
  }
}

// Create and export singleton instance
const notificationManager = new NotificationManager();

// Add animations to document if not already present
if (!document.querySelector('style[data-notifications]')) {
  const style = document.createElement('style');
  style.setAttribute('data-notifications', 'true');
  style.textContent = `
    @keyframes slideInRight {
      from {
        transform: translateX(400px);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }
    @keyframes slideOutRight {
      from {
        transform: translateX(0);
        opacity: 1;
      }
      to {
        transform: translateX(400px);
        opacity: 0;
      }
    }
  `;
  document.head.appendChild(style);
}

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = notificationManager;
}

// Make available globally
window.notificationManager = notificationManager;
