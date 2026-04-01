/**
 * Navbar Module - User Info and Dropdown Handlers
 * Accesses AuthSystem from window (injected by auth-system.js)
 */

/**
 * Initialize Navbar with User Info and Event Handlers
 */
async function initNavbar() {
  console.log('[Navbar] Initializing...');
  
  // Wait for AuthSystem to be available globally
  const waitStart = Date.now();
  while (!window.AuthSystem && Date.now() - waitStart < 5000) {
    await new Promise(r => setTimeout(r, 100));
  }
  
  if (!window.AuthSystem) {
    console.error('[Navbar] AuthSystem not available globally');
    return;
  }
  
  // Wait for AuthSystem to initialize (with timeout)
  const authWaitStart = Date.now();
  while (!window.AuthSystem.isInitialized && Date.now() - authWaitStart < 5000) {
    await new Promise(r => setTimeout(r, 100));
  }
  
  if (!window.AuthSystem.isInitialized) {
    console.warn('[Navbar] AuthSystem timeout - using cached user or guest mode');
  }
  
  // Get user (either from init or cache)
  const user = window.AuthSystem.getUser();
  console.log('[Navbar] User:', user ? `${user.username || user.first_name}` : 'null');
  
  // Update user display
  updateUserDisplay(user);
  
  // Setup event listeners
  setupEventListeners();
  
  // Listen for auth events
  window.addEventListener('auth:success', () => {
    const updatedUser = window.AuthSystem.getUser();
    updateUserDisplay(updatedUser);
  });
}

/**
 * Update user name and avatar display
 */
function updateUserDisplay(user) {
  try {
    // Update user name in navbar
    const userNameEl = document.getElementById('navbar-user');
    if (userNameEl) {
      if (user) {
        const userName = user.first_name || user.username || user.full_name || 'User';
        userNameEl.innerText = userName;
      } else {
        userNameEl.innerText = 'Guest';
      }
    }

    // ✅ Update avatars with Telegram profile picture support
    const avatarSelectors = [
      '#profileAvatar',
      '#profileAvatarLarge', 
      '#navbar-profile-avatar',
      '[id*="avatar"]'
    ];
    
    avatarSelectors.forEach(selector => {
      try {
        const avatarElements = document.querySelectorAll(selector);
        avatarElements.forEach(el => {
          if (!el) return;
          
          // Get user's initial for fallback
          const userName = user ? (user.first_name || user.username || user.full_name || 'U') : 'U';
          const initial = userName[0].toUpperCase();
          
          if (user && user.photo_url) {
            // ✅ Use Telegram photo_url as background image
            el.style.backgroundImage = `url('${user.photo_url}')`;
            el.style.backgroundSize = 'cover';
            el.style.backgroundPosition = 'center';
            el.style.backgroundRepeat = 'no-repeat';
            
            // Create image element for preloading and fallback
            const img = new Image();
            img.onload = () => {
              console.log('[Navbar] Photo loaded:', user.photo_url);
              el.classList.add('photo-loaded');
            };
            img.onerror = () => {
              console.warn('[Navbar] Photo failed to load:', user.photo_url);
              // Fallback to initial
              el.style.backgroundImage = '';
              el.textContent = initial;
            };
            img.src = user.photo_url;
            
            // Clear text to show background image
            el.textContent = '';
          } else if (user) {
            // Fallback to initial
            el.style.backgroundImage = '';
            el.textContent = initial;
          } else {
            // Guest
            el.style.backgroundImage = '';
            el.textContent = 'G';
          }
        });
      } catch (e) {
        console.warn(`[Navbar] Avatar selector error for "${selector}":`, e);
      }
    });

    // Update profile dropdown user info
    const profileName = document.getElementById('user-name');
    const profileEmail = document.getElementById('user-email');
    const userName = document.getElementById('userName');
    
    if (user) {
      const displayName = user.first_name || user.username || user.full_name || 'User';
      if (profileName) profileName.innerText = displayName;
      if (userName) userName.innerText = displayName;
      if (profileEmail) profileEmail.innerText = user.email || '@' + (user.username || 'user');
    } else {
      if (profileName) profileName.innerText = 'Guest';
      if (userName) userName.innerText = 'Guest';
      if (profileEmail) profileEmail.innerText = 'Not authenticated';
    }
  } catch (e) {
    console.warn('[Navbar] Failed to update user display:', e);
  }
}

