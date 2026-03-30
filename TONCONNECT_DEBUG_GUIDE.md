# TON Connect Debugging Guide

## Overview of Fixes Applied

### Problem Identified
The TON Connect module was incomplete. The HTML files were calling methods that didn't exist:
- `isConnected()` - Check if wallet connected
- `isReady` - Property to check ready state
- `waitForReady()` - Wait for initialization
- `openModal()` - Open wallet selection modal
- `getWalletAddress()` - Get wallet address
- `sendTransaction()` - Send blockchain transaction
- `initialize()` - Initialize module

### Solution Implemented
Rewrote `app/static/webapp/js/tonconnect.js` to:
1. **Properly load SDK**: Load both JS and CSS from unpkg CDN
2. **Implement all required methods**: All missing methods now implemented
3. **Better error handling**: Enhanced error logging and recovery
4. **Improved initialization**: Proper async initialization with promise tracking
5. **Dynamic container creation**: Auto-create button container if needed

## Testing Checklist

### Step 1: Verify SDK Loading ✓
**What happens**: When you open the app, tonconnect.js auto-initializes and loads the SDK from CDN.

**How to verify**:
1. Open Developer Tools (F12)
2. Go to **Console** tab
3. Look for log messages starting with `[TONConnect]`

Expected output:
```
[TONConnect] Module loaded and ready
[TONConnect] Setting up auto-init...
[TONConnect] Initializing immediately
[TONConnect] Initializing v2 UI...
[TONConnect] SDK script loaded
[TONConnect] Manifest URL: https://your-domain.com/tonconnect-manifest.json
[TONConnect] ✅ Initialized successfully
[TONConnect] Event: tonconnect:ready
```

### Step 2: Verify Manifest Endpoint ✓
**What should happen**: The manifest file must be accessible at `/tonconnect-manifest.json`

**How to test**:
```bash
# In browser console:
fetch('/tonconnect-manifest.json').then(r => r.json()).then(console.log)

# Expected response:
{
  "url": "https://your-domain.com",
  "name": "GiftedForge",
  "iconUrl": "https://your-image-url..."
}
```

**Common issues**:
- 404 error → Manifest file missing from `app/static/tonconnect-manifest.json`
- Wrong URL → Origin detection failed in `app/main.py`
- CORS error → Backend not allowing manifest requests

### Step 3: Verify CSS Loading ✓
**How to verify**:
1. Open DevTools → **Network** tab
2. Filter for `css`
3. Look for `tonconnect-ui.min.css`

**Expected**:
- Status: 200 OK
- Size: ~50KB
- Source: unpkg.com

**If CSS doesn't load** (non-critical):
- The app continues to work
- UI styles from TonConnect won't apply
- Tokens still rendered correctly

### Step 4: Test Wallet Connection

**Scenario**: Click "Connect TON Wallet" button

**Steps to follow**:
1. Open Telegram and go to NFT Platform Mini App
2. Navigate to **Wallet** page
3. Click **"Connect TON Wallet"** button
4. You should see wallet selection modal

**Expected flow**:
```
[TONConnect] Opening wallet modal...
[TONConnect] Wallet connected: {
  "address": "EQCD...",
  "publicKey": "key...",
  ...
}
[TONConnect] Status change: {account: {...}}
[TONConnect] Session saved
[TONConnect] Event: tonconnect:connected
```

**If modal doesn't appear**:

1. **Check SDK availability**:
   ```javascript
   // In console:
   window.TonConnectUI  // Should not be undefined
   window.tonConnect.isReady  // Should be true
   ```

2. **Check for JavaScript errors**:
   - Look at **Console** tab for red errors
   - Look at **Network** tab for failed requests

3. **Check manifest URL**:
   ```javascript
   window.tonConnect.ui  // Should have ui object
   ```

### Step 5: Test Wallet Address Display

**Expected**:
- After connecting, button changes to show "Connected to TON"
- Wallet address displays below

**How to verify in console**:
```javascript
window.tonConnect.getWalletAddress()  // Should return address
window.tonConnect.isConnected()  // Should return true
window.tonConnect.getAccount()  // Should return full account object
```

### Step 6: Test Transaction Sending

**Scenario** (from NFT Purchase):
1. Click "Connect Wallet" → connects successfully
2. Create purchase transaction
3. Click "Sign & Pay"

**Expected flow**:
```javascript
// Before:
const walletAddress = tonConnect.getWalletAddress();  // Gets address

// During:
const result = await tonConnect.sendTransaction(transaction);
// Shows modal for user to approve

// After:
[TONConnect] Transaction sent: {
  "boc": "...",
  "hash": "..."
}
[TONConnect] Event: tonconnect:transaction-sent
```

## Troubleshooting Common Issues

### Issue 1: "Connection Unavailable" Error

**Root causes**:
1. Manifest endpoint returning wrong origin
2. SDK not loading from CDN
3. Browser cache issues

