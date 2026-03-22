import { apiFetch } from './api.js';

export async function getCurrentUser() {
  try {
    const resp = await apiFetch('/api/v1/me');
    if (!resp || resp.status === 401) return null;
    const ct = resp.headers.get('content-type') || '';
    if (ct.includes('application/json')) {
      const data = await resp.json();
      return data;
    }
    return null;
  } catch (e) {
    console.warn('[CoreAuth] getCurrentUser failed', e);
    return null;
  }
}
