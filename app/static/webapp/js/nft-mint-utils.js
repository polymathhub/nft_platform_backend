/**
 * NFT Minting Utilities
 * Production-grade utilities for NFT minting operations
 */

export class NFTMintingService {
  constructor(apiClient, authManager) {
    this.api = apiClient;
    this.authManager = authManager;
    this.SUPPORTED_BLOCKCHAINS = [
      { id: 'ton', name: 'TON', symbol: 'TON' },
      { id: 'ethereum', name: 'Ethereum', symbol: 'ETH' },
      { id: 'polygon', name: 'Polygon', symbol: 'MATIC' },
      { id: 'arbitrum', name: 'Arbitrum', symbol: 'ARB' },
      { id: 'optimism', name: 'Optimism', symbol: 'OP' },
      { id: 'base', name: 'Base', symbol: 'BASE' },
      { id: 'solana', name: 'Solana', symbol: 'SOL' },
      { id: 'avalanche', name: 'Avalanche', symbol: 'AVAX' }
    ];
  }

  /**
   * Get all supported blockchains
   */
  getSupportedBlockchains() {
    return this.SUPPORTED_BLOCKCHAINS;
  }

  /**
   * Get blockchains that user has wallets for
   */
  async getAvailableBlockchains() {
    try {
      const response = await this.api.get('/api/v1/wallets');
      const wallets = response.wallets || [];
      const blockchainIds = new Set(wallets.map(w => w.blockchain.toLowerCase()));
      return this.SUPPORTED_BLOCKCHAINS.filter(b => blockchainIds.has(b.id));
    } catch (error) {
      console.error('Failed to get available blockchains:', error);
      return [];
    }
  }

  /**
   * Load wallets for a specific blockchain
   */
  async loadWalletsForBlockchain(blockchain) {
    try {
      const response = await this.api.get(`/api/v1/wallets?blockchain=${blockchain}`);
      const wallets = response.wallets || [];
      
      if (wallets.length === 0) {
        throw new Error(`No wallets found for ${blockchain}. Please create one first.`);
      }

      return wallets.map(wallet => ({
        id: wallet.id,
        address: wallet.address,
        blockchain: wallet.blockchain,
        isPrimary: wallet.is_primary,
        displayAddress: `${wallet.address.slice(0, 6)}...${wallet.address.slice(-4)}`
      }));
    } catch (error) {
      throw new Error(`Failed to load wallets: ${error.message}`);
    }
  }

  /**
   * Validate file for minting
   */
  validateFile(file) {
    const validTypes = [
      'image/jpeg',
      'image/png',
      'image/gif',
      'image/webp',
      'video/mp4',
      'video/webm'
    ];

    if (!validTypes.includes(file.type)) {
      return {
        valid: false,
        error: 'Invalid file type. Supported: PNG, JPG, GIF, WebP, MP4, WebM'
      };
    }

    const maxSize = 50 * 1024 * 1024;
    if (file.size > maxSize) {
      return {
        valid: false,
        error: `File too large. Maximum: ${this.formatFileSize(maxSize)}`
      };
    }

    return { valid: true };
  }

  /**
   * Upload file to storage
   */
  async uploadFile(file) {
    const validation = this.validateFile(file);
    if (!validation.valid) {
      throw new Error(validation.error);
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/v1/images/upload', {
        method: 'POST',
        headers: {
          'X-Telegram-Init-Data': this.authManager.getTelegramInitData()
        },
        body: formData
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'File upload failed');
      }

