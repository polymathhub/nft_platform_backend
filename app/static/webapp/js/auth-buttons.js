/**
 * Auth Button Components Module
 * Standardized, error-free button implementations for TON Wallet and Telegram
 * Handles loading states, error scenarios, and accessibility
 */

import { authManager } from './unified-auth.js';
import { Toast } from './components.js';

/**
 * Create a TON Connect button with proper error handling
 */
export function createTonConnectButton(options = {}) {
  const button = document.createElement('button');
  button.className = 'btn-ton-connect';
  button.id = options.id || 'ton-connect-btn';
  button.setAttribute('aria-label', 'Connect TON Wallet');
  button.type = 'button';
  button.disabled = false;

  // HTML structure
  button.innerHTML = `
    <span class="btn-icon">
      <svg width="20" height="20" viewBox="0 0 32 32" fill="currentColor">
        <path d="M8 4h16a4 4 0 014 4v16a4 4 0 01-4 4H8a4 4 0 01-4-4V8a4 4 0 014-4z"/>
      </svg>
    </span>
    <span class="btn-text">Connect TON Wallet</span>
    <span class="btn-loader" style="display: none;">
      <svg class="spinner" width="16" height="16" viewBox="0 0 50 50">
        <circle cx="25" cy="25" r="20" fill="none" stroke-width="4" stroke="currentColor" stroke-dasharray="31.4 94.2"/>
      </svg>
    </span>
  `;

  // Event handler
  button.addEventListener('click', async (e) => {
    e.preventDefault();
    await handleTonConnectClick(button);
  });

  // Cleanup on auth events
  window.addEventListener('auth:login_ton', () => {
    setButtonLoading(button, false);
    button.disabled = true;
  });

  return button;
}

/**
 * Handle TON Connect button click with error management
 */
async function handleTonConnectClick(button) {
  try {
    // Update button state
    setButtonLoading(button, true);

    // Check if TonConnect is initialized
    if (!authManager.tonConnectUI) {
      throw new Error('TonConnect UI not initialized. Please reload the page.');
    }

    // Open TonConnect modal
    await authManager.tonConnectUI.openModal();

    // Wait for wallet connection
    const wallet = authManager.tonConnectUI.wallet;
    
    if (wallet && wallet.account?.address) {
      // Trigger login event
      window.dispatchEvent(new CustomEvent('auth:login_ton', {
        detail: { wallet }
      }));
    } else {
      throw new Error('No wallet address received');
    }
  } catch (error) {
    console.error('TON Connect error:', error);
    
    // User cancelled the modal (expected behavior)
    if (error.message?.includes('cancelled') || error.message?.includes('closed')) {
      console.log('User cancelled TON Connect modal');
    } else {
      Toast.error(`Connection failed: ${error.message}`);
    }
  } finally {
    setButtonLoading(button, false);
  }
}

/**
 * Create a Telegram login button
 */
export function createTelegramLoginButton(options = {}) {
  const button = document.createElement('button');
  button.className = 'btn-telegram-login';
  button.id = options.id || 'telegram-login-btn';
  button.setAttribute('aria-label', 'Login with Telegram');
  button.type = 'button';
  button.disabled = false;

  // HTML structure
  button.innerHTML = `
    <span class="btn-icon">
      <svg width="20" height="20" viewBox="0 0 32 32" fill="currentColor">
        <path d="M16 2C8.268 2 2 8.268 2 16s6.268 14 14 14 14-6.268 14-14-6.268-14-14-14zm0 2c6.627 0 12 5.373 12 12s-5.373 12-12 12-12-5.373-12-12 5.373-12 12-12z"/>
        <path d="M13 21l-3-5h-1l5-8v5l3 5h1l-5 8z"/>
      </svg>
    </span>
    <span class="btn-text">Login with Telegram</span>
    <span class="btn-loader" style="display: none;">
      <svg class="spinner" width="16" height="16" viewBox="0 0 50 50">
        <circle cx="25" cy="25" r="20" fill="none" stroke-width="4" stroke="currentColor" stroke-dasharray="31.4 94.2"/>
      </svg>
    </span>
  `;

  // Event handler
  button.addEventListener('click', async (e) => {
    e.preventDefault();
    await handleTelegramLoginClick(button);
  });

  // Cleanup on auth events
  window.addEventListener('auth:login_telegram', () => {
    setButtonLoading(button, false);
    button.disabled = true;
  });

  return button;
}

/**
 * Handle Telegram login button click
 */
