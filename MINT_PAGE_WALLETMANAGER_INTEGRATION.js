/**
 * ═══════════════════════════════════════════════════════════════════════════
 * MINT PAGE WALLET INTEGRATION - Using WalletManager Singleton
 * ═══════════════════════════════════════════════════════════════════════════
 * 
 * This example shows how to integrate the production-grade WalletManager 
 * into the mint page for blockchain selection and wallet connection.
 * 
 * Replace the "TON CONNECT WALLET INTEGRATION" section in mint.html with this code.
 */

// ═══════════════════════════════════════════════════════════════════════════
// WALLET PAGE INTEGRATION - Uses WalletManager singleton
// ═══════════════════════════════════════════════════════════════════════════

const blockchainSelect = document.getElementById('blockchain-select');
const walletSelect = document.getElementById('wallet-select');

// Initialize wallet integration
async function initMintWalletIntegration() {
  return new Promise((resolve) => {
    const checkInterval = setInterval(() => {
      if (window.walletManager) {
        clearInterval(checkInterval);
        setupMintWalletListeners();
        updateWalletFields();
        resolve();
      }
    }, 100);

    setTimeout(() => {
      clearInterval(checkInterval);
      console.warn('[MintPage] Wallet manager not initialized after 10 seconds');
      resolve();
    }, 10000);
  });
}

// Setup event listeners
function setupMintWalletListeners() {
  const walletManager = window.walletManager;
  if (!walletManager) return;

  walletManager.on('connected', (data) => {
    console.log('[MintPage] Wallet connected');
    updateWalletFields();
  });

  walletManager.on('disconnected', () => {
    console.log('[MintPage] Wallet disconnected');
    updateWalletFields();
  });
}

// Update wallet fields based on blockchain selection
function updateWalletFields() {
  const blockchain = blockchainSelect.value;
  const walletManager = window.walletManager;

  if (blockchain === 'ton') {
    // TON blockchain - use connected wallet
    if (walletManager && walletManager.isConnected()) {
      const address = walletManager.getFormattedAddress();
      walletSelect.innerHTML = `<option value="ton-connect" selected>${address}</option>`;
      walletSelect.disabled = false;
      console.log('[MintPage] TON wallet available:', address);
    } else {
      // Wallet not connected
      walletSelect.innerHTML = `
        <option value="">TON Wallet not connected</option>
        <option value="go-to-wallet">→ Go to Wallet Tab to Connect</option>
      `;
      walletSelect.disabled = false;

      // Handle redirect
      walletSelect.addEventListener('change', (e) => {
        if (e.target.value === 'go-to-wallet') {
          alert('Please connect your TON wallet from the Wallet tab first');
          window.location.href = '/webapp/wallet.html';
        }
      }, { once: true });
    }
  }
}

// Blockchain change handler
if (blockchainSelect) {
  blockchainSelect.addEventListener('change', async (e) => {
    const blockchain = e.target.value;
    walletSelect.innerHTML = '<option value="">Loading wallets...</option>';
    walletSelect.disabled = true;

    if (!blockchain) {
      walletSelect.innerHTML = '<option value="">Select blockchain first</option>';
      walletSelect.disabled = true;
      return;
    }

    if (blockchain === 'ton') {
      updateWalletFields();
      return;
    }

    // OTHER BLOCKCHAINS - Load from backend
    try {
      const response = await api.get(`/api/v1/wallets?blockchain=${blockchain}`);
      const wallets = response.wallets || [];

      walletSelect.innerHTML = '<option value="">Select wallet</option>';
      if (wallets.length === 0) {
        walletSelect.innerHTML += '<option disabled>No wallets found</option>';
        walletSelect.disabled = true;
        return;
      }

      wallets.forEach(wallet => {
        const option = document.createElement('option');
        option.value = wallet.id;
        option.textContent = `${wallet.address.slice(0, 10)}...${wallet.address.slice(-4)}`;
        walletSelect.appendChild(option);
      });

      walletSelect.disabled = false;
    } catch (error) {
      walletSelect.innerHTML = '<option disabled>Failed to load wallets</option>';
      walletSelect.disabled = true;
      console.error('[MintPage] Error:', error);
    }
  });
}

