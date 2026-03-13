# TON Connect Button - Connection Failed Fix

## Root Cause Analysis

The TON Connect button was failing with "connection failed" error due to **manifest URL path mismatch** and **missing APP_URL configuration**.

### Issue 1: Wrong Manifest Path (Frontend)
**Location:** `app/static/webapp/js/unified-auth.js` line 54

**Problem:** The TonConnect UI was initialized with the wrong manifest path:
```javascript
// WRONG - loads hardcoded static file
manifestUrl: '/static/tonconnect-manifest.json'
```

This path loads the **static file** at `app/static/tonconnect-manifest.json` which contains:
```json
{
  "url": "https://localhost:8000",  // ❌ HARDCODED - WRONG FOR PRODUCTION
  ...
}
```

**Why it fails:** 
- TonConnect SDK validates that the manifest's `url` field matches the current domain
- Hardcoded `localhost:8000` causes CORS/validation failure when deployed to production
- Frontend accesses from different domain → manifest domain mismatch → connection fails

**Solution:** Use the **dynamic endpoint** which generates correct origin at runtime:
```javascript
// CORRECT - uses dynamic endpoint that sets correct origin
manifestUrl: '/tonconnect-manifest.json'  
```

---

### Issue 2: Missing APP_URL Configuration (Backend)
**Location:** `.env` and `.env.production` files

**Problem:** The backend's manifest endpoint (`app/main.py` line 203) tries to determine the correct origin using:

```python
# Method 1: Check for configured APP_URL
origin = ""
if settings.app_url:
    origin = settings.app_url.rstrip('/')
```

But `APP_URL` was **never set** in environment variables, so it falls back to:
- X-Forwarded headers (may not work depending on proxy)
- Incoming request origin (unreliable in some deployments)
- Hardcoded `https://localhost:8000` (always wrong)

**Solution:** Explicitly set `APP_URL` in `.env` files:
```env
APP_URL=https://nftplatformbackend-production-9081.up.railway.app
```

---

## Fixes Applied

### 1. ✅ Frontend Fix - Correct Manifest Path
**File:** `app/static/webapp/js/unified-auth.js` line 54

**Changed from:**
```javascript
manifestUrl: '/static/tonconnect-manifest.json',
```

**Changed to:**
```javascript
manifestUrl: '/tonconnect-manifest.json',
```

### 2. ✅ Backend Fix - Add APP_URL Configuration

**File:** `.env`
```env
TELEGRAM_WEBAPP_URL=https://nftplatformbackend-production-9081.up.railway.app/webapp/
APP_URL=https://nftplatformbackend-production-9081.up.railway.app
```

**File:** `.env.production`
```env
# App URL (used for TON Connect manifest and other absolute URLs)
# IMPORTANT: Set this to your actual deployment domain
APP_URL=https://yourdomain.com
```

### 3. ✅ Backend Robustness - Fallback Logic
**File:** `app/main.py` lines 223-228

Added fallback to use `TELEGRAM_WEBAPP_URL` if `APP_URL` is not set:
```python
# Method 1b: If APP_URL not set, try to derive from TELEGRAM_WEBAPP_URL
if not origin and settings.telegram_webapp_url:
    parsed = urlparse(settings.telegram_webapp_url)
    if parsed.scheme and parsed.netloc:
        origin = f"{parsed.scheme}://{parsed.netloc}"
```

---

## How the Fix Works

### Flow Diagram

```
1. Frontend loads index.html
   ↓
2. TonConnect UI initializes with manifestUrl: '/tonconnect-manifest.json'
   ↓
3. Browser fetches manifest from /tonconnect-manifest.json
   ↓
4. Backend endpoint @app.get("/tonconnect-manifest.json")
   ├─ Gets APP_URL from settings (or derives from TELEGRAM_WEBAPP_URL)
   ├─ Falls back to X-Forwarded headers (Railway proxy)
   ├─ Falls back to request origin
   ↓
5. Endpoint returns JSON with correct origin:
   {
     "url": "https://nftplatformbackend-production-9081.up.railway.app",
     "name": "GiftedForge",
     ...
   }
   ↓
6. TonConnect SDK validates origin matches browser domain ✓
   ↓
7. TON wallet connection succeeds ✓
```

---

## Verification Steps

### 1. Test Manifest Endpoint (Backend)
```bash
# Check that manifest returns correct origin
curl https://youdomain.com/tonconnect-manifest.json | jq .url

# Expected output:
# "https://yourdomain.com"
```

### 2. Check Frontend Console
1. Open DevTools (F12)
2. Go to Console tab
3. You should see:
   ```
   ✅ TonConnect UI initialized
   ✓ TonConnect manifest loaded: https://yourdomain.com
   ```

### 3. Test TON Connect Button
1. Click TON Connect button
2. You should see wallet selection dialog (not "connection failed")
3. Select wallet and complete connection

### 4. Verify Configuration
```bash
# Check .env file has APP_URL
grep "APP_URL=" .env

# Expected output:
# APP_URL=https://yourdomain.com
```

---

## Production Deployment Checklist

- [ ] Update `.env` with correct `APP_URL` for your domain
- [ ] Update `.env.production` template with your domain
- [ ] Rebuild and deploy application
- [ ] Test TON Connect button in production
- [ ] Verify `/tonconnect-manifest.json` endpoint returns correct origin
- [ ] Check browser console for errors
- [ ] Test with actual TON wallet (Tonkeeper, Telegram Wallet, etc.)

---

## Environment Variable Reference

```env
# Required for TON Connect to work
APP_URL=https://your-domain.com

# Also update Telegram webhook to match
TELEGRAM_WEBAPP_URL=https://your-domain.com/webapp/
TELEGRAM_WEBHOOK_URL=https://your-domain.com/api/v1/telegram/webhook
```

---

## Why This Solution is Robust

1. **Dynamic Origin**: Manifest origin is generated at runtime, not hardcoded
2. **Multiple Fallbacks**: Works with `APP_URL`, `TELEGRAM_WEBAPP_URL`, X-Forwarded headers, or request origin
3. **Proxy Compatible**: Handles Railway's reverse proxy headers
4. **No Cache Issues**: Manifest is always fresh on each request
5. **Correct Path**: Uses the correct endpoint that dynamic generation logic
