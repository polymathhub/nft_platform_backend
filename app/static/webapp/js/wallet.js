/**
 * Wallet Module
 * Handles Web3 wallet connection, signing transactions, and blockchain interactions
 * @module js/wallet
 */

import { api, endpoints } from '/webapp/static/js/api.js';

class WalletManager {
  constructor() {
    this.connected = false;
    this.walletAddress = null;
    this.network = null;
    this.balance = '0';
    this.provider = null;
    this.detectedWallets = [];
    this.initializeWalletDetection();
  }

  /**
   * Detect available wallets (MetaMask, Phantom, etc.)
   * @private
   */
  initializeWalletDetection() {
    // Check for Ethereum/EVM wallets
    if (window.ethereum) {
      this.detectedWallets.push({
        name: 'MetaMask',
        provider: window.ethereum,
        type: 'evm',
      });
    }

    // Check for Solana wallets
    if (window.solana) {
      this.detectedWallets.push({
        name: 'Phantom',
        provider: window.solana,
        type: 'solana',
      });
    }

    // Setup event listeners
    this.setupEventListeners();
  }

  /**
   * Setup wallet event listeners
   * @private
   */
  setupEventListeners() {
    if (window.ethereum) {
      window.ethereum.on('accountsChanged', (accounts) => {
        this.dispatchEvent('wallet:accountsChanged', { accounts });
        if (accounts.length === 0) {
          this.connected = false;
          this.walletAddress = null;
        }
      });

      window.ethereum.on('chainChanged', (chainId) => {
        this.dispatchEvent('wallet:chainChanged', { chainId });
      });

      window.ethereum.on('connect', (connectInfo) => {
        this.dispatchEvent('wallet:connected', { connectInfo });
      });

      window.ethereum.on('disconnect', () => {
        this.dispatchEvent('wallet:disconnected');
        this.connected = false;
      });
    }
  }

  /**
   * Connect to wallet
   */
  async connect(walletName) {
    try {
      const wallet = this.detectedWallets.find(w => w.name === walletName);
      if (!wallet) {
        throw new Error(`Wallet ${walletName} not found`);
      }

      this.provider = wallet.provider;

      if (wallet.type === 'evm') {
        return await this.connectEVM();
      } else if (wallet.type === 'solana') {
        return await this.connectSolana();
      }

      throw new Error('Unknown wallet type');
    } catch (error) {
      this.dispatchEvent('wallet:error', { error: error.message });
      throw error;
    }
  }

  /**
   * Connect to EVM-compatible wallet (MetaMask, etc.)
   * @private
   */
  async connectEVM() {
    try {
      const accounts = await this.provider.request({
        method: 'eth_requestAccounts',
      });

      if (!accounts || accounts.length === 0) {
        throw new Error('No accounts returned');
      }

      this.walletAddress = accounts[0];
      this.connected = true;

      // Get network info
      const chainId = await this.provider.request({ method: 'eth_chainId' });
      this.network = this.parseChainId(chainId);

      // Get balance
      await this.getBalance();

      // Register wallet on backend
      await this.registerWallet();

      this.dispatchEvent('wallet:connected', {
        address: this.walletAddress,
        network: this.network,
        balance: this.balance,
      });

      return {
        address: this.walletAddress,
        network: this.network,
        balance: this.balance,
      };
    } catch (error) {
      throw new Error(`EVM connection failed: ${error.message}`);
    }
  }

  /**
   * Connect to Solana wallet
   * @private
   */
  async connectSolana() {
    try {
      const response = await this.provider.connect();
      this.walletAddress = response.publicKey.toString();
      this.connected = true;
      this.network = 'solana-mainnet';

      // Register wallet on backend
      await this.registerWallet();

      this.dispatchEvent('wallet:connected', {
        address: this.walletAddress,
        network: this.network,
      });

      return {
        address: this.walletAddress,
        network: this.network,
      };
    } catch (error) {
      throw new Error(`Solana connection failed: ${error.message}`);
    }
  }

  /**
   * Register wallet on backend
   * @private
   */
  async registerWallet() {
    try {
      await api.post(endpoints.wallets.connect, {
        address: this.walletAddress,
        blockchain: this.network || 'ethereum',
      });
    } catch (error) {
      console.error('Failed to register wallet on backend:', error);
      // Don't throw - wallet connection is still valid
    }
  }

  /**
   * Get wallet balance
   */
  async getBalance() {
    try {
      if (!this.connected) {
        throw new Error('Wallet not connected');
      }

      if (this.provider === window.ethereum) {
        const balanceHex = await this.provider.request({
          method: 'eth_getBalance',
          params: [this.walletAddress, 'latest'],
        });

        this.balance = this.formatBalance(balanceHex);
      } else if (this.provider === window.solana) {
        // For Solana, get from backend or provider
        const balance = await this.provider.connection.getBalance(
          new window.solana.PublicKey(this.walletAddress)
        );
        this.balance = (balance / 1e9).toString(); // Convert lamports to SOL
      }

      return this.balance;
    } catch (error) {
      console.error('Failed to get balance:', error);
      return '0';
    }
  }

