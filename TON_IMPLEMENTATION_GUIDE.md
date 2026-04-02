# TON Production System - Implementation Guide

**Status:** Ready to integrate into existing pages  
**Estimated time:** 30 minutes  
**Complexity:** Low (simple copy-paste integration)

---

## 📋 STEP 1: Update index.html (or main entry point)

Add these script tags to your main HTML file (before other scripts load):

```html
<!DOCTYPE html>
<html>
<head>
    <!-- Existing head content -->
    
    <!-- ✅ ADD THESE LINES -->
    <!-- TonConnect UI (must be first) -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tonconnect/ui@latest/dist/tonconnect-ui.min.css">
    <script src="https://cdn.jsdelivr.net/npm/@tonconnect/ui@latest/dist/tonconnect-ui.min.js"></script>
    
    <!-- Our Production System (in order) -->
    <script src="/webapp/js/wallet-manager.js"></script>
    <script src="/webapp/js/ton-transaction-engine.js"></script>
    <script src="/webapp/js/ton-smart-contracts.js"></script>
    <script src="/webapp/js/ton-system-integration.js"></script>
    <!-- ✅ END NEW LINES -->
</head>
<body>
    <!-- Existing body content -->
    
    <script>
    // Initialize TON System on page load
    window.addEventListener('load', async () => {
        try {
            console.log('[App] Initializing TON System...');
            await window.TONSystem.initializeTONSystem();
            console.log('✅ TON System ready - wallet connection handling active');
        } catch (error) {
            console.error('❌ TON System initialization failed:', error);
        }
    });
    </script>
</body>
</html>
```

---

## 🪙 STEP 2: Update wallet.html

Replace or update the existing wallet.html TON Connect section with this production-ready code.

> Find the section with the connect button and replace it with:

```html
<!-- TON CONNECT WALLET MANAGEMENT SECTION -->
<div id="ton-wallet-section">
    <h2>TON Wallet</h2>
    
    <button id="connectBtn" class="btn btn-primary">
        Connect TON Wallet
    </button>
    
    <div id="walletInfo" style="display: none; margin-top: 20px;">
        <p><strong>Wallet:</strong> <span id="walletAddress"></span></p>
        <p><strong>Status:</strong> <span id="walletStatus">Connected</span></p>
        <button id="disconnectBtn" class="btn btn-danger">Disconnect</button>
    </div>
</div>

<script>
// ═══════════════════════════════════════════════════════════════
// TON WALLET MANAGEMENT (Production System)
// ═══════════════════════════════════════════════════════════════

async function initializeWalletUI() {
    // Get UIelements
    const connectBtn = document.getElementById('connectBtn');
    const disconnectBtn = document.getElementById('disconnectBtn');
    const walletInfo = document.getElementById('walletInfo');
    const walletAddress = document.getElementById('walletAddress');
    const walletStatus = document.getElementById('walletStatus');
    
    // Listen for wallet events
    document.addEventListener('ton-wallet-connected', (event) => {
        const wallet = event.detail;
        console.log('[WalletUI] Wallet connected:', wallet.address);
        
        // Format address
        const formatted = wallet.address.slice(0, 10) + '...' + wallet.address.slice(-6);
        walletAddress.textContent = formatted;
        walletStatus.textContent = 'Connected';
        
        // Update UI
        connectBtn.style.display = 'none';
        walletInfo.style.display = 'block';
    });
    
    document.addEventListener('ton-wallet-disconnected', () => {
        console.log('[WalletUI] Wallet disconnected');
        
        // Update UI
        connectBtn.style.display = 'block';
        walletInfo.style.display = 'none';
    });
    
    // Connect button handler
    connectBtn.addEventListener('click', async () => {
        try {
            connectBtn.disabled = true;
            connectBtn.textContent = 'Connecting...';
            
            const wallet = await window.TONSystem.connectWallet();
            console.log('✅ Wallet connected:', wallet.address);
            
            connectBtn.textContent = 'Connect TON Wallet';
        } catch (error) {
            console.error('❌ Connection failed:', error);
            alert(`Connection failed: ${error.message}`);
            connectBtn.textContent = 'Connect TON Wallet';
        } finally {
            connectBtn.disabled = false;
        }
    });
    
    // Disconnect button handler
    disconnectBtn.addEventListener('click', async () => {
        try {
            disconnectBtn.disabled = true;
            disconnectBtn.textContent = 'Disconnecting...';
            
            await window.TONSystem.disconnectWallet();
            console.log('✅ Wallet disconnected');
            
            disconnectBtn.textContent = 'Disconnect';
        } catch (error) {
            console.error('❌ Disconnect failed:', error);
            alert(`Disconnect failed: ${error.message}`);
            disconnectBtn.textContent = 'Disconnect';
        } finally {
            disconnectBtn.disabled = false;
        }
    });
    
    // Update UI if already connected
    const wallet = window.TONSystem.getConnectedWallet();
    if (wallet) {
        const formatted = wallet.address.slice(0, 10) + '...' + wallet.address.slice(-6);
        walletAddress.textContent = formatted;
        connectBtn.style.display = 'none';
        walletInfo.style.display = 'block';
    }
}

// Initialize when page is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeWalletUI);
} else {
    initializeWalletUI();
}
</script>
```

