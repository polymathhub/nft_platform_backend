/**
 * UI Components Module
 * Reusable component functions using vanilla JavaScript
 * @module js/components
 */

import { escapeHTML, generateId } from './utils.js';

/**
 * Toast notification system
 */
export class Toast {
  static container = null;

  static show(message, type = 'info', duration = 3000) {
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.className = 'toast-container';
      document.body.appendChild(this.container);
    }

    const id = generateId('toast-');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.id = id;
    toast.innerHTML = `
      <div style="flex: 1;">
        <p style="margin: 0;">${escapeHTML(message)}</p>
      </div>
      <button class="toast-close" aria-label="Close">×</button>
    `;

    const closeBtn = toast.querySelector('.toast-close');
    closeBtn.addEventListener('click', () => this.remove(id));

    this.container.appendChild(toast);

    if (duration > 0) {
      setTimeout(() => this.remove(id), duration);
    }

    return id;
  }

  static remove(id) {
    const toast = document.getElementById(id);
    if (toast) {
      toast.style.animation = 'fadeOut 150ms forwards';
      setTimeout(() => toast.remove(), 150);
    }
  }

  static success(message, duration) {
    return this.show(message, 'success', duration);
  }

  static error(message, duration) {
    return this.show(message, 'error', duration);
  }

  static warning(message, duration) {
    return this.show(message, 'warning', duration);
  }

  static info(message, duration) {
    return this.show(message, 'info', duration);
  }
}

/**
 * Modal dialog
 */
export class Modal {
  constructor(options = {}) {
    this.id = generateId('modal-');
    this.options = {
      title: '',
      content: '',
      primaryBtn: { label: 'OK', callback: null },
      secondaryBtn: null,
      closeBtn: true,
      backdrop: true,
      onClose: null,
      ...options,
    };

    this.create();
  }

  create() {
    // Create backdrop
    this.backdrop = document.createElement('div');
    this.backdrop.className = 'modal-backdrop';
    this.backdrop.id = `${this.id}-backdrop`;

    if (this.options.backdrop) {
      this.backdrop.addEventListener('click', () => this.close());
    }

    // Create modal
    this.element = document.createElement('div');
    this.element.className = 'modal';
    this.element.id = this.id;

    const content = document.createElement('div');
    content.className = 'modal-content';

    let html = '';

    // Header
    if (this.options.title || this.options.closeBtn) {
      html += '<div class="modal-header">';
      if (this.options.title) {
        html += `<h2 class="modal-title">${escapeHTML(this.options.title)}</h2>`;
      }
      if (this.options.closeBtn) {
        html += '<button class="modal-close" aria-label="Close">×</button>';
      }
      html += '</div>';
    }

    // Body
    if (this.options.content) {
      if (typeof this.options.content === 'string') {
        html += `<div class="modal-body">${this.options.content}</div>`;
      } else {
        html += '<div class="modal-body"></div>';
      }
    }

    // Footer
    if (this.options.primaryBtn || this.options.secondaryBtn) {
      html += '<div class="modal-footer">';
      if (this.options.secondaryBtn) {
        html += `<button class="btn btn-secondary" id="${this.id}-secondary">
          ${escapeHTML(this.options.secondaryBtn.label)}
        </button>`;
      }
      if (this.options.primaryBtn) {
        html += `<button class="btn btn-primary" id="${this.id}-primary">
          ${escapeHTML(this.options.primaryBtn.label)}
        </button>`;
      }
      html += '</div>';
    }

    content.innerHTML = html;

    // Insert dynamic content if HTMLElement
    if (typeof this.options.content !== 'string') {
      const bodyEl = content.querySelector('.modal-body');
      if (bodyEl && this.options.content instanceof HTMLElement) {
        bodyEl.appendChild(this.options.content);
      }
    }

    // Attach event listeners
    const closeBtn = content.querySelector('.modal-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.close());
    }

    const primaryBtn = content.querySelector(`#${this.id}-primary`);
    if (primaryBtn && this.options.primaryBtn?.callback) {
      primaryBtn.addEventListener('click', () => {
        this.options.primaryBtn.callback();
        this.close();
      });
    }

    const secondaryBtn = content.querySelector(`#${this.id}-secondary`);
    if (secondaryBtn && this.options.secondaryBtn?.callback) {
      secondaryBtn.addEventListener('click', () => {
        this.options.secondaryBtn.callback();
      });
    }

    this.element.appendChild(content);
  }