  /**
   * Sign message (for authentication)
   */
  async signMessage(message) {
    try {
      if (!this.connected) {
        throw new Error('Wallet not connected');
      }

      if (!this.provider) {
        throw new Error('No wallet provider available');
      }

      let signature;

      // EVM signing
      if (this.provider === window.ethereum) {
        signature = await this.provider.request({
          method: 'personal_sign',
          params: [message, this.walletAddress],
        });
      }
      // Solana signing
      else if (this.provider === window.solana) {
        const messageBytes = new TextEncoder().encode(message);
        const result = await this.provider.signMessage(messageBytes);
        signature = Buffer.from(result.signature).toString('hex');
      }

      return signature;
    } catch (error) {
      throw new Error(`Failed to sign message: ${error.message}`);
    }
  }

  /**
   * Send transaction
   */
  async sendTransaction(to, amount, data = null) {
    try {
      if (!this.connected) {
        throw new Error('Wallet not connected');
      }

      if (this.provider === window.ethereum) {
        return await this.sendEVMTransaction(to, amount, data);
      } else if (this.provider === window.solana) {
        return await this.sendSolanaTransaction(to, amount);
      }

      throw new Error('Unknown wallet type');
    } catch (error) {
      this.dispatchEvent('wallet:error', { error: error.message });
      throw error;
    }
  }

  /**
   * Send EVM transaction
   * @private
   */
  async sendEVMTransaction(to, amount, data) {
    try {
      const amountWei = this.toWei(amount);

      const txParams = {
        from: this.walletAddress,
        to: String(to),
        value: amountWei,
      };

      if (data) {
        txParams.data = String(data);
      }

      const txHash = await this.provider.request({
        method: 'eth_sendTransaction',
        params: [txParams],
      });

      this.dispatchEvent('wallet:transactionSent', { txHash });
      return txHash;
    } catch (error) {
      throw new Error(`Failed to send transaction: ${error.message}`);
    }
  }

  /**
   * Send Solana transaction
   * @private
   */
  async sendSolanaTransaction(to, amount) {
    try {
      // This is simplified - full implementation would use @solana/web3.js
      throw new Error('Solana transactions require @solana/web3.js library');
    } catch (error) {
      throw new Error(`Failed to send Solana transaction: ${error.message}`);
    }
  }

  /**
   * Mint NFT (calls backend)
   */
  async mintNFT(nftData) {
    try {
      if (!this.connected) {
        throw new Error('Wallet not connected');
      }

      if (!nftData || typeof nftData !== 'object') {
        throw new Error('Invalid NFT data');
      }

      const response = await api.post(endpoints.nfts.create, {
        walletAddress: this.walletAddress,
        network: this.network,
        ...nftData,
      });

      this.dispatchEvent('wallet:nftMinted', { nft: response });
      return response;
    } catch (error) {
      throw new Error(`Failed to mint NFT: ${error.message}`);
    }
  }

  /**
   * Disconnect wallet
   */
  async disconnect() {
    try {
      if (this.walletAddress) {
        await api.post(endpoints.wallets.disconnect(this.walletAddress), {});
      }

      this.connected = false;
      this.walletAddress = null;
      this.network = null;
      this.balance = '0';
      this.provider = null;

      this.dispatchEvent('wallet:disconnected');
    } catch (error) {
      console.error('Disconnect error:', error);
    }
  }

  /**
   * Parse chain ID to network name
   * @private
   */
  parseChainId(chainId) {
    const chains = {
      '0x1': 'ethereum-mainnet',
      '0x5': 'ethereum-goerli',
      '0x38': 'binance-mainnet',
      '0x89': 'polygon-mainnet',
      '0xa4b1': 'arbitrum-mainnet',
      '0xa': 'optimism-mainnet',
    };

    return chains[chainId] || `chain-${chainId}`;
  }

  /**
   * Convert Ether to Wei
   * @private
   */
  toWei(eth) {
    return (BigInt(Math.floor(parseFloat(eth) * 1e6)) * BigInt(1e12)).toString();
  }

  /**
   * Format balance from Wei to Ether
   * @private
   */
  formatBalance(balanceHex) {
    const wei = BigInt(balanceHex);
    const ether = wei / BigInt(1e18);
    return ether.toString();
  }

  /**
   * Get detected wallets
   */
  getDetectedWallets() {
    return this.detectedWallets;
  }

  /**
   * Check if connected
   */
  isConnected() {
    return this.connected;
  }

  /**
   * Get wallet address
   */
  getAddress() {
    return this.walletAddress;
  }

  /**
   * Dispatch wallet events
   * @private
   */
  dispatchEvent(eventName, detail = {}) {
    window.dispatchEvent(new CustomEvent(eventName, { detail }));
  }
}

// Global wallet manager instance
export const wallet = new WalletManager();

export default wallet;
