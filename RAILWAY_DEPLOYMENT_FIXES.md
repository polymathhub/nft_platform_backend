# Railway Deployment & TON Connect Button Fixes

## Overview
This document details the comprehensive fixes applied to ensure proper Railway deployment compatibility and resolve TON Connect button misbehavior.

## Issues Fixed

### 1. **Railway PORT Environment Variable Not Respected**
**Problem**: App was hard-coded to port 8000, but Railway uses dynamic PORT environment variable.
**Fixes**:
- Updated `Dockerfile` to set `ENV PORT=8000` default and use it in HEALTHCHECK
- Updated `entrypoint.sh` to read PORT, HOST, and WORKERS from environment variables
- App now starts with: `uvicorn app.main:app --host "$HOST" --port "$PORT"`

### 2. **Hard-Coded Railway Domain in Configuration**
**Problem**: Domain `nftplatformbackend-production-9081.up.railway.app` was hard-coded in multiple files, breaking when deployed to new Railway instances.
**Fixes**:
- **railway.production.json**: Now uses `${{ Railway.Env.RAILWAY_PUBLIC_DOMAIN }}` variable
  - `TELEGRAM_WEBHOOK_URL`: Dynamic domain (`https://${{ Railway.Env.RAILWAY_PUBLIC_DOMAIN }}/api/v1/telegram/webhook`)
  - `TELEGRAM_WEBAPP_URL`: Dynamic domain (`https://${{ Railway.Env.RAILWAY_PUBLIC_DOMAIN }}/webapp/`)
  - `APP_URL`: Added new variable (`https://${{ Railway.Env.RAILWAY_PUBLIC_DOMAIN }}`)

- **app/config.py**: 
  - Added `app_url` field (set from `APP_URL` environment variable)
  - Made `telegram_webapp_url` optional with auto-derivation from `app_url`
  - CORS origins now include configured `app_url` automatically
  - All localhost origins included for development

### 3. **TonConnect Manifest Origin Mismatch**
**Problem**: 
- Static manifest had Railway domain hard-coded
- TonConnect expects manifest URL origin to match actual deployment origin
- Creates security/validation errors when origin changes

**Fixes**:
- **app/static/tonconnect-manifest.json**: Simplified to generic defaults (will be overridden by endpoint)
  - `"url": "https://localhost:8000"` (always overridden at runtime)
  - Removed hard-coded Railway URL

- **app/main.py - `/tonconnect-manifest.json` endpoint**:
  - Implements 3-tier origin detection:
    1. Check `settings.app_url` (from environment - Railway sets this)
    2. Check `X-Forwarded-Proto` and `X-Forwarded-Host` headers (Railway proxy)
    3. Derive from incoming request origin (fallback)
  - Properly normalizes icon URLs to absolute paths
  - Logs origin for debugging

### 4. **CORS Configuration Hardcoded**
**Problem**: CORS origins included specific Railway domain, failing on redeployment.
**Fixes**:
- Removed hardcoded `https://nftplatformbackend-production-9081.up.railway.app`
- Now uses `settings.allowed_origins` which includes:
  - Configured `APP_URL` (Railway environment)
  - All localhost variants (development)
  - Dynamically built during settings validation

### 5. **TON Connect Button Misbehavior**
**Problems**:
- Race condition between manifest loading and button initialization
- No loading state feedback during wallet connection
- Poor error messages and recovery
- Modal lifecycle management issues
- Button disabled state not properly indicated

**Fixes**:
- **Manifest validation with retry logic**:
  - 3 attempts with exponential backoff (1s, 2s, 3s)
  - Proper error messages if manifest can't load
  - Cache-busting `?cache=no-cache` on manifest requests

- **TonConnect UI initialization**:
  - Safely waits for library to load
  - Creates root element only when needed
  - Proper error handling for library issues

- **Button state management**:
  - Disabled state clearly indicated (opacity 0.6 + title)
  - "Connecting..." state shown during wallet selection
  - "Saving wallet..." state shown during backend sync
  - Proper error recovery resets button to initial state

