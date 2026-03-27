# TonConnect Integration & Troubleshooting Guide

## Problem: "Connection Unavailable" Error

If you're seeing "Connection Unavailable" when clicking the wallet connect button, this guide will help diagnose and fix it.

---

## Diagnostic Checklist

### 1. Verify TonConnect Manifest is Serving
**What to check:** The manifest file must be accessible at the root domain.

```bash
# Test if manifest is accessible
curl -X GET https://your-domain.com/tonconnect-manifest.json

# Expected response (200 OK):
{
  "url": "https://your-domain.com",
  "name": "GiftedForge",
  "iconUrl": "https://image2url.com/r2/default/images/..."
}
```

**If you get 404:** The manifest file is missing or the endpoint is broken.

### 2. Browser Console Check
**What to do:**
1. Open your Telegram WebApp in browser
2. Press F12 to open Developer Tools
3. Go to **Console** tab
4. Look for errors containing:
   - `TonConnect`
   - `tonconnect-manifest.json`
   - `Failed to load`
   - `CORS`
   - `network error`

**Common errors:**
```javascript
// ❌ CORS error
Uncaught (in promise) TypeError: Failed to fetch tonconnect-manifest.json

// ❌ Manifest not found
404 Not Found: /tonconnect-manifest.json

// ❌ Wrong domain in manifest
TonConnect initialized with url: https://wrong-domain.com

// ✅ Good sign (in console)
TonConnect UI initialized successfully
```

### 3. Network Tab Check
**What to do:**
1. Open DevTools → Network tab
2. Click the connect wallet button
3. Look for `tonconnect-manifest.json` request

**Expected:**
- Status: `200 OK`
- Size: ~200 bytes
- Response: Valid JSON

**Problem if:**
- Status: `404 Not Found`
- Status: `CORS error`
- Request doesn't appear (connection never attempted)

---

## Common Causes & Fixes

### Issue 1: Manifest File Missing or Broken

**Symptom:** 404 error when loading `/tonconnect-manifest.json`

**Root cause:** 
- File not at `app/static/tonconnect-manifest.json`
- Path misconfiguration in FastAPI

**Fix:**

```bash
# 1. Verify file exists
ls -la app/static/tonconnect-manifest.json

# 2. Check content
cat app/static/tonconnect-manifest.json

# 3. Verify it has proper structure
```

**If file is missing, create it:**
```bash
cat > app/static/tonconnect-manifest.json << 'EOF'
{
  "url": "https://your-domain.com",
  "name": "GiftedForge",
  "iconUrl": "https://image2url.com/r2/default/images/1773286803181-3e04067a-db2d-48b1-93e7-d486c16f805c.jpg"
}
EOF
```

### Issue 2: Wrong Domain in Manifest

**Symptom:** TonConnect initializes but can't connect wallets

**Root cause:** 
- Manifest has hardcoded `url` pointing to wrong domain
- Origin mismatch between Telegram WebApp and manifest URL

**Fix in `app/static/tonconnect-manifest.json`:**
```json
{
  "url": "https://your-actual-domain.com",  // ← Must match request origin
  "name": "GiftedForge",
  "iconUrl": "https://image2url.com/..."
}
```

**Or let FastAPI auto-detect:**

The endpoint `@app.get("/tonconnect-manifest.json")` in `app/main.py` (lines 186-231) automatically detects and sets the correct origin:

```python
# Auto-detection order:
1. settings.app_url (if set)
2. settings.telegram_webapp_url parsed
3. x-forwarded-proto + x-forwarded-host headers (proxy)
4. request.url scheme + hostname
5. Fallback to hardcoded production URL
```

### Issue 3: TonConnect Script Not Loading

**Symptom:** 
- Console error: `TonConnect is not defined`
- No UI button appears
- "Connection Unavailable" fails immediately

**Root cause:**
- Script tag missing
- Script loading from wrong CDN
- Script blocked by CSP (Content Security Policy)

