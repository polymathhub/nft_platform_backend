/**
 * HOME PAGE / DASHBOARD
 * Main view showing balance, stats, collection, and activity
 * Data bound to backend endpoints
 */

import DESIGN_TOKENS from './design-tokens.js';
import {
  createBalanceCard,
  createStatCard,
  createQuickActionButton,
  createNFTCard,
  createActivityItem,
  createSectionHeader,
} from './components.js';

const DT = DESIGN_TOKENS;

export class HomePage {
  constructor(apiService) {
    this.api = apiService;
    this.data = {
      wallet: null,
      stats: null,
      nfts: [],
      activities: [],
    };
  }

  async loadData() {
    try {
      const [walletRes, statsRes, nftsRes, activitiesRes] = await Promise.all([
        this.api.get('/api/v1/wallet/balance'),
        this.api.get('/api/v1/dashboard/stats'),
        this.api.get('/api/v1/nfts/user'),
        this.api.get('/api/v1/transactions/recent'),
      ]);

      this.data = {
        wallet: walletRes,
        stats: statsRes,
        nfts: nftsRes.nfts || [],
        activities: activitiesRes.transactions || [],
      };

      return this.data;
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      // Return mock data for development
      return this.getMockData();
    }
  }

  getMockData() {
    return {
      wallet: {
        balance: 12450.5,
        currency: 'USD',
        tokenBalance: 1.24,
        tokenSymbol: 'ETH',
        totalProfit: 450,
      },
      stats: {
        nftsOwned: 16,
        activeListings: 3,
        walletBalance: 1.24,
        totalProfit: 450,
      },
      nfts: [
        {
          id: '1',
          name: 'Liquid Soil',
          owner: 'Owner',
          price: 2.5,
          image: 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22200%22 height=%22200%22%3E%3Cdefs%3E%3ClinearGradient id=%22g1%22 x1=%220%25%22 y1=%220%25%22 x2=%22100%25%22 y2=%22100%25%22%3E%3Cstop offset=%220%25%22 style=%22stop-color:%236B5B95;stop-opacity:1%22 /%3E%3Cstop offset=%22100%25%22 style=%22stop-color:%238B5CF6;stop-opacity:1%22 /%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width=%22200%22 height=%22200%22 fill=%22url(%23g1)%22/%3E%3C/svg%3E',
        },
        {
          id: '2',
          name: 'Neon Dreams',
          owner: 'Owner',
          price: 3.2,
          image: 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22200%22 height=%22200%22%3E%3Cdefs%3E%3ClinearGradient id=%22g2%22 x1=%220%25%22 y1=%220%25%22 x2=%22100%25%22 y2=%22100%25%22%3E%3Cstop offset=%220%25%22 style=%22stop-color:%23EC4899;stop-opacity:1%22 /%3E%3Cstop offset=%22100%25%22 style=%22stop-color:%238B5CF6;stop-opacity:1%22 /%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width=%22200%22 height=%22200%22 fill=%22url(%23g2)%22/%3E%3C/svg%3E',
        },
      ],
      activities: [
        {
          id: '1',
          icon: '📊',
          title: 'Merged Cosmotic Cube',
          description: '3 hours ago',
          type: 'positive',
          amount: '+$150.00',
        },
        {
          id: '2',
          icon: '💰',
          title: 'Sold Atlantis #22',
          description: '5 hours ago',
          type: 'positive',
          amount: '+$3,500.00',
        },
        {
          id: '3',
          icon: '🎁',
          title: 'Received Illiminal Punk',
          description: '7 hours ago',
          type: 'neutral',
          amount: 'Received',
        },
      ],
    };
  }

