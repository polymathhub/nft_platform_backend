// Minimal Telegram WebApp auth client (stateless)
(function () {
  function getInitData() {
    try {
      return (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initData) || null;
    } catch (e) {
      return null;
    }
  }

  async function apiFetch(url, options = {}) {
    const headers = Object.assign({}, options.headers || {});
    const initData = getInitData();
    if (initData) headers['X-Telegram-Init-Data'] = initData;
    if (!headers['Content-Type'] && !(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
    }

    const fetchOptions = Object.assign({}, options, { headers, credentials: options.credentials || 'same-origin' });
    return fetch(url, fetchOptions);
  }

  async function fetchProfile() {
    try {
      const res = await apiFetch('/api/v1/me', { method: 'GET' });
      if (!res.ok) return null;
      return await res.json();
    } catch (e) {
      return null;
    }
  }

  // Simple navbar helper that fills elements with data-user-name and data-user-avatar
  async function renderNavbar() {
    const profile = await fetchProfile();
    const nameEls = document.querySelectorAll('[data-user-name]');
    const avatarEls = document.querySelectorAll('[data-user-avatar]');
    if (!profile || !profile.id) {
      nameEls.forEach(el => el.textContent = 'Open in Telegram');
      avatarEls.forEach(el => el.style.display = 'none');
      return;
    }
    const display = profile.full_name || profile.username || 'User';
    nameEls.forEach(el => el.textContent = display);
    if (profile.photo_url) {
      avatarEls.forEach(el => {
        if (el.tagName === 'IMG') el.src = profile.photo_url; else el.style.backgroundImage = `url(${profile.photo_url})`;
        el.style.display = '';
      });
    }
  }

  window.TelegramAuth = {
    getInitData,
    apiFetch,
    fetchProfile,
    renderNavbar,
  };

  // Install global apiFetch if not present
  if (!window.apiFetch) window.apiFetch = async (url, options = {}) => {
    const res = await apiFetch(url, options);
    if (!res.ok) throw new Error(`apiFetch error: ${res.status}`);
    return res.json();
  };

})();
