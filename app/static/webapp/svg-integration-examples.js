/**
 * SVG Icon System Integration Examples
 * Professional patterns for using SVG icons in your application
 * 
 * @module svg-integration-examples
 * @description Production-ready examples showing best practices
 */

// ========== PATTERN 1: ICON MANAGEMENT UTILITIES ==========

/**
 * Utility class for managing UI icons in various contexts
 */
class IconManager {
  constructor(svgIconSystem) {
    this.icons = svgIconSystem;
  }

  /**
   * Create a loading spinner with proper accessibility
   */
  createLoadingSpinner(ariaLabel = 'Loading') {
    return this.icons.createIcon('loading', {
      size: '32',
      className: 'icon icon--lg svg-icon-animate',
      ariaLabel,
      animate: true,
    });
  }

  /**
   * Create a status icon with appropriate color
   */
  createStatusIcon(status) {
    const statusConfig = {
      success: { icon: 'check', class: 'icon--success', label: 'Success' },
      error: { icon: 'alert', class: 'icon--error', label: 'Error' },
      warning: { icon: 'warning', class: 'icon--warning', label: 'Warning' },
      info: { icon: 'info', class: 'icon--info', label: 'Information' },
    };

    const config = statusConfig[status] || statusConfig.info;
    return this.icons.createIcon(config.icon, {
      size: '24',
      className: `icon ${config.class}`,
      ariaLabel: config.label,
    });
  }

  /**
   * Create navigation icon with tooltip
   */
  createNavIcon(iconId, tooltip) {
    return this.icons.createIcon(iconId, {
      size: '24',
      className: 'icon',
      title: tooltip,
      ariaLabel: tooltip,
    });
  }

  /**
   * Create action button with icon and label
   */
  createActionButton(iconId, label, onClick) {
    const button = document.createElement('button');
    button.className = 'btn btn-secondary';
    button.innerHTML = `
      <svg class="icon icon--md" aria-hidden="true">
        <use xlink:href="icons.svg#icon-${iconId}"></use>
      </svg>
      <span>${label}</span>
    `;
    button.addEventListener('click', onClick);
    return button;
  }
}

// ========== PATTERN 2: LOADING STATE MANAGEMENT ==========

/**
 * Manage loading states with icon animations
 */
class LoadingStateManager {
  constructor(svgIconSystem) {
    this.icons = svgIconSystem;
  }

  /**
   * Apply loading state to a button
   */
  setButtonLoading(button, isLoading = true) {
    const icon = button.querySelector('.icon');
    const label = button.querySelector('span');

    if (isLoading) {
      button.disabled = true;
      if (icon) {
        this.icons.toggleAnimation(icon, true);
        icon.classList.add('svg-icon-animate');
      }
      if (label) label.style.opacity = '0.6';
    } else {
      button.disabled = false;
      if (icon) {
        this.icons.toggleAnimation(icon, false);
        icon.classList.remove('svg-icon-animate');
      }
      if (label) label.style.opacity = '1';
    }
  }

  /**
   * Show result state (success/error)
   */
  setResultState(button, result) {
    const icon = button.querySelector('.icon');
    const iconMap = {
      success: 'check',
      error: 'alert',
      loading: 'loading',
    };

    if (!icon) return;

    // Remove previous state
    icon.classList.remove('svg-icon-animate', 'icon--success', 'icon--error');

    // Apply new state
    const iconId = iconMap[result] || iconMap.loading;
    const statusClass = result === 'success' ? 'icon--success' : 'icon--error';

    if (result === 'loading') {
      icon.classList.add('svg-icon-animate');
    } else {
      icon.classList.add(statusClass);
    }
  }
}

// ========== PATTERN 3: FORM ENHANCEMENT ==========

/**
 * Enhance forms with icon indicators
 */
class FormIconEnhancer {
  constructor(svgIconSystem) {
    this.icons = svgIconSystem;
  }

