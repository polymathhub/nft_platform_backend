/**
 * Activity Page JavaScript
 * Handles activity feed display with filtering and pagination
 */

class ActivityPage {
  constructor() {
    this.currentPage = 1;
    this.limit = 15;
    this.days = 7;
    this.currentFilter = 'all';
    this.activities = [];
    this.init();
  }

  init() {
    this.setupFilters();
    this.setupRefresh();
    this.loadActivityFeed();
  }

  setupFilters() {
    const filterBtns = document.querySelectorAll('.filter-btn');
    filterBtns.forEach(btn => {
      btn.addEventListener('click', () => this.applyFilter(btn));
    });
  }

  setupRefresh() {
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
      refreshBtn.addEventListener('click', () => {
        this.currentPage = 1;
        this.loadActivityFeed();
      });
    }
  }

  applyFilter(btn) {
    // Remove active from all filter buttons
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    // Get filter type
    if (btn.hasAttribute('data-days')) {
      this.days = parseInt(btn.getAttribute('data-days'));
    } else if (btn.hasAttribute('data-filter')) {
      this.currentFilter = btn.getAttribute('data-filter');
    }

    this.currentPage = 1;
    this.loadActivityFeed();
  }

  async loadActivityFeed() {
    const container = document.getElementById('activity-feed');
    container.innerHTML = '<div class="loading"></div>';

    try {
      const url = new URL('/api/v1/trending/feed', window.location.origin);
      url.searchParams.append('skip', (this.currentPage - 1) * this.limit);
      url.searchParams.append('limit', this.limit);
      url.searchParams.append('days', this.days);

      if (this.currentFilter !== 'all') {
        url.searchParams.append('activity_types', this.currentFilter === 'sale' ? 'purchase_completed' : 'nft_listed');
      }

      const response = await fetch(url.toString(), {
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch activity: ${response.status}`);
      }

      const data = await response.json();
      this.activities = data.items || [];
      const total = data.total || 0;

      if (this.activities.length === 0) {
        container.innerHTML = `
          <div class="empty-state">
            <div class="empty-state-icon">📭</div>
            <p>No activity found</p>
            <small>Try adjusting the filters</small>
          </div>
        `;
      } else {
        container.innerHTML = `<div class="timeline">${this.renderActivities()}</div>`;
      }

      this.renderPagination(total);
    } catch (error) {
      console.error('Error loading activity:', error);
      container.innerHTML = `
        <div class="error-state">
          <strong>Failed to load activity</strong>
          <p>${error.message}</p>
          <button onclick="activityPage.loadActivityFeed()">Retry</button>
        </div>
      `;
    }
  }

  renderActivities() {
    return this.activities.map((activity, index) => {
      const timestamp = new Date(activity.timestamp);
      const timeStr = this.formatTime(timestamp);
      const icon = activity.type === 'sale' ? '✓' : '📌';
      const iconClass = activity.type === 'sale' ? 'sale' : 'listing';

      return `
        <div class="activity-item">
          <div class="activity-icon ${iconClass}">${icon}</div>
          <div class="activity-content">
            <div class="activity-header">
              <span class="activity-type">
                ${activity.type === 'sale' ? '🛒 Sold' : '📌 Listed'}
              </span>
              <span class="activity-time">${timeStr}</span>
            </div>
            
            <div class="activity-nft" onclick="activityPage.openNFT('${activity.nft_id}')">
              <div class="activity-nft-image">
                ${activity.nft_image ? `<img src="${activity.nft_image}" alt="${activity.nft_name}" onerror="this.src='📷'">` : '🖼️'}
              </div>
              <div class="activity-nft-info">
                <div class="activity-nft-name">${activity.nft_name}</div>
                <div class="activity-nft-collection">NFT</div>
              </div>
            </div>

            <div style="display: flex; justify-content: space-between; align-items: center;">
              <div class="activity-details">
                <span class="activity-detail">${activity.currency}</span>
                ${activity.buyer_id ? `<span class="activity-detail">Buyer ID: ${activity.buyer_id.slice(0, 8)}...</span>` : ''}
              </div>
              <div class="activity-price">Ⓟ ${activity.price.toFixed(2)}</div>
            </div>
          </div>
        </div>
      `;
    }).join('');
  }

  renderPagination(total) {
    const container = document.getElementById('pagination');
    const totalPages = Math.ceil(total / this.limit);

    if (totalPages <= 1) {
      container.innerHTML = '';
      return;
    }

    let html = '';

    // Previous button
    if (this.currentPage > 1) {
      html += `<button onclick="activityPage.goToPage(${this.currentPage - 1})">← Prev</button>`;
    }

    // Page numbers
    for (let i = 1; i <= Math.min(totalPages, 5); i++) {
      const className = i === this.currentPage ? 'active' : '';
      html += `<button class="${className}" onclick="activityPage.goToPage(${i})">${i}</button>`;
    }

    if (totalPages > 5) {
      html += `<span style="padding: 8px;">...</span>`;
      if (this.currentPage < totalPages) {
        html += `<button onclick="activityPage.goToPage(${totalPages})">${totalPages}</button>`;
      }
    }

    // Next button
    if (this.currentPage < totalPages) {
      html += `<button onclick="activityPage.goToPage(${this.currentPage + 1})">Next →</button>`;
    }

    container.innerHTML = html;
  }

  goToPage(page) {
    this.currentPage = page;
    this.loadActivityFeed();
    window.scrollTo(0, 0);
  }

  formatTime(date) {
    const now = new Date();
    const diffMs = now - date;
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffSecs < 60) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }

  openNFT(nftId) {
    console.log('Opening NFT:', nftId);
    // TODO: Navigate to NFT detail page
    // window.location.href = `/webapp/nft-detail.html?id=${nftId}`;
    alert(`NFT ${nftId} clicked - detail view coming soon`);
  }
}

// Initialize page when DOM is ready
let activityPage;
document.addEventListener('DOMContentLoaded', () => {
  activityPage = new ActivityPage();
});