// Initialize on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initMintWalletIntegration);
} else {
  initMintWalletIntegration();
}

// Listen to global wallet system ready event
document.addEventListener('wallet-system-ready', () => {
  console.log('[MintPage] Wallet system ready');
  setupMintWalletListeners();
  updateWalletFields();
});

// ═══════════════════════════════════════════════════════════════════════════
// MINTING WITH WALLET - Use walletManager for transactions
// ═══════════════════════════════════════════════════════════════════════════

// Example: Update the handleMint function to use walletManager.sendTransaction()
/*

Original in handleMint():
  if (formData.blockchain === 'ton') {
    const tonWallet = getTONWallet();
    if (!tonWallet || !tonWallet.isTONConnect) {
      alert('TON wallet not connected');
      return;
    }
    // ... create payload ...
    const mintResponse = await api.post('/api/v1/nfts/mint', mintPayload);
  }

Updated with WalletManager:
  if (formData.blockchain === 'ton') {
    const walletManager = window.walletManager;
    if (!walletManager || !walletManager.isConnected()) {
      alert('TON wallet not connected');
      return;
    }

    try {
      // 1. Upload media
      submitBtn.textContent = 'Uploading media...';
      const uploadFormData = new FormData();
      uploadFormData.append('file', formState.imageFile);
      const uploadResponse = await api.upload('/api/v1/images/upload', uploadFormData);

      // 2. Create mint payload with backend
      submitBtn.textContent = 'Preparing transaction...';
      const metadata = {
        name: formData.name,
        description: formData.description,
        image: uploadResponse.image_url,
        royalties: formData.royalty_percentage
      };

      // 3. Send transaction via walletManager
      submitBtn.textContent = 'Waiting for wallet approval...';
      const txResult = await walletManager.sendTransaction({
        to: NFT_COLLECTION_ADDRESS,
        amount: 0.05,  // TON
        payload: buildMintPayload(metadata),
        metadata: {
          type: 'nft-mint',
          collection: 'user-nfts',
          name: formData.name
        }
      });

      console.log('[MintPage] Transaction successful:', txResult);
      alert(`NFT minting initiated! Transaction: ${txResult.hash}`);

      // 4. Notify backend of transaction
      submitBtn.textContent = 'Recording transaction...';
      await api.post('/api/v1/transaction/confirm', {
        tx_hash: txResult.boc,
        type: 'mint',
        wallet_address: walletManager.getAddress(),
        metadata: metadata
      });

      form.reset();
      setTimeout(() => window.location.href = '/webapp/dashboard.html', 2000);
    } catch (error) {
      if (error.message !== 'User declined') {
        alert(`Minting failed: ${error.message}`);
      }
      console.error('[MintPage] Mint error:', error);
    }
  }

*/

// ═══════════════════════════════════════════════════════════════════════════
// GLOBAL API AVAILABLE IN MINT.HTML
// ═══════════════════════════════════════════════════════════════════════════

/*

After walletManager.js and walletInit.js are loaded, these are available globally:

// Check wallet status
window.walletManager.isConnected()  // true/false
window.walletManager.getAddress()   // "UQxx..."
window.walletManager.getFormattedAddress()  // "UQxx...xxxx"
window.walletManager.getWallet()    // { account: { address, publicKey, ... } }

// Connect/disconnect
await window.walletManager.connect()     // Opens modal, returns wallet
await window.walletManager.disconnect()  // Disconnects wallet

// Send transactions
await window.walletManager.sendTransaction({
  to: 'destination_address',
  amount: 1.5,        // in TON
  payload: 'base64',  // optional
  stateInit: 'base64',// optional
  metadata: { ... }   // optional tracking data
});

// Listen to events
window.walletManager.on('connected', (data) => {
  console.log('Wallet connected:', data.address);
});
window.walletManager.on('disconnected', () => console.log('Disconnected'));
window.walletManager.on('error', (err) => console.error('Error:', err));
window.walletManager.on('transaction-sent', (tx) => console.log('TX:', tx));

*/