  /**
   * Add validation indicator to form field
   */
  setFieldValidation(field, isValid) {
    let indicator = field.nextElementSibling;

    if (!indicator || !indicator.classList.contains('field-indicator')) {
      indicator = document.createElement('div');
      indicator.className = 'field-indicator';
      field.parentNode.insertBefore(indicator, field.nextSibling);
    }

    indicator.innerHTML = '';
    const icon = this.icons.createIcon(isValid ? 'check' : 'alert', {
      size: '18',
      className: isValid ? 'icon icon--success' : 'icon icon--error',
      ariaLabel: isValid ? 'Valid' : 'Invalid',
    });
    indicator.appendChild(icon);
  }

  /**
   * Show field help with icon
   */
  showFieldHelp(field, message) {
    let helper = field.nextElementSibling;

    if (!helper || !helper.classList.contains('field-help')) {
      helper = document.createElement('div');
      helper.className = 'field-help';
      field.parentNode.appendChild(helper);
    }

    helper.innerHTML = '';
    const icon = this.icons.createIcon('info', {
      size: '16',
      className: 'icon icon--muted',
      ariaHidden: true,
    });
    helper.appendChild(icon);
    helper.appendChild(document.createTextNode(` ${message}`));
  }
}

// ========== PATTERN 4: NOTIFICATION SYSTEM ==========

/**
 * Create notifications with appropriate icons
 */
class NotificationBuilder {
  constructor(svgIconSystem) {
    this.icons = svgIconSystem;
  }

  /**
   * Create notification element
   */
  createNotification(type, message, duration = 3000) {
    const typeConfig = {
      success: { icon: 'check', class: 'notification--success' },
      error: { icon: 'alert', class: 'notification--error' },
      warning: { icon: 'warning', class: 'notification--warning' },
      info: { icon: 'info', class: 'notification--info' },
    };

    const config = typeConfig[type] || typeConfig.info;

    const notification = document.createElement('div');
    notification.className = `notification ${config.class}`;

    const icon = this.icons.createIcon(config.icon, {
      size: '20',
      className: 'icon',
      ariaHidden: true,
    });

    notification.appendChild(icon);
    notification.appendChild(document.createTextNode(message));

    if (duration > 0) {
      setTimeout(() => notification.remove(), duration);
    }

    return notification;
  }
}

// ========== PATTERN 5: MODAL ENHANCEMENTS ==========

/**
 * Enhance modals with icons
 */
class ModalIconManager {
  constructor(svgIconSystem) {
    this.icons = svgIconSystem;
  }

  /**
   * Create close button with icon
   */
  createCloseButton(onClose) {
    const button = document.createElement('button');
    button.className = 'modal-close';
    button.setAttribute('aria-label', 'Close dialog');

    const icon = this.icons.createIcon('close', {
      size: '20',
      className: 'icon',
      ariaHidden: true,
    });

    button.appendChild(icon);
    button.addEventListener('click', onClose);

    return button;
  }

  /**
   * Create confirmation dialog with icon
   */
  createConfirmDialog(iconId, title, message) {
    const dialog = document.createElement('div');
    dialog.className = 'confirm-dialog';

    const icon = this.icons.createIcon(iconId, {
      size: '48',
      className: 'icon icon--2xl',
      ariaHidden: true,
    });

    const titleEl = document.createElement('h2');
    titleEl.textContent = title;

    const messageEl = document.createElement('p');
    messageEl.textContent = message;

    dialog.appendChild(icon);
    dialog.appendChild(titleEl);
    dialog.appendChild(messageEl);

    return dialog;
  }
}

// ========== PATTERN 6: DYNAMIC BUTTON STATES ==========

/**
 * Manage dynamic button state changes with icons
 */
class DynamicButtonManager {
  constructor(svgIconSystem) {
    this.icons = svgIconSystem;
  }

  /**
   * Create toggle button with icon switching
   */
  createToggleButton(onIconId, offIconId, initialState = false) {
    const button = document.createElement('button');
    button.className = 'toggle-button';
    button.dataset.state = initialState ? 'on' : 'off';

    const icon = this.icons.createIcon(
      initialState ? onIconId : offIconId,
      {
        size: '24',
        className: 'icon',
        ariaHidden: true,
      }
    );

    button.appendChild(icon);

    button.addEventListener('click', () => {
      const isOn = button.dataset.state === 'on';
      const newIconId = isOn ? offIconId : onIconId;

      button.dataset.state = isOn ? 'off' : 'on';

      const newIcon = this.icons.createIcon(newIconId, {
        size: '24',
        className: 'icon',
        ariaHidden: true,
      });

      icon.replaceWith(newIcon);
    });

    return button;
  }