/**
 * Setup all navbar event listeners
 */
function setupEventListeners() {
  console.log('[Navbar] Setting up event listeners');
  
  // Get elements
  const notificationBtn = document.getElementById('notificationBtn');
  const profileBtn = document.getElementById('profileBtn');
  const notificationDropdown = document.getElementById('notificationDropdown');
  const profileDropdown = document.getElementById('profileDropdown');
  const headerOverlay = document.getElementById('headerOverlay');
  const logoutBtn = document.getElementById('logoutBtn');
  const darkModeToggle = document.getElementById('darkModeToggle');
  const notificationClose = document.getElementById('notificationClose');

  // Close dropdowns when overlay clicked
  if (headerOverlay) {
    headerOverlay.addEventListener('click', () => {
      closeAllDropdowns();
    });
  }

  // Notification button
  if (notificationBtn) {
    notificationBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (notificationDropdown?.classList.contains('active')) {
        closeAllDropdowns();
      } else {
        closeAllDropdowns();
        if (notificationDropdown) {
          notificationDropdown.classList.add('active');
          showOverlay();
        }
      }
    });
  }

  // Profile button
  if (profileBtn) {
    profileBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (profileDropdown?.classList.contains('active')) {
        closeAllDropdowns();
      } else {
        closeAllDropdowns();
        if (profileDropdown) {
          profileDropdown.classList.add('active');
          showOverlay();
        }
      }
    });
  }

  // Notification close button
  if (notificationClose) {
    notificationClose.addEventListener('click', () => {
      closeAllDropdowns();
    });
  }

  // Logout handler
  if (logoutBtn) {
    logoutBtn.addEventListener('click', (e) => {
      e.preventDefault();
      handleLogout();
    });
  }

  // Dark mode toggle
  if (darkModeToggle) {
    darkModeToggle.addEventListener('click', (e) => {
      e.preventDefault();
      toggleDarkMode();
    });
  }

  // Close dropdowns when clicking outside
  document.addEventListener('click', (e) => {
    const isNotificationArea = notificationBtn?.contains(e.target) || 
                                notificationDropdown?.contains(e.target);
    const isProfileArea = profileBtn?.contains(e.target) || 
                           profileDropdown?.contains(e.target);
    
    if (!isNotificationArea && !isProfileArea) {
      closeAllDropdowns();
    }
  });

  // Close on escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeAllDropdowns();
    }
  });
}

/**
 * Close all dropdowns and hide overlay
 */
function closeAllDropdowns() {
  const notificationDropdown = document.getElementById('notificationDropdown');
  const profileDropdown = document.getElementById('profileDropdown');
  const headerOverlay = document.getElementById('headerOverlay');
  
  if (notificationDropdown) notificationDropdown.classList.remove('active');
  if (profileDropdown) profileDropdown.classList.remove('active');
  hideOverlay();
}

/**
 * Show overlay
 */
function showOverlay() {
  const headerOverlay = document.getElementById('headerOverlay');
  if (headerOverlay) {
    headerOverlay.classList.add('active');
  }
}

/**
 * Hide overlay
 */
function hideOverlay() {
  const headerOverlay = document.getElementById('headerOverlay');
  if (headerOverlay) {
    headerOverlay.classList.remove('active');
  }
}

/**
 * Toggle dark mode
 */
function toggleDarkMode() {
  const html = document.documentElement;
  const isDark = html.getAttribute('data-theme') === 'dark';
  
  if (isDark) {
    html.setAttribute('data-theme', 'light');
    localStorage.setItem('theme', 'light');
  } else {
    html.setAttribute('data-theme', 'dark');
    localStorage.setItem('theme', 'dark');
  }
  
  console.log('[Navbar] Dark mode toggled to:', !isDark);
}

/**
 * Handle logout
 */
async function handleLogout() {
  console.log('[Navbar] Logging out...');
  
  if (confirm('Are you sure you want to logout?')) {
    if (window.AuthSystem) {
      window.AuthSystem.logout();
    }
    updateUserDisplay(null);
    closeAllDropdowns();
    
    // Redirect after logout
    setTimeout(() => {
      window.location.href = '/';
    }, 500);
  }
}

// Initialize navbar when DOM is ready and AuthSystem is available
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initNavbar);
} else {
  initNavbar().catch(e => console.error('[Navbar] Init error:', e));
}

// Also make initNavbar globally accessible for manual calls
window.initNavbar = initNavbar;
