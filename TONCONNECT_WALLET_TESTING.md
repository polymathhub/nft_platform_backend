# TON Connect - Supported Wallets & Testing Guide

## Testing Your TON Connect Integration

### Step 1: Verify Backend Is Working

```bash
# Test the manifest endpoint
curl https://your-domain.com/tonconnect-manifest.json

# Expected response (200 OK):
{
  "url": "https://your-domain.com",
  "name": "GiftedForge",
  "iconUrl": "https://your-image-url..."
}
```

### Step 2: Open Browser Console

When you open the Wallet page, you should see:
```
[TONConnect] Module loaded and ready
[TONConnect] Initializing v2 UI...
[TONConnect] Manifest URL: https://your-domain.com/tonconnect-manifest.json
[TONConnect] ✅ Initialized successfully
```

### Step 3: Click "Connect TON Wallet" Button

You should see the wallet selection modal showing available wallets.

---

## Supported Wallets for Testing

### Desktop Testing (Browser)

#### 1. **TonKeeper Browser Extension** (Recommended)
- **Platform**: Chrome, Firefox, Edge
- **Download**: https://tonkeeper.com
- **Setup**:
  1. Install extension
  2. Create/import wallet
  3. Switch to **TON Testnet** in settings
  4. Get test TON from: https://testnet.tonconsole.com

#### 2. **Tonhub Wallet** (Telegram Mini App)
- **Platform**: Telegram
- **Download**: Via @tonhub_bot
- **Setup**:
  1. Open Telegram
  2. Search for @tonhub_bot
  3. Create wallet
  4. Switch to testnet

#### 3. **TON Wallet** (Official)
- **Platform**: Desktop & Mobile
- **Download**: https://ton.org/en/download
- **Note**: More for production, testnet available

### Mobile Testing (iOS/Android)

#### 1. **Tonkeeper Mobile**
- **Platform**: iOS (App Store), Android (Google Play)
- **Download**:
  - iOS: https://apps.apple.com/app/tonkeeper/id1607734314
  - Android: https://play.google.com/store/apps/details?id=com.tonkeeper.android

#### 2. **TonHub Mobile**
- **Platform**: Telegram Mini App
- **Features**: Seamless Telegram integration
- **Access**: @tonhub_bot in Telegram

#### 3. **OpenMask**
- **Platform**: iOS/Android
- **Download**: App Store / Google Play
- **Features**: Web3-like experience

---

## Testing Flow

### Scenario 1: Connect Wallet (Basic Test)

```
1. Open NFT Platform Mini App in Telegram
2. Navigate to Wallet page
3. Click "Connect TON Wallet"
4. ✓ Wallet modal should appear
5. Select a wallet (e.g., Tonkeeper)
6. ✓ Wallet app opens (or extension shows UI)
7. Approve connection
8. ✓ Back to app showing wallet address
9. Check console for: [TONConnect] Connected to: EQ...
```

### Scenario 2: Purchase NFT (Full Test)

```
1. Connect wallet (see above)
2. Navigate to NFT Marketplace
3. Click "Buy" on an NFT
4. Approve purchase in UI
5. ✓ Wallet modal appears for signing
6. Approve transaction in wallet
7. ✓ Transaction receipt shown
8. Check console for: [TONConnect] Transaction sent
```

### Scenario 3: Mint NFT (Advanced Test)

```
1. Connect wallet
2. Navigate to Mint page
3. Upload image and fill metadata
4. Click "Mint NFT"
5. ✓ Wallet shows transaction for approval
6. Approve in wallet
7. ✓ NFT minted successfully
8. Check your wallet in miniapp shows new NFT
```

---

## Using Testnet (Recommended for Development)

### Setting Up Testnet Wallet

#### For TonKeeper:
1. Open TonKeeper extension
2. Settings → Switch Network → **Testnet**
3. Get test TON from faucet:
   - https://testnet.tonconsole.com (free 10 TON)

#### For TON CLI:
```bash
TESTNET_RPC_ENDPOINT=https://testnet.toncenter.com/api/v2/jsonRPC
TON_TESTNET=true  # Set environment variable
```

### Testnet Faucets (Get Free Test TON)

| Faucet | URL | Amount |
|--------|-----|--------|
| TON Console | https://testnet.tonconsole.com | 10 TON |
| TON Testnet | https://testnet.ton.org/faucet | 5 TON |
| TonTools | https://tontools.io/testnet/faucet | 10 TON |

---

## Console Commands for Debugging

