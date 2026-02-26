/**
 * UI Component Utilities
 * Reusable UI patterns and state management bindings
 */

class UIUtils {
  /**
   * Show loading skeleton for content
   */
  static showLoadingSkeleton(container, count = 3) {
    if (!container) return;
    container.innerHTML = Array(count)
      .fill(0)
      .map(
        () => `
      <div class="skeleton-item">
        <div class="skeleton skeleton-text"></div>
        <div class="skeleton skeleton-text short"></div>
      </div>
    `
      )
      .join('');
  }

  /**
   * Show empty state message
   */
  static showEmptyState(container, title, description = '') {
    if (!container) return;
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">📭</div>
        <h3 class="empty-state-title">${title}</h3>
        ${description ? `<p class="empty-state-description">${description}</p>` : ''}
      </div>
    `;
  }

  /**
   * Show error message
   */
  static showError(container, title, description = '') {
    if (!container) return;
    container.innerHTML = `
      <div class="error-state">
        <div class="error-state-icon">⚠️</div>
        <h3 class="error-state-title">${title}</h3>
        ${description ? `<p class="error-state-description">${description}</p>` : ''}
        <button class="error-state-retry">Retry</button>
      </div>
    `;
  }

  /**
   * Show toast notification
   */
  static showToast(message, type = 'info', duration = 3000) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
      position: fixed;
      bottom: 100px;
      left: 50%;
      transform: translateX(-50%);
      background: ${
        type === 'success'
          ? '#10b981'
          : type === 'error'
            ? '#ef4444'
            : '#f59e0b'
      };
      color: white;
      padding: 12px 20px;
      border-radius: 8px;
      font-size: 14px;
      z-index: 10000;
      animation: slideUp 0.3s ease-out;
    `;

    document.body.appendChild(toast);
    setTimeout(() => {
      toast.style.animation = 'slideDown 0.3s ease-in';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  }

  /**
   * Show error modal
   */
  static showErrorModal(title, message, onRetry = null) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
      <div class="modal-content error-modal">
        <h2>${title}</h2>
        <p>${message}</p>
        <div class="modal-actions">
          <button class="btn-primary modal-close">Dismiss</button>
          ${onRetry ? '<button class="btn-secondary modal-retry">Retry</button>' : ''}
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    modal.querySelector('.modal-close').onclick = () => modal.remove();
    if (onRetry) {
      modal.querySelector('.modal-retry').onclick = () => {
        modal.remove();
        onRetry();
      };
    }
  }

  /**
   * Format currency
   */
  static formatCurrency(amount, currency = 'USD') {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency === 'USD' ? 'USD' : 'USD',
    }).format(amount);
  }

  /**
   * Format address (truncate with ellipsis)
   */
  static formatAddress(address, chars = 6) {
    if (!address) return '';
    return `${address.substring(0, chars)}...${address.substring(address.length - chars)}`;
  }

  /**
   * Format date
   */
  static formatDate(date, format = 'short') {
    const d = new Date(date);
    if (format === 'short') {
      return d.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      });
    }
    return d.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  }

  /**
   * Bind element for data refresh
   */
  static bindDataRefresh(element, refreshFunction, interval = 30000) {
    const refresh = async () => {
      try {
        await refreshFunction();
      } catch (error) {
        console.error('Refresh failed:', error);
      }
    };

    // Initial load
    refresh();

    // Set interval for periodic refresh
    if (interval > 0) {
      return setInterval(refresh, interval);
    }
  }

  /**
   * Create loading indicator
   */
  static createLoadingIndicator() {
    return `
      <div class="loading-indicator">
        <div class="spinner"></div>
        <p>Loading...</p>
      </div>
    `;
  }

  /**
   * Disable button during loading
   */
  static setButtonLoading(button, isLoading = true) {
    if (!button) return;
    if (isLoading) {
      button.disabled = true;
      button.dataset.originalText = button.textContent;
      button.innerHTML = `<span class="spinner"></span> Loading...`;
    } else {
      button.disabled = false;
      button.textContent = button.dataset.originalText || 'Submit';
    }
  }

  /**
   * Validate email
   */
  static isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }

  /**
   * Validate blockchain address
   */
  static isValidBlockchainAddress(address, blockchain = 'ETH') {
    if (blockchain === 'ETH') {
      return /^0x[a-fA-F0-9]{40}$/.test(address);
    }
    return address.length > 20; // Simplified check
  }
}

/**
 * State-Aware Component Binder
 * Automatically synchronizes UI elements with app state
 */
class StateBinder {
  static bindView(viewElement, stateKey) {
    appState.subscribe(stateKey, (data) => {
      if (viewElement) {
        viewElement.style.display = data ? 'block' : 'none';
      }
    });
  }

