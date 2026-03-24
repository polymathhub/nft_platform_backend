// Global Auth Bootstrap for Telegram WebApp
(function () {
  const STORAGE_KEY = 'app_tg_user';
  const LOG = (...args) => console.debug('[auth-global]', ...args);

  async function setUser(user) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
    } catch (e) {
      console.warn('[auth-global] Failed to persist user to localStorage', e);
    }
    window.authManager = window.authManager || {};
    window.authManager.user = user;
    const ev = new CustomEvent('auth:initialized', { detail: { user } });
    window.dispatchEvent(ev);
    LOG('auth:initialized dispatched', user && user.username);
  }

  function getStoredUser() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return null;
      return JSON.parse(raw);
    } catch (e) {
      console.warn('[auth-global] Failed to parse stored user', e);
      return null;
    }
  }

  async function fetchProfileWithInitData(initData) {
    try {
      const res = await fetch('/api/v1/me', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-Telegram-Init-Data': initData,
        },
        credentials: 'include',
      });
      if (!res.ok) {
        LOG('Profile fetch failed', res.status);
        return null;
      }
      const body = await res.json();
      if (body && body.user) return body.user;
      return null;
    } catch (e) {
      console.warn('[auth-global] Failed to fetch profile', e);
      return null;
    }
  }

  async function bootstrap() {
    LOG('Starting bootstrap');

    // 1) Try localStorage
    const stored = getStoredUser();
    if (stored && stored.telegram_id) {
      LOG('Restored user from localStorage', stored.username || stored.first_name);
      await setUser(stored);
      // Still attempt a background refresh with Telegram initData if available
    }

    // 2) If Telegram WebApp is available, try to validate with backend
    const tg = (typeof window !== 'undefined' && window.Telegram && window.Telegram.WebApp) ? window.Telegram.WebApp : null;
    // Only use signed initData for backend validation. Do NOT send initDataUnsafe to backend.
    const initData = tg && tg.initData ? tg.initData : null;

    if (initData) {
      LOG('Telegram initData detected, validating with backend');
      const profile = await fetchProfileWithInitData(initData);
      if (profile) {
        LOG('Backend validated user', profile.username || profile.telegram_id);
        await setUser(profile);
        return;
      }
      LOG('Backend did not return profile for initData');
    }

    // 3) If no stored user, but Telegram SDK has unsafe user, use that as fallback
    if (!stored && tg && tg.initDataUnsafe && tg.initDataUnsafe.user) {
      const u = tg.initDataUnsafe.user;
      const user = {
        telegram_id: String(u.id),
        username: u.username || `${u.first_name || 'user'}_${u.id}`,
        first_name: u.first_name || '',
        last_name: u.last_name || '',
        photo_url: u.photo_url || null,
      };
      LOG('Using Telegram SDK user as fallback', user.username);
      await setUser(user);
      return;
    }

    // 4) No auth available - dispatch event with null
    window.authManager = window.authManager || {};
    window.authManager.user = null;
    window.dispatchEvent(new CustomEvent('auth:initialized', { detail: { user: null } }));
    LOG('No user available - guest mode');
  }

  // Expose a small API
  window.AuthGlobal = {
    bootstrap,
    getUser: () => (window.authManager && window.authManager.user) || getStoredUser(),
    clear: function () {
      try { localStorage.removeItem(STORAGE_KEY); } catch (e) {}
      if (window.authManager) window.authManager.user = null;
      window.dispatchEvent(new CustomEvent('auth:initialized', { detail: { user: null } }));
    }
  };

  // Run bootstrap as soon as possible
  try {
    bootstrap();
  } catch (e) {
    console.error('[auth-global] Bootstrap error', e);
  }

})();
