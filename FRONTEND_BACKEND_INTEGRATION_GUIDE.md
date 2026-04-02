# 🚀 FRONTEND-BACKEND INTEGRATION GUIDE
**Production Web3 Wallet System**  
**Date**: April 2, 2026

---

## 📋 TABLE OF CONTENTS

1. [New Endpoints Overview](#new-endpoints)
2. [Integration Flow](#integration-flow)
3. [Code Examples](#code-examples)
4. [Error Handling](#error-handling)
5. [Testing Checklist](#testing)

---

## 🔗 NEW ENDPOINTS ADDED

### GROUP 1: Transaction Confirmation
```
POST   /api/v1/transactions/confirm           - Confirm signed TX
GET    /api/v1/transactions/{tx_hash}         - Get TX status
GET    /api/v1/transactions/history/user      - Get TX history
POST   /api/v1/transactions/retry/{tx_hash}   - Retry confirmation
```

### GROUP 2: Wallet Persistence
```
GET    /api/v1/wallets/current                - Get primary connected wallet
GET    /api/v1/wallets/status                 - Check wallet status
GET    /api/v1/wallets/primary                - Get primary wallet (alias)
GET    /api/v1/wallets                        - List all user's wallets
GET    /api/v1/wallets/balance/{address}      - Get wallet balance
POST   /api/v1/wallets/primary                - Set wallet as primary
POST   /api/v1/wallets/refresh-status/{addr}  - Refresh balance
```

---

## 🔄 INTEGRATION FLOW

### MINTING FLOW (Real Web3)

```
┌─────────────────────────────────────────────────────────┐
│ 1. USER CONNECTS WALLET (on wallet.html)               │
│    - Click "Connect TON Wallet"                        │
│    - TON Connect modal opens                           │
│    - User signs with wallet                           │
│    - wallet.html stores wallet in global state         │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│ 2. USER NAVIGATES TO MINT                              │
│    - mint.html loads                                    │
│    - getTONWallet() retrieves from sessionStorage       │
│    - Wallet address auto-fills                         │
│    - Backend call: GET /api/v1/wallets/current         │
│    - Confirms wallet is connected                      │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│ 3. USER FILLS MINT FORM & SUBMITS                       │
│    - Name, description, image                          │
│    - Blockchain: TON                                   │
│    - Wallet: [auto-filled connected wallet]           │
│    - POST /api/v1/images/upload (upload image)       │
│    - Backend returns image_id & image_url             │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│ 4. BUILD MINT PAYLOAD                                   │
│    - Frontend builds TX payload using @ton/core        │
│    - Includes: metadata_uri, wallet address, fees      │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│ 5. SIGN WITH TON CONNECT                               │
│    - Call: tonConnectUI.sendTransaction(payload)       │
│    - User approves in wallet app                       │
│    - Wallet signs and broadcasts TX                    │
│    - TON Connect returns: tx_hash                      │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│ 6. CONFIRM TRANSACTION (NEW!)                           │
│    - Backend call:                                     │
│      POST /api/v1/transactions/confirm                │
│      {                                                 │
│        tx_hash: "...",                                 │
│        wallet_address: "...",                          │
│        type: "mint",                                   │
│        nft_id: "...",                                  │
│        metadata: { to_address: "...", ... }           │
│      }                                                 │
│    - Backend verifies TX on blockchain                │
│    - Saves to DB with status: PENDING/CONFIRMED       │
│    - Returns transaction record                       │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│ 7. POLL FOR CONFIRMATION (optional)                    │
│    - If TX is PENDING, poll: GET /api/v1/transactions/│
│    - Poll every 5-10 seconds                          │
│    - Retry: POST /api/v1/transactions/retry/{hash}    │
│    - Once CONFIRMED, show success                     │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│ 8. SHOW RESULTS                                        │
│    - NFT minted! Hash: 0x123...                       │
│    - View on TON Explorer                            │
│    - Navigate to portfolio                            │
└─────────────────────────────────────────────────────────┘
```

---

## 💻 CODE EXAMPLES

### EXAMPLE 1: Check If Wallet Is Connected

```javascript
// Frontend - mint.html
async function checkWalletStatus() {
  try {
    const { telegramFetch } = await import('./telegram-fetch.js');
    
    const response = await telegramFetch('/api/v1/wallets/current');
    
    if (response.connected && response.wallet) {
      console.log('✅ Wallet connected:', response.wallet.address);
      console.log('Balance:', response.wallet.balance_ton, 'TON');
      return response.wallet;
    } else {
      console.log('❌ Wallet not connected');
      console.log('Message:', response.message);
      return null;
    }
  } catch (error) {
    console.error('Error checking wallet:', error);
    return null;
  }
}
```

### EXAMPLE 2: Get Wallet Balance

```javascript
// Frontend
async function getWalletBalance(address) {
  try {
    const { telegramFetch } = await import('./telegram-fetch.js');
    
    const response = await telegramFetch(
      `/api/v1/wallets/balance/${address}`
    );
    
    console.log('Balance:', response.balance_ton, 'TON');
    console.log('Last updated:', response.last_checked);
    return response.balance_ton;
  } catch (error) {
    console.error('Balance error:', error);
    return null;
  }
}
```

### EXAMPLE 3: Confirm A Minted NFT

```javascript
// Frontend - after TON Connect signing returns tx_hash
async function confirmMintTransaction(tx_hash, nft_id, wallet_address) {
  try {
    const { telegramFetch } = await import('./telegram-fetch.js');
    
    const response = await telegramFetch('/api/v1/transactions/confirm', {
      method: 'POST',
      body: JSON.stringify({
        tx_hash: tx_hash,
        wallet_address: wallet_address,
        type: 'mint',
        nft_id: nft_id,
        metadata: {
          to_address: wallet_address,
          fee_details: 'recorded'
        }
      })
    });
    
    if (response.success) {
      console.log('✅ Transaction confirmed!');
      console.log('Status:', response.status);
      console.log('TX:', response.tx_hash);
      return response;
    } else {
      console.log('⏳ Transaction pending...');
      console.log('Check status with: GET /api/v1/transactions/' + tx_hash);
      return response;
    }
  } catch (error) {
    console.error('Confirmation error:', error);
  }
}
```

### EXAMPLE 4: Get Transaction Status

```javascript
// Frontend - poll for confirmation
async function pollTransactionStatus(tx_hash, maxRetries = 30) {
  const { telegramFetch } = await import('./telegram-fetch.js');
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await telegramFetch(
        `/api/v1/transactions/${tx_hash}`
      );
      
      console.log(`[${i + 1}/${maxRetries}] Status:`, response.status);
      
      if (response.status === 'confirmed') {
        console.log('✅ Transaction confirmed on blockchain!');
        return response;
      }
      
      if (response.status === 'failed') {
        console.log('❌ Transaction failed:', response.error_message);
        return response;
      }
      
      // Still pending, wait 2 seconds
      await new Promise(resolve => setTimeout(resolve, 2000));
      
    } catch (error) {
      console.error('Poll error:', error);
    }
  }
  
  console.log('⏰ Timeout: Transaction still pending after 1 minute');
  return null;
}
```

### EXAMPLE 5: Get Transaction History

```javascript
// Frontend
async function getTransactionHistory(limit = 20) {
  try {
    const { telegramFetch } = await import('./telegram-fetch.js');
    
    const response = await telegramFetch(
      `/api/v1/transactions/history/user?skip=0&limit=${limit}`
    );
    
    console.log('Total transactions:', response.total);
    
    response.transactions.forEach(tx => {
      console.log(`${tx.type}: ${tx.status} - ${tx.tx_hash}`);
    });
    
    return response.transactions;
  } catch (error) {
    console.error('History error:', error);
  }
}
```

### EXAMPLE 6: Retry Confirmation

```javascript
// Frontend - if transaction stuck in pending
async function retryConfirmation(tx_hash) {
  try {
    const { telegramFetch } = await import('./telegram-fetch.js');
    
    const response = await telegramFetch(
      `/api/v1/transactions/retry/${tx_hash}`,
      { method: 'POST' }
    );
    
    if (response.status === 'confirmed') {
      console.log('✅ Transaction now confirmed!');
    } else {
      console.log('Still pending, try again in 10 seconds');
    }
    
    return response;
  } catch (error) {
    console.error('Retry error:', error);
  }
}
```

### EXAMPLE 7: List All Connected Wallets

```javascript
// Frontend
async function listWallets() {
  try {
    const { telegramFetch } = await import('./telegram-fetch.js');
    
    const response = await telegramFetch('/api/v1/wallets');
    
    console.log('Total wallets:', response.total);
    
    response.wallets.forEach(wallet => {
      console.log(
        `${wallet.address}: ${wallet.status}, ` +
        `Balance: ${wallet.balance_ton} TON, ` +
        `Primary: ${wallet.is_primary}`
      );
    });
    
    if (response.primary_wallet) {
      console.log('Primary:', response.primary_wallet.address);
    }
    
    return response.wallets;
  } catch (error) {
    console.error('List wallets error:', error);
  }
}
```

---

## ⚠️ ERROR HANDLING

### Common Errors & Solutions

```javascript
// Error 401: Wallet not connected
// Solution: Redirect to wallet.html to connect

// Error 403: Wallet doesn't belong to user
// Solution: Verify wallet address matches connected wallet

// Error 404: Transaction not found
// Solution: Wait a few seconds, blockchain takes time to confirm

// Error 503: Cannot query blockchain
// Solution: Retry after 30 seconds
```

### Retry Logic Pattern

```javascript
async function apiCallWithRetry(
  endpoint,
  options = {},
  maxRetries = 3,
  delayMs = 1000
) {
  const { telegramFetch } = await import('./telegram-fetch.js');
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const response = await telegramFetch(endpoint, options);
      return response;
    } catch (error) {
      if (attempt === maxRetries) throw error;
      
      console.warn(`Attempt ${attempt} failed, retrying...`);
      await new Promise(r => setTimeout(r, delayMs * attempt));
    }
  }
}
```

---

## ✅ TESTING CHECKLIST

### Wallet Connection
- [ ] User connects wallet on wallet.html
- [ ] Wallet address saved in DB
- [ ] GET /api/v1/wallets/current returns connected wallet
- [ ] Balance is fetched and shown

### Minting
- [ ] mint.html detects that wallet is connected
- [ ] Wallet auto-fills in blockchain selector
- [ ] User submits mint form
- [ ] Frontend uploads image and gets image_id
- [ ] TON Connect opens and user signs TX
- [ ] TX hash returned to frontend
- [ ] POST /api/v1/transactions/confirm saves TX in DB
- [ ] Status returned as "pending" or "confirmed"
- [ ] GET /api/v1/transactions/{hash} shows transaction
- [ ] Polling updates status to "confirmed"

### Portfolio/Dashboard
- [ ] GET /api/v1/wallets/balance shows current balance
- [ ] GET /api/v1/transactions/history/user shows all user's TXs
- [ ] Can filter by status and type

### Error Scenarios
- [ ] User navigates away during signing → TX still saved
- [ ] Blockchain confirmation delayed → Polling retries
- [ ] User disconnects wallet → Status shows "disconnected"
- [ ] Invalid TX hash → Returns error 400

---

## 📊 DATABASE UPDATES

The Transaction table now tracks:
- `user_id` - who initiated TX
- `wallet_id` - which wallet
- `transaction_hash` - blockchain TX hash
- `status` - pending/confirmed/failed
- `transaction_type` - mint/transfer/buy/offer
- `transaction_metadata` - JSON with custom data
- `confirmed_at` - when TX confirmed

The TONWallet table now tracks:
- `status` - pending/connected/disconnected/failed
- `connected_at` - when wallet connected
- `disconnected_at` - when wallet disconnected
- `wallet_metadata` - JSON with device info, last activity
- `is_primary` - mark primary wallet for operations

---

## 🔄 MARKETPLACE EXAMPLE (Coming Soon)

```javascript
// This pattern will be used for buy/offer operations:

async function buyNFT(nft_id, price_ton, seller_address) {
  // 1. Get primary wallet
  const wallet = await checkWalletStatus();
  
  // 2. Build marketplace contract payload
  const payload = buildMarketplaceBuyPayload(nft_id, price_ton, seller_address);
  
  // 3. Sign with TON Connect
  const tx_hash = await tonConnectUI.sendTransaction(payload);
  
  // 4. Confirm on backend
  await confirmMarketplaceTransaction(tx_hash, 'buy', nft_id);
  
  // 5. Poll for confirmation
  await pollTransactionStatus(tx_hash);
  
  // 6. Show success
  console.log('✅ NFT purchased!');
}
```

---

## 🚀 DEPLOYMENT CHECKLIST

- [ ] All new endpoints registered in main.py
- [ ] Transaction verification service tested
- [ ] Wallet persistence working across page reloads
- [ ] Balance queries working on TON API
- [ ] Error handling for all scenarios
- [ ] Logging enabled for debugging
- [ ] Database migrations applied
- [ ] Frontend using new endpoints
- [ ] Testing with real TON Connect
- [ ] Production deployment

---

## 📞 SUPPORT

For issues:
1. Check logs: `docker logs backend`
2. Verify TX hash on TON Explorer
3. Ensure wallet is connected: GET /api/v1/wallets/current
4. Check transaction status: GET /api/v1/transactions/{hash}

---

**Status**: ✅ Ready for Integration  
**Next Phase**: Marketplace transaction support (buy, offer, transfer)  
**Timeline**: 1-2 days for full implementation

