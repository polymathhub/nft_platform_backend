/**
 * ═══════════════════════════════════════════════════════════════════════════════
 * TON SMART CONTRACTS - Contract Interaction Helpers
 * ═══════════════════════════════════════════════════════════════════════════════
 * 
 * Provides high-level abstractions for TON smart contract interactions:
 * ✅ NFT Collection operations (mint, metadata)
 * ✅ NFT Item operations (transfer, burn, metadata)
 * ✅ Marketplace operations (buy, offer, list)
 * ✅ Token operations (Jetton transfers)
 * ✅ Standard address & amount validation
 * ✅ Contract call payload building
 * 
 * TEP Compliance:
 * - TEP-62: NFT Standard (Collection, Item, Royalty)
 * - TEP-64: Metadata Schema
 * - TEP-89: Wallet Contract Interface
 * 
 * Usage:
 *   const nftOps = new NFTCollectionOps(addresses.collection);
 *   const payload = nftOps.buildMintPayload(metadata);
 *   
 *   const itemOps = new NFTItemOps(nftAddress);
 *   const txPayload = itemOps.buildTransferPayload(newOwner);
 * ═══════════════════════════════════════════════════════════════════════════════
 */

// ═══════════════════════════════════════════════════════════════════════════════
// ADDRESS & VALIDATION UTILITIES
// ═══════════════════════════════════════════════════════════════════════════════

class TONAddressValidator {
  // TON address format: base64url encoded 36 bytes (32-byte hash + 4-byte flags)
  static TON_ADDRESS_REGEX = /^[A-Za-z0-9_-]{48}$/;

  static validate(address) {
    if (!address || typeof address !== 'string') {
      return { valid: false, error: 'Address must be a string' };
    }

    address = address.trim();

    // Check format (USDT format)
    if (!this.TON_ADDRESS_REGEX.test(address)) {
      return { valid: false, error: 'Invalid TON address format' };
    }

    // Check workchain (first 48 chars, standard workchain 0)
    if (!address.startsWith('UQ')) {
      return { valid: false, error: 'Invalid workchain' };
    }

    return { valid: true };
  }

