/**
 * COMPONENT LIBRARY
 * Reusable UI components matching design tokens
 */

import DESIGN_TOKENS, { GRADIENTS } from './design-tokens.js';

const DT = DESIGN_TOKENS;

// ==================== CARD COMPONENT ====================
export function createCard(content, options = {}) {
  const {
    gradient = false,
    padding = DT.card.padding,
    shadow = DT.card.shadow,
    className = '',
  } = options;

  const card = document.createElement('div');
  card.className = `card ${className}`;
  card.style.cssText = `
    background: ${gradient ? GRADIENTS.primaryWeak : DT.colors.background.card};
    border-radius: ${DT.card.radius};
    padding: ${padding};
    box-shadow: ${shadow};
    border: 1px solid ${DT.colors.border.light};
    transition: all ${DT.transitions.base};
  `;

  if (typeof content === 'string') {
    card.innerHTML = content;
  } else {
    card.appendChild(content);
  }

  return card;
}

// ==================== BALANCE CARD HERO ====================
export function createBalanceCard(balance, currency = 'USD') {
  const html = `
    <style>
      .balance-card {
        background: ${GRADIENTS.primary};
        border-radius: ${DT.card.radius};
        padding: ${DT.spacing['3xl']};
        box-shadow: ${DT.shadows.medium};
        position: relative;
        overflow: hidden;
      }

      .balance-card::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -20%;
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, transparent 70%);
        border-radius: 50%;
      }

      .balance-card-content {
        position: relative;
        z-index: 1;
      }

      .balance-label {
        font-size: ${DT.typography.body.small.size};
        color: ${DT.colors.text.secondary};
        margin-bottom: ${DT.spacing.sm};
        font-weight: 400;
      }

      .balance-amount {
        font-size: 32px;
        font-weight: 700;
        color: ${DT.colors.text.primary};
        margin-bottom: ${DT.spacing.md};
        letter-spacing: -1px;
      }

      .balance-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-top: ${DT.spacing.lg};
        border-top: 1px solid rgba(255, 255, 255, 0.1);
      }

      .balance-stat {
        display: flex;
        flex-direction: column;
        gap: ${DT.spacing.xs};
      }

      .balance-stat-label {
        font-size: ${DT.typography.body.small.size};
        color: rgba(255, 255, 255, 0.7);
        font-weight: 400;
      }

      .balance-stat-value {
        font-size: 16px;
        font-weight: 600;
        color: ${DT.colors.text.primary};
      }
    </style>

    <div class="balance-card">
      <div class="balance-card-content">
        <div class="balance-label">Total Balance</div>
        <div class="balance-amount">$${balance.toLocaleString('en-US', { maximumFractionDigits: 2 })}</div>
        <div class="balance-label" style="margin-bottom: ${DT.spacing.lg};">${currency}</div>
        
        <div class="balance-footer">
          <div class="balance-stat">
            <div class="balance-stat-label">Total Owns</div>
            <div class="balance-stat-value">1.24 ETH</div>
          </div>
          <div class="balance-stat">
            <div class="balance-stat-label">Total Profit</div>
            <div class="balance-stat-value">$450</div>
          </div>
        </div>
      </div>
    </div>
  `;

  const container = document.createElement('div');
  container.innerHTML = html;
  return container.firstElementChild;
}

// ==================== STAT CARD ====================
export function createStatCard(icon, label, value, unit = '', trend = null) {
  const html = `
    <style>
      .stat-card {
        background: ${DT.colors.background.card};
        border: 1px solid ${DT.colors.border.light};
        border-radius: ${DT.card.radius};
        padding: ${DT.spacing.xl};
        display: flex;
        flex-direction: column;
        gap: ${DT.spacing.md};
        transition: all ${DT.transitions.base};
      }

      .stat-card:active {
        transform: translateY(2px);
      }

      .stat-icon {
        width: 40px;
        height: 40px;
        border-radius: 12px;
        background: rgba(139, 92, 246, 0.15);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
      }

      .stat-label {
        font-size: ${DT.typography.body.small.size};
        color: ${DT.colors.text.secondary};
        font-weight: 400;
      }

      .stat-value-group {
        display: flex;
        align-items: baseline;
        gap: ${DT.spacing.sm};
      }

      .stat-value {
        font-size: 20px;
        font-weight: 700;
        color: ${DT.colors.text.primary};
      }

      .stat-unit {
        font-size: 12px;
        color: ${DT.colors.text.secondary};
      }

      .stat-trend {
        font-size: 12px;
        font-weight: 600;
        padding: 4px 8px;
        border-radius: 6px;
        width: fit-content;
      }

      .stat-trend.positive {
        background: rgba(16, 185, 129, 0.15);
        color: #10B981;
      }

      .stat-trend.negative {
        background: rgba(239, 68, 68, 0.15);
        color: #EF4444;
      }
    </style>

    <div class="stat-card">
      <div class="stat-icon">${icon}</div>
      <div>
        <div class="stat-label">${label}</div>
        <div class="stat-value-group">
          <div class="stat-value">${value}</div>
          ${unit ? `<span class="stat-unit">${unit}</span>` : ''}
        </div>
      </div>
      ${trend ? `<div class="stat-trend ${trend.direction}">${trend.symbol}${trend.value}</div>` : ''}
    </div>
  `;

  const container = document.createElement('div');
  container.innerHTML = html;
  return container.firstElementChild;
}