```javascript
// ===== STATUS CHECK =====
// Check if TON Connect is ready
window.tonConnect.isReady
// Output: true (if ready) or false

// Check if wallet is connected
window.tonConnect.isConnected()
// Output: true/false

// Get wallet address (if connected)
window.tonConnect.getWalletAddress()
// Output: "EQ..." (or null if not connected)

// Get full account data
window.tonConnect.getAccount()
// Output: {address: "EQ...", publicKey: "...", ...}

// ===== MANUAL ACTIONS =====
// Open wallet connection modal
window.tonConnect.openModal()

// Disconnect wallet
window.tonConnect.disconnect()

// Force re-initialization
window.tonConnect.init()

// ===== EVENT LISTENING =====
// Listen for connection events
window.tonConnect.on('connected', (account) => {
  console.log('Wallet connected:', account.address);
});

window.tonConnect.on('disconnected', () => {
  console.log('Wallet disconnected');
});

window.tonConnect.on('error', (error) => {
  console.log('TON Connect error:', error.message);
});

// ===== SESSION MANAGEMENT =====
// Check if session saved
localStorage.getItem('tonconnect_session')
// Output: JSON string of session (or null)

// Clear session (debug only!)
localStorage.removeItem('tonconnect_session');

// ===== SDK CHECK =====
// Verify SDK is loaded
typeof window.TonConnectUI
// Output: "function" (if loaded)

// Check TonConnect UI instance
window.tonConnect.ui
// Output: TonConnectUI instance (or null)
```

---

## Troubleshooting Specific Issues

### Issue: "Wallet not found" Error

**Fix**:
1. Install one of the supported wallets above
2. Enable wallet in browser/app
3. Make sure wallet is on correct network (mainnet/testnet)
4. Refresh the page

**Debug**:
```javascript
window.tonConnect.open()  // Try opening modal manually
```

### Issue: Modal Shows but Wallet Doesn't Connect

**Possible Causes**:
1. Wallet app crashed
2. Wrong network selected in wallet (should match app's network)
3. Browser cache issue

**Fix**:
1. Restart wallet app
2. Reload NFT Platform page (Cmd/Ctrl + R)
3. Clear browser cache (Cmd/Ctrl + Shift + Delete)
4. Click "Connect" again

### Issue: "Transaction Failed" When Sending

**Possible Causes**:
1. Insufficient balance (need TON for gas)
2. Wallet rejected transaction
3. Network connectivity issue

**Fix**:
1. Check wallet balance (should have >0.1 TON)
2. Get free testnet TON from faucet
3. Try again

### Issue: Session Not Persisting

**Cause**: Wallet connection resets on page reload

**Expected Behavior**:
- First load: Click connect, select wallet, approve
- After page reload: Should auto-reconnect with saved session

**Debug**:
```javascript
// Check if session was saved
JSON.parse(localStorage.getItem('tonconnect_session'))

// Return value should show account details
```

---

## Production Wallets vs Testnet

| Feature | Testnet | Mainnet |
|---------|---------|---------|
| Real money | ❌ No | ✅ Yes |
| Testing | ✅ Safe | ❌ Not recommended |
| Faucets | ✅ Available | ❌ N/A |
| Speed | Fast | Normal |
| Balance | Free test TON | Requires purchase |

**Recommendation for Development**: Always use testnet until app is production-ready!

---

## Network Issues

### If Manifest Returns 404

```bash
# Test manifest endpoint
curl -v https://your-domain.com/tonconnect-manifest.json

# Should see:
# HTTP/1.1 200 OK
# Content-Type: application/json
```

**If 404**:
1. Check file exists: `app/static/tonconnect-manifest.json`
2. Restart backend server  
3. Check backend logs for errors

### If SDK Fails to Load

The SDK loads from unpkg CDN. If blocked:

1. **CDN might be down**: Wait and retry
2. **Corporate firewall**: Use VPN or different network
3. **Browser extension blocking**: Disable ad-blockers temporarily

**Fallback**: SDK will try to load from multiple CDN mirrors

---

## Quick Checklist Before Going Live

- [ ] Test wallet connection works
- [ ] Test transaction signing (even tiny transaction)
- [ ] Clear browser cache and test fresh session
- [ ] Test on mobile device (iOS/Android)
- [ ] Test in Telegram Mini App (not just browser)
- [ ] Monitor console for [TONConnect] errors
- [ ] Verify manifest endpoint working
- [ ] Set correct network (mainnet for production)
- [ ] Test with production wallet (not just testnet)
- [ ] Have backup wallet for testing disconnection

---

## Getting Help

### Check Logs
```bash
# Backend logs
tail -f backend.log | grep -i tonconnect

# Browser console (F12)
# Filter for: [TONConnect]
```

### Resources
- **TON Docs**: https://docs.ton.org/develop/dapps/ton-connect/overview
- **TonConnect GitHub**: https://github.com/ton-connect/sdk
- **TonKeeper Support**: https://tonkeeper.com/support
- **Community**: https://t.me/tondev (Telegram)