  render(containerId = 'app') {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.style.cssText = `
      background: linear-gradient(180deg, ${DT.colors.background.base} 0%, ${DT.colors.background.elevated} 100%);
      min-height: 100vh;
      color: ${DT.colors.text.primary};
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      padding: 0;
      margin: 0;
    `;

    container.innerHTML = '';

    // Header
    const header = this.createHeader();
    container.appendChild(header);

    // Scroll container
    const scrollContainer = document.createElement('div');
    scrollContainer.style.cssText = `
      overflow-y: auto;
      padding-bottom: calc(${DT.navigation.bottomHeight} + ${DT.spacing.xl});
      padding-top: ${DT.spacing.lg};
    `;

    // Balance Card
    const balanceCard = createBalanceCard(
      this.data.wallet.balance,
      this.data.wallet.currency
    );
    scrollContainer.appendChild(balanceCard);

    // Stats Section
    const statsSection = this.createStatsSection();
    scrollContainer.appendChild(statsSection);

    // Quick Actions Section
    const actionsSection = this.createQuickActionsSection();
    scrollContainer.appendChild(actionsSection);

    // Collection Section
    const collectionSection = this.createCollectionSection();
    scrollContainer.appendChild(collectionSection);

    // Activity Section
    const activitySection = this.createActivitySection();
    scrollContainer.appendChild(activitySection);

    container.appendChild(scrollContainer);

    // Bottom Navigation
    const bottomNav = this.createBottomNav();
    container.appendChild(bottomNav);

    // Add padding to main container for fixed nav
    container.style.position = 'relative';
    container.style.minHeight = '100vh';
  }

  createHeader() {
    const html = `
      <style>
        .header {
          padding: ${DT.spacing.lg};
          display: flex;
          justify-content: space-between;
          align-items: center;
          border-bottom: 1px solid ${DT.colors.border.light};
        }

        .header-title {
          font-size: ${DT.typography.heading[2].size};
          font-weight: ${DT.typography.heading[2].weight};
          color: ${DT.colors.text.primary};
        }

        .header-subtitle {
          font-size: ${DT.typography.body.small.size};
          color: ${DT.colors.text.secondary};
        }

        .header-actions {
          display: flex;
          gap: ${DT.spacing.md};
        }

        .header-icon {
          width: 36px;
          height: 36px;
          border-radius: ${DT.radius.md};
          background: ${DT.colors.background.elevated};
          border: 1px solid ${DT.colors.border.light};
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          font-size: 16px;
          transition: all ${DT.transitions.fast};
        }

        .header-icon:active {
          background: ${DT.colors.background.card};
        }
      </style>

      <div class="header">
        <div>
          <div class="header-title">Welcome back, John 👋</div>
          <div class="header-subtitle">Your portfolio overview</div>
        </div>
        <div class="header-actions">
          <div class="header-icon">🔔</div>
          <div class="header-icon">⚙️</div>
        </div>
      </div>
    `;

    const container = document.createElement('div');
    container.innerHTML = html;
    return container.firstElementChild;
  }

  createStatsSection() {
    const html = `
      <style>
        .stats-container {
          padding: ${DT.spacing.lg};
        }

        .stats-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: ${DT.spacing.lg};
        }
      </style>

      <div class="stats-container">
        ${createSectionHeader('Overview').outerHTML}
        <div class="stats-grid" id="stats-grid"></div>
      </div>
    `;

    const container = document.createElement('div');
    container.innerHTML = html;

    const statsGrid = container.querySelector('#stats-grid');

    const stats = [
      {
        icon: '🖼️',
        label: 'NFTs Owned',
        value: this.data.stats.nftsOwned,
        unit: '',
      },
      {
        icon: '📈',
        label: 'Active Listings',
        value: this.data.stats.activeListings,
        unit: '',
      },
      {
        icon: '💎',
        label: 'Wallet Balance',
        value: this.data.stats.walletBalance,
        unit: 'ETH',
      },
      {
        icon: '💰',
        label: 'Total Profit',
        value: `$${this.data.stats.totalProfit}`,
        unit: 'USD',
      },
    ];

    stats.forEach(stat => {
      const card = createStatCard(stat.icon, stat.label, stat.value, stat.unit);
      statsGrid.appendChild(card);
    });

    return container;
  }

