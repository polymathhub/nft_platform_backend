import { getCurrentUser } from './js/core/auth.js';

async function initNavbar() {
  const userNameEl = document.getElementById('navbar-user');
  const profileAvatarEl = document.getElementById('navbar-profile-avatar');
  
  if (userNameEl) userNameEl.innerText = 'Loading...';

  try {
    const user = await getCurrentUser();
    if (!user) {
      if (userNameEl) userNameEl.innerText = 'Guest';
      return;
    }

    // Display user name
    const userName = user.first_name || user.username || user.full_name || 'User';
    if (userNameEl) userNameEl.innerText = userName;

    // Display profile picture on all avatar elements
    const avatarElements = document.querySelectorAll('#profileAvatar, #profileAvatarLarge, #navbar-profile-avatar');
    
    if (user.photo_url) {
      // Use Telegram photo_url for all avatars
      avatarElements.forEach(el => {
        el.style.backgroundImage = `url('${user.photo_url}')`;
        el.style.backgroundSize = 'cover';
        el.style.backgroundPosition = 'center';
        el.textContent = '';
      });
    } else {
      // Fallback to user initial
      const initial = userName[0].toUpperCase();
      avatarElements.forEach(el => {
        el.textContent = initial;
        el.style.backgroundImage = '';
      });
    }
  } catch (e) {
    console.warn('[Navbar] getCurrentUser failed', e);
    if (userNameEl) userNameEl.innerText = 'Guest';
  }
}

initNavbar();