  static bindText(element, stateKey, accessor = null) {
    const update = (data) => {
      if (!element) return;
      const value = accessor ? accessor(data) : data;
      if (value !== null && value !== undefined) {
        element.textContent = value;
      }
    };

    appState.subscribe(stateKey, update);
    // Initial update
    if (stateKey === 'user') {
      update(appState.currentUser);
    }
  }

  static bindHTML(element, stateKey, accessor = null) {
    const update = (data) => {
      if (!element) return;
      const value = accessor ? accessor(data) : data;
      if (value !== null && value !== undefined) {
        element.innerHTML = value;
      }
    };

    appState.subscribe(stateKey, update);
  }

  static bindClass(element, stateKey, className, condition = null) {
    const update = (data) => {
      if (!element) return;
      const shouldAdd = condition ? condition(data) : !!data;
      if (shouldAdd) {
        element.classList.add(className);
      } else {
        element.classList.remove(className);
      }
    };

    appState.subscribe(stateKey, update);
  }

  static bindAttribute(element, stateKey, attributeName, accessor = null) {
    const update = (data) => {
      if (!element) return;
      const value = accessor ? accessor(data) : data;
      if (value !== null && value !== undefined) {
        element.setAttribute(attributeName, value);
      }
    };

    appState.subscribe(stateKey, update);
  }
}

/**
 * Add CSS animations
 */
const styleSheet = document.createElement('style');
styleSheet.textContent = `
  @keyframes slideUp {
    from {
      transform: translateX(-50%) translateY(100%);
      opacity: 0;
    }
    to {
      transform: translateX(-50%) translateY(0);
      opacity: 1;
    }
  }

  @keyframes slideDown {
    from {
      transform: translateX(-50%) translateY(0);
      opacity: 1;
    }
    to {
      transform: translateX(-50%) translateY(100%);
      opacity: 0;
    }
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }

  .spinner {
    display: inline-block;
    width: 16px;
    height: 16px;
    border: 2px solid rgba(255,255,255,0.3);
    border-top-color: white;
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
    margin-right: 8px;
    vertical-align: middle;
  }

  .loading-indicator {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 20px;
    gap: 16px;
    color: rgba(255,255,255,0.7);
  }

  .skeleton-item {
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 12px;
  }

  .skeleton {
    background: linear-gradient(90deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.2) 50%, rgba(255,255,255,0.1) 100%);
    background-size: 200% 100%;
    animation: loading 1.5s infinite;
    border-radius: 4px;
  }

  .skeleton-text {
    height: 12px;
    margin-bottom: 8px;
  }

  .skeleton-text.short {
    width: 60%;
  }

  @keyframes loading {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 20px;
    text-align: center;
    min-height: 200px;
    color: rgba(255,255,255,0.6);
  }

  .empty-state-icon {
    font-size: 48px;
    margin-bottom: 16px;
  }

  .empty-state-title {
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 8px;
    color: rgba(255,255,255,0.9);
  }

  .empty-state-description {
    font-size: 14px;
    margin: 0;
  }

  .error-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 30px 20px;
    border-radius: 12px;
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
  }

  .error-state-icon {
    font-size: 48px;
    margin-bottom: 12px;
  }

  .error-state-title {
    color: #ef4444;
    margin-bottom: 8px;
  }

  .error-state-description {
    color: rgba(255,255,255,0.6);
    font-size: 14px;
    margin-bottom: 16px;
  }

  .error-state-retry {
    padding: 8px 16px;
    background: #ef4444;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 600;
  }

  .error-state-retry:hover {
    background: #dc2626;
  }

  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0,0,0,0.75);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
  }

  .modal-content {
    background: linear-gradient(135deg, rgba(91, 75, 219, 0.1), rgba(217, 70, 166, 0.1));
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px;
    padding: 24px;
    max-width: 90%;
    width: 360px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
  }

  .error-modal {
    border-color: rgba(239, 68, 68, 0.3);
  }

  .modal-content h2 {
    margin: 0 0 12px 0;
    font-size: 18px;
    color: white;
  }

  .modal-content p {
    margin: 0 0 20px 0;
    font-size: 14px;
    color: rgba(255,255,255,0.7);
  }

  .modal-actions {
    display: flex;
    gap: 12px;
    justify-content: flex-end;
  }

  .modal-actions button {
    padding: 8px 16px;
    border-radius: 6px;
    border: none;
    cursor: pointer;
    font-size: 14px;
    font-weight: 600;
    transition: all 0.28s ease;
  }

  .modal-close,
  .modal-retry {
    flex: 1;
  }

  .modal-close {
    background: rgba(255,255,255,0.1);
    color: white;
  }

  .modal-close:hover {
    background: rgba(255,255,255,0.2);
  }

  .modal-retry {
    background: #5b4bdb;
    color: white;
  }

  .modal-retry:hover {
    background: #4936b8;
  }
`;
document.head.appendChild(styleSheet);