  show() {
    document.body.appendChild(this.backdrop);
    document.body.appendChild(this.element);

    // Trigger animation
    requestAnimationFrame(() => {
      this.backdrop.classList.add('active');
      this.element.classList.add('active');
    });

    return this;
  }

  close() {
    this.backdrop.classList.remove('active');
    this.element.classList.remove('active');

    setTimeout(() => {
      this.backdrop.remove();
      this.element.remove();
      if (this.options.onClose) {
        this.options.onClose();
      }
    }, 150);

    return this;
  }

  destroy() {
    this.close();
  }
}

/**
 * Form validation and handling
 */
export class Form {
  constructor(formElement, options = {}) {
    this.form = formElement;
    this.options = {
      onSubmit: null,
      onError: null,
      showErrors: true,
      ...options,
    };

    this.errors = {};
    this.initialize();
  }

  initialize() {
    this.form.addEventListener('submit', (e) => this.handleSubmit(e));
    this.form.addEventListener('change', (e) => this.handleChange(e));
  }

  async handleSubmit(e) {
    e.preventDefault();
    this.errors = {};
    this.clearErrors();

    const formData = new FormData(this.form);
    const data = Object.fromEntries(formData);

    if (this.options.onSubmit) {
      try {
        await this.options.onSubmit(data);
      } catch (error) {
        if (this.options.onError) {
          this.options.onError(error);
        }
        if (error.validationErrors) {
          this.setErrors(error.validationErrors);
        }
      }
    }
  }

  handleChange(e) {
    const field = e.target.name;
    if (field && this.errors[field]) {
      delete this.errors[field];
      this.clearFieldError(field);
    }
  }

  setErrors(errors) {
    this.errors = errors;
    if (this.options.showErrors) {
      Object.entries(errors).forEach(([field, message]) => {
        this.showFieldError(field, message);
      });
    }
  }

  showFieldError(fieldName, message) {
    const field = this.form.querySelector(`[name="${fieldName}"]`);
    if (!field) return;

    field.classList.add('error');

    let errorEl = field.parentElement.querySelector('.form-error');
    if (!errorEl) {
      errorEl = document.createElement('div');
      errorEl.className = 'form-error';
      field.parentElement.appendChild(errorEl);
    }

    errorEl.textContent = escapeHTML(message);
  }

  clearFieldError(fieldName) {
    const field = this.form.querySelector(`[name="${fieldName}"]`);
    if (!field) return;

    field.classList.remove('error');

    const errorEl = field.parentElement.querySelector('.form-error');
    if (errorEl) {
      errorEl.remove();
    }
  }

  clearErrors() {
    this.form.querySelectorAll('.form-control.error').forEach(field => {
      field.classList.remove('error');
    });

    this.form.querySelectorAll('.form-error').forEach(el => {
      el.remove();
    });
  }

  getData() {
    const formData = new FormData(this.form);
    return Object.fromEntries(formData);
  }

  setData(data) {
    Object.entries(data).forEach(([key, value]) => {
      const field = this.form.querySelector(`[name="${key}"]`);
      if (field) {
        if (field.type === 'checkbox' || field.type === 'radio') {
          field.checked = value;
        } else {
          field.value = value;
        }
      }
    });
  }

  disable() {
    this.form.querySelectorAll('input, textarea, select, button').forEach(el => {
      el.disabled = true;
    });
  }

  enable() {
    this.form.querySelectorAll('input, textarea, select, button').forEach(el => {
      el.disabled = false;
    });
  }

  reset() {
    this.form.reset();
    this.clearErrors();
  }
}

/**
 * Loading spinner
 */
export function createSpinner(size = 'md') {
  const sizeMap = {
    sm: '20px',
    md: '40px',
    lg: '60px',
  };

  const spinner = document.createElement('div');
  spinner.className = 'spinner skeleton';
  spinner.style.cssText = `
    width: ${sizeMap[size] || sizeMap.md};
    height: ${sizeMap[size] || sizeMap.md};
    border-radius: 50%;
    display: inline-block;
  `;

  return spinner;
}