**Verify in `app/static/webapp/mint.html` (line 25):**
```html
<!-- TON Connect UI -->
<script src="https://cdn.jsdelivr.net/gh/ton-connect/ui@latest/dist/tonconnect-ui.min.js"></script>
<link href="https://cdn.jsdelivr.net/gh/ton-connect/ui@latest/dist/tonconnect-ui.min.css" rel="stylesheet" />
```

**If not present, add it:**
```html
<!DOCTYPE html>
<html>
<head>
    <!-- ... other head content ... -->
    
    <!-- Add these lines -->
    <script src="https://cdn.jsdelivr.net/gh/ton-connect/ui@latest/dist/tonconnect-ui.min.js"></script>
    <link href="https://cdn.jsdelivr.net/gh/ton-connect/ui@latest/dist/tonconnect-ui.min.css" rel="stylesheet" />
</head>
<body>
    <!-- Your content -->
</body>
</html>
```

### Issue 4: TonConnect Initialization Code Missing or Broken

**Symptom:**
- Script loads but no connect button appears
- "Connection Unavailable" message

**Root cause:**
- JavaScript not calling `TonConnectUI()`
- Initialization code has errors

**Check `app/static/webapp/mint.html` for:**
```javascript
// Must initialize TonConnect UI
const tonConnectUI = new TonConnectUI({
    manifestUrl: '/tonconnect-manifest.json',
});

// Or with CDN manifest:
const tonConnectUI = new TonConnectUI({
    manifestUrl: 'https://your-domain.com/tonconnect-manifest.json',
});
```

**If missing, add this before mint form:**
```html
<script>
    // Initialize TonConnect UI
    const tonConnectUI = new TonConnectUI({
        manifestUrl: '/tonconnect-manifest.json',
    });

    // Expose for form usage
    window.tonConnectUI = tonConnectUI;
</script>
```

### Issue 5: Incorrect Manifest URL Path

**Symptom:**
- Manifest loads with different path
- TonConnect can't find expected callback

**Root cause:**
- Using absolute CDN URL instead of relative path
- Path mismatch between manifest declaration and actual location

**Fix:**

❌ **Wrong:**
```javascript
new TonConnectUI({
    manifestUrl: 'https://cdn.example.com/tonconnect.json'  // Absolute URL
});
```

✅ **Correct:**
```javascript
new TonConnectUI({
    manifestUrl: '/tonconnect-manifest.json'  // Relative to domain root
});
```

---

## Complete TonConnect Setup

### 1. FastAPI Manifest Endpoint (Already Done ✅)
**File:** `app/main.py` (lines 186-231)

```python
@app.get("/tonconnect-manifest.json", include_in_schema=False)
async def tonconnect_manifest(request: Request):
    """Serves TonConnect manifest with auto-detected origin"""
    # Auto-detects correct domain
    # Sets manifest["url"] to request origin
    # Returns proper JSON headers
```

### 2. Manifest File (Already Done ✅)
**File:** `app/static/tonconnect-manifest.json`

```json
{
  "url": "https://your-domain.com",
  "name": "GiftedForge",
  "iconUrl": "https://..."
}
```

### 3. HTML Script Tags (Check/Fix ✅)
**File:** `app/static/webapp/mint.html` (lines 24-26)

```html
<!-- TON Connect UI -->
<script src="https://cdn.jsdelivr.net/gh/ton-connect/ui@latest/dist/tonconnect-ui.min.js"></script>
<link href="https://cdn.jsdelivr.net/gh/ton-connect/ui@latest/dist/tonconnect-ui.min.css" rel="stylesheet" />
```

### 4. JavaScript Initialization (Check/Fix ✅)
**Add to `app/static/webapp/mint.html` before form:**

```javascript
<script>
    // Initialize TonConnect UI
    const tonConnectUI = new TonConnectUI({
        manifestUrl: '/tonconnect-manifest.json',
    });

    // Expose globally for form handlers
    window.tonConnectUI = tonConnectUI;

    // Debug logging
    tonConnectUI.connectionRestored.subscribe((isConnected) => {
        console.log(`[TonConnect] Connection restored: ${isConnected}`);
    });

    tonConnectUI.statusChangeSubscription.subscribe((walletInfo) => {
        console.log(`[TonConnect] Status changed:`, walletInfo);
    });
</script>
```

