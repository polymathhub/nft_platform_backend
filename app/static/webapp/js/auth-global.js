// Deprecated - replaced by telegram-auth.js
// This file is kept for compatibility and forwards to the new client.
(function () {
  console.warn('[auth-global] Deprecated - use telegram-auth.js');

  window.AuthGlobal = window.AuthGlobal || {};
  window.AuthGlobal.bootstrap = async function () {
    if (window.TelegramAuth && window.TelegramAuth.fetchProfile) {
      await window.TelegramAuth.fetchProfile();
    }
    return null;
  };
  window.AuthGlobal.getUser = function () {
    return null;
  };
  window.AuthGlobal.clear = function () {
    try { localStorage.removeItem('__auth_user_cache'); } catch (e) {}
  };
})();