/**
 * Card component
 */
export function createCard(content, options = {}) {
  const card = document.createElement('div');
  card.className = `card ${options.compact ? 'card-compact' : ''}`;

  if (typeof content === 'string') {
    card.innerHTML = content;
  } else if (content instanceof HTMLElement) {
    card.appendChild(content);
  }

  return card;
}

/**
 * Button component
 */
export function createButton(label, options = {}) {
  const btn = document.createElement('button');
  btn.className = `btn ${options.variant || 'btn-primary'} ${options.size ? `btn-${options.size}` : ''} ${options.full ? 'btn-full' : ''}`;
  btn.textContent = label;

  if (options.id) btn.id = options.id;
  if (options.disabled) btn.disabled = true;
  if (options.type) btn.type = options.type;
  if (options.onclick) btn.addEventListener('click', options.onclick);

  return btn;
}

/**
 * Navbar component
 */
export function createNavbar(options = {}) {
  const navbar = document.createElement('nav');
  navbar.className = 'navbar';

  let html = '';

  if (options.brand) {
    html += `<a href="${escapeHTML(options.brand.href)}" class="navbar-brand">
      ${escapeHTML(options.brand.label)}
    </a>`;
  }

  if (options.nav && options.nav.length > 0) {
    html += '<ul class="navbar-nav">';
    options.nav.forEach(item => {
      const active = item.active ? ' active' : '';
      html += `<li><a href="${escapeHTML(item.href)}" class="nav-link${active}">${escapeHTML(item.label)}</a></li>`;
    });
    html += '</ul>';
  }

  navbar.innerHTML = html;
  return navbar;
}

/**
 * Grid component
 */
export function createGrid(items, columns = 3, options = {}) {
  const grid = document.createElement('div');
  grid.className = `grid ${options.className || ''}`;
  grid.style.gridTemplateColumns = `repeat(${columns}, minmax(0, 1fr))`;
  grid.style.gap = options.gap || '1rem';

  items.forEach(item => {
    const cell = document.createElement('div');
    if (item instanceof HTMLElement) {
      cell.appendChild(item);
    } else {
      cell.innerHTML = item;
    }
    grid.appendChild(cell);
  });

  return grid;
}

/**
 * Pagination component
 */
export function createPagination(totalPages, currentPage = 1, onPageChange = null) {
  const container = document.createElement('div');
  container.className = 'flex items-center justify-center gap-md';

  // Previous button
  const prevBtn = createButton('←', {
    variant: 'btn-secondary',
    size: 'sm',
    disabled: currentPage === 1,
    onclick: () => onPageChange && onPageChange(currentPage - 1),
  });
  container.appendChild(prevBtn);

  // Page numbers
  for (let i = Math.max(1, currentPage - 2); i <= Math.min(totalPages, currentPage + 2); i++) {
    const btn = createButton(i.toString(), {
      variant: i === currentPage ? 'btn-primary' : 'btn-secondary',
      size: 'sm',
      onclick: () => onPageChange && onPageChange(i),
    });
    container.appendChild(btn);
  }

  // Next button
  const nextBtn = createButton('→', {
    variant: 'btn-secondary',
    size: 'sm',
    disabled: currentPage === totalPages,
    onclick: () => onPageChange && onPageChange(currentPage + 1),
  });
  container.appendChild(nextBtn);

  return container;
}

/**
 * Badge component
 */
export function createBadge(text, variant = 'primary') {
  const badge = document.createElement('span');
  badge.className = `badge badge-${variant}`;
  badge.textContent = text;
  return badge;
}

/**
 * Avatar component
 */
export function createAvatar(src, name = '', size = 'md') {
  const sizeMap = {
    sm: '32px',
    md: '40px',
    lg: '56px',
  };

  const avatar = document.createElement('img');
  avatar.src = src;
  avatar.alt = name;
  avatar.style.cssText = `
    width: ${sizeMap[size] || sizeMap.md};
    height: ${sizeMap[size] || sizeMap.md};
    border-radius: 50%;
    object-fit: cover;
  `;

  return avatar;
}

export default {
  Toast,
  Modal,
  Form,
  createSpinner,
  createCard,
  createButton,
  createNavbar,
  createGrid,
  createPagination,
  createBadge,
  createAvatar,
};