  createQuickActionsSection() {
    const html = `
      <style>
        .actions-container {
          padding: ${DT.spacing.lg};
        }

        .actions-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: ${DT.spacing.md};
        }
      </style>

      <div class="actions-container">
        ${createSectionHeader('Quick Actions').outerHTML}
        <div class="actions-grid" id="actions-grid"></div>
      </div>
    `;

    const container = document.createElement('div');
    container.innerHTML = html;

    const actionsGrid = container.querySelector('#actions-grid');

    const actions = [
      { icon: '➕', label: 'Create Wallet', action: 'create-wallet' },
      { icon: '✨', label: 'Mint NFT', action: 'mint-nft' },
      { icon: '🏪', label: 'Browse Market', action: 'browse-market' },
    ];

    actions.forEach(action => {
      const btn = createQuickActionButton(action.icon, action.label, () => {
        console.log('Action:', action.action);
      });
      actionsGrid.appendChild(btn);
    });

    return container;
  }

  createCollectionSection() {
    const html = `
      <style>
        .collection-container {
          padding: ${DT.spacing.lg};
        }

        .collection-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: ${DT.spacing.lg};
        }
      </style>

      <div class="collection-container">
        ${createSectionHeader('Your Collection', 'View All').outerHTML}
        <div class="collection-grid" id="collection-grid"></div>
      </div>
    `;

    const container = document.createElement('div');
    container.innerHTML = html;

    const collectionGrid = container.querySelector('#collection-grid');

    this.data.nfts.slice(0, 2).forEach(nft => {
      const card = createNFTCard(nft);
      collectionGrid.appendChild(card);
    });

    return container;
  }

  createActivitySection() {
    const html = `
      <style>
        .activity-container {
          padding: ${DT.spacing.lg};
        }

        .activity-list {
          background: ${DT.colors.background.card};
          border: 1px solid ${DT.colors.border.light};
          border-radius: ${DT.card.radius};
          overflow: hidden;
        }
      </style>

      <div class="activity-container">
        ${createSectionHeader('Recent Activity', 'View All').outerHTML}
        <div class="activity-list" id="activity-list"></div>
      </div>
    `;

    const container = document.createElement('div');
    container.innerHTML = html;

    const activityList = container.querySelector('#activity-list');

    this.data.activities.forEach(activity => {
      const item = createActivityItem(activity);
      activityList.appendChild(item);
    });

    return container;
  }

  createBottomNav() {
    const html = `
      <style>
        .nav-wrapper {
          background: linear-gradient(180deg, transparent 0%, ${DT.colors.background.base} 100%);
          padding: ${DT.spacing.lg} 0 0 0;
          position: fixed;
          bottom: 0;
          left: 0;
          right: 0;
          z-index: ${DT.zIndex.sticky};
        }

        .bottom-navigation {
          display: flex;
          justify-content: space-around;
          padding: ${DT.spacing.md} 0 ${DT.spacing.lg} 0;
          border-top: 1px solid ${DT.colors.border.light};
          background: ${DT.colors.background.base};
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
          font-size: 12px;
        }

        .nav-item.active {
          background: rgba(139, 92, 246, 0.15);
          border: 1px solid ${DT.colors.border.medium};
        }

        .nav-icon {
          font-size: 20px;
        }

        .nav-label {
          font-size: 11px;
          font-weight: 600;
          color: ${DT.colors.text.secondary};
        }

        .nav-item.active .nav-label {
          color: ${DT.colors.text.primary};
        }
      </style>

      <div class="nav-wrapper">
        <div class="bottom-navigation">
          <div class="nav-item active" data-page="home">
            <div class="nav-icon">🏠</div>
            <div class="nav-label">Home</div>
          </div>
          <div class="nav-item" data-page="wallet">
            <div class="nav-icon">💳</div>
            <div class="nav-label">Wallet</div>
          </div>
          <div class="nav-item" data-page="mint">
            <div class="nav-icon">✨</div>
            <div class="nav-label">Mint</div>
          </div>
          <div class="nav-item" data-page="market">
            <div class="nav-icon">🏪</div>
            <div class="nav-label">Market</div>
          </div>
          <div class="nav-item" data-page="profile">
            <div class="nav-icon">👤</div>
            <div class="nav-label">Profile</div>
          </div>
        </div>
      </div>
    `;

    const container = document.createElement('div');
    container.innerHTML = html;
    return container.firstElementChild;
  }
}

export default HomePage;