async function handleTelegramLoginClick(button) {
  try {
    setButtonLoading(button, true);

    // Get Telegram data
    const tgData = authManager.getTelegramData();

    if (!tgData || !tgData.initData) {
      throw new Error('Telegram WebApp not available. Please run this app inside Telegram.');
    }

    if (!tgData.user) {
      throw new Error('Unable to get Telegram user data');
    }

    // Trigger login event
    window.dispatchEvent(new CustomEvent('auth:login_telegram', {
      detail: { telegramData: tgData }
    }));

  } catch (error) {
    console.error('Telegram login error:', error);
    Toast.error(`Login failed: ${error.message}`);
  } finally {
    setButtonLoading(button, false);
  }
}

/**
 * Set button loading state
 * @private
 */
function setButtonLoading(button, isLoading) {
  const loaderEl = button.querySelector('.btn-loader');
  const textEl = button.querySelector('.btn-text');

  if (isLoading) {
    button.disabled = true;
    button.classList.add('loading');
    if (loaderEl) loaderEl.style.display = 'inline-flex';
    if (textEl) textEl.style.opacity = '0.5';
  } else {
    button.disabled = false;
    button.classList.remove('loading');
    if (loaderEl) loaderEl.style.display = 'none';
    if (textEl) textEl.style.opacity = '1';
  }
}

/**
 * Create authentication method selector UI
 */
export function createAuthMethodSelector() {
  const container = document.createElement('div');
  container.className = 'auth-methods-container';
  container.innerHTML = `
    <div class="auth-methods">
      <h2 class="auth-title">Choose Login Method</h2>
      
      <div class="auth-buttons">
        <!-- TON Connect -->
        <div id="ton-wallet-container" class="auth-button-wrapper"></div>
        
        <!-- Telegram -->
        <div id="telegram-login-container" class="auth-button-wrapper"></div>
      </div>

      <div class="auth-divider">
        <span>or</span>
      </div>

      <!-- Email/Password fallback -->
      <button class="btn btn-secondary" id="email-login-btn">
        Login with Email
      </button>
    </div>
  `;

  // Mount buttons into containers
  const tonContainer = container.querySelector('#ton-wallet-container');
  const tgContainer = container.querySelector('#telegram-login-container');

  if (tonContainer) {
    tonContainer.appendChild(createTonConnectButton());
  }

  if (tgContainer) {
    tgContainer.appendChild(createTelegramLoginButton());
  }

  // Email login fallback
  const emailBtn = container.querySelector('#email-login-btn');
  if (emailBtn) {
    emailBtn.addEventListener('click', () => {
      window.location.href = '/login';
    });
  }

  return container;
}

/**
 * Export CSS styles for buttons
 */
export const AUTH_BUTTON_STYLES = `
  /* TON Connect Button */
  .btn-ton-connect,
  .btn-telegram-login {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    width: 100%;
    padding: 14px 20px;
    border: none;
    border-radius: 12px;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    transition: all 200ms cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
  }

  .btn-ton-connect {
    background: linear-gradient(135deg, #0c9bed 0%, #0098d4 100%);
    color: white;
    box-shadow: 0 4px 12px rgba(12, 155, 237, 0.3);
  }

  .btn-ton-connect:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(12, 155, 237, 0.4);
  }

  .btn-telegram-login {
    background: linear-gradient(135deg, #0088cc 0%, #0077b5 100%);
    color: white;
    box-shadow: 0 4px 12px rgba(0, 136, 204, 0.3);
  }

  .btn-telegram-login:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(0, 136, 204, 0.4);
  }

  .btn-ton-connect:disabled,
  .btn-telegram-login:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .btn-ton-connect.loading,
  .btn-telegram-login.loading {
    pointer-events: none;
  }

  .btn-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .btn-text {
    flex: 1;
    text-align: center;
  }

  .btn-loader {
    display: none;
    align-items: center;
    justify-content: center;
  }

  .btn-loader .spinner {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }

  /* Auth Methods Container */
  .auth-methods-container {
    width: 100%;
    max-width: 400px;
    margin: 0 auto;
    padding: 24px;
  }

  .auth-methods {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  .auth-title {
    text-align: center;
    font-size: 20px;
    font-weight: 700;
    margin: 0;
  }

  .auth-buttons {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .auth-button-wrapper {
    width: 100%;
  }

  .auth-divider {
    text-align: center;
    position: relative;
    margin: 12px 0;
  }

  .auth-divider::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 0;
    right: 0;
    height: 1px;
    background: #e5e7eb;
  }

  .auth-divider span {
    position: relative;
    background: white;
    padding: 0 8px;
    font-size: 12px;
    color: #6b7280;
    font-weight: 500;
  }
`;
