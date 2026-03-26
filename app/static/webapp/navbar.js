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

    // Display profile picture
    if (profileAvatarEl) {
      if (user.avatar_url) {
        // Load actual profile picture
        const img = document.createElement('img');
        img.src = user.avatar_url;
        img.alt = 'Profile';
        img.style.cssText = 'width: 100%; height: 100%; object-fit: cover; border-radius: 50%;';
        
        img.onload = () => {
          profileAvatarEl.innerHTML = '';
          profileAvatarEl.appendChild(img);
        };
        
        img.onerror = () => {
          // Fallback to initial
          const initial = userName[0].toUpperCase();
          profileAvatarEl.innerHTML = initial;
        };
      } else {
        // Show user initial as fallback
        const initial = userName[0].toUpperCase();
        profileAvatarEl.innerHTML = initial;
      }
    }
  } catch (e) {
    console.warn('[Navbar] getCurrentUser failed', e);
    if (userNameEl) userNameEl.innerText = 'Guest';
  }
}

initNavbar();
