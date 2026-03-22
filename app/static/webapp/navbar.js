import { getCurrentUser } from './js/core/auth.js';

async function initNavbar() {
  const el = document.getElementById('navbar-user');
  if (!el) return;

  el.innerText = 'Loading...';

  try {
    const user = await getCurrentUser();
    if (!user) {
      el.innerText = 'Guest';
      return;
    }

    el.innerText = user.first_name || user.username || user.full_name || 'User';
  } catch (e) {
    console.warn('[Navbar] getCurrentUser failed', e);
    el.innerText = 'Guest';
  }
}

initNavbar();
