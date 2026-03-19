import { api, endpoints } from './api.js';

class MarketplaceService {
  constructor() {
    this.listings = [];
    this.updateInterval = null;
    this.wsConnection = null;
  }

  async fetchListings(skip = 0, limit = 50, blockchain = null) {
    try {
      const params = new URLSearchParams({ skip, limit });
      if (blockchain) params.append('blockchain', blockchain);
      
      const response = await api.get(`${endpoints.marketplace.listings}?${params}`);
      this.listings = response.listings || [];
      return this.listings;
    } catch (error) {
      console.error('Error fetching listings:', error);
      return [];
    }
  }

  async fetchNFTDetails(nftId) {
    try {
      return await api.get(`${endpoints.nft.details(nftId)}`);
    } catch (error) {
      console.error('Error fetching NFT details:', error);
      return null;
    }
  }

  async createListing(nftId, price, currency = 'STARS', blockchain = 'ethereum') {
    try {
      return await api.post(endpoints.marketplace.listings, {
        nft_id: nftId,
        price,
        currency,
        blockchain,
      });
    } catch (error) {
      console.error('Error creating listing:', error);
      throw error;
    }
  }

  async cancelListing(listingId) {
    try {
      return await api.post(`${endpoints.marketplace.listings}/${listingId}/cancel`, {});
    } catch (error) {
      console.error('Error cancelling listing:', error);
      throw error;
    }
  }

  async buyNow(listingId) {
    try {
      return await api.post(`${endpoints.marketplace.listings}/${listingId}/buy-now`, {});
    } catch (error) {
      console.error('Error buying NFT:', error);
      throw error;
    }
  }

  async makeOffer(listingId, offerPrice, expiresAt = null) {
    try {
      return await api.post(`${endpoints.marketplace.listings}/${listingId}/offer`, {
        offer_price: offerPrice,
        expires_at: expiresAt,
      });
    } catch (error) {
      console.error('Error making offer:', error);
      throw error;
    }
  }

  startRealtimeUpdates(onUpdate) {
    // DISABLED: Was fetching listings every 5 seconds - WAY too aggressive
    // This caused constant network requests and UI refreshes
    // Marketplace now loads only when user navigates to the page or manually refreshes
    console.log('[Marketplace] Real-time updates disabled - using on-demand loading');
    // No interval set - call fetchListings() manually when needed instead
  }

  stopRealtimeUpdates() {
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
      this.updateInterval = null;
    }
  }

  connectWebSocket(onMessage) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/ws/marketplace`;
    
    try {
      this.wsConnection = new WebSocket(wsUrl);
      
      this.wsConnection.onopen = () => {
        console.log('WebSocket connected to marketplace feed');
      };
      
      this.wsConnection.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (onMessage) onMessage(data);
        } catch (e) {
          console.error('Error parsing WebSocket message:', e);
        }
      };
      
      this.wsConnection.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
      this.wsConnection.onclose = () => {
        console.log('WebSocket disconnected');
      };
    } catch (error) {
      console.error('Error connecting WebSocket:', error);
      this.startRealtimeUpdates(onMessage);
    }
  }

  disconnectWebSocket() {
    if (this.wsConnection) {
      this.wsConnection.close();
      this.wsConnection = null;
    }
  }
}

export const marketplaceService = new MarketplaceService();
