/**
 * TON Connect + Telegram SDK Integration Guide
 * 
 * Complete reference for frontend developers to integrate with Phase 2 backend
 * 
 * Architecture:
 * 1. Telegram Web App SDK provides X-Telegram-Init-Data header (authentication)
 * 2. Frontend imports telegramFetch for proper header handling
 * 3. TON Connect handles wallet connection and transaction signing
 * 4. Backend blockchain_router processes transactions and syncs state
 */

// ═══════════════════════════════════════════════════════════════
// 1. INITIALIZATION - Setup TON Connect and Telegram SDK
// ═══════════════════════════════════════════════════════════════

/**
 * Initialize TON Connect UI in your HTML (in <head>)
 * 
 * <script src="https://cdn.jsdelivr.net/npm/@tonconnect/ui@latest/dist/tonconnect-ui.min.js"></script>
 * <script>
 *   TonConnectUI.init({
 *     manifestUrl: 'https://your-domain.com/tonconnect-manifest.json'
 *   });
 * </script>
 */

// Get TON Connect UI instance
const tonConnect = window.TonConnectUI;

// ═══════════════════════════════════════════════════════════════
// 2. WALLET CONNECTION - Sync wallet state with backend
// ═══════════════════════════════════════════════════════════════

async function setupWalletListeners() {
  // Listen for wallet connect events
  tonConnect.onStatusChange(async (wallet) => {
    try {
      const { telegramFetch } = await import('./telegram-fetch.js');
      
      if (wallet) {
        // User connected wallet
        console.log('✅ Wallet connected:', wallet.account.address);
        
        const response = await telegramFetch('/api/v1/blockchain/wallet/sync', {
          method: 'POST',
          body: JSON.stringify({
            wallet_address: wallet.account.address,
            wallet_name: wallet.provider,
            is_connected: true
          })
        });
        
        if (!response.ok) {
          console.error('Failed to sync wallet:', response.status);
          return;
        }
        
        const data = await response.json();
        console.log('Backend wallet synced:', data);
        
        // Update UI to show connected wallet
        updateWalletUI(wallet.account.address, true);
        
      } else {
        // User disconnected wallet
        console.log('❌ Wallet disconnected');
        
        // Optional: sync disconnection to backend
        // await telegramFetch('/api/v1/blockchain/wallet/sync', {
        //   method: 'POST',
        //   body: JSON.stringify({
        //     wallet_address: previousWalletAddress,
        //     wallet_name: 'unknown',
        //     is_connected: false
        //   })
        // });
        
        updateWalletUI(null, false);
      }
    } catch (error) {
      console.error('Wallet sync error:', error);
    }
  });
}

// ═══════════════════════════════════════════════════════════════
// 3. PREPARE MINT - Get transaction ready for signing
// ═══════════════════════════════════════════════════════════════

