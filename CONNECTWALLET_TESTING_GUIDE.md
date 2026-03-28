# ConnectWallet Testing & Verification Guide

**Quick Reference for Verifying the System Works**

---

## QUICK START: Verify in 5 Minutes

### Step 1: Open DevTools Console
```
1. Open wallet.html page
2. Press F12 to open DevTools
3. Click "Console" tab
```

### Step 2: Check Telegram Initialization
**Expected log (should appear immediately):**
```
[Telegram Init] ✅ Telegram.WebApp.ready() called successfully
[Telegram Init] Telegram initialization complete
[Telegram Init] Info: { context: 'TELEGRAM_MINI_APP' | 'NOT_TELEGRAM', ... }
```

**If NOT in Telegram:** Log will show:
```
[Telegram Init] Not in Telegram context, skipping WebApp.ready()
```
✅ This is **expected** if testing in browser (not Telegram Mini App)

### Step 3: Check Manifest Loading
**Expected log (should appear within 2-3 seconds):**
```
[TonConnect] Manifest URL: /tonconnect-manifest.json
[TonConnect] Validating manifest (1/2): /tonconnect-manifest.json
[TonConnect] Manifest response status: 200
[TonConnect] ✅ Manifest valid, app URL: https://nftplatformbackend-production-ee5f.up.railway.app
```

**Go to Network Tab to verify:**
1. Open DevTools → Network tab
2. Type "manifest" in filter
3. Should see: `/tonconnect-manifest.json` with status **200**
4. Click it → Response tab → Should show JSON with `"url"` field

### Step 4: Test ConnectWallet Button
```
1. Find "Connect Wallet" button on page
2. Click it
3. Check Console for logs:
   [Connect Wallet] Starting wallet connection flow
   [Connect Wallet] Step 1: Checking Telegram context...
   [Connect Wallet] Step 2: Checking TonConnect availability...
   [Connect Wallet] Step 3: Ensuring TonConnect is initialized...
   [Connect Wallet] Step 4: Opening wallet selection modal...
```

**Expected outcome:**
- **In Telegram Mini App:** Wallet selection modal appears
- **In Browser:** No modal (expected - Telegram required), but logs show initialization succeeded

---

## DETAILED VERIFICATION TESTS

### Test 1: Manifest URL Accessibility
```
BROWSER CONSOLE:
> fetch('/tonconnect-manifest.json').then(r => r.json()).then(x => console.log(x))

EXPECTED RESULT:
{
  "name": "GiftedForge",
  "url": "https://nftplatformbackend-production-ee5f.up.railway.app",
  "icons": [...],
  "version": "1",
  "tsStartParam": "startapp"
}
```

### Test 2: Telegram State Object
```
BROWSER CONSOLE:
> window._telegramState

EXPECTED RESULT:
{
  isInitialized: true,
  inTelegramContext: true,  // or false if not in Telegram
  readyCalled: true,
  initData: "query_id=..." or null,
  error: null
}
```

### Test 3: Telegram Info Function
```
BROWSER CONSOLE:
> window._getTelegramInfo()

EXPECTED RESULT:
{
  context: "TELEGRAM_MINI_APP" | "NOT_TELEGRAM",
  hasInitData: true | false,
  hasUser: true | false,
  userId: 12345 | null,
  isDark: true | false,
  platform: "ios" | "android" | "web",
  version: "7.0"
}
```

### Test 4: TonConnect Manager State
```
BROWSER CONSOLE:
> window.tonConnect

EXPECTED RESULT:
{
  isReady: true,
  isInitialized: true,
  tonConnectUI: TonConnectUI { ... },
  wallet: null | { account: { address: "..." } }
}
```

### Test 5: Manual Wallet Connection
```
BROWSER CONSOLE:
> window.connectWallet()

EXPECTED RESULT:
- If in Telegram: Wallet modal appears, returns { success: true, address: "..." }
- If in browser: Console shows all initialization steps succeeds, modal doesn't appear (expected)
```

---

## ERROR CASES & WHAT THEY MEAN

### Error 1: "[TonConnect] ❌ Manifest validation failed"
**Cause:** Cannot fetch `/tonconnect-manifest.json`  
**Fix:** 
1. Check manifest file exists: `/app/static/tonconnect-manifest.json`
2. Check manifest endpoint in main.py (around line 186)
3. Verify catch-all route working: `/js/` requests should return 200

### Error 2: "[Connect Wallet] ❌ TonConnect not initialized"
**Cause:** Module didn't load or initialize  
**Fix:**
1. Check JavaScript console for any 404/403 errors
2. Check Network tab: `tonconnect.js` should be 200 OK
3. Wait 3 seconds after page load before clicking button
4. Refresh page and try again

### Error 3: "[Telegram Init] ❌ Error calling Telegram.WebApp.ready()"
**Cause:** Telegram SDK not loaded or error  
**Fix:**
1. Only expected when NOT in Telegram Mini App
2. Check Telegram SDK loads: Script tag should load from Telegram CDN
3. In Telegram Mini App: This indicates SDK initialization failure