### 5. Connect Button in Form

```html
<div id="ton-connect-button"></div>

<script>
    // After TonConnect initialized
    tonConnectUI.attachUi(document.getElementById('ton-connect-button'));
</script>
```

---

## Testing Steps

### Test 1: Manifest Accessibility
```bash
# From your local machine or CI
curl -I https://your-domain.com/tonconnect-manifest.json

# Expected:
# HTTP/2 200
# Content-Type: application/json
```

### Test 2: Browser Network
1. Open Telegram WebApp in browser
2. DevTools → Network tab
3. Filter by "tonconnect"
4. Click connect
5. Verify manifest request succeeds (200)

### Test 3: Console Logs
```javascript
// In browser console, should show:
console.log(TonConnectUI);  // Should be a class/function

// After initialization:
console.log(window.tonConnectUI);  // Should be initialized instance
```

### Test 4: End-to-End Connect
1. Click "Connect Wallet" button
2. Should open wallet selection modal
3. Choose wallet type (MetaMask, TrustWallet, etc)
4. Should not show "Connection Unavailable"

---

## Debugging Script

**Add this to browser console to diagnose issues:**

```javascript
// Check 1: TonConnect library loaded
console.log('1. TonConnectUI loaded:', typeof TonConnectUI !== 'undefined');

// Check 2: Manifest accessible
fetch('/tonconnect-manifest.json')
  .then(r => r.json())
  .then(m => console.log('2. Manifest loaded:', m))
  .catch(e => console.error('2. Manifest failed:', e));

// Check 3: TonConnect UI initialized
console.log('3. TonConnectUI instance:', window.tonConnectUI);

// Check 4: Check connection status
if (window.tonConnectUI) {
  console.log('4. Connection status:', window.tonConnectUI.connected);
}

// Check 5: Try to open connect dialog
if (window.tonConnectUI) {
  console.log('5. Attempting to open connect dialog...');
  window.tonConnectUI.openModal();  // This should open wallet selection
}
```

---

## Deployment Checklist

Before deploying, verify:

- [ ] Manifest file exists at `app/static/tonconnect-manifest.json`
- [ ] Manifest `url` field matches your production domain
- [ ] `app/main.py` has `/tonconnect-manifest.json` endpoint (lines 186-231)
- [ ] `app/static/webapp/mint.html` includes TonConnect scripts (lines 24-26)
- [ ] JavaScript initializes `TonConnectUI` (check for init code)
- [ ] HTTPS enabled (TonConnect requires secure context)
- [ ] CORS headers allow manifest requests
- [ ] CSP (Content Security Policy) doesn't block scripts

---

## Production Settings

### For Railway Deployment

```bash
# Environment variables to set:
TELEGRAM_WEBAPP_URL=https://your-domain.com/webapp
APP_URL=https://your-domain.com

# These auto-update the manifest origin
```

### For Docker Deployment

```dockerfile
# Ensure manifest file is copied
COPY app/static/tonconnect-manifest.json /app/app/static/

# Or pre-generate with correct domain:
RUN sed -i 's|https://example.com|'$DOMAIN'|g' /app/app/static/tonconnect-manifest.json
```

---

## Support & Escalation

If issues persist:

1. **Check logs:**
   ```bash
   tail -f /var/log/app.log | grep -i tonconnect
   ```

2. **Test manifest directly:**
   ```bash
   curl -v https://your-domain.com/tonconnect-manifest.json
   ```

3. **Verify network in DevTools:**
   - Network tab → XHR/Fetch filter
   - Look for `tonconnect-manifest.json` request
   - Check response body and headers

4. **Check TonConnect docs:**
   - https://ton-connect.github.io/docs/

5. **If still failing:**
   - Verify domain HTTPS
   - Check DNS resolution
   - Test with `curl` before browser test
