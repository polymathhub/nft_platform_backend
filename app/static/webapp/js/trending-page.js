/**
 * Trending Page JavaScript
 * Handles tab navigation, data fetching, and rendering of trending NFTs and collections
 */

class TrendingPage {
  constructor() {
    this.currentTab = 'trending-nfts';
    this.trendingNFTs = [];
    this.trendingCollections = [];
    this.floorPrices = [];
    this.volumeData = [];
    this.init();
  }

  init() {
    this.setupTabs();
    this.setupRefreshButton();
    this.loadTrendingNFTs();
  }

  setupTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
      btn.addEventListener('click', () => this.switchTab(btn));
    });
  }

  setupRefreshButton() {
    // Optional refresh button if we want to add it later
  }

  async switchTab(btn) {
    // Remove active from all buttons
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

    // Add active to clicked button
    btn.classList.add('active');
    const tabId = btn.getAttribute('data-tab');
    document.getElementById(tabId).classList.add('active');

    this.currentTab = tabId;

    // Load data based on tab
    switch (tabId) {
      case 'trending-nfts':
        if (this.trendingNFTs.length === 0) {
          await this.loadTrendingNFTs();
        }
        break;
      case 'trending-collections':
        if (this.trendingCollections.length === 0) {
          await this.loadTrendingCollections();
        }
        break;
      case 'floor-prices':
        if (this.floorPrices.length === 0) {
          await this.loadFloorPrices();
        }
        break;
      case 'volume':
        if (this.volumeData.length === 0) {
          await this.loadVolumeData();
        }
        break;
    }
  }

  async loadTrendingNFTs() {
    const container = document.getElementById('trending-nfts-list');
    container.innerHTML = '<div class="loading"></div>';

    try {
      let response;
      try {
        const { telegramFetch } = await import('./telegram-fetch.js');
        response = await telegramFetch('/api/v1/trending/nfts?skip=0&limit=20&days=7&sort_by=sales');
      } catch (importErr) {
        const initData = window.Telegram?.WebApp?.initData || '';
        response = await fetch('/api/v1/trending/nfts?skip=0&limit=20&days=7&sort_by=sales', {
          headers: {
            'Content-Type': 'application/json',
            ...(initData && { 'X-Telegram-Init-Data': initData })
          },
        });
      }

      if (!response.ok) {
        throw new Error(`Failed to fetch trending NFTs: ${response.status}`);
      }

      const data = await response.json();
      this.trendingNFTs = data.items || [];

      if (this.trendingNFTs.length === 0) {
        container.innerHTML = `
          <div class="empty-state">
            <div class="empty-state-icon">📭</div>
            <p>No trending NFTs found</p>
          </div>
        `;
        return;
      }

      container.innerHTML = this.trendingNFTs.map(nft => `
        <div class="trending-item" onclick="trendingPage.openNFT('${nft.id}')">
          <div class="trending-item-image">
            ${nft.image_url ? `<img src="${nft.image_url}" alt="${nft.name}" onerror="this.src='📷'">` : '🖼️'}
          </div>
          <div class="trending-item-info">
            <div class="trending-item-title">${nft.name}</div>
            <div class="trending-item-meta">${nft.sale_count} sales</div>
            <div class="trending-item-price">${nft.total_volume.toFixed(2)} VOL</div>
          </div>
        </div>
      `).join('');
    } catch (error) {
      console.error('Error loading trending NFTs:', error);
      container.innerHTML = `
        <div class="error-state">
          <strong>Failed to load trending NFTs</strong>
          <p>${error.message}</p>
          <button onclick="trendingPage.loadTrendingNFTs()">Retry</button>
        </div>
      `;
    }
  }

  async loadTrendingCollections() {
    const container = document.getElementById('trending-collections-list');
    container.innerHTML = '<div class="loading"></div>';

    try {
      let response;
      try {
        const { telegramFetch } = await import('./telegram-fetch.js');
        response = await telegramFetch('/api/v1/trending/collections?skip=0&limit=20&days=7&sort_by=volume');
      } catch (importErr) {
        const initData = window.Telegram?.WebApp?.initData || '';
        response = await fetch('/api/v1/trending/collections?skip=0&limit=20&days=7&sort_by=volume', {
          headers: {
            'Content-Type': 'application/json',
            ...(initData && { 'X-Telegram-Init-Data': initData })
          },
        });
      }

      if (!response.ok) {
        throw new Error(`Failed to fetch trending collections: ${response.status}`);
      }

      const data = await response.json();
      this.trendingCollections = data.items || [];

      if (this.trendingCollections.length === 0) {
        container.innerHTML = `
          <div class="empty-state">
            <div class="empty-state-icon">📭</div>
            <p>No trending collections found</p>
          </div>
        `;
        return;
      }

      container.innerHTML = this.trendingCollections.map(col => `
        <div class="floor-price-item" onclick="trendingPage.openCollection('${col.id}')">
          <div class="floor-price-image">
            ${col.image_url ? `<img src="${col.image_url}" alt="${col.name}" onerror="this.src='🖼️'">` : '🎨'}
          </div>
          <div class="floor-price-info">
            <h3>${col.name}</h3>
            <p>${col.sale_count} sales last 7d</p>
          </div>
          <div class="floor-price-value">
            <div class="price">Ⓟ ${col.floor_price.toFixed(2)}</div>
            <div class="count">${col.total_volume.toFixed(0)} vol</div>
          </div>
        </div>
      `).join('');
    } catch (error) {
      console.error('Error loading trending collections:', error);
      container.innerHTML = `
        <div class="error-state">
          <strong>Failed to load trending collections</strong>
          <p>${error.message}</p>
          <button onclick="trendingPage.loadTrendingCollections()">Retry</button>
        </div>
      `;
    }
  }

  async loadFloorPrices() {
    const container = document.getElementById('floor-prices-list');
    container.innerHTML = '<div class="loading"></div>';

    try {
      let response;
      try {
        const { telegramFetch } = await import('./telegram-fetch.js');
        response = await telegramFetch('/api/v1/trending/floor-prices?skip=0&limit=50');
      } catch (importErr) {
        const initData = window.Telegram?.WebApp?.initData || '';
        response = await fetch('/api/v1/trending/floor-prices?skip=0&limit=50', {
          headers: {
            'Content-Type': 'application/json',
            ...(initData && { 'X-Telegram-Init-Data': initData })
          },
        });
      }

      if (!response.ok) {
        throw new Error(`Failed to fetch floor prices: ${response.status}`);
      }

      const data = await response.json();
      this.floorPrices = data.items || [];

      if (this.floorPrices.length === 0) {
        container.innerHTML = `
          <div class="empty-state">
            <div class="empty-state-icon">💰</div>
            <p>No collections found</p>
          </div>
        `;
        return;
      }

      container.innerHTML = this.floorPrices.map(col => `
        <div class="floor-price-item" onclick="trendingPage.openCollection('${col.id}')">
          <div class="floor-price-image">
            ${col.image_url ? `<img src="${col.image_url}" alt="${col.name}" onerror="this.src='🖼️'">` : '🎨'}
          </div>
          <div class="floor-price-info">
            <h3>${col.name}</h3>
            <p>${col.nft_count} NFTs • ${col.total_sales} sales</p>
          </div>
          <div class="floor-price-value">
            <div class="price">Ⓟ ${col.floor_price.toFixed(2)}</div>
            <div class="count">Avg: ${col.average_price.toFixed(2)}</div>
          </div>
        </div>
      `).join('');
    } catch (error) {
      console.error('Error loading floor prices:', error);
      container.innerHTML = `
        <div class="error-state">
          <strong>Failed to load floor prices</strong>
          <p>${error.message}</p>
          <button onclick="trendingPage.loadFloorPrices()">Retry</button>
        </div>
      `;
    }
  }

  async loadVolumeData() {
    const container = document.getElementById('volume-chart');
    const statsContainer = document.getElementById('volume-stats');
    container.innerHTML = '<div class="loading"></div>';

    try {
      let response;
      try {
        const { telegramFetch } = await import('./telegram-fetch.js');
        response = await telegramFetch('/api/v1/trending/volume?days=7&group_by=day');
      } catch (importErr) {
        const initData = window.Telegram?.WebApp?.initData || '';
        response = await fetch('/api/v1/trending/volume?days=7&group_by=day', {
          headers: {
            'Content-Type': 'application/json',
            ...(initData && { 'X-Telegram-Init-Data': initData })
          },
        });
      }

      if (!response.ok) {
        throw new Error(`Failed to fetch volume data: ${response.status}`);
      }

      const data = await response.json();
      this.volumeData = data.data || [];

      if (this.volumeData.length === 0) {
        container.innerHTML = `
          <div class="empty-state">
            <div class="empty-state-icon">📊</div>
            <p>No volume data available</p>
          </div>
        `;
        return;
      }

      // Find max volume for scaling
      const maxVolume = Math.max(...this.volumeData.map(v => v.total_volume));
      const scale = 200 / maxVolume; // Scale to 200px max height

      container.innerHTML = this.volumeData.map(vol => {
        const height = Math.max((vol.total_volume * scale), 10);
        return `
          <div class="chart-bar" style="height: ${height}px;" 
               data-value="${vol.period}: ${vol.total_volume.toFixed(0)}">
          </div>
        `;
      }).join('');

      // Add statistics
      const totalVolume = this.volumeData.reduce((sum, v) => sum + v.total_volume, 0);
      const avgVolume = totalVolume / this.volumeData.length;
      const totalTransactions = this.volumeData.reduce((sum, v) => sum + v.transaction_count, 0);
      const avgPrice = this.volumeData.reduce((sum, v) => sum + v.average_price, 0) / this.volumeData.length;

      statsContainer.innerHTML = `
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 16px;">
          <div style="background: var(--bg-secondary); padding: 12px; border-radius: 8px; text-align: center;">
            <div style="font-size: 12px; color: var(--text-secondary);">Total Volume</div>
            <div style="font-size: 18px; font-weight: 700; color: var(--color-accent);">Ⓟ ${totalVolume.toFixed(0)}</div>
          </div>
          <div style="background: var(--bg-secondary); padding: 12px; border-radius: 8px; text-align: center;">
            <div style="font-size: 12px; color: var(--text-secondary);">Transactions</div>
            <div style="font-size: 18px; font-weight: 700; color: var(--color-primary);">${totalTransactions}</div>
          </div>
          <div style="background: var(--bg-secondary); padding: 12px; border-radius: 8px; text-align: center;">
            <div style="font-size: 12px; color: var(--text-secondary);">Avg Volume/Day</div>
            <div style="font-size: 18px; font-weight: 700; color: var(--color-primary);">Ⓟ ${avgVolume.toFixed(0)}</div>
          </div>
          <div style="background: var(--bg-secondary); padding: 12px; border-radius: 8px; text-align: center;">
            <div style="font-size: 12px; color: var(--text-secondary);">Avg Price</div>
            <div style="font-size: 18px; font-weight: 700; color: var(--color-accent);">Ⓟ ${avgPrice.toFixed(2)}</div>
          </div>
        </div>
      `;
    } catch (error) {
      console.error('Error loading volume data:', error);
      container.innerHTML = `
        <div class="error-state">
          <strong>Failed to load volume data</strong>
          <p>${error.message}</p>
          <button onclick="trendingPage.loadVolumeData()">Retry</button>
        </div>
      `;
    }
  }

  openNFT(nftId) {
    if (!nftId) {
      console.error('[TrendingPage] Invalid NFT ID');
      return;
    }
    window.location.href = `/webapp/nft-detail.html?id=${nftId}`;
  }

  openCollection(collectionId) {
    if (!collectionId) {
      console.error('[TrendingPage] Invalid collection ID');
      return;
    }
    window.location.href = `/webapp/marketplace.html?collection=${collectionId}`;
  }
}

// Initialize page when DOM is ready
let trendingPage;
document.addEventListener('DOMContentLoaded', () => {
  trendingPage = new TrendingPage();
});
