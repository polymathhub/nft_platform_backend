'use strict';

/**
 * GiftedForge - Modal & Form Manager
 * Lightweight, production-ready UI interactions
 */

class ModalManager {
  constructor() {
    this.overlay = document.getElementById('modalOverlay');
    this.closeBtn = document.getElementById('modalClose');
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.init());
    } else {
      this.init();
    }
  }

  init() {
    this.setupEventListeners();
    this.setupTelegramApp();
    this.setupNavigation();
    this.setupButtons();
    this.updateDashboard();
  }

  setupEventListeners() {
    if (this.closeBtn) {
      this.closeBtn.addEventListener('click', () => this.close());
    }

    if (this.overlay) {
      this.overlay.addEventListener('click', (e) => {
        if (e.target === this.overlay) this.close();
      });
    }

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.overlay?.classList.contains('active')) {
        this.close();
      }
    });
  }

  setupTelegramApp() {
    // Initialize Telegram Web App if available
    if (typeof Telegram !== 'undefined' && Telegram.WebApp) {
      Telegram.WebApp.ready();
      Telegram.WebApp.setHeaderColor('#ffffff');
      Telegram.WebApp.setBackgroundColor('#ffffff');
    }
  }

  open(title = 'Modal', content = '') {
    if (!this.overlay) return;

    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');

    if (modalTitle) modalTitle.textContent = title;
    if (modalBody) modalBody.innerHTML = content;

    this.overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  close() {
    if (!this.overlay) return;

    this.overlay.classList.remove('active');
    document.body.style.overflow = '';
  }

  setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');

    navItems.forEach(item => {
      item.addEventListener('click', () => {
        navItems.forEach(nav => nav.classList.remove('active'));
        item.classList.add('active');

        const page = item.dataset.page;
        if (page) this.handlePageSwitch(page);
      });
    });
  }

  setupButtons() {
    // Deposit button
    const depositBtn = document.getElementById('depositBtn');
    if (depositBtn) {
      depositBtn.addEventListener('click', () => {
        this.open('Deposit Funds', '<div class="form-group"><p>Deposit functionality coming soon</p></div>');
      });
    }

    // Create Wallet
    const createWalletBtn = document.getElementById('createWalletBtn');
    if (createWalletBtn) {
      createWalletBtn.addEventListener('click', () => {
        this.open('Create Wallet', '<div class="form-group"><p>Create Wallet functionality coming soon</p></div>');
      });
    }

    // Mint NFT
    const mintNftBtn = document.getElementById('mintNftBtn');
    if (mintNftBtn) {
      mintNftBtn.addEventListener('click', () => {
        this.open('Mint NFT', '<div class="form-group"><p>Mint NFT functionality coming soon</p></div>');
      });
    }

    // Browse button
    const browseBtn = document.getElementById('browseBtn');
    if (browseBtn) {
      browseBtn.addEventListener('click', () => {
        this.handlePageSwitch('market');
      });
    }

    // Profile button
    const profileBtn = document.getElementById('profileBtn');
    if (profileBtn) {
      profileBtn.addEventListener('click', () => {
        this.open('Profile', '<div class="form-group"><p>Profile settings coming soon</p></div>');
      });
    }

    // Notification button
    const notificationBtn = document.getElementById('notificationBtn');
    if (notificationBtn) {
      notificationBtn.addEventListener('click', () => {
        this.open('Notifications', '<div class="form-group"><p>No new notifications</p></div>');
      });
    }

    // Collection buttons
    const collectionButtons = document.querySelectorAll('.collection-button');
    collectionButtons.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const cardName = btn.closest('.collection-card')?.querySelector('.collection-name')?.textContent || 'Item';
        this.open('View NFT', `<div class="form-group"><p>Viewing: ${cardName}</p></div>`);
      });
    });

    // Activity items
    const activityItems = document.querySelectorAll('.activity-item');
    activityItems.forEach(item => {
      item.addEventListener('click', () => {
        const title = item.querySelector('.activity-title')?.textContent || 'Transaction';
        this.open('Transaction Details', `<div class="form-group"><p>${title}</p></div>`);
      });
    });
  }

  handlePageSwitch(page) {
    const pageNames = {
      dashboard: 'Dashboard',
      wallet: 'My Wallets',
      mint: 'Mint NFT',
      market: 'Marketplace',
      profile: 'Profile'
    };

    this.open(pageNames[page] || 'Page', `<div class="form-group"><p>${pageNames[page] || 'Page'} content coming soon</p></div>`);
  }

  updateDashboard() {
    // Update user info from Telegram if available
    if (typeof Telegram !== 'undefined' && Telegram.WebApp?.initDataUnsafe?.user) {
      const user = Telegram.WebApp.initDataUnsafe.user;
      const userName = document.getElementById('userName');
      const avatarInitial = document.getElementById('avatarInitial');

      if (userName && user.first_name) {
        userName.textContent = user.first_name;
      }

      if (avatarInitial && user.first_name) {
        avatarInitial.textContent = user.first_name.charAt(0).toUpperCase();
      }
    }
  }
}

// Initialize when DOM is ready
if (!window.modalManager) {
  window.modalManager = new ModalManager();
}
