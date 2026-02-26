/**
 * Application State Management
 * Central state store for all UI components
 */

class AppState {
  constructor() {
    // User & Auth State
    this.currentUser = null;
    this.isAuthenticated = false;
    this.isLoading = false;
    this.error = null;

    // Wallet State
    this.wallets = [];
    this.selectedWalletId = null;

    // NFT State
    this.userNFTs = [];
    this.nftLoading = false;
    this.nftError = null;

    // Marketplace State
    this.activeListings = [];
    this.userListings = [];
    this.listingsLoading = false;
    this.listingsError = null;

    // Notification State
    this.notifications = [];
    this.unreadCount = 0;

    // UI State
    this.activeView = 'home';
    this.showModal = null;
    this.modalData = null;

    // Subscribers for state changes
    this.subscribers = {
      user: [],
      wallets: [],
      nfts: [],
      listings: [],
      notifications: [],
      view: [],
      all: [],
    };

    // Load persisted state from localStorage
    this.loadPersistedState();
  }

  /**
   * STATE MANAGEMENT
   */

  subscribe(key, callback) {
    if (this.subscribers[key]) {
      this.subscribers[key].push(callback);
    }
    // Also subscribe to 'all' for global changes
    this.subscribers.all.push(callback);

    // Return unsubscribe function
    return () => {
      if (this.subscribers[key]) {
        this.subscribers[key] = this.subscribers[key].filter(cb => cb !== callback);
      }
      this.subscribers.all = this.subscribers.all.filter(cb => cb !== callback);
    };
  }

  notify(key, data) {
    if (this.subscribers[key]) {
      this.subscribers[key].forEach(cb => cb(data));
    }
    this.subscribers.all.forEach(cb => cb({ [key]: data }));
  }

  /**
   * USER & AUTH
   */

  setCurrentUser(user) {
    this.currentUser = user;
    this.isAuthenticated = !!user;
    localStorage.setItem('currentUser', JSON.stringify(user));
    this.notify('user', user);
  }

  clearAuth() {
    this.currentUser = null;
    this.isAuthenticated = false;
    this.wallets = [];
    this.selectedWalletId = null;
    localStorage.removeItem('currentUser');
    this.notify('user', null);
  }

  /**
   * WALLETS
   */

  setWallets(wallets) {
    this.wallets = wallets;
    // Auto-select first wallet if none selected
    if (!this.selectedWalletId && wallets.length > 0) {
      this.setSelectedWallet(wallets[0].id);
    }
    this.notify('wallets', wallets);
  }

  setSelectedWallet(walletId) {
    this.selectedWalletId = walletId;
    localStorage.setItem('selectedWalletId', walletId);
    this.notify('wallets', { selectedWalletId: walletId });
  }

  getSelectedWallet() {
    return this.wallets.find(w => w.id === this.selectedWalletId);
  }

  addWallet(wallet) {
    this.wallets.push(wallet);
    if (!this.selectedWalletId) {
      this.setSelectedWallet(wallet.id);
    } else {
      this.notify('wallets', this.wallets);
    }
  }

  /**
   * NFTs
   */

  setUserNFTs(nfts) {
    this.userNFTs = nfts;
    this.nftError = null;
    this.notify('nfts', nfts);
  }

  setNFTLoading(loading) {
    this.nftLoading = loading;
  }

  setNFTError(error) {
    this.nftError = error;
    this.notify('nfts', { error });
  }

  getNFTCount() {
    return this.userNFTs.length;
  }

  /**
   * LISTINGS & MARKETPLACE
   */

  setActiveListings(listings) {
    this.activeListings = listings;
    this.listingsError = null;
    this.notify('listings', { activeListings: listings });
  }

  setUserListings(listings) {
    this.userListings = listings;
    this.listingsError = null;
    this.notify('listings', { userListings: listings });
  }

  setListingsLoading(loading) {
    this.listingsLoading = loading;
  }

  setListingsError(error) {
    this.listingsError = error;
    this.notify('listings', { error });
  }

  getActiveListingCount() {
    return this.userListings.filter(l => l.status === 'ACTIVE').length;
  }

  /**
   * NOTIFICATIONS
   */

  setNotifications(notifications) {
    this.notifications = notifications;
    this.unreadCount = notifications.filter(n => !n.read).length;
    this.notify('notifications', notifications);
  }

  addNotification(notification) {
    this.notifications.unshift(notification);
    if (!notification.read) this.unreadCount++;
    this.notify('notifications', notification);
  }

  /**
   * UI STATE
   */

  setActiveView(view) {
    this.activeView = view;
    this.notify('view', view);
  }

  showModalDialog(modalName, data = null) {
    this.showModal = modalName;
    this.modalData = data;
    this.notify('view', { modal: modalName, data });
  }

  closeModalDialog() {
    this.showModal = null;
    this.modalData = null;
    this.notify('view', { modal: null });
  }

  /**
   * ERROR HANDLING
   */

  setError(message) {
    this.error = message;
    this.notify('all', { error: message });
    // Auto-clear error after 5 seconds
    setTimeout(() => {
      this.error = null;
    }, 5000);
  }

  clearError() {
    this.error = null;
  }

  /**
   * PERSISTENCE
   */

  loadPersistedState() {
    const savedUser = localStorage.getItem('currentUser');
    if (savedUser) {
      try {
        this.currentUser = JSON.parse(savedUser);
        this.isAuthenticated = true;
      } catch (e) {
        console.error('Failed to load persisted user:', e);
      }
    }

    const savedWalletId = localStorage.getItem('selectedWalletId');
    if (savedWalletId) {
      this.selectedWalletId = savedWalletId;
    }
  }

  /**
   * COMPUTED PROPERTIES
   */

  getTotalWalletBalance() {
    return this.wallets.reduce((sum, w) => sum + (w.balance || 0), 0);
  }

  getWalletBalanceInUSD(walletBalance) {
    // This would integrate with price oracle in production
    // For now, simple conversion
    return walletBalance * 1; // Placeholder
  }

  /**
   * SUMMARY FOR UI
   */

  getSummary() {
    return {
      user: this.currentUser,
      isAuthenticated: this.isAuthenticated,
      wallets: this.wallets.length,
      selectedWallet: this.getSelectedWallet(),
      nfts: this.userNFTs.length,
      activeListings: this.getActiveListingCount(),
      walletBalance: this.getTotalWalletBalance(),
      notifications: this.unreadCount,
      error: this.error,
    };
  }
}

// Create global instance
if (!window.appState) {
  window.appState = new AppState();
}
