/**
 * SVG Icon System
 * Professional icon management with proper accessibility and performance
 * @module svg-icons
 */

class SvgIconSystem {
  constructor(config = {}) {
    this.config = {
      spritePath: config.spritePath || 'icons.svg',
      defaultSize: config.defaultSize || '24',
      defaultClass: config.defaultClass || 'icon',
      fallbackText: config.fallbackText || '●',
      cacheIcons: config.cacheIcons !== false,
      ...config,
    };

    this.cache = new Map();
    this.spriteLoaded = false;
    this.spriteDoc = null;
    this.init();
  }

  /**
   * Initialize the SVG icon system
   */
  async init() {
    try {
      await this.loadSprite();
      this.spriteLoaded = true;
      document.dispatchEvent(new CustomEvent('svg-icons-ready'));
    } catch (error) {
      console.error('Failed to load SVG sprite:', error);
    }
  }

  /**
   * Load the SVG sprite document
   */
  async loadSprite() {
    if (this.spriteLoaded && this.spriteDoc) return this.spriteDoc;

    try {
      const response = await fetch(this.config.spritePath);
      const text = await response.text();
      const parser = new DOMParser();
      this.spriteDoc = parser.parseFromString(text, 'image/svg+xml');

      if (this.spriteDoc.parsererror) {
        throw new Error('Failed to parse SVG sprite');
      }

      return this.spriteDoc;
    } catch (error) {
      console.error('Error loading SVG sprite:', error);
      throw error;
    }
  }

  /**
   * Get a single icon symbol from sprite
   */
  getSymbol(iconId) {
    if (!this.spriteDoc) return null;
    return this.spriteDoc.querySelector(`#${iconId}`);
  }

  /**
   * Create an icon element with proper SVG structure
   * @param {string} iconId - Icon identifier (without 'icon-' prefix)
   * @param {Object} options - Icon configuration options
   * @returns {SVGSVGElement} SVG element
   */
  createIcon(iconId, options = {}) {
    const {
      size = this.config.defaultSize,
      className = this.config.defaultClass,
      ariaLabel = null,
      ariaHidden = false,
      title = null,
      animate = false,
      fillColor = 'currentColor',
      strokeWidth = '1.5',
    } = options;

    const iconIdWithPrefix = this._normalizeIconId(iconId);
    const symbol = this.getSymbol(iconIdWithPrefix);

    if (!symbol) {
      console.warn(`Icon "${iconIdWithPrefix}" not found in sprite`);
      return this._createFallback(iconId, size, className);
    }

    // Create SVG element
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('class', className);
    svg.setAttribute('width', size);
    svg.setAttribute('height', size);
    svg.setAttribute('viewBox', symbol.getAttribute('viewBox') || '0 0 24 24');
    svg.setAttribute('fill', 'none');

    // Accessibility attributes
    if (ariaLabel) {
      svg.setAttribute('role', 'img');
      svg.setAttribute('aria-label', ariaLabel);
    } else if (ariaHidden) {
      svg.setAttribute('aria-hidden', 'true');
    }

    if (title) {
      const titleEl = document.createElementNS('http://www.w3.org/2000/svg', 'title');
      titleEl.textContent = title;
      svg.appendChild(titleEl);
    }

    // Use reference for better performance
    const use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
    use.setAttributeNS('http://www.w3.org/1999/xlink', 'xlink:href', `#${iconIdWithPrefix}`);
    svg.appendChild(use);

    // Apply styling
    svg.style.color = fillColor;
    svg.dataset.iconId = iconId;

    if (animate) {
      svg.classList.add('svg-icon-animate');
    }

    return svg;
  }

  /**
   * Create multiple icons efficiently
   */
  createIcons(icons) {
    return icons.map(icon => {
      if (typeof icon === 'string') {
        return this.createIcon(icon);
      }
      return this.createIcon(icon.id, icon.options);
    });
  }

  /**
   * Replace HTML elements with SVG icons
   */
  replaceIconPlaceholders(container = document) {
    const placeholders = container.querySelectorAll('[data-icon]');

    placeholders.forEach(el => {
      const iconId = el.dataset.icon;
      const options = {
        size: el.dataset.size || this.config.defaultSize,
        className: el.dataset.iconClass || this.config.defaultClass,
        ariaLabel: el.dataset.ariaLabel || null,
        ariaHidden: el.dataset.ariaHidden === 'true',
        title: el.dataset.title || null,
        animate: el.dataset.animate === 'true',
        fillColor: el.dataset.color || 'currentColor',
      };

      const icon = this.createIcon(iconId, options);
      el.replaceWith(icon);
    });
  }

  /**
   * Insert icon into an element
   */
  insertIcon(container, iconId, options = {}, position = 'append') {
    const icon = this.createIcon(iconId, options);

    if (position === 'append') {
      container.appendChild(icon);
    } else if (position === 'prepend') {
      container.insertBefore(icon, container.firstChild);
    } else if (typeof position === 'number') {
      container.insertBefore(icon, container.children[position]);
    }

    return icon;
  }

  /**
   * Update icon color dynamically
   */
  updateIconColor(iconElement, color) {
    iconElement.style.color = color;
  }

  /**
   * Toggle icon animation
   */
  toggleAnimation(iconElement, animate = true) {
    if (animate) {
      iconElement.classList.add('svg-icon-animate');
    } else {
      iconElement.classList.remove('svg-icon-animate');
    }
  }

  /**
   * Get all available icon IDs from sprite
   */
  getAvailableIcons() {
    if (!this.spriteDoc) return [];
    return Array.from(this.spriteDoc.querySelectorAll('symbol'))
      .map(symbol => symbol.id);
  }

  /**
   * Normalize icon ID format
   */
  _normalizeIconId(iconId) {
    if (iconId.startsWith('icon-')) {
      return iconId;
    }
    return `icon-${iconId}`;
  }

  /**
   * Create fallback element when icon not found
   */
  _createFallback(iconId, size, className) {
    const fallback = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    fallback.setAttribute('class', `${className} svg-icon-fallback`);
    fallback.setAttribute('width', size);
    fallback.setAttribute('height', size);
    fallback.setAttribute('viewBox', '0 0 24 24');
    fallback.setAttribute('aria-label', `Missing icon: ${iconId}`);
    fallback.setAttribute('role', 'img');

    const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    text.setAttribute('x', '12');
    text.setAttribute('y', '13');
    text.setAttribute('text-anchor', 'middle');
    text.setAttribute('font-size', '16');
    text.setAttribute('fill', 'currentColor');
    text.textContent = this.config.fallbackText;

    fallback.appendChild(text);
    return fallback;
  }
}

/**
 * Icon helper function - convenience wrapper
 */
function createSvgIcon(iconId, options = {}) {
  if (!window.svgIcons) {
    console.warn('SVG Icon System not initialized');
    return null;
  }
  return window.svgIcons.createIcon(iconId, options);
}

/**
 * Batch initialize with data attributes
 */
document.addEventListener('DOMContentLoaded', () => {
  if (window.svgIcons) {
    window.svgIcons.replaceIconPlaceholders();
  }
});

// Export for use
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { SvgIconSystem, createSvgIcon };
}