---

## 🖼️ STEP 3: Update mint.html

Replace the existing mint form handler with the production handler:

```javascript
// ═══════════════════════════════════════════════════════════════
// NFT MINTING - Production System Integration
// ═══════════════════════════════════════════════════════════════

/**
 * Handle NFT minting form submission
 */
window.handleMint = async (event) => {
    event.preventDefault();
    
    try {
        const form = event.target;
        const submitBtn = form.querySelector('button[type="submit"]');
        
        // ✅ Check wallet connection FIRST
        if (!window.TONSystem.isWalletConnected()) {
            alert('❌ Please connect your TON wallet first (on Wallet page)');
            return;
        }
        
        // Get form data
        const name = form.querySelector('input[placeholder*="Cosmic"]')?.value;
        const description = form.querySelector('textarea')?.value;
        const blockchain = document.getElementById('blockchain-select')?.value;
        const royalty = parseInt(form.querySelectorAll('input[type="number"]')[0]?.value || '0');
        
        // ✅ Validate inputs
        if (!name || name.trim() === '') {
            alert('❌ Please enter an NFT name');
            return;
        }
        
        if (!description || description.trim() === '') {
            alert('❌ Please enter a description');
            return;
        }
        
        if (blockchain !== 'ton') {
            alert('❌ TON blockchain must be selected for this demo');
            return;
        }
        
        if (!window.formState?.imageFile) {
            alert('❌ Please upload an image');
            return;
        }
        
        if (royalty < 0 || royalty > 100) {
            alert('❌ Royalty must be between 0% and 100%');
            return;
        }
        
        // ✅ STEP 1: Upload image to backend
        console.log('[Mint] Step 1: Uploading image...');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Uploading image...';
        
        const uploadFormData = new FormData();
        uploadFormData.append('file', window.formState.imageFile);
        
        let imageUrl = '';
        try {
            const { telegramFetch } = await import('./telegram-fetch.js');
            const uploadResponse = await telegramFetch('/api/v1/images/upload', {
                method: 'POST',
                body: uploadFormData,
            });
            imageUrl = uploadResponse.image_url || uploadResponse.image_ref || '';
            console.log('[Mint] Image uploaded:', imageUrl);
        } catch (uploadError) {
            console.error('[Mint] Image upload failed:', uploadError);
            alert('Failed to upload image: ' + uploadError.message);
            submitBtn.disabled = false;
            submitBtn.textContent = 'Create NFT';
            return;
        }
        
        // ✅ STEP 2: Perform blockchain minting
        console.log('[Mint] Step 2: Minting on blockchain...');
        submitBtn.textContent = 'Minting on blockchain...';
        
        const collectionAddress = 'YOUR_COLLECTION_ADDRESS'; // ← SET THIS!
        
        const mintResult = await window.TONSystem.performNFTMint({
            name: name,
            description: description,
            imageUrl: imageUrl,
            royalty: royalty,
            collectionAddress: collectionAddress,
        });
        
        console.log('[Mint] ✅ NFT minted successfully:', mintResult);
        
        // ✅ STEP 3: Success - redirect
        submitBtn.textContent = 'Success! Redirecting...';
        
        alert(`✅ NFT minted successfully!\n\nTransaction: ${mintResult.blockchainHash}\nID: ${mintResult.backendId}`);
        
        // Reset form
        form.reset();
        window.formState.imageFile = null;
        
        // Redirect after 2 seconds
        setTimeout(() => {
            window.location.href = '/webapp/dashboard.html';
        }, 2000);
        
    } catch (error) {
        console.error('[Mint] ❌ Minting failed:', error);
        alert(`❌ Minting failed: ${error.message}`);
        
        const submitBtn = event.target.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Create NFT';
        }
    }
};
```

