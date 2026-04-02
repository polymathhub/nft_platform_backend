/**
 * ═══════════════════════════════════════════════════════════════════════════════
 * TON WEB3 SYSTEM - PRODUCTION INTEGRATION GUIDE
 * ═══════════════════════════════════════════════════════════════════════════════
 * 
 * This guide shows how to integrate the professional TON Web3 system into your pages
 * 
 * Three-Layer Architecture:
 * 1. WalletManager: Session lifecycle & persistence
 * 2. TransactionEngine: Real blockchain execution  
 * 3. SmartContracts: Contract abstractions
 * ═══════════════════════════════════════════════════════════════════════════════
 */

// ═══════════════════════════════════════════════════════════════════════════════
// 1. INITIALIZATION (Call once on app startup, e.g., in index.html or main.html)
// ═══════════════════════════════════════════════════════════════════════════════

async function initializeTONSystem() {
  try {
    console.log('[TONSystem] Initializing...');
    
    // Initialize WalletManager singleton
    const walletManager = window.WalletManager.getInstance();
    const isConnected = await walletManager.initialize();
    
    console.log(`[TONSystem] Wallet status: ${isConnected ? 'Connected' : 'Not connected'}`);
    
    // Create TransactionEngine (do this once, keep reference)
    window.tonTransactionEngine = new TONTransactionEngine(walletManager);
    
    // Setup event listeners
    walletManager.on('connected', (wallet) => {
      console.log('[TONSystem] Wallet connected:', wallet.address);
      // Update UI, enable transaction buttons
      document.dispatchEvent(new CustomEvent('ton-wallet-connected', { detail: wallet }));
    });
    
    walletManager.on('disconnected', (data) => {
      console.log('[TONSystem] Wallet disconnected');
      // Update UI, disable transaction buttons
      document.dispatchEvent(new CustomEvent('ton-wallet-disconnected'));
    });
    
    walletManager.on('error', (error) => {
      console.error('[TONSystem] Wallet error:', error);
      alert(`Wallet error: ${error.message}`);
    });
    
    return { walletManager, isConnected };
  } catch (error) {
    console.error('[TONSystem] Initialization failed:', error);
    throw error;
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// 2. WALLET OPERATIONS
// ═══════════════════════════════════════════════════════════════════════════════

async function connectWallet() {
  const walletManager = window.WalletManager.getInstance();
  
  try {
    const wallet = await walletManager.connect();
    console.log('[TONSystem] Connected wallet:', wallet.address);
    return wallet;
  } catch (error) {
    console.error('[TONSystem] Connection failed:', error);
    throw error;
  }
}

async function disconnectWallet() {
  const walletManager = window.WalletManager.getInstance();
  
  try {
    await walletManager.disconnect();
    console.log('[TONSystem] Wallet disconnected');
  } catch (error) {
    console.error('[TONSystem] Disconnect failed:', error);
    throw error;
  }
}

function getConnectedWallet() {
  const walletManager = window.WalletManager.getInstance();
  return walletManager.getWallet();
}

function isWalletConnected() {
  const walletManager = window.WalletManager.getInstance();
  return walletManager.isConnected();
}

// ═══════════════════════════════════════════════════════════════════════════════
// 3. TRANSACTION OPERATIONS
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Send raw TON to an address
 * Usage: await sendTON({ to: address, amount: 5.5 })
 */
async function sendTON(params) {
  const engine = window.tonTransactionEngine;
  if (!engine) throw new Error('Transaction engine not initialized');
  
  try {
    engine.on('status', (status) => console.log('[TON Send]', status));
    
    const result = await engine.sendTransaction({
      to: params.to,
      amount: params.amount,
    });
    
    console.log('[TON Send] Success:', result.hash);
    return result;
  } catch (error) {
    console.error('[TON Send] Failed:', error);
    throw error;
  }
}

/**
 * Mint NFT on blockchain
 * Usage:
 *   const hash = await mintNFT({
 *     collectionAddress: 'UQXXXX...',
 *     metadata: {
 *       name: 'My NFT',
 *       description: 'A beautiful NFT',
 *       image: 'https://example.com/nft.jpg'
 *     },
 *     royalty: 5
 *   });
 */
async function mintNFT(params) {
  const engine = window.tonTransactionEngine;
  if (!engine) throw new Error('Transaction engine not initialized');
  
  try {
    engine.on('status', (status) => console.log('[NFT Mint]', status));
    
    const result = await engine.mintNFT({
      collectionAddress: params.collectionAddress,
      metadata: params.metadata,
      royalty: params.royalty || 0,
    });
    
    console.log('[NFT Mint] Success:', result.hash);
    return result;
  } catch (error) {
    console.error('[NFT Mint] Failed:', error);
    throw error;
  }
}

/**
 * Transfer NFT to another address
 * Usage:
 *   const hash = await transferNFT({
 *     nftAddress: 'UQXXXX...',
 *     to: 'UQYYYY...'
 *   });
 */
async function transferNFT(params) {
  const engine = window.tonTransactionEngine;
  if (!engine) throw new Error('Transaction engine not initialized');
  
  try {
    engine.on('status', (status) => console.log('[NFT Transfer]', status));
    
    const result = await engine.transferNFT({
      nftAddress: params.nftAddress,
      to: params.to,
      responseAddress: params.responseAddress,
    });
    
    console.log('[NFT Transfer] Success:', result.hash);
    return result;
  } catch (error) {
    console.error('[NFT Transfer] Failed:', error);
    throw error;
  }
}

/**
 * Buy NFT from marketplace
 * Usage:
 *   const hash = await buyNFT({
 *     listingAddress: 'UQXXXX...',
 *     nftAddress: 'UQZZZZ...',
 *     price: 10.5
 *   });
 */
async function buyNFT(params) {
  const engine = window.tonTransactionEngine;
  if (!engine) throw new Error('Transaction engine not initialized');
  
  try {
    engine.on('status', (status) => console.log('[Buy NFT]', status));
    
    const result = await engine.buyNFT({
      listingAddress: params.listingAddress,
      nftAddress: params.nftAddress,
      price: params.price,
    });
    
    console.log('[Buy NFT] Success:', result.hash);
    return result;
  } catch (error) {
    console.error('[Buy NFT] Failed:', error);
    throw error;
  }
}

/**
 * Make offer on NFT
 * Usage:
 *   const hash = await makeOffer({
 *     nftAddress: 'UQXXXX...',
 *     offerAmount: 7.5
 *   });
 */
async function makeOffer(params) {
  const engine = window.tonTransactionEngine;
  if (!engine) throw new Error('Transaction engine not initialized');
  
  try {
    engine.on('status', (status) => console.log('[Make Offer]', status));
    
    const result = await engine.makeOffer({
      nftAddress: params.nftAddress,
      offerAmount: params.offerAmount,
    });
    
    console.log('[Make Offer] Success:', result.hash);
    return result;
  } catch (error) {
    console.error('[Make Offer] Failed:', error);
    throw error;
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// 4. SMART CONTRACT HELPERS
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Example: Build NFT metadata for minting
 */
function buildNFTMetadata(params) {
  const { TEP64MetadataBuilder } = window.TONSmartContracts;
  
  return TEP64MetadataBuilder.buildNFTMetadata({
    name: params.name,
    description: params.description,
    image: params.image,
    attributes: params.attributes || {},
  });
}

/**
 * Example: Create NFT collection operator
 */
function createCollectionOperator(collectionAddress) {
  const { NFTCollectionOps } = window.TONSmartContracts;
  return new NFTCollectionOps(collectionAddress);
}

/**
 * Example: Create NFT item operator
 */
function createNFTItemOperator(itemAddress) {
  const { NFTItemOps } = window.TONSmartContracts;
  return new NFTItemOps(itemAddress);
}

/**
 * Example: Validate TON address
 */
function validateTONAddress(address) {
  const { TONAddressValidator } = window.TONSmartContracts;
  return TONAddressValidator.validate(address);
}

/**
 * Example: Convert TON amounts
 */
function convertTONAmount(tonAmount) {
  const { TONAmountConverter } = window.TONSmartContracts;
  return TONAmountConverter.toNanoTON(tonAmount);
}

// ═══════════════════════════════════════════════════════════════════════════════
// 5. COMPLETE MINT WORKFLOW (mint.html integration)
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Complete NFT minting workflow
 * This is what your mint.html form handler should call
 */
async function performNFTMint(params) {
  const {
    name,
    description,
    imageUrl,
    royalty,
    collectionAddress, // Get from your config/backend
  } = params;

  try {
    console.log('[Mint Workflow] Starting...');
    
    // Step 1: Check wallet connection
    if (!isWalletConnected()) {
      throw new Error('Please connect TON wallet first');
    }
    
    const wallet = getConnectedWallet();
    console.log('[Mint Workflow] Using wallet:', wallet.address);
    
    // Step 2: Build metadata
    const metadata = buildNFTMetadata({
      name,
      description,
      image: imageUrl,
      attributes: {
        creator: wallet.address,
        created: new Date().toISOString(),
      },
    });
    
    console.log('[Mint Workflow] Metadata prepared:', metadata);
    
    // Step 3: Send minting transaction
    const txResult = await mintNFT({
      collectionAddress: collectionAddress,
      metadata: metadata,
      royalty: royalty || 5,
    });
    
    console.log('[Mint Workflow] NFT minted on blockchain:', txResult.hash);
    
    // Step 4: Sync with backend (create NFT record)
    const { telegramFetch } = await import('./telegram-fetch.js');
    const backendResult = await telegramFetch('/api/v1/nfts/mint', {
      method: 'POST',
      body: JSON.stringify({
        name: name,
        description: description,
        image_url: imageUrl,
        blockchain: 'ton',
        wallet_id: wallet.address,
        transaction_hash: txResult.hash,
        royalty_percentage: royalty || 5,
      }),
    });
    
    console.log('[Mint Workflow] NFT recorded on backend:', backendResult.id);
    
    return {
      success: true,
      blockchainHash: txResult.hash,
      backendId: backendResult.id,
      nftAddress: backendResult.token_id,
    };
  } catch (error) {
    console.error('[Mint Workflow] Failed:', error);
    throw error;
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// 6. EXPORT FOR MODULE SYSTEMS
// ═══════════════════════════════════════════════════════════════════════════════

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    initializeTONSystem,
    connectWallet,
    disconnectWallet,
    getConnectedWallet,
    isWalletConnected,
    sendTON,
    mintNFT,
    transferNFT,
    buyNFT,
    makeOffer,
    buildNFTMetadata,
    createCollectionOperator,
    createNFTItemOperator,
    validateTONAddress,
    convertTONAmount,
    performNFTMint,
  };
}

window.TONSystem = {
  initializeTONSystem,
  connectWallet,
  disconnectWallet,
  getConnectedWallet,
  isWalletConnected,
  sendTON,
  mintNFT,
  transferNFT,
  buyNFT,
  makeOffer,
  buildNFTMetadata,
  createCollectionOperator,
  createNFTItemOperator,
  validateTONAddress,
  convertTONAmount,
  performNFTMint,
};