// ==================== QUICK ACTION PILL ====================
export function createQuickActionButton(icon, label, onClick = null) {
  const html = `
    <style>
      .quick-action {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: ${DT.spacing.md};
        padding: ${DT.spacing.lg};
        background: ${DT.colors.background.card};
        border: 1px solid ${DT.colors.border.light};
        border-radius: ${DT.radius.xl};
        cursor: pointer;
        transition: all ${DT.transitions.base};
        flex: 1;
        min-height: 100px;
        justify-content: center;
      }

      .quick-action:active {
        background: ${DT.colors.background.elevated};
        transform: scale(0.95);
      }

      .quick-action-icon {
        width: 40px;
        height: 40px;
        border-radius: 12px;
        background: ${GRADIENTS.primaryWeak};
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
      }

      .quick-action-label {
        font-size: ${DT.typography.body.normal.size};
        font-weight: 600;
        color: ${DT.colors.text.primary};
        text-align: center;
      }
    </style>

    <button class="quick-action" type="button">
      <div class="quick-action-icon">${icon}</div>
      <div class="quick-action-label">${label}</div>
    </button>
  `;

  const container = document.createElement('div');
  container.innerHTML = html;
  const button = container.firstElementChild;

  if (onClick) {
    button.addEventListener('click', onClick);
  }

  return button;
}

// ==================== NFT CARD ====================
export function createNFTCard(nft) {
  const { id, name, image, price, currency = 'USD', owner } = nft;

  const html = `
    <style>
      .nft-card {
        background: ${DT.colors.background.card};
        border-radius: ${DT.card.radius};
        overflow: hidden;
        box-shadow: ${DT.shadows.soft};
        transition: all ${DT.transitions.base};
        cursor: pointer;
      }

      .nft-card:active {
        transform: translateY(-4px);
        box-shadow: ${DT.shadows.elevated};
      }

      .nft-image {
        width: 100%;
        aspect-ratio: 1;
        background: ${GRADIENTS.darkElevated};
        object-fit: cover;
        display: block;
      }

      .nft-info {
        padding: ${DT.spacing.lg};
      }

      .nft-name {
        font-size: ${DT.typography.heading[3].size};
        font-weight: ${DT.typography.heading[3].weight};
        color: ${DT.colors.text.primary};
        margin-bottom: ${DT.spacing.sm};
      }

      .nft-owner {
        font-size: ${DT.typography.body.small.size};
        color: ${DT.colors.text.secondary};
        margin-bottom: ${DT.spacing.lg};
      }

      .nft-price {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-top: ${DT.spacing.lg};
        border-top: 1px solid ${DT.colors.border.light};
      }

      .nft-price-label {
        font-size: ${DT.typography.body.small.size};
        color: ${DT.colors.text.secondary};
      }

      .nft-price-value {
        font-size: 16px;
        font-weight: 700;
        color: ${DT.colors.text.primary};
      }
    </style>

    <div class="nft-card">
      <img src="${image}" alt="${name}" class="nft-image" />
      <div class="nft-info">
        <div class="nft-name">${name}</div>
        <div class="nft-owner">Owner: ${owner}</div>
        <div class="nft-price">
          <div class="nft-price-label">Listed Price</div>
          <div class="nft-price-value">$${price.toLocaleString()}</div>
        </div>
      </div>
    </div>
  `;

  const container = document.createElement('div');
  container.innerHTML = html;
  return container.firstElementChild;
}

