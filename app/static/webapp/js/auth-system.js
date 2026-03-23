
// Deprecated: lightweight compatibility layer that delegates to telegram-auth.js
(function () {
  console.warn('[auth-system] Deprecated - using telegram-auth.js');

  window.AuthSystem = window.AuthSystem || {};

  window.AuthSystem.initialize = async function () {
    if (window.TelegramAuth && window.TelegramAuth.fetchProfile) {
      return window.TelegramAuth.fetchProfile();
    }
    return null;
  };

  window.AuthSystem.renderNavbar = function () {
    if (window.TelegramAuth && window.TelegramAuth.renderNavbar) {
      try { window.TelegramAuth.renderNavbar(); } catch (e) {}
    }
  };

})();