---

## 🛒 STEP 4: Update marketplace.html

Add buy/offer functionality:

```javascript
// ═══════════════════════════════════════════════════════════════
// MARKETPLACE OPERATIONS - Production System
// ═══════════════════════════════════════════════════════════════

/**
 * Buy NFT from marketplace
 * Call this when user clicks "Buy" button
 */
async function buyNFT(nftId, nftAddress, listingAddress, price) {
    try {
        // Check wallet
        if (!window.TONSystem.isWalletConnected()) {
            alert('❌ Please connect TON wallet first');
            return;
        }
        
        console.log('[Buy] Starting purchase:', { nft: nftId, price: price });
        
        // Disable button
        const btn = event.target;
        if (btn) btn.disabled = true;
        
        // Execute purchase
        const result = await window.TONSystem.buyNFT({
            listingAddress: listingAddress,
            nftAddress: nftAddress,
            price: parseFloat(price),
        });
        
        console.log('[Buy] ✅ Purchase successful:', result.hash);
        alert(`✅ NFT purchased!\n\nTransaction: ${result.hash}`);
        
        // Re-fetch NFT data
        setTimeout(() => location.reload(), 2000);
        
    } catch (error) {
        console.error('[Buy] ❌ Purchase failed:', error);
        alert(`❌ Purchase failed: ${error.message}`);
        const btn = event.target;
        if (btn) btn.disabled = false;
    }
}

/**
 * Make offer on NFT
 */
async function makeOfferOnNFT(nftId, nftAddress) {
    try {
        // Prompt for offer amount
        const offer = prompt('Enter your offer amount (in TON):');
        if (!offer) return;
        
        const offerAmount = parseFloat(offer);
        if (isNaN(offerAmount) || offerAmount <= 0) {
            alert('Invalid offer amount');
            return;
        }
        
        // Check wallet
        if (!window.TONSystem.isWalletConnected()) {
            alert('❌ Please connect TON wallet first');
            return;
        }
        
        console.log('[Offer] Making offer:', { nft: nftId, amount: offerAmount });
        
        const result = await window.TONSystem.makeOffer({
            nftAddress: nftAddress,
            offerAmount: offerAmount,
        });
        
        console.log('[Offer] ✅ Offer made:', result.hash);
        alert(`✅ Offer submitted!\n\nTransaction: ${result.hash}`);
        
        // Re-fetch NFT data
        setTimeout(() => location.reload(), 2000);
        
    } catch (error) {
        console.error('[Offer] ❌ Failed:', error);
        alert(`❌ Offer failed: ${error.message}`);
    }
}

// Usage in HTML:
// <button onclick="buyNFT('nft-id', 'UQ...', 'UQMARKET...', '5.5')">Buy Now</button>
// <button onclick="makeOfferOnNFT('nft-id', 'UQ...')">Make Offer</button>
```

---

## 👤 STEP 5: Update profile.html

Show owned NFTs:

```javascript
// ═══════════════════════════════════════════════════════════════
// USER PROFILE - Show Owned NFTs
// ═══════════════════════════════════════════════════════════════

async function loadUserNFTs() {
    try {
        const wallet = window.TONSystem.getConnectedWallet();
        if (!wallet) {
            console.log('[Profile] No wallet connected');
            return;
        }
        
        console.log('[Profile] Loading NFTs for:', wallet.address);
        
        // Fetch user's NFTs from backend
        const { telegramFetch } = await import('./telegram-fetch.js');
        const response = await telegramFetch('/api/v1/nfts/my-nfts', {
            headers: { 'X-Wallet-Address': wallet.address },
        });
        
        const nfts = response.nfts || [];
        console.log('[Profile] Found NFTs:', nfts.length);
        
        // Display NFTs
        const container = document.getElementById('my-nfts-container');
        if (!container) return;
        
        if (nfts.length === 0) {
            container.innerHTML = '<p>No NFTs yet. Create one on the Mint page!</p>';
            return;
        }
        
        container.innerHTML = nfts.map(nft => `
            <div class="nft-card">
                <img src="${nft.image_url}" alt="${nft.name}">
                <h3>${nft.name}</h3>
                <p>${nft.description}</p>
                <p><strong>Blockchain:</strong> ${nft.blockchain}</p>
                <button onclick="transferNFT('${nft.id}', '${nft.token_id}')">Transfer</button>
                <button onclick="listForSale('${nft.id}', '${nft.token_id}')">List for Sale</button>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('[Profile] Failed to load NFTs:', error);
    }
}