      const data = await response.json();
      return {
        url: data.image_url || data.media_url,
        type: this.getMediaType(file.type),
        size: file.size
      };
    } catch (error) {
      throw new Error(`Upload error: ${error.message}`);
    }
  }

  /**
   * Mint NFT on blockchain
   */
  async mintNFT(payload) {
    try {
      const response = await this.api.post('/api/v1/nfts/mint', {
        wallet_id: payload.walletId,
        name: payload.name,
        description: payload.description,
        image_url: payload.imageUrl,
        royalty_percentage: payload.royaltyPercentage,
        metadata: {
          blockchain: payload.blockchain,
          ...payload.additionalMetadata
        }
      });

      return {
        id: response.id,
        globalId: response.global_nft_id,
        transactionHash: response.transaction_hash,
        status: response.status,
        contractAddress: response.contract_address,
        tokenId: response.token_id
      };
    } catch (error) {
      throw new Error(`Minting failed: ${error.message}`);
    }
  }

  /**
   * Get estimated gas fees
   */
  async getEstimatedGas(blockchain) {
    try {
      // This would call a backend endpoint if available
      // For now, return placeholder values
      const gasEstimates = {
        'ton': { gas: 0.1, unit: 'TON', note: 'Estimated' },
        'ethereum': { gas: 0.01, unit: 'ETH', note: 'Current: ~50 GWEI' },
        'polygon': { gas: 0.001, unit: 'MATIC', note: 'Current: ~50 GWEI' },
        'solana': { gas: 0.00025, unit: 'SOL', note: '~5000 lamports' },
        'arbitrum': { gas: 0.0005, unit: 'ETH', note: 'Current: ~1 GWEI' },
        'optimism': { gas: 0.0005, unit: 'ETH', note: 'Current: ~1 GWEI' },
        'base': { gas: 0.0005, unit: 'ETH', note: 'Current: ~1 GWEI' },
        'avalanche': { gas: 0.001, unit: 'AVAX', note: 'Current' }
      };
      
      return gasEstimates[blockchain] || { gas: 0, unit: '?', note: 'N/A' };
    } catch (error) {
      return null;
    }
  }

  /**
   * Get media type from MIME type
   */
  getMediaType(mimeType) {
    if (mimeType.startsWith('image/')) {
      return mimeType === 'image/gif' ? 'gif' : 'image';
    }
    if (mimeType.startsWith('video/')) {
      return 'video';
    }
    return 'unknown';
  }

  /**
   * Format file size for display
   */
  formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  }

  /**
   * Validate NFT metadata
   */
  validateMetadata(data) {
    const errors = [];

    if (!data.name || data.name.trim().length === 0) {
      errors.push('NFT name is required');
    }

    if (data.name && data.name.length > 100) {
      errors.push('NFT name must be 100 characters or less');
    }

    if (data.description && data.description.length > 500) {
      errors.push('Description must be 500 characters or less');
    }

    if (!data.blockchain) {
      errors.push('Blockchain selection is required');
    }

    if (!data.walletId) {
      errors.push('Wallet selection is required');
    }

    if (!data.imageUrl) {
      errors.push('Image/media is required');
    }

    if (typeof data.royaltyPercentage !== 'number' || data.royaltyPercentage < 0 || data.royaltyPercentage > 10) {
      errors.push('Royalty must be between 0% and 10%');
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }

  /**
   * Create preview URL for file
   */
  createPreviewUrl(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target.result);
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

  /**
   * Get transaction explorer URL
   */
  getExplorerUrl(blockchain, transactionHash) {
    const explorers = {
      'ton': `https://tonviewer.com/${transactionHash}`,
      'ethereum': `https://etherscan.io/tx/${transactionHash}`,
      'polygon': `https://polygonscan.com/tx/${transactionHash}`,
      'arbitrum': `https://arbiscan.io/tx/${transactionHash}`,
      'optimism': `https://optimistic.etherscan.io/tx/${transactionHash}`,
      'base': `https://basescan.org/tx/${transactionHash}`,
      'solana': `https://solscan.io/tx/${transactionHash}`,
      'avalanche': `https://snowtrace.io/tx/${transactionHash}`
    };

    return explorers[blockchain] || null;
  }

  /**
   * Format transaction hash for display
   */
  formatTransactionHash(hash) {
    if (!hash || hash.length < 16) return hash;
    return `${hash.slice(0, 8)}...${hash.slice(-8)}`;
  }
}

/**
 * Form state management
 */
export class FormStateManager {
  constructor() {
    this.state = {
      name: '',
      description: '',
      blockchain: '',
      wallet: '',
      royalty: 0,
      file: null,
      imageUrl: null,
      errors: {}
    };
  }

  setState(updates) {
    this.state = { ...this.state, ...updates };
  }

  getState() {
    return { ...this.state };
  }

  setError(field, message) {
    this.state.errors = { ...this.state.errors, [field]: message };
  }

  clearError(field) {
    const { [field]: _, ...rest } = this.state.errors;
    this.state.errors = rest;
  }

  clearAllErrors() {
    this.state.errors = {};
  }

  hasErrors() {
    return Object.keys(this.state.errors).length > 0;
  }

  reset() {
    this.state = {
      name: '',
      description: '',
      blockchain: '',
      wallet: '',
      royalty: 0,
      file: null,
      imageUrl: null,
      errors: {}
    };
  }
}

/**
 * Toast notification system
 */
export class ToastManager {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.toasts = new Map();
  }

  show(message, type = 'info', duration = 3000) {
    const id = Date.now().toString();
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    toast.setAttribute('role', 'status');
    toast.setAttribute('aria-live', 'polite');

    this.container.appendChild(toast);
    this.toasts.set(id, toast);

    if (duration > 0) {
      setTimeout(() => this.dismiss(id), duration);
    }

    return id;
  }

  dismiss(id) {
    const toast = this.toasts.get(id);
    if (toast) {
      toast.remove();
      this.toasts.delete(id);
    }
  }

  success(message, duration) {
    return this.show(message, 'success', duration);
  }

  error(message, duration) {
    return this.show(message, 'error', duration);
  }

  info(message, duration) {
    return this.show(message, 'info', duration);
  }

  warning(message, duration) {
    return this.show(message, 'warning', duration);
  }
}

export default {
  NFTMintingService,
  FormStateManager,
  ToastManager
};
