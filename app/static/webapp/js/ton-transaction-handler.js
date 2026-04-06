// Handles all blockchain transactions - minting, transfers, payments
// Uses TEP-62 standard for NFT contracts on TON 

class TONTransactionHandler {
  // Blockchain constants
  static #CONSTANTS = {
    TRANSFER_GAS_FEE: 1000000000n, // 1 TON in nano
    MINT_GAS_FEE: 2000000000n,     // 2 TON in nano
    MIN_BALANCE: 500000000n,        // 0.5 TON minimum
    ADDRESS_ZERO: 'UQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5H' // Standard zero address
  };

  #tonConnectManager = null;
  #tonWallet = null;
  #retryConfig = { attempts: 3, delay: 1000, backoff: 1.5 };

  constructor(tonConnectManager, tonWallet) {
    if (!tonConnectManager || !tonWallet) {
      throw new Error('TONConnectManager and TonWallet instances required');
    }

    this.#tonConnectManager = tonConnectManager;
    this.#tonWallet = tonWallet;
  }

  /**
   * CREATE NFT - Mint a new NFT via collection contract
   * 
   * Process:
   * 1. Validate metadata
   * 2. Build Collection.mint() transaction
   * 3. Estimate gas
   * 4. User signs transaction
   * 5. Broadcast to blockchain
   * 6. Track on backend
   */
  async mintNFT(collectionAddress, nftMetadata, options = {}) {
    console.log('[TX Handler] Starting NFT mint...', { collectionAddress, metadata: nftMetadata });

    try {
      // Validation
      this._validateCollectionAddress(collectionAddress);
      this._validateNFTMetadata(nftMetadata);

      if (!this.#tonConnectManager.isConnected()) {
        throw new Error('Wallet not connected');
      }

      const userAddress = this.#tonConnectManager.getAddress();

      // Build mint message for collection contract
      const mintMessage = this._buildMintMessage({
        collectionAddress,
        ownerAddress: userAddress,
        nftMetadata,
        ...options
      });

      console.log('[TX Handler] Mint message built:', mintMessage);

      // Estimate gas
      const gasEstimate = await this._estimateGasMint(nftMetadata);
      console.log('[TX Handler] Gas estimate:', gasEstimate);

      // Request signature from wallet
      const txResult = await this._sendTransaction(mintMessage);

      console.log('[TX Handler] Transaction signed:', txResult.boc);

      // Track transaction
      const txRecord = {
        type: 'mint',
        status: 'pending',
        hash: txResult.hash || null,
        collection: collectionAddress,
        owner: userAddress,
        metadata: nftMetadata,
        gasUsed: gasEstimate,
        timestamp: new Date().toISOString()
      };

      this.#tonConnectManager.addTransaction(txRecord);

      // Sync with backend
      await this._syncMintBackend({
        wallet_address: userAddress,
        collection_address: collectionAddress,
        nft_metadata: nftMetadata,
        transaction_hash: txResult.hash,
        gas_estimate: gasEstimate
      });

      return {
        success: true,
        txHash: txResult.hash,
        boc: txResult.boc,
        metadata: nftMetadata
      };
    } catch (error) {
      console.error('[TX Handler] Mint failed:', error);
      return this._handleTransactionError('mint', error);
    }
  }

  /**
   * TRANSFER NFT - Send NFT item contract to new owner
   * 
   * Process:
   * 1. Validate item address & owner
   * 2. Build Item.transfer() message
   * 3. Send ownership update to item contract
   * 4. Notify new owner
   * 5. Update backend
   */
  async transferNFT(itemAddress, newOwnerAddress, options = {}) {
    console.log('[TX Handler] Starting NFT transfer...', { itemAddress, newOwner: newOwnerAddress });

    try {
      // Validation
      this._validateItemAddress(itemAddress);
      this._validateAddress(newOwnerAddress);

      if (!this.#tonConnectManager.isConnected()) {
        throw new Error('Wallet not connected');
      }

      const currentOwner = this.#tonConnectManager.getAddress();

      // Build transfer message for item contract
      const transferMessage = this._buildTransferMessage({
        itemAddress,
        currentOwner,
        newOwner: newOwnerAddress,
        ...options
      });

      console.log('[TX Handler] Transfer message built:', transferMessage);

      // Estimate gas
      const gasEstimate = await this._estimateGasTransfer();
      console.log('[TX Handler] Gas estimate:', gasEstimate);

      // Request signature
      const txResult = await this._sendTransaction(transferMessage);

      console.log('[TX Handler] Transfer transaction signed:', txResult.boc);

      // Track transaction
      const txRecord = {
        type: 'transfer',
        status: 'pending',
        hash: txResult.hash || null,
        item: itemAddress,
        from: currentOwner,
        to: newOwnerAddress,
        gasUsed: gasEstimate,
        timestamp: new Date().toISOString()
      };

      this.#tonConnectManager.addTransaction(txRecord);

      // Sync with backend
      await this._syncTransferBackend({
        wallet_address: currentOwner,
        item_address: itemAddress,
        new_owner: newOwnerAddress,
        transaction_hash: txResult.hash
      });

      return {
        success: true,
        txHash: txResult.hash,
        boc: txResult.boc,
        from: currentOwner,
        to: newOwnerAddress
      };
    } catch (error) {
      console.error('[TX Handler] Transfer failed:', error);
      return this._handleTransactionError('transfer', error);
    }
  }

  /**
   * BUILD MINT MESSAGE - TEP-62 Collection Contract Message
   * @private
   */
  _buildMintMessage({ collectionAddress, ownerAddress, nftMetadata }) {
    return {
      address: collectionAddress,
      amount: '2000000000', // 2 TON in nano
      payload: {
        operation: 'mint', // Collection.mint()
        nextItemIndex: null, // Auto-increment on contract
        ownerAddress: ownerAddress,
        itemContentUri: nftMetadata.uri,
        itemMetadata: {
          name: nftMetadata.name,
          description: nftMetadata.description,
          image: nftMetadata.image,
          attributes: nftMetadata.attributes || []
        }
      }
    };
  }

  /**
   * BUILD TRANSFER MESSAGE - TEP-62 Item Contract Message
   * @private
   */
  _buildTransferMessage({ itemAddress, currentOwner, newOwner }) {
    return {
      address: itemAddress,
      amount: '1000000000', // 1 TON in nano
      payload: {
        operation: 'transfer', // Item.transfer()
        newOwner: newOwner,
        responseAddress: currentOwner, // Send excess back
        forwardAmount: 0
      }
    };
  }

  /**
   * SEND TRANSACTION - Via TonConnect UI
   * @private
   */
  async _sendTransaction(message) {
    if (!this.#tonWallet?.ui) {
      throw new Error('TonConnect UI not initialized');
    }

    try {
      const result = await this.#tonWallet.ui.sendTransaction({
        validUntil: Math.floor(Date.now() / 1000) + 600, // 10 min
        messages: [message]
      });

      return {
        hash: result.boc ? this._extractHashFromBoc(result.boc) : null,
        boc: result.boc
      };
    } catch (error) {
      if (error.message === 'User declined') {
        throw new Error('Transaction cancelled by user');
      }
      throw error;
    }
  }

  /**
   * ESTIMATE GAS for mint operation
   * @private
   */
  async _estimateGasMint(metadata) {
    try {
      const metadataSize = JSON.stringify(metadata).length;
      // Base fee + metadata size * 0.001 TON
      const estimate = Number(TONTransactionHandler.#CONSTANTS.MINT_GAS_FEE) + (metadataSize * 1000000);
      return estimate.toString();
    } catch (error) {
      console.warn('[TX Handler] Gas estimation failed, using default:', error);
      return TONTransactionHandler.#CONSTANTS.MINT_GAS_FEE.toString();
    }
  }

  /**
   * ESTIMATE GAS for transfer operation
   * @private
   */
  async _estimateGasTransfer() {
    return TONTransactionHandler.#CONSTANTS.TRANSFER_GAS_FEE.toString();
  }

  /**
   * VALIDATE collection address format
   * @private
   */
  _validateCollectionAddress(address) {
    if (!this._isValidTONAddress(address)) {
      throw new Error(`Invalid collection address: ${address}`);
    }
  }

  /**
   * VALIDATE item address format
   * @private
   */
  _validateItemAddress(address) {
    if (!this._isValidTONAddress(address)) {
      throw new Error(`Invalid item address: ${address}`);
    }
  }

  /**
   * VALIDATE general TON address
   * @private
   */
  _validateAddress(address) {
    if (!this._isValidTONAddress(address)) {
      throw new Error(`Invalid TON address: ${address}`);
    }
  }

  /**
   * VALIDATE NFT metadata
   * @private
   */
  _validateNFTMetadata(metadata) {
    if (!metadata.name || typeof metadata.name !== 'string') {
      throw new Error('NFT name is required');
    }

    if (!metadata.image || typeof metadata.image !== 'string') {
      throw new Error('NFT image is required');
    }

    if (metadata.name.length > 500) {
      throw new Error('NFT name too long (max 500 chars)');
    }

    if (metadata.description && metadata.description.length > 5000) {
      throw new Error('NFT description too long (max 5000 chars)');
    }
  }

  /**
   * CHECK if valid TON address format
   * @private
   */
  _isValidTONAddress(address) {
    if (!address || typeof address !== 'string') return false;
    if (address.length !== 48) return false;
    if (!address.match(/^[UQ]/)) return false;
    if (!address.match(/^[UQ0-9A-Za-z_-]+$/)) return false;
    return true;
  }

  /**
   * EXTRACT hash from BOC (Bag of Cells)
   * @private
   */
  _extractHashFromBoc(boc) {
    try {
      // BOC hash is typically the first hash of the transaction
      // This is a simplified extraction
      const hashMatch = boc.match(/([A-Fa-f0-9]{64})/);
      return hashMatch ? hashMatch[1] : null;
    } catch {
      return null;
    }
  }

  /**
   * SYNC mint operation with backend
   * @private
   */
  async _syncMintBackend(data) {
    try {
      const initData = window.Telegram?.WebApp?.initData || '';

      const response = await fetch('/api/v1/nfts/mint', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(initData && { 'X-Telegram-Init-Data': initData })
        },
        body: JSON.stringify(data)
      });

      if (!response.ok) {
        console.warn('[TX Handler] Backend mint sync failed:', response.status);
        return null;
      }

      const result = await response.json();
      console.log('[TX Handler] Backend mint sync successful');
      return result;
    } catch (error) {
      console.warn('[TX Handler] Backend mint sync error:', error);
    }
  }

  /**
   * SYNC transfer operation with backend
   * @private
   */
  async _syncTransferBackend(data) {
    try {
      const initData = window.Telegram?.WebApp?.initData || '';

      const response = await fetch('/api/v1/nfts/transfer', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(initData && { 'X-Telegram-Init-Data': initData })
        },
        body: JSON.stringify(data)
      });

      if (!response.ok) {
        console.warn('[TX Handler] Backend transfer sync failed:', response.status);
        return null;
      }

      const result = await response.json();
      console.log('[TX Handler] Backend transfer sync successful');
      return result;
    } catch (error) {
      console.warn('[TX Handler] Backend transfer sync error:', error);
    }
  }

  /**
   * HANDLE transaction errors with retry logic
   * @private
   */
  async _handleTransactionError(type, error) {
    let attempts = 0;
    let lastError = error;

    while (attempts < this.#retryConfig.attempts) {
      try {
        const delay = this.#retryConfig.delay * Math.pow(this.#retryConfig.backoff, attempts);
        console.log(`[TX Handler] Retry ${type} in ${delay}ms...`);
        await new Promise(resolve => setTimeout(resolve, delay));
        
        // Note: Actual retry logic would re-run the operation
        // For now, we propagate the error
        break;
      } catch (retryError) {
        lastError = retryError;
        attempts++;
      }
    }

    return {
      success: false,
      error: lastError.message,
      type,
      retriable: this._isRetriableError(lastError)
    };
  }

  /**
   * CHECK if error is retriable
   * @private
   */
  _isRetriableError(error) {
    const message = error.message || '';
    return message.includes('network') || 
           message.includes('timeout') || 
           message.includes('temporary');
  }
}

// Export handler
export default TONTransactionHandler;