async function transferNFT(nftId, tokenId) {
    try {
        const destination = prompt('Enter destination wallet address:');
        if (!destination) return;
        
        // Validate address
        const validation = window.TONSmartContracts.TONAddressValidator.validate(destination);
        if (!validation.valid) {
            alert('Invalid wallet address: ' + validation.error);
            return;
        }
        
        const result = await window.TONSystem.transferNFT({
            nftAddress: tokenId,
            to: destination,
        });
        
        alert(`✅ NFT transferred!\n\nTransaction: ${result.hash}`);
        loadUserNFTs(); // Refresh
        
    } catch (error) {
        alert(`❌ Transfer failed: ${error.message}`);
    }
}

// Load NFTs when profile page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadUserNFTs);
} else {
    loadUserNFTs();
}
```

---

## ⚙️ STEP 6: Configuration

Create or update `/webapp/js/ton-config.js`:

```javascript
/**
 * TON System Configuration
 */

const TON_CONFIG = {
    // ✅ SET THESE VALUES FOR YOUR DEPLOYMENT
    
    // NFT Collection contract address (from your collection deployment)
    COLLECTION_ADDRESS: 'UQ..._YOUR_COLLECTION_ADDRESS_HERE',
    
    // Marketplace address (if using one)
    MARKETPLACE_ADDRESS: 'UQ..._MARKETPLACE_ADDRESS',
    
    // RPC endpoint (optional, defaults to toncenter.com)
    RPC_URL: 'https://toncenter.com/api/v2/jsonRPC',
    
    // Network (testnet or mainnet)
    NETWORK: 'mainnet', // Set to 'testnet' for development
    
    // Default gas fees (in TON)
    DEFAULT_FEES: {
        TRANSFER: 0.1,
        MINT: 1.5,
        BUY: 0.2,
        OFFER: 0.05,
    },
};

// Use in your code:
// const collectionAddr = TON_CONFIG.COLLECTION_ADDRESS;
```

Use in mint.html:
```javascript
// Replace this line:
const collectionAddress = 'YOUR_COLLECTION_ADDRESS';

// With this:
const collectionAddress = TON_CONFIG.COLLECTION_ADDRESS;
```

---

## ✅ VERIFICATION CHECKLIST

After implementing, test with:

```javascript
// 1. Check initialization
console.log(window.WalletManager);           // Should exist
console.log(window.tonTransactionEngine);    // Should exist
console.log(window.TONSystem);               // Should exist

// 2. Test wallet connection
const wallet = window.TONSystem.getConnectedWallet();
console.log('Wallet:', wallet);

// 3. Check connection status
console.log('Connected?', window.TONSystem.isWalletConnected());

// 4. View transaction history
console.log(window.tonTransactionEngine.getHistory());

// 5. Test address validation
const validation = window.TONSmartContracts.TONAddressValidator.validate('UQXX...');
console.log('Valid address?', validation);
```

---

## 🚀 DEPLOYMENT CHECKLIST

- [ ] Added script tags to main HTML (4 modules + TonConnect UI)
- [ ] Updated wallet.html with connect/disconnect handlers
- [ ] Updated mint.html with `performNFTMint()` call
- [ ] Updated marketplace.html with `buyNFT()` and `makeOffer()`
- [ ] Updated profile.html with NFT display
- [ ] Set `COLLECTION_ADDRESS` in config or mint.html
- [ ] Tested in Telegram Mini App (NOT browser)
- [ ] Verify backend endpoints are responding
- [ ] Check browser console for any `[ComponentName]` logs
- [ ] Test actual wallet connection and transaction
- [ ] Deploy to production

---

## 🔧 TROUBLESHOOTING

**"TON System not ready" error:**
```javascript
// Make sure you called this first
await window.TONSystem.initializeTONSystem();
```

**"Wallet not connected" when trying to mint:**
```javascript
// Check wallet status
if (!window.TONSystem.isWalletConnected()) {
    // Show connect button
}
```

**Transaction silently fails:**
```javascript
// Check browser console for [TxEngine] logs
// Check wallet app (Tonkeeper) for transaction approval
// Verify you have enough TON for gas fees
```

**Collection address shows error:**
```javascript
// Verify you set the correct address
console.log(TON_CONFIG.COLLECTION_ADDRESS);
// Make sure address is valid format: UQxxxx...
```

---

**Status:** ✅ Ready to implement  
**Time estimate:** 30 minutes  
**Difficulty:** Easy - mostly copy-paste
