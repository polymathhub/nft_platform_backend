/**
 * Marketplace Module
 * Independent marketplace initialization and functionality
 * Does NOT require TON Connect authentication
 * @module js/marketplace.js
 */

import { api, endpoints } from './api.js';

class MarketplaceManager {
  constructor() {
    this.isInitialized = false;
    this.page = 1;
    this.listings = [];
    this.socket = null;
  }

  /**
   * Initialize marketplace independently
   * Accessible without authentication
   */
  async initialize() {
    try {
      console.log('🏪 Initializing Marketplace (independent from auth)...');
      
      // Load initial listings
      await this.loadListings();
      
      this.isInitialized = true;
      console.log('✅ Marketplace initialized successfully');
      return true;
    } catch (error) {
      console.error('Marketplace initialization error:', error);
      return false;
    }
  }

  /**
   * Load listings from backend
   * Public endpoint - no authentication required
   */
  async loadListings(page = 1, limit = 50) {
    try {
      const skip = (page - 1) * limit;
      const response = await api.get(
        `${endpoints.marketplace.listings}?skip=${skip}&limit=${limit}`
      );
      
      this.listings = response.items || response;
      this.page = page;
      
      console.log(`📊 Loaded ${this.listings.length} listings`);
      return this.listings;
    } catch (error) {
      console.error('Error loading listings:', error);
      // Don't throw - allow marketplace to load even if backend is unavailable
      return [];
    }
  }

  /**
   * Get listing details
   */
  async getListingDetails(listingId) {
    try {
      return await api.get(`${endpoints.marketplace.listings}/${listingId}`);
    } catch (error) {
      console.error('Error fetching listing details:', error);
      return null;
    }
  }

  /**
   * Check if user is authenticated (optional)
   * Needed for authenticated marketplace operations (buy, offer, etc.)
   */
  isUserAuthenticated() {
    // Check if user has valid token
    try {
      const token = localStorage.getItem('token');
      return !!token;
    } catch {
      return false;
    }
  }

  /**
   * For authenticated users only: Create listing
   */
  async createListing(nftId, price, currency = 'STARS') {
    if (!this.isUserAuthenticated()) {
      throw new Error('Authentication required to create listing');
    }
    
    try {
      return await api.post(endpoints.marketplace.listings, {
        nft_id: nftId,
        price,
        currency,
        blockchain: 'ethereum',
      });
    } catch (error) {
      console.error('Error creating listing:', error);
      throw error;
    }
  }

  /**
   * For authenticated users only: Buy NFT
   */
  async buyNow(listingId) {
    if (!this.isUserAuthenticated()) {
      throw new Error('Authentication required to purchase');
    }
    
    try {
      return await api.post(
        `${endpoints.marketplace.listings}/${listingId}/buy-now`,
        {}
      );
    } catch (error) {
      console.error('Error purchasing NFT:', error);
      throw error;
    }
  }

  /**
   * For authenticated users only: Make offer
   */
  async makeOffer(listingId, offerPrice) {
    if (!this.isUserAuthenticated()) {
      throw new Error('Authentication required to make offer');
    }
    
    try {
      return await api.post(
        `${endpoints.marketplace.listings}/${listingId}/offer`,
        { offer_price: offerPrice }
      );
    } catch (error) {
      console.error('Error making offer:', error);
      throw error;
    }
  }

  /**
   * Setup real-time updates
   * Optional WebSocket connection for live price updates
   */
  connectRealtimeUpdates(onUpdate) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/ws/marketplace`;
    
    try {
      this.socket = new WebSocket(wsUrl);
      
      this.socket.onopen = () => {
        console.log('📡 Real-time marketplace updates enabled');
      };
      
      this.socket.onmessage = (event) => {
        try {
          const update = JSON.parse(event.data);
          if (onUpdate) onUpdate(update);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
      
      this.socket.onerror = (error) => {
        console.warn('WebSocket error:', error);
      };
      
      this.socket.onclose = () => {
        console.log('📡 Real-time updates disconnected');
      };
    } catch (error) {
      console.warn('WebSocket connection failed:', error);
    }
  }

  /**
   * Disconnect from real-time updates
   */
  disconnectRealtimeUpdates() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }
}

export const marketplace = new MarketplaceManager();
