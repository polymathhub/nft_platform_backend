/**
 * Telegram Authentication Module
 * Handles Telegram user authentication, profile data capture, and storage
 * Works seamlessly for anyone accessing the webapp via Telegram
 */

class TelegramAuthManager {
  constructor() {
    this.tg = window.Telegram?.WebApp || null;
    this.user = null;
    this.token = null;
  }

  /**
   * Initialize Telegram auth and check for existing session
   */
  async initialize() {
    try {
      // Check if user is already authenticated
      this.token = localStorage.getItem('token');
      const storedUser = localStorage.getItem('user');
      
      if (this.token && storedUser) {
        this.user = JSON.parse(storedUser);
        console.log('Existing session found:', this.user.username);
        return { authenticated: true, user: this.user };
      }

      // Check if running in Telegram
      if (!this.tg) {
        console.log('Not running in Telegram environment');
        return { authenticated: false };
      }

      // Get Telegram user data
      this.user = this.tg.initDataUnsafe?.user;
      if (!this.user) {
        console.warn('No Telegram user data available');
        return { authenticated: false };
      }

      return { authenticated: false, telegramUser: this.user };
    } catch (error) {
      console.error('Error initializing Telegram auth:', error);
      return { authenticated: false, error };
    }
  }

  /**
   * Authenticate with backend using Telegram initData
   */
  async authenticateWithBackend() {
    try {
      if (!this.tg?.initData) {
        throw new Error('Telegram data not available');
      }

      const response = await fetch('/api/v1/auth/telegram/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ init_data: this.tg.initData })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Auth failed (${response.status})`);
      }

      const data = await response.json();
      
      if (!data.token || !data.user) {
        throw new Error('Invalid response from server');
      }

      // Store authentication data
      this.token = data.token;
      localStorage.setItem('token', this.token);

      // Enrich user data with Telegram profile photo
      const telegramUser = this.tg.initDataUnsafe?.user || {};
      const userProfile = {
        ...data.user,
        avatar_url: data.user.avatar_url || telegramUser.photo_url || '',
        telegram_username: data.user.telegram_username || telegramUser.username || '',
        full_name: data.user.full_name || `${telegramUser.first_name || ''} ${telegramUser.last_name || ''}`.trim() || 'User',
        username: data.user.username || telegramUser.first_name || 'User',
        email: data.user.email || '',
        telegram_id: telegramUser.id
      };

      localStorage.setItem('user', JSON.stringify(userProfile));
      this.user = userProfile;

      return { success: true, user: userProfile };
    } catch (error) {
      console.error('Backend authentication error:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated() {
    return !!(this.token && this.user);
  }

  /**
   * Get current user profile
   */
  getUser() {
    return this.user;
  }

  /**
   * Get authentication token
   */
  getToken() {
    return this.token;
  }

  /**
   * Logout and clear session
   */
  logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    this.token = null;
    this.user = null;
    return true;
  }

  /**
   * Sync profile with Telegram real-time updates
   */
  syncWithTelegram() {
    try {
      if (!this.tg) return;

      const telegramUser = this.tg.initDataUnsafe?.user;
      if (!telegramUser) return;

      const storedUser = JSON.parse(localStorage.getItem('user') || '{}');
      
      // Update stored profile with latest Telegram data
      const updatedUser = {
        ...storedUser,
        // Always prefer Telegram's latest photo
        avatar_url: telegramUser.photo_url || storedUser.avatar_url,
        // Update username and name if they changed
        telegram_username: telegramUser.username || storedUser.telegram_username,
        full_name: storedUser.full_name || `${telegramUser.first_name || ''} ${telegramUser.last_name || ''}`.trim()
      };

      localStorage.setItem('user', JSON.stringify(updatedUser));
      this.user = updatedUser;
    } catch (error) {
      console.warn('Error syncing with Telegram:', error);
    }
  }

  /**
   * Get user's profile picture URL
   */
  getProfilePictureUrl() {
    if (!this.user) return null;
    
    // Priority: telegram photo > stored avatar > none
    const telegramUser = this.tg?.initDataUnsafe?.user;
    return telegramUser?.photo_url || this.user.avatar_url || null;
  }

  /**
   * Get user's display name
   */
  getDisplayName() {
    if (!this.user) return 'Guest';
    return this.user.full_name || this.user.username || this.user.email?.split('@')[0] || 'User';
  }

  /**
   * Get user's initial for avatar
   */
  getInitial() {
    const name = this.getDisplayName();
    return name.charAt(0).toUpperCase();
  }

  /**
   * Pre-fetch profile data before redirecting
   */
  async prefetchProfileData() {
    try {
      if (!this.token) return null;

      const response = await fetch('/api/v1/auth/profile', {
        headers: { 'Authorization': `Bearer ${this.token}` }
      });

      if (!response.ok) return null;

      const data = await response.json();
      const apiUser = data.data || data;

      // Merge with existing user data
      const mergedUser = { ...this.user, ...apiUser };
      localStorage.setItem('user', JSON.stringify(mergedUser));
      this.user = mergedUser;

      return mergedUser;
    } catch (error) {
      console.warn('Error prefetching profile data:', error);
      return null;
    }
  }
}

// Export as singleton
export const telegramAuth = new TelegramAuthManager();