  static normalize(address) {
    const validation = this.validate(address);
    if (!validation.valid) throw new Error(validation.error);
    return address.trim();
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// AMOUNT CONVERSIONS
// ═══════════════════════════════════════════════════════════════════════════════

class TONAmountConverter {
  static TON_DECIMALS = 9;

  // TON to nanoTON
  static toNanoTON(tonAmount) {
    if (typeof tonAmount === 'string') {
      tonAmount = parseFloat(tonAmount);
    }
    if (tonAmount < 0 || isNaN(tonAmount)) {
      throw new Error('Invalid TON amount');
    }
    const nano = Math.floor(tonAmount * Math.pow(10, this.TON_DECIMALS));
    return nano.toString();
  }

  // nanoTON to TON
  static fromNanoTON(nanoAmount) {
    if (typeof nanoAmount === 'string') {
      nanoAmount = BigInt(nanoAmount);
    }
    if (typeof nanoAmount === 'number') {
      nanoAmount = BigInt(nanoAmount);
    }
    const ton = Number(nanoAmount) / Math.pow(10, this.TON_DECIMALS);
    return ton.toFixed(9).replace(/0+$/, '').replace(/\.$/, '');
  }

  // Jetton amount handling (assumes 9 decimals, customizable)
  static toJettonAmount(amount, decimals = 9) {
    if (typeof amount === 'string') {
      amount = parseFloat(amount);
    }
    const jetton = Math.floor(amount * Math.pow(10, decimals));
    return jetton.toString();
  }

  static formatTON(nanoAmount) {
    const ton = this.fromNanoTON(nanoAmount);
    return `${ton} TON`;
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// NFT COLLECTION OPERATIONS (TEP-62)
// ═══════════════════════════════════════════════════════════════════════════════

class NFTCollectionOps {
  #collectionAddress;
  #owner = null;
  #nextItemIndex = 0;

  constructor(collectionAddress) {
    const validation = TONAddressValidator.validate(collectionAddress);
    if (!validation.valid) {
      throw new Error(`Invalid collection address: ${validation.error}`);
    }
    this.#collectionAddress = collectionAddress;
  }

  /**
   * Build mint payload (Operation 0x1674C6E3 = mint)
   * TEP-62: https://github.com/ton-blockchain/TEPs/blob/master/text/0062-nft-standard.md
   */
  buildMintPayload(params) {
    const {
      to, // Address to receive NFT
      content, // Cell with NFT metadata (TEP-64)
      royaltyPercent = 0, // 0-10000 (where 10000 = 100%)
      queryId = 0,
    } = params;

    if (!to) throw new Error('Mint: missing "to" address');
    if (!content) throw new Error('Mint: missing "content" (metadata)');
    if (royaltyPercent < 0 || royaltyPercent > 10000) {
      throw new Error('Mint: royalty must be 0-10000');
    }

    // Simplified payload structure (for production, use @ton/core)
    // In real implementation, this would be proper BOC-encoded
    const payload = {
      op: 'mint',
      queryId: queryId.toString(),
      itemIndex: this.#nextItemIndex++,
      amount: '1500000000', // 1.5 TON (should be from wallet)
      owner: to,
      content: content,
      royaltyPercent: royaltyPercent,
    };

    return this._encodePayload(payload);
  }

  /**
   * Build change owner payload (Operation 0x3d0b0f0f)
   */
  buildChangeOwnerPayload(newOwner) {
    const validation = TONAddressValidator.validate(newOwner);
    if (!validation.valid) {
      throw new Error(`Invalid new owner address: ${validation.error}`);
    }

    const payload = {
      op: 'change_owner',
      newOwner: newOwner,
    };

    return this._encodePayload(payload);
  }

  /**
   * Build royalty parameters payload (Operation 0x2fc73cf0)
   */
  buildRoyaltyPayload(params) {
    const { numerator, denominator, destination } = params;

    if (!destination) throw new Error('Royalty: missing destination address');
    if (!numerator || !denominator) throw new Error('Royalty: missing numerator/denominator');

    const validation = TONAddressValidator.validate(destination);
    if (!validation.valid) {
      throw new Error(`Invalid royalty destination: ${validation.error}`);
    }

    const payload = {
      op: 'set_royalty',
      numerator,
      denominator,
      destination,
    };

    return this._encodePayload(payload);
  }

  /**
   * Get collection info
   *   Used for querying collection metadata
   */
  getInfoPayload() {
    return this._encodePayload({
      op: 'get_collection_data',
      queryId: '0',
    });
  }

  _encodePayload(data) {
    return btoa(JSON.stringify(data));
  }

  getAddress() {
    return this.#collectionAddress;
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// NFT ITEM OPERATIONS (TEP-62)
// ═══════════════════════════════════════════════════════════════════════════════

class NFTItemOps {
  #itemAddress;

  constructor(itemAddress) {
    const validation = TONAddressValidator.validate(itemAddress);
    if (!validation.valid) {
      throw new Error(`Invalid NFT address: ${validation.error}`);
    }
    this.#itemAddress = itemAddress;
  }

  /**
   * Build transfer payload (Operation 0x5fcc3d14)
   * TEP-62: Transfer NFT to new owner
   */
  buildTransferPayload(params) {
    const {
      newOwner,
      responseAddress = null,
      forwardAmount = 1000000, // 0.001 TON default
      queryId = 0,
    } = params;

    const newOwnerValidation = TONAddressValidator.validate(newOwner);
    if (!newOwnerValidation.valid) {
      throw new Error(`Invalid new owner: ${newOwnerValidation.error}`);
    }

    if (responseAddress) {
      const respValidation = TONAddressValidator.validate(responseAddress);
      if (!respValidation.valid) {
        throw new Error(`Invalid response address: ${respValidation.error}`);
      }
    }

    const payload = {
      op: 'transfer',
      queryId: queryId.toString(),
      newOwner: newOwner,
      responseAddress: responseAddress,
      forwardAmount: TONAmountConverter.toNanoTON(forwardAmount),
    };

    return this._encodePayload(payload);
  }

  /**
   * Build burn payload (Operation 0x2d364e3d)
   * Destroys NFT
   */
  buildBurnPayload(queryId = 0) {
    const payload = {
      op: 'burn',
      queryId: queryId.toString(),
    };

    return this._encodePayload(payload);
  }

  /**
   * Build edit content payload (Operation 0xd0d3d3d3)
   * Updates metadata
   */
  buildEditContentPayload(params) {
    const { content, queryId = 0 } = params;

    if (!content) throw new Error('EditContent: missing "content"');

    const payload = {
      op: 'edit_content',
      queryId: queryId.toString(),
      content: content,
    };

    return this._encodePayload(payload);
  }

  /**
   * Get NFT data
   * Returns current owner, collection, index, etc
   */
  getDataPayload() {
    return this._encodePayload({
      op: 'get_nft_data',
      queryId: '0',
    });
  }

  _encodePayload(data) {
    return btoa(JSON.stringify(data));
  }

  getAddress() {
    return this.#itemAddress;
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// MARKETPLACE OPERATIONS
// ═══════════════════════════════════════════════════════════════════════════════

class MarketplaceOps {
  #marketplaceAddress;

  constructor(marketplaceAddress) {
    const validation = TONAddressValidator.validate(marketplaceAddress);
    if (!validation.valid) {
      throw new Error(`Invalid marketplace address: ${validation.error}`);
    }
    this.#marketplaceAddress = marketplaceAddress;
  }

  /**
   * Build list NFT for sale payload
   */
  buildListPayload(params) {
    const { nftAddress, price, feeBasis = 250 } = params; // 250 = 2.5% fee

    const nftValidation = TONAddressValidator.validate(nftAddress);
    if (!nftValidation.valid) {
      throw new Error(`Invalid NFT address: ${nftValidation.error}`);
    }

    if (!price || price <= 0) {
      throw new Error('Invalid price');
    }

    const payload = {
      op: 'list',
      nft: nftAddress,
      price: TONAmountConverter.toNanoTON(price),
      feeBasis: feeBasis,
    };

    return this._encodePayload(payload);
  }

  /**
   * Build buy NFT payload
   */
  buildBuyPayload(params) {
    const { nftAddress, buyerAddress, queryId = 0 } = params;

    const nftValidation = TONAddressValidator.validate(nftAddress);
    if (!nftValidation.valid) {
      throw new Error(`Invalid NFT address: ${nftValidation.error}`);
    }

    const buyerValidation = TONAddressValidator.validate(buyerAddress);
    if (!buyerValidation.valid) {
      throw new Error(`Invalid buyer address: ${buyerValidation.error}`);
    }

    const payload = {
      op: 'buy',
      queryId: queryId.toString(),
      nft: nftAddress,
      buyer: buyerAddress,
    };

    return this._encodePayload(payload);
  }

  /**
   * Build delist payload
   */
  buildDelistPayload(nftAddress) {
    const nftValidation = TONAddressValidator.validate(nftAddress);
    if (!nftValidation.valid) {
      throw new Error(`Invalid NFT address: ${nftValidation.error}`);
    }

    const payload = {
      op: 'delist',
      nft: nftAddress,
    };

    return this._encodePayload(payload);
  }

  _encodePayload(data) {
    return btoa(JSON.stringify(data));
  }

  getAddress() {
    return this.#marketplaceAddress;
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// JETTON (TOKEN) OPERATIONS (TEP-89)
// ═══════════════════════════════════════════════════════════════════════════════

class JettonOps {
  #jettonMasterAddress;
  #decimals = 9; // Usually 9, but can vary

  constructor(jettonMasterAddress, decimals = 9) {
    const validation = TONAddressValidator.validate(jettonMasterAddress);
    if (!validation.valid) {
      throw new Error(`Invalid Jetton address: ${validation.error}`);
    }
    this.#jettonMasterAddress = jettonMasterAddress;
    this.#decimals = decimals;
  }

  /**
   * Build transfer payload (Jetton)
   */
  buildTransferPayload(params) {
    const { to, amount, forwardAmount = 0, queryId = 0 } = params;

    const toValidation = TONAddressValidator.validate(to);
    if (!toValidation.valid) {
      throw new Error(`Invalid recipient address: ${toValidation.error}`);
    }

    const payload = {
      op: 'transfer',
      queryId: queryId.toString(),
      amount: TONAmountConverter.toJettonAmount(amount, this.#decimals),
      destination: to,
      forwardAmount: TONAmountConverter.toNanoTON(forwardAmount),
    };

    return this._encodePayload(payload);
  }

  /**
   * Build burn payload
   */
  buildBurnPayload(params) {
    const { amount, queryId = 0 } = params;

    const payload = {
      op: 'burn',
      queryId: queryId.toString(),
      amount: TONAmountConverter.toJettonAmount(amount, this.#decimals),
    };

    return this._encodePayload(payload);
  }

  _encodePayload(data) {
    return btoa(JSON.stringify(data));
  }

  getAddress() {
    return this.#jettonMasterAddress;
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// METADATA BUILDER (TEP-64)
// ═══════════════════════════════════════════════════════════════════════════════

class TEP64MetadataBuilder {
  /**
   * Build TEP-64 compliant NFT metadata
   */
  static buildNFTMetadata(params) {
    const { name, description = '', image, attributes = {}, externalUrl = '' } = params;

    if (!name) throw new Error('Metadata: missing "name"');
    if (!image) throw new Error('Metadata: missing "image"');

    return {
      name: name,
      description: description,
      image: image,
      external_url: externalUrl,
      attributes: attributes,
    };
  }

  /**
   * Build collection metadata
   */
  static buildCollectionMetadata(params) {
    const { name, description = '', image, externalUrl = '' } = params;

    if (!name) throw new Error('Collection metadata: missing "name"');
    if (!image) throw new Error('Collection metadata: missing "image"');

    return {
      name: name,
      description: description,
      image: image,
      external_url: externalUrl,
    };
  }

  /**
   * Encode metadata as base64
   */
  static encodeAsJSON(metadata) {
    return btoa(JSON.stringify(metadata));
  }

  /**
   * Encode metadata as base64URL (for web)
   */
  static encodeAsBase64URL(metadata) {
    const json = JSON.stringify(metadata);
    return btoa(json)
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// EXPORT ALL CLASSES
// ═══════════════════════════════════════════════════════════════════════════════

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    TONAddressValidator,
    TONAmountConverter,
    NFTCollectionOps,
    NFTItemOps,
    MarketplaceOps,
    JettonOps,
    TEP64MetadataBuilder,
  };
}

window.TONSmartContracts = {
  TONAddressValidator,
  TONAmountConverter,
  NFTCollectionOps,
  NFTItemOps,
  MarketplaceOps,
  JettonOps,
  TEP64MetadataBuilder,
};