**Fixes**:
```javascript
// In console:
// 1. Check manifest URL
await fetch('/tonconnect-manifest.json').then(r => r.json()).then(console.log)

// 2. Check if SDK is loaded
console.log(typeof window.TonConnectUI)  // Should be 'function'

// 3. Hard refresh browser
// Ctrl+Shift+R or Cmd+Shift+R
```

### Issue 2: "Already connecting..." Loop

**Cause**: Race condition where multiple connect attempts overlap

**Fix** (already applied):
```javascript
if (this.isConnecting) {
  console.log('[TONConnect] Already connecting');
  return this.currentAccount;
}
```

**Manual workaround**:
```javascript
// In console:
window.tonConnect.isConnecting = false;  // Reset state
```

### Issue 3: Session Not Persisting

**Cause**: localStorage not saving properly

**How to verify**:
```javascript
// In console:
localStorage.getItem('tonconnect_session')  // Should have data
```

**Fix**:
- Clear localStorage and reconnect
- Check browser privacy settings (shouldn't block localStorage)

### Issue 4: Manifest Returns Wrong URL

**Cause**: Settings not configured correctly

**Fix in `app/main.py`**:
```python
# Settings configuration should have:
# - app_url (highest priority)
# - telegram_webapp_url (fallback)
# - x-forwarded-proto/x-forwarded-host headers (for proxies)
```

**Debug**:
```python
# Add temporary logging in tonconnect_manifest endpoint:
logger.info(f"Detected origin: {origin}")
logger.info(f"app_url setting: {settings.app_url}")
logger.info(f"Request headers: {dict(request.headers)}")
```

## Browser Console Command Reference

```javascript
// === Status Checks ===
window.tonConnect.isInitialized          // Is module initialized?
window.tonConnect.isReady                // Is ready for use?
window.tonConnect.isConnecting           // Currently connecting?
window.tonConnect.isConnected()          // Is wallet connected?

// === Account Info ===
window.tonConnect.getAccount()           // Get full account object
window.tonConnect.getWalletAddress()     // Get wallet address

// === Manual Control ===
window.tonConnect.init()                 // Force re-init
window.tonConnect.connect()              // Start connection
window.tonConnect.disconnect()           // Disconnect wallet
window.tonConnect.openModal()            // Open wallet modal

// === Event Monitoring ===
window.tonConnect.on('ready', (data) => console.log('Ready:', data))
window.tonConnect.on('connected', (data) => console.log('Connected:', data))
window.tonConnect.on('disconnected', () => console.log('Disconnected'))
window.tonConnect.on('error', (data) => console.log('Error:', data))
```

## Network Requests to Monitor

### 1. Manifest Request
```
GET /tonconnect-manifest.json
Expected: 200 OK, ~50 bytes JSON response
```

### 2. SDK Script Load
```
GET https://unpkg.com/@tonconnect/ui@latest/dist/tonconnect-ui.min.js
Expected: 200 OK, ~60KB
```

### 3. SDK Stylesheet Load
```
GET https://unpkg.com/@tonconnect/ui@latest/dist/tonconnect-ui.min.css
Expected: 200 OK, ~50KB (or 404 if CSS fails non-critically)
```

## Recovery Steps

If TON Connect is broken:

1. **Clear browser cache and localStorage**:
   ```javascript
   localStorage.clear();
   sessionStorage.clear();
   // Then: Ctrl+Shift+Delete to clear cache
   ```

2. **Force reload**:
   ```
   Ctrl+Shift+R (or Cmd+Shift+R on Mac)
   ```

3. **Check backend logs**:
   ```bash
   # Look for TON Connect related errors:
   grep -i tonconnect app.log
   ```

4. **Verify manifest file exists**:
   ```bash
   ls -la app/static/tonconnect-manifest.json
   ```

5. **Test manifest endpoint directly**:
   ```bash
   curl -X GET http://localhost:8000/tonconnect-manifest.json
   ```

## Performance Metrics

Expected timings:
- Manifest load: <100ms
- SDK script load: <500ms (first time, cached after)
- Wallet modal open: <300ms
- Transaction sign: User-dependent (wallet app response)

## Related Configuration

### Backend Settings (`app/config.py`)
```python
APP_URL = "https://your-production-domain.com"
TELEGRAM_WEBAPP_URL = "https://web.telegram.org/app"
```

### Frontend Files
- Module: `app/static/webapp/js/tonconnect.js`
- Manifest: `app/static/tonconnect-manifest.json`
- Integration: `app/static/webapp/js/telegram-wallet.js`

## Next Steps if Issues Persist

1. **Enable verbose logging**:
   ```javascript
   // Add to tonconnect.js:
   const DEBUG = true;  // Enable extra logging
   ```

2. **Check TonConnect v2 docs**:
   - https://docs.ton.org/develop/dapps/ton-connect/overview
   - https://github.com/ton-connect/sdk

3. **Monitor real-time wallet connections**:
   - Check `/health/tonconnect` endpoint for diagnostics
   - Verify database tracking of wallet connections

4. **Test on real Telegram WebApp**:
   - App might behave differently in Telegram vs browser
   - Use actual TON testnet for testing
