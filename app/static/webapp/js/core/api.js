// Minimal Telegram-native API wrapper (stateless)
// Attaches raw Telegram.WebApp.initData to every request header.

// Ensure Telegram SDK is initialized (best-effort)
try {
  if (window.Telegram && window.Telegram.WebApp && typeof window.Telegram.WebApp.ready === 'function') {
    window.Telegram.WebApp.ready();
  }
} catch (e) {
  // ignore
}

const TG_INIT_DATA = (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initData) || '';

export async function apiFetch(url, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  if (TG_INIT_DATA) headers['X-Telegram-Init-Data'] = TG_INIT_DATA;

  const fullUrl = url.startsWith('http') ? url : `${window.location.origin}${url}`;

  return fetch(fullUrl, {
    ...options,
    headers,
  });
}

export function getInitDataForDebug() {
  return TG_INIT_DATA;
}
