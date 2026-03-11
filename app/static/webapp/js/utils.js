/**
 * Utility Functions
 * Common helpers, validators, formatters
 * @module js/utils
 */

/**
 * Debounce function calls
 */
export function debounce(func, delay = 300) {
  let timeoutId;
  return function (...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func.apply(this, args), delay);
  };
}

/**
 * Throttle function calls
 */
export function throttle(func, limit = 300) {
  let inThrottle;
  return function (...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

/**
 * Format currency
 */
export function formatCurrency(amount, currency = 'USD', locale = 'en-US') {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
  }).format(amount);
}

/**
 * Format number with thousand separators
 */
export function formatNumber(num, decimals = 2) {
  return parseFloat(num).toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

/**
 * Format date
 */
export function formatDate(date, format = 'short') {
  const d = new Date(date);
  if (isNaN(d.getTime())) return 'Invalid date';

  const options = {
    short: { year: 'numeric', month: 'short', day: 'numeric' },
    long: { year: 'numeric', month: 'long', day: 'numeric' },
    time: { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' },
    iso: {},
  };

  if (format === 'iso') {
    return d.toISOString();
  }

  return d.toLocaleDateString('en-US', options[format] || options.short);
}

/**
 * Format time relative to now (e.g., "2 hours ago")
 */
export function formatTimeAgo(date) {
  const now = new Date();
  const d = new Date(date);
  const seconds = Math.floor((now - d) / 1000);

  const intervals = {
    year: 31536000,
    month: 2592000,
    week: 604800,
    day: 86400,
    hour: 3600,
    minute: 60,
  };

  for (const [name, value] of Object.entries(intervals)) {
    const interval = Math.floor(seconds / value);
    if (interval >= 1) {
      return `${interval} ${name}${interval > 1 ? 's' : ''} ago`;
    }
  }

  return 'just now';
}

/**
 * Truncate string
 */
export function truncate(str, length = 50, suffix = '...') {
  if (!str || str.length <= length) return str;
  return str.substring(0, length - suffix.length) + suffix;
}

/**
 * Abbreviate wallet address
 */
export function abbreviateAddress(address, chars = 4) {
  if (!address) return '';
  if (address.length <= chars * 2) return address;
  return `${address.substring(0, chars)}...${address.substring(address.length - chars)}`;
}

/**
 * Copy to clipboard
 */
export async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (error) {
    console.error('Failed to copy:', error);
    return false;
  }
}

/**
 * Validate email
 */
export function isValidEmail(email) {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex .test(email);
}

/**
 * Validate URL
 */
export function isValidURL(url) {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

/**
 * Validate Ethereum address
 */
export function isValidEthereumAddress(address) {
  const regex = /^0x[a-fA-F0-9]{40}$/;
  return regex.test(address);
}

/**
 * Validate Solana address
 */
export function isValidSolanaAddress(address) {
  try {
    // Solana addresses are base58 encoded, 32 bytes = 44 characters in base58
    if (address.length < 32 || address.length > 44) return false;
    // Check if valid base58
    const base58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';
    return [...address].every(char => base58.includes(char));
  } catch {
    return false;
  }
}

/**
 * Safe JSON parse
 */
export function safeJSONParse(json, fallback = null) {
  try {
    return JSON.parse(json);
  } catch {
    return fallback;
  }
}

/**
 * Escape HTML characters to prevent XSS
 */
export function escapeHTML(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

/**
 * Generate unique ID
 */
export function generateId(prefix = '') {
  return `${prefix}${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Deep clone object
 */
export function deepClone(obj) {
  if (obj === null || typeof obj !== 'object') return obj;
  if (obj instanceof Date) return new Date(obj.getTime());
  if (obj instanceof Array) return obj.map(item => deepClone(item));
    if (obj instanceof Object) {
    const cloned = {};
    for (const key in obj) {
      if (Object.prototype.hasOwnProperty.call(obj, key)) {
        cloned[key] = deepClone(obj[key]);
      }
    }
    return cloned;
  }
}

/**
 * Merge objects
 */
export function mergeObjects(target, source) {
  const result = { ...target };
  for (const key in source) {
    if (Object.prototype.hasOwnProperty.call(source, key)) {
      if (typeof source[key] === 'object' && source[key] !== null) {
        result[key] = mergeObjects(result[key] || {}, source[key]);
      } else {
        result[key] = source[key];
      }
    }
  }
  return result;
}

/**
 * Wait/sleep
 */
export function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Retry function with exponential backoff
 */
export async function retry(fn, maxRetries = 3, delay = 1000) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await sleep(delay * Math.pow(2, i));
    }
  }
}

/**
 * Get query parameter
 */
export function getQueryParam(name) {
  const params = new URLSearchParams(window.location.search);
  return params.get(name);
}

/**
 * Update query parameter
 */
export function updateQueryParam(key, value) {
  const url = new URL(window.location);
  if (value === null) {
    url.searchParams.delete(key);
  } else {
    url.searchParams.set(key, value);
  }
  window.history.replaceState({}, '', url);
}

/**
 * Check device type
 */
export function getDeviceType() {
  const userAgent = navigator.userAgent.toLowerCase();
  if (/mobile|android|webos|iphone|ipad|ipod/.test(userAgent)) {
    return 'mobile';
  }
  if (/tablet|ipad/.test(userAgent)) {
    return 'tablet';
  }
  return 'desktop';
}

/**
 * Check if online
 */
export function isOnline() {
  return navigator.onLine;
}

/**
 * Request animation frame wrapper
 */
export function requestAnimFrame(callback) {
  return (
    window.requestAnimationFrame ||
    window.webkitRequestAnimationFrame ||
    window.mozRequestAnimationFrame ||
    function(callback) {
      window.setTimeout(callback, 1000 / 60);
    }
  )(callback);
}

/**
 * Intersection Observer helper
 */
export function observeElements(selector, callback, options = {}) {
  const elements = document.querySelectorAll(selector);
  if (elements.length === 0) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => callback(entry));
  }, options);

  elements.forEach(el => observer.observe(el));

  return observer;
}

/**
 * Mutation Observer helper
 */
export function observeMutations(selector, callback, options = { childList: true, subtree: true }) {
  const element = document.querySelector(selector);
  if (!element) return;

  const observer = new MutationObserver(callback);
  observer.observe(element, options);

  return observer;
}