### Error 4: "Modal already opening"
**Cause:** User clicked button twice quickly  
**Fix:** 
1. Normal behavior - second click is queued
2. Wait for first modal to close
3. Can click again, it will automatically retry

### Error 5: "User cancelled wallet selection"
**Cause:** User clicked X or back button on wallet modal  
**Status:** ✅ Not an error, expected behavior  
**Response:** `{ success: false, reason: "User cancelled" }`

---

## BROWSER DEV TOOLS GUIDE

### Network Tab Checklist
- [ ] `/js/telegram-init.js` → **200** ✅
- [ ] `/js/tonconnect.js` → **200** ✅
- [ ] `/tonconnect-manifest.json` → **200** ✅ (JSON response)
- [ ] `telegram-web-app.js` → **200** ✅ (from Telegram CDN)
- [ ] `tonconnect-ui.min.js` → **200** ✅ (from CDN)

### Console Tab Checklist
- [ ] `[Telegram Init]` logs appearing ✅
- [ ] `[TonConnect]` initialization logs ✅
- [ ] No red **❌** errors (warnings ⚠️ are OK)
- [ ] Can call `window.connectWallet()` without error

### Application Tab (Cookies/Storage)
- [ ] Check localStorage for TonConnect state (if saved)
- [ ] Check if any errors in DevTools red icon

---

## SERVER SIDE VERIFICATION

### Check Manifest Endpoint
```bash
curl https://nftplatformbackend-production-ee5f.up.railway.app/tonconnect-manifest.json

# Should return:
{
  "url": "https://nftplatformbackend-production-ee5f.up.railway.app",
  "icons": [...],
  "name": "GiftedForge",
  ...
}
```

### Check Static Files Serving
```bash
curl https://nftplatformbackend-production-ee5f.up.railway.app/js/tonconnect.js
curl https://nftplatformbackend-production-ee5f.up.railway.app/js/telegram-init.js

# Both should return 200 OK with JavaScript content
```

### Check Server Logs
```
Expected logs when page loads:

INFO: TonConnect manifest origin: https://nftplatformbackend-production-ee5f.up.railway.app
INFO: [GET /tonconnect-manifest.json] 200 OK
INFO: [GET /js/telegram-init.js] 200 OK
INFO: [GET /js/tonconnect.js] 200 OK
```

---

## REAL WORLD TESTING (In Telegram Mini App)

### Step 1: Open in Telegram
1. Start bot in Telegram
2. Click "Open App" button
3. This loads the Mini App in Telegram context

### Step 2: Verify Logs
Open DevTools in Telegram (if supported) or use remote debugging

### Step 3: Test Wallet Connection
1. Click "Connect Wallet" button
2. Wallet selection modal should appear
3. Select wallet (Tonkeeper, TonWallet, etc.)
4. Follow wallet prompts
5. Should return to app with connected wallet

### Step 4: Test Minting
1. With wallet connected, proceed to mint
2. Should be able to complete mint transaction

---

## PERFORMANCE EXPECTATIONS

| Operation | Expected Time | Max Acceptable |
|-----------|---|---|
| Page load | 1-2 sec | 3 sec |
| Telegram init | 100-200ms | 500ms |
| Manifest validation | 200-500ms | 1 sec |
| Modal open | 500ms-1 sec | 2 sec |
| Total wallet connection | 1-2 sec | 3 sec |

**If times exceed "Max Acceptable":**
1. Check network latency (DevTools Network tab)
2. Check server load (CPU/Memory)
3. Check if manifest endpoint is slow
4. Check if TonConnect CDN is slow

---

## QUICK FIXES

### Issue: Button not clickable
```
FIX: Wait 3 seconds after page load, or refresh page
```

### Issue: Modal doesn't appear
```
FIX: 
- Check manifest URL working (F12 Network tab)
- Check you're in Telegram Mini App (not just browser)
- Refresh page and try again
```

### Issue: Weird console errors
```
FIX:
- Open and close console (F12)
- Refresh page completely (Ctrl+Shift+R)
- Clear cache and reload
```

### Issue: Can't connect after wallet selection
```
FIX:
- Check wallet is actually connected (check account field)
- Check no network errors (DevTools Network tab)
- Try different wallet
- Restart Telegram
```

---

## WHO TO NOTIFY IF ISSUES PERSIST

If you've verified everything above and still have issues:

**Provide this information:**
1. Browser console output (F12 → Console → Copy all logs)
2. Network tab screenshot (F12 → Network → Screenshot)
3. Whether in Telegram Mini App or browser
4. Steps to reproduce
5. Expected vs actual behavior

**Then check:**
- Server logs for errors
- Manifest endpoint returning correct data
- All static files accessible
- TonConnect CDN accessible

---

**Last Updated:** Production Session  
**Tested:** ✅ All code paths verified  
**Status:** Ready for Telegram deployment
