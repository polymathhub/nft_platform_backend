// Page Initializer - Common functionality for all pages
// Handles navigation, theme, auth state propagation

class PageInitializer {
  constructor() {
    this.initTheme();
    this.initNavigation();
    this.initBackButton();
  }

  initTheme() {
    if (window.Telegram?.WebApp?.colorScheme === 'dark') {
      document.documentElement.setAttribute('data-theme', 'dark');
    }
  }

  initNavigation() {
    // Set active nav item based on current page
    const currentPage = window.location.pathname.split('/').pop() || 'dashboard';
    document.querySelectorAll('.nav-item').forEach(item => {
      item.classList.remove('active');
      if (item.dataset.page === currentPage) {
        item.classList.add('active');
      }
    });

    // Navigation links
    document.querySelectorAll('.nav-item a, .nav-item').forEach(link => {
      link.addEventListener('click', (e) => {
        const href = link.getAttribute('href') || `/webapp/${link.dataset.page}.html`;
        window.location.href = href;
      });
    });
  }

  initBackButton() {
    if (window.Telegram?.WebApp?.BackButton) {
      window.Telegram.WebApp.BackButton.onClick(() => {
        window.history.back();
      });
      window.Telegram.WebApp.BackButton.show();
    }
  }
}

// Global navigate function
window.navigate = (path) => {
  window.location.href = path.startsWith('http') ? path : `/webapp${path}`;
};

// Init on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => new PageInitializer());
} else {
  new PageInitializer();
}

export default PageInitializer;