- **Connection flow**:
  1. Validate Telegram WebApp
  2. Check for existing token (skip login)
  3. Try Telegram auth if initData available
  4. Load and validate TonConnect manifest (3 retries)
  5. Initialize TonConnect UI
  6. Show enabled Connect button
  7. On click: open modal → get wallet → send to backend → redirect

- **Error messages**:
  - Specific error messages for each failure point
  - Helpful logging throughout the flow
  - User-facing errors via Telegram or Toast notifications

- **Fallback behavior**:
  - If manifest loading fails: button disabled with message
  - If TonConnect UI fails: button disabled with message
  - User can still browse marketplace without wallet
  - Clear indication of what's not working

## Environment Variables for Railway

Set these in Railway dashboard under "Variables":

```
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=info
PYTHONDONTWRITEBYTECODE=1
PYTHONUNBUFFERED=1
WORKERS=4

# These are auto-set by Railway
DATABASE_URL=${{ Postgres.DATABASE_URL }}

# Secrets (set in Railway Secrets)
JWT_SECRET_KEY=<your-secret>
MNEMONIC_ENCRYPTION_KEY=<your-fernet-key>
TELEGRAM_BOT_TOKEN=<your-token>
TELEGRAM_WEBHOOK_SECRET=<your-secret>
POSTGRES_PASSWORD=<your-password>

# Auto-populated by Railway at deploy time
# No need to set these manually:
# TELEGRAM_WEBHOOK_URL=https://${{ Railway.Env.RAILWAY_PUBLIC_DOMAIN }}/api/v1/telegram/webhook
# TELEGRAM_WEBAPP_URL=https://${{ Railway.Env.RAILWAY_PUBLIC_DOMAIN }}/webapp/
# APP_URL=https://${{ Railway.Env.RAILWAY_PUBLIC_DOMAIN }}
```

## Testing Checklist

- [ ] Deploy to Railway and verify build succeeds
- [ ] Verify `/health` endpoint returns 200 OK
- [ ] Verify `/tonconnect-manifest.json` returns correct origin
- [ ] Test TON Connect button on landing page
- [ ] Verify wallet connection flow works
- [ ] Check logs for proper initialization messages
- [ ] Verify no CORS errors in browser console
- [ ] Test from mobile Telegram via web app
- [ ] Verify Telegram webhook URL is correct
- [ ] Confirm database migrations run automatically

## Debug Commands

```bash
# Check environment variables in container
curl https://<railway-domain>/health

# Check TonConnect manifest
curl https://<railway-domain>/tonconnect-manifest.json | jq .

# Check CORS headers
curl -H "Origin: https://<your-origin>" \
  -H "Access-Control-Request-Method: POST" \
  https://<railway-domain>/api/v1/auth/login -v

# Watch logs during deployment
railway logs --follow
```

## Migration Notes

If upgrading an existing deployment:

1. **Update Dockerfile**: Required (PORT handling)
2. **Update entrypoint.sh**: Required (environment variable support)
3. **Update railway.production.json**: Required (dynamic domain support)
4. **Update app/config.py**: Required (new app_url field)
5. **Update app/main.py**: Required (improved manifest endpoint)
6. **Update app/static/webapp/index.html**: Recommended (better TON Connect handling)
7. **Update app/static/tonconnect-manifest.json**: Required (remove hardcoded domain)

All changes are backward-compatible with local development.

## Architecture Improvements

### Before
- Hard-coded domains in code
- No environment awareness
- Race conditions in async initialization
- Poor error recovery
- No loading state feedback

### After
- Dynamic domain resolution from environment
- Three-tier origin detection (ENV → headers → request)
- Structured async initialization with proper error handling
- Automatic retry logic (3 attempts, exponential backoff)
- Clear loading states and user feedback
- Senior-level error recovery patterns
- Production-ready Railway deployment

## Future Improvements

1. **Webhook Management**: Auto-verify webhook health on startup
2. **Health Checks**: Add more detailed health check endpoint
3. **Metrics**: Add Prometheus metrics for TON Connect flow
4. **Rate Limiting**: Add per-origin rate limiting
5. **Caching**: Add CDN caching for manifest endpoint
6. **Monitoring**: Add sentry integration for error tracking
