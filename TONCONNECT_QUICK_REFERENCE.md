# SimpleTonConnect - Quick Reference

## One-Liner Setup

```html
<script type="module">
  import { initWalletConnect } from './js/wallet-connect-simple.js';
  initWalletConnect();
</script>
```

## What You Need

1. **HTML elements** (already in wallet.html):
   ```html
   <div id="tonconnect-button"></div>
   <button id="connectBtn">Connect Wallet</button>
   <span id="walletAddress"></span>
   <span id="status"></span>
   ```

2. **Files**: 
   - `js/simple-tonconnect.js` ✅
   - `js/wallet-connect-simple.js` ✅

3. **Backend endpoint**:
   ```
   POST /api/v1/walletconnect/connect
   ```

## API Cheat Sheet

```javascript
import SimpleTonConnect from './js/simple-tonconnect.js';

const tonConnect = new SimpleTonConnect('tonconnect-button');

// Initialize
await tonConnect.init();

// Connect
await tonConnect.connectWallet();

// Disconnect
await tonConnect.disconnectWallet();

// Get info
tonConnect.getAddress();        // '0QAx...'
tonConnect.isConnected();       // true/false
tonConnect.getWallet();         // full wallet object

// Listen
tonConnect.on('connected', (account) => {});
tonConnect.on('disconnected', () => {});
tonConnect.on('error', (error) => {});
tonConnect.on('ready', () => {});
tonConnect.on('synced', (data) => {});
```

## Full Flow

```
User clicks "Connect Wallet"
    ↓
TonConnect modal opens
    ↓
User selects wallet (Tonkeeper, etc.)
    ↓
'connected' event fires → Account data available
    ↓
Backend sync triggered automatically
    ↓
'synced' event fires → Backend response received
    ↓
UI updates with address
```

## Event Listener Patterns

```javascript
// Single connection
tonConnect.on('connected', (account) => {
  console.log('Connected to:', account.address);
  // Storage, UI update, etc.
});

// Handle errors
tonConnect.on('error', (error) => {
  console.error('Failed:', error.message);
  alert('Connection failed');
});

// Backend sync complete
tonConnect.on('synced', (data) => {
  console.log('Server confirmed:', data);
  // Can now redirect, etc.
});
```

## Common Patterns

### Check if Connected
```javascript
if (tonConnect.isConnected()) {
  const addr = tonConnect.getAddress();
  console.log('Connected to:', addr);
}
```

### Manual Button Handler
```javascript
document.getElementById('myBtn').onclick = async () => {
  try {
    await tonConnect.connectWallet();
    // 'connected' event will fire
  } catch (error) {
    console.error('Connection failed:', error);
  }
};
```

### Custom UI Updates
```javascript
tonConnect.on('connected', (account) => {
  // Update button text
  document.getElementById('connectBtn').textContent = 'Disconnect';
  
  // Show address
  document.getElementById('wallet-address').textContent = 
    account.address.slice(0, 6) + '...';
  
  // Store in localStorage
  localStorage.setItem('walletAddress', account.address);
});

tonConnect.on('disconnected', () => {
  // Reset UI
  document.getElementById('connectBtn').textContent = 'Connect Wallet';
  document.getElementById('wallet-address').textContent = '';
  localStorage.removeItem('walletAddress');
});
```

### Auto-Connect on Page Load
```javascript
import SimpleTonConnect from './js/simple-tonconnect.js';

const tonConnect = new SimpleTonConnect('tonconnect-button');
await tonConnect.init();

// If wallet is already connected, info is available immediately
if (tonConnect.isConnected()) {
  console.log('Already connected to:', tonConnect.getAddress());
  // Auto-logout, redirect, etc.
}
```

## File Sizes

- `simple-tonconnect.js`: ~8KB
- `wallet-connect-simple.js`: ~3KB
- **Total**: ~11KB before gzip

When served from CDN (TonConnectUI SDK): ~200KB additional

## Network Requests

### On Init
```
GET /tonconnect-manifest.json
GET https://cdn.jsdelivr.net/npm/@tonconnect/ui@latest/...
```

### On Connect
```
(User interaction with wallet app)
POST /api/v1/walletconnect/connect
```

## Debug Checklist

- [ ] SDK loaded: `console.log(window.TonConnectUI)`
- [ ] Telegram ready: `console.log(window.Telegram?.WebApp)`
- [ ] Init data: `console.log(window.Telegram?.WebApp?.initData)`
- [ ] Manifest accessible: `curl https://domain.com/tonconnect-manifest.json`
- [ ] Events firing: Check console logs with `[TONConnect]` prefix
- [ ] Backend sync: Check Network tab for POST to `/api/v1/walletconnect/connect`

## Error Messages

| Error | Cause | Fix |
|-------|-------|-----|
| "TON Connect not initialized" | Called methods before `init()` | Call `await tonConnect.init()` first |
| "Cannot read TonConnectUI" | SDK didn't load from CDN | Check network, firewall |
| "Manifest URL must be HTTPS" | Using HTTP in production | Switch to HTTPS domain |
| "Backend sync failed" | API endpoint issue | Check `/api/v1/walletconnect/connect` |

## Production Checklist

- [ ] HTTPS enabled ✅
- [ ] `/tonconnect-manifest.json` serving ✅
- [ ] `/api/v1/walletconnect/connect` implemented ✅
- [ ] Button styled properly ✅
- [ ] Error notifications configured ✅
- [ ] Tested in real Telegram (not emulator) ✅
- [ ] Console logs clean (no errors) ✅

## Key Differences from Old System

| Old | New |
|-----|-----|
| `TelegramWalletIntegrator` | `SimpleTonConnect` |
| Complex state management | Simple events |
| ~500 lines of code | ~300 lines total |
| Multiple files required | 2 files |
| Hard to understand | Self-documenting |

## Migration

If upgrading from `TelegramWalletIntegrator`:

1. Remove old script from wallet.html
2. Add new module script:
   ```html
   <script type="module">
     import { initWalletConnect } from './js/wallet-connect-simple.js';
     initWalletConnect();
   </script>
   ```
3. Delete: `js/telegram-wallet.js`, `js/tonconnect.js`, `js/wallet-connection-flow.js`
4. Test in Telegram Mini App

## Links

- [TON Connect Docs](https://docs.ton.org/develop/wallets/tonconnect)
- [Telegram Mini App](https://core.telegram.org/bots/webapps)
- [TonConnect UI](https://github.com/ton-connect/ton-connect-js)

---

**Version**: 1.0  
**Status**: Production Ready ✅  
**Last Updated**: March 31, 2026