// ==================== ACTIVITY ITEM ====================
export function createActivityItem(activity) {
  const { icon, title, description, time, amount, type = 'neutral' } = activity;

  const typeColor = {
    positive: '#10B981',
    negative: '#EF4444',
    neutral: '#A0AEC0',
  }[type] || '#A0AEC0';

  const html = `
    <style>
      .activity-item {
        display: flex;
        gap: ${DT.spacing.lg};
        padding: ${DT.spacing.lg};
        border-bottom: 1px solid ${DT.colors.border.light};
        transition: background ${DT.transitions.fast};
      }

      .activity-item:last-child {
        border-bottom: none;
      }

      .activity-item:active {
        background: rgba(139, 92, 246, 0.05);
      }

      .activity-icon {
        width: 40px;
        height: 40px;
        border-radius: 12px;
        background: ${GRADIENTS.primaryWeak};
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        flex-shrink: 0;
      }

      .activity-content {
        flex: 1;
        min-width: 0;
      }

      .activity-title {
        font-size: ${DT.typography.body.large.size};
        font-weight: 600;
        color: ${DT.colors.text.primary};
        margin-bottom: ${DT.spacing.xs};
      }

      .activity-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }

      .activity-description {
        font-size: ${DT.typography.body.small.size};
        color: ${DT.colors.text.secondary};
      }

      .activity-time {
        font-size: ${DT.typography.body.small.size};
        color: ${DT.colors.text.tertiary};
      }

      .activity-amount {
        font-size: ${DT.typography.body.large.size};
        font-weight: 700;
        color: ${typeColor};
        text-align: right;
        white-space: nowrap;
      }
    </style>

    <div class="activity-item">
      <div class="activity-icon">${icon}</div>
      <div class="activity-content">
        <div class="activity-title">${title}</div>
        <div class="activity-meta">
          <div class="activity-description">${description}</div>
          <div class="activity-time">${time}</div>
        </div>
      </div>
      ${amount ? `<div class="activity-amount">${amount}</div>` : ''}
    </div>
  `;

  const container = document.createElement('div');
  container.innerHTML = html;
  return container.firstElementChild;
}

// ==================== BOTTOM NAVIGATION ====================
export function createBottomNav(activeTab = 'home', onTabChange = null) {
  const tabs = [
    { id: 'home', icon: '🏠', label: 'Home' },
    { id: 'wallet', icon: '💳', label: 'Wallet' },
    { id: 'mint', icon: '✨', label: 'Mint' },
    { id: 'market', icon: '🏪', label: 'Market' },
    { id: 'profile', icon: '👤', label: 'Profile' },
  ];

  const html = `
    <style>
      .bottom-nav {
        display: flex;
        justify-content: space-around;
        align-items: center;
        height: ${DT.navigation.bottomHeight};
        padding: ${DT.spacing.md} 0;
        border-top: 1px solid ${DT.colors.border.light};
        background: ${DT.colors.background.base};
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        z-index: ${DT.zIndex.sticky};
      }

      .nav-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: ${DT.spacing.xs};
        padding: ${DT.spacing.md} ${DT.spacing.lg};
        cursor: pointer;
        border-radius: ${DT.radius['3xl']};
        transition: all ${DT.transitions.base};
        border: 1px solid transparent;
        flex: 1;
      }

      .nav-item.active {
        background: ${GRADIENTS.primaryWeak};
        border: 1px solid ${DT.colors.border.medium};
      }

      .nav-icon {
        font-size: 20px;
      }

      .nav-label {
        font-size: ${DT.typography.label.size};
        font-weight: ${DT.typography.label.weight};
        color: ${DT.colors.text.secondary};
      }

      .nav-item.active .nav-label {
        color: ${DT.colors.text.primary};
      }
    </style>

    <div class="bottom-nav">
      ${tabs.map(tab => `
        <div class="nav-item ${activeTab === tab.id ? 'active' : ''}" data-tab="${tab.id}">
          <div class="nav-icon">${tab.icon}</div>
          <div class="nav-label">${tab.label}</div>
        </div>
      `).join('')}
    </div>
  `;

  const container = document.createElement('div');
  container.innerHTML = html;
  const nav = container.firstElementChild;

  nav.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
      nav.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
      item.classList.add('active');

      if (onTabChange) {
        onTabChange(item.dataset.tab);
      }
    });
  });

  return nav;
}

// ==================== SECTION HEADER ====================
export function createSectionHeader(title, actionText = null, onAction = null) {
  const html = `
    <style>
      .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: ${DT.spacing.lg};
        padding: 0 ${DT.spacing.lg};
      }

      .section-title {
        font-size: ${DT.typography.heading[2].size};
        font-weight: ${DT.typography.heading[2].weight};
        color: ${DT.colors.text.primary};
      }

      .section-action {
        font-size: ${DT.typography.body.small.size};
        font-weight: 600;
        color: ${DT.colors.surface.secondary};
        cursor: pointer;
        padding: ${DT.spacing.sm} ${DT.spacing.md};
        border-radius: ${DT.radius.md};
        transition: all ${DT.transitions.fast};
      }

      .section-action:active {
        background: rgba(139, 92, 246, 0.15);
      }
    </style>

    <div class="section-header">
      <h2 class="section-title">${title}</h2>
      ${actionText ? `<button class="section-action">${actionText}</button>` : ''}
    </div>
  `;

  const container = document.createElement('div');
  container.innerHTML = html;
  const header = container.firstElementChild;

  if (onAction && actionText) {
    header.querySelector('.section-action').addEventListener('click', onAction);
  }

  return header;
}

export default {
  createCard,
  createBalanceCard,
  createStatCard,
  createQuickActionButton,
  createNFTCard,
  createActivityItem,
  createBottomNav,
  createSectionHeader,
};
