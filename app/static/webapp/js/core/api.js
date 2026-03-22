// Central Telegram-native API wrapper
// Keeps initData in memory and attaches it to every request

// Wait for Telegram WebApp SDK to be ready
function ensureTelegramReady() {
  return new Promise((resolve) => {
    try {
      if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initData) {
        resolve(true);
      } else if (window.Telegram && window.Telegram.WebApp && typeof window.Telegram.WebApp.ready === 'function') {
        // Some environments expose ready()
        try {
          window.Telegram.WebApp.ready();
        } catch (e) {
          // ignore
        }
        // give it a tick
        setTimeout(() => resolve(true), 0);
      } else {
        // Poll for availability briefly
        const start = Date.now();
        const iv = setInterval(() => {
          if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initData) {
            clearInterval(iv);
            resolve(true);
          } else if (Date.now() - start > 5000) {
            clearInterval(iv);
            resolve(false);
          }
        }, 100);
      }
    } catch (e) {
      resolve(false);
    }
  });
}

let TG_INIT_DATA = null;

async function ensureInitData() {
  if (TG_INIT_DATA !== null) return TG_INIT_DATA;
  const ready = await ensureTelegramReady();
  if (!ready) {
    TG_INIT_DATA = '';
    return TG_INIT_DATA;
  }
  try {
    TG_INIT_DATA = window.Telegram.WebApp.initData || '';
  } catch (e) {
    TG_INIT_DATA = '';
  }
  return TG_INIT_DATA;
}

export async function apiFetch(url, options = {}) {
  await ensureInitData();

  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  if (TG_INIT_DATA) {
    headers['X-Telegram-Init-Data'] = TG_INIT_DATA;
  }

  const fullUrl = url.startsWith('http') ? url : `${window.location.origin}${url}`;

  return fetch(fullUrl, {
    ...options,
    headers,
    credentials: 'include',
  });
}

export function getInitDataForDebug() {
  return TG_INIT_DATA;
}