  /**
   * Create state-dependent dropdown with icons
   */
  createStateDropdown(states) {
    const dropdown = document.createElement('div');
    dropdown.className = 'state-dropdown';

    const button = document.createElement('button');
    button.className = 'dropdown-trigger';

    const currentStateConfig = states[0];
    const icon = this.icons.createIcon(currentStateConfig.icon, {
      size: '20',
      className: 'icon',
      ariaHidden: true,
    });

    button.appendChild(icon);
    button.appendChild(document.createTextNode(currentStateConfig.label));

    dropdown.appendChild(button);

    return dropdown;
  }
}

// ========== PATTERN 7: REAL-TIME STATUS UPDATES ==========

/**
 * Update UI icons in real-time based on status changes
 */
class RealtimeStatusUpdater {
  constructor(svgIconSystem) {
    this.icons = svgIconSystem;
    this.statusElements = new Map();
  }

  /**
   * Create a status indicator
   */
  createStatusIndicator(initialStatus, options = {}) {
    const container = document.createElement('div');
    container.className = 'status-indicator';

    const iconContainer = document.createElement('div');
    iconContainer.className = 'status-icon';

    const icon = this.icons.createIcon(this._getIconForStatus(initialStatus), {
      size: options.size || '24',
      className: 'icon',
      ariaLabel: `Status: ${initialStatus}`,
    });

    iconContainer.appendChild(icon);
    container.appendChild(iconContainer);

    if (options.showLabel) {
      const label = document.createElement('span');
      label.className = 'status-label';
      label.textContent = initialStatus;
      container.appendChild(label);
    }

    this.statusElements.set(container, { status: initialStatus, options });

    return container;
  }

  /**
   * Update status indicator
   */
  updateStatus(statusContainer, newStatus) {
    const data = this.statusElements.get(statusContainer);
    if (!data) return;

    data.status = newStatus;

    const iconContainer = statusContainer.querySelector('.status-icon');
    if (iconContainer) {
      iconContainer.innerHTML = '';
      const newIcon = this.icons.createIcon(
        this._getIconForStatus(newStatus),
        {
          size: data.options.size || '24',
          className: 'icon',
          ariaLabel: `Status: ${newStatus}`,
        }
      );
      iconContainer.appendChild(newIcon);
    }

    if (data.options.showLabel) {
      const label = statusContainer.querySelector('.status-label');
      if (label) label.textContent = newStatus;
    }
  }

  _getIconForStatus(status) {
    const statusMap = {
      online: 'check',
      offline: 'alert',
      pending: 'loading',
      error: 'alert',
      success: 'check',
      warning: 'warning',
    };
    return statusMap[status] || 'info';
  }
}

// ========== INITIALIZATION HELPER ==========

/**
 * Initialize all icon utilities when SVG system is ready
 */
function initializeIconUtilities() {
  if (!window.svgIcons) {
    console.error('SVG Icon System not initialized');
    return;
  }

  // Create global instances
  window.iconManager = new IconManager(window.svgIcons);
  window.loadingStateManager = new LoadingStateManager(window.svgIcons);
  window.formIconEnhancer = new FormIconEnhancer(window.svgIcons);
  window.notificationBuilder = new NotificationBuilder(window.svgIcons);
  window.modalIconManager = new ModalIconManager(window.svgIcons);
  window.dynamicButtonManager = new DynamicButtonManager(window.svgIcons);
  window.realtimeStatusUpdater = new RealtimeStatusUpdater(window.svgIcons);

  console.log('Icon Utilities initialized successfully');
}

// Auto-initialize when SVG system is ready
if (document.readyState === 'loading') {
  document.addEventListener('svg-icons-ready', initializeIconUtilities);
} else {
  initializeIconUtilities();
}

// Export utilities
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    IconManager,
    LoadingStateManager,
    FormIconEnhancer,
    NotificationBuilder,
    ModalIconManager,
    DynamicButtonManager,
    RealtimeStatusUpdater,
  };
}