async function prepareMint(nftData) {
  try {
    const { telegramFetch } = await import('./telegram-fetch.js');
    
    console.log('📋 Preparing mint...');
    
    const response = await telegramFetch('/api/v1/blockchain/nft/prepare-mint', {
      method: 'POST',
      body: JSON.stringify({
        name: nftData.name,
        description: nftData.description,
        image_url: nftData.imageUrl,
        collection_address: nftData.collectionAddress || null,
        royalty_percent: nftData.royaltyPercent || 0,
        attributes: nftData.attributes || []
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to prepare mint');
    }
    
    const prepareResponse = await response.json();
    
    if (!prepareResponse.success) {
      throw new Error(prepareResponse.message || 'Mint preparation failed');
    }
    
    console.log('✅ Mint prepared, ready for signing');
    console.log('Estimated fee:', prepareResponse.estimated_fee_ton, 'TON');
    console.log('Metadata URI:', prepareResponse.metadata_uri);
    
    return {
      nftId: prepareResponse.nft_id,
      tonconnectTx: prepareResponse.tonconnect_tx,
      metadataUri: prepareResponse.metadata_uri,
      estimatedFee: prepareResponse.estimated_fee_ton
    };
    
  } catch (error) {
    console.error('❌ Prepare mint error:', error);
    showNotification('Error', error.message, 'error');
    throw error;
  }
}

// ═══════════════════════════════════════════════════════════════
// 4. SEND TRANSACTION - Sign with wallet via TON Connect
// ═══════════════════════════════════════════════════════════════

async function sendMintTransaction(tonconnectTx) {
  try {
    console.log('🔐 Sending transaction to wallet for signing...');
    
    // Send transaction to user's wallet
    // User will see confirmation dialog in wallet
    const result = await tonConnect.sendTransaction(tonconnectTx);
    
    console.log('✅ Transaction signed and sent');
    console.log('Transaction hash:', result.boc);
    
    // Extract transaction hash from result
    // (Different wallets return different formats)
    const transactionHash = extractTransactionHash(result);
    
    return transactionHash;
    
  } catch (error) {
    if (error.code === 'BACK_ERROR') {
      console.log('User cancelled transaction');
    } else {
      console.error('❌ Transaction send error:', error);
      showNotification('Error', 'Failed to send transaction', 'error');
    }
    throw error;
  }
}

function extractTransactionHash(result) {
  // Different wallet SDKs return hash differently
  if (result.hash) return result.hash;
  if (result.boc) return result.boc;
  if (result.transaction_hash) return result.transaction_hash;
  if (result && typeof result === 'string') return result;
  
  console.warn('Could not extract transaction hash, result:', result);
  return null;
}

// ═══════════════════════════════════════════════════════════════
// 5. CONFIRM MINT - Store transaction in backend
// ═══════════════════════════════════════════════════════════════

async function confirmMint(transactionHash, nftId, walletAddress) {
  try {
    const { telegramFetch } = await import('./telegram-fetch.js');
    
    console.log('📝 Confirming transaction:', transactionHash);
    
    const response = await telegramFetch('/api/v1/blockchain/nft/confirm-mint', {
      method: 'POST',
      body: JSON.stringify({
        transaction_hash: transactionHash,
        nft_id: nftId,
        wallet_address: walletAddress
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to confirm mint');
    }
    
    const confirmResponse = await response.json();
    
    console.log('✅ Mint confirmed, status:', confirmResponse.status);
    console.log('Confirmations:', confirmResponse.confirmations);
    
    return {
      status: confirmResponse.status,
      confirmations: confirmResponse.confirmations,
      trustLevel: confirmResponse.trust_level
    };
    
  } catch (error) {
    console.error('❌ Confirm mint error:', error);
    throw error;
  }
}

// ═══════════════════════════════════════════════════════════════
// 6. POLL VERIFICATION - Check transaction confirmations
// ═══════════════════════════════════════════════════════════════

async function pollMintVerification(transactionHash, nftId, options = {}) {
  const {
    maxWaitTime = 5 * 60 * 1000,  // 5 minutes
    pollInterval = 5000,           // Poll every 5 seconds
    onProgress = null              // Callback for updates
  } = options;
  
  const startTime = Date.now();
  let pollCount = 0;
  
  try {
    const { telegramFetch } = await import('./telegram-fetch.js');
    
    while (Date.now() - startTime < maxWaitTime) {
      pollCount++;
      console.log(`🔍 Verification poll #${pollCount}...`);
      
      const response = await telegramFetch(`/api/v1/blockchain/transaction/${transactionHash}/verify`, {
        method: 'POST'
      });
      
      if (!response.ok) {
        console.warn(`Poll returned ${response.status}, retrying...`);
        await new Promise(resolve => setTimeout(resolve, pollInterval));
        continue;
      }
      
      const verifyResponse = await response.json();
      
      if (!verifyResponse.success) {
        throw new Error('Verification failed: ' + verifyResponse.message);
      }
      
      console.log(`Status: ${verifyResponse.status} (${verifyResponse.confirmations} confirmations)`);
      
      if (onProgress) {
        onProgress({
          status: verifyResponse.status,
          confirmations: verifyResponse.confirmations,
          trustLevel: verifyResponse.trust_level
        });
      }
      
      // Check if confirmed
      if (verifyResponse.status === 'confirmed') {
        console.log('✅ Transaction confirmed!');
        return {
          status: 'confirmed',
          confirmations: verifyResponse.confirmations,
          trustLevel: verifyResponse.trust_level,
          verified: true
        };
      }
      
      if (verifyResponse.status === 'failed') {
        throw new Error('Transaction failed on blockchain');
      }
      
      // Still pending/in_progress, wait and poll again
      await new Promise(resolve => setTimeout(resolve, pollInterval));
    }
    
    // Timeout reached
    console.warn('⏱️ Verification timeout - transaction may still be pending');
    return {
      status: 'pending',
      confirmations: 0,
      trustLevel: 0,
      verified: false,
      timedOut: true
    };
    
  } catch (error) {
    console.error('❌ Verification poll error:', error);
    throw error;
  }
}

// ═══════════════════════════════════════════════════════════════
// 7. FULL FLOW - Complete mint from start to finish
// ═══════════════════════════════════════════════════════════════

async function executeMint(nftData) {
  try {
    // Check wallet connected
    if (!tonConnect.wallet) {
      throw new Error('Please connect your TON wallet first');
    }
    
    console.log('🚀 Starting NFT mint flow...');
    
    // Step 1: Prepare
    const prepareResult = await prepareMint(nftData);
    console.log('Step 1/4: Prepared ✓');
    
    // Step 2: Send for signing
    const txHash = await sendMintTransaction(prepareResult.tonconnectTx);
    console.log('Step 2/4: Signed ✓');
    
    if (!txHash) {
      throw new Error('No transaction hash returned');
    }
    
    // Step 3: Confirm in backend
    await confirmMint(txHash, prepareResult.nftId, tonConnect.wallet.account.address);
    console.log('Step 3/4: Confirmed ✓');
    
    // Step 4: Poll verification
    const verifyResult = await pollMintVerification(txHash, prepareResult.nftId, {
      onProgress: (update) => {
        updateMintProgress(update.confirmations, update.status);
      }
    });
    console.log('Step 4/4: Verified ✓');
    
    console.log('✅ NFT mint complete!');
    return {
      success: true,
      nftId: prepareResult.nftId,
      transactionHash: txHash,
      confirmations: verifyResult.confirmations
    };
    
  } catch (error) {
    console.error('❌ Mint failed:', error);
    showNotification('Mint Failed', error.message, 'error');
    throw error;
  }
}

// ═══════════════════════════════════════════════════════════════
// 8. UI HELPERS
// ═══════════════════════════════════════════════════════════════

function updateWalletUI(address, isConnected) {
  const walletBtn = document.getElementById('walletButton');
  
  if (isConnected && address) {
    walletBtn.textContent = `Connected: ${address.slice(0, 10)}...`;
    walletBtn.disabled = false;
    walletBtn.classList.add('connected');
  } else {
    walletBtn.textContent = 'Connect Wallet';
    walletBtn.disabled = false;
    walletBtn.classList.remove('connected');
  }
}

function updateMintProgress(confirmations, status) {
  const progressEl = document.getElementById('mintProgress');
  if (!progressEl) return;
  
  const percent = Math.min((confirmations / 101) * 100, 100);
  
  progressEl.innerHTML = `
    <div class="progress-bar">
      <div class="progress-fill" style="width: ${percent}%"></div>
    </div>
    <p>Confirmations: ${confirmations}/101</p>
    <p>Status: ${status}</p>
  `;
}

function showNotification(title, message, type = 'info') {
  // Use Telegram.WebApp.showAlert or your UI library
  console.log(`[${type.toUpperCase()}] ${title}: ${message}`);
  
  if (window.Telegram?.WebApp) {
    window.Telegram.WebApp.showAlert(`${title}\n\n${message}`);
  }
}

// ═══════════════════════════════════════════════════════════════
// 9. USAGE EXAMPLE
// ═══════════════════════════════════════════════════════════════

/*
// On page load
document.addEventListener('DOMContentLoaded', () => {
  setupWalletListeners();
});

// On mint button click
document.getElementById('mintButton').addEventListener('click', async () => {
  await executeMint({
    name: 'My Amazing NFT',
    description: 'A wonderful digital collectible',
    imageUrl: 'https://example.com/image.jpg',
    attributes: [
      { trait_type: 'Rarity', value: 'Legendary' }
    ]
  });
});

// On connect wallet button click
document.getElementById('walletButton').addEventListener('click', async () => {
  try {
    await tonConnect.connectWallet();
  } catch (error) {
    console.error('Failed to connect wallet:', error);
  }
});
*/

// ═══════════════════════════════════════════════════════════════
// 10. ERROR HANDLING
// ═══════════════════════════════════════════════════════════════

const ErrorMessages = {
  'WALLET_NOT_CONNECTED': 'Please connect your TON wallet first',
  'INVALID_WALLET_ADDRESS': 'Invalid TON wallet address',
  'TRANSACTION_FAILED': 'Transaction was rejected by the blockchain',
  'INSUFFICIENT_BALANCE': 'Your wallet does not have enough TON',
  'USER_CANCELLED': 'You cancelled the transaction',
  'NETWORK_ERROR': 'Network connection error. Please check your connection',
  'SERVER_ERROR': 'Backend server error. Please try again later',
};

async function handleMintError(error) {
  let userMessage = error.message || 'Unknown error occurred';
  
  // Map error types
  if (error.code === 'BACK_ERROR') {
    userMessage = ErrorMessages.USER_CANCELLED;
  } else if (error.message.includes('wallet')) {
    userMessage = ErrorMessages.WALLET_NOT_CONNECTED;
  } else if (error.message.includes('balance')) {
    userMessage = ErrorMessages.INSUFFICIENT_BALANCE;
  } else if (error.message.includes('network')) {
    userMessage = ErrorMessages.NETWORK_ERROR;
  }
  
  showNotification('Error', userMessage, 'error');
}

// ═══════════════════════════════════════════════════════════════
// Export for use in other modules
// ═══════════════════════════════════════════════════════════════

export {
  setupWalletListeners,
  prepareMint,
  sendMintTransaction,
  confirmMint,
  pollMintVerification,
  executeMint,
  updateWalletUI,
  updateMintProgress,
  showNotification,
  handleMintError
};

