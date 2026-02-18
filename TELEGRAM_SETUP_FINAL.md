# Final Telegram Integration - Production Flow

## ✅ COMPLETED FIXES

### 1. Webhook Endpoint Routing
- **Route**: `POST /api/v1/telegram/webhook`  
- **Mounted**: At prefix `/api/v1/telegram` in `app/main.py`
- **Handler**: `telegram_webhook()` in `app/routers/telegram_mint_router.py` line 290
- **Returns**: `{"ok": True}` on success (200 OK)
- **Returns**: `{"ok": True}` even on error (prevents Telegram retry loops)
- **Auth**: Validates `X-Telegram-Bot-Api-Secret-Token` header if configured
- **Status Code**: Returns 401 Unauthorized ONLY if secret validation fails (then raises exception)

### 2. Fallback Route Protection
- **New Route**: `POST /telegram/webhook` (without `/api/v1` prefix)
- **Handler**: Logs warning and returns 404 with helpful message
- **Purpose**: Catches misconfigured clients trying old path

### 3. WebApp Init Endpoint
- **Route**: `GET /api/v1/telegram/web-app/init`
- **Query**: `?init_data=...` (Telegram SDK initData)
- **Handler**: `web_app_init()` in `app/routers/telegram_mint_router.py` line 1656
- **Flow**:
  1. Parse init_data URL-encoded string
  2. Verify HMAC-SHA256 signature using bot token
  3. Extract user JSON from parsed data
  4. Get telegram_id from user data
  5. Authenticate user (create if new)
  6. Return user with REAL telegram_id
- **Returns**:
  ```json
  {
    "success": true,
    "user": {
      "id": "uuid-string",
      "telegram_id": 123456789,
      "telegram_username": "username",
      "full_name": "Full Name",
      "avatar_url": "url or null",
      "email": "email or null",
      "is_verified": true/false,
      "user_role": "user",
      "created_at": "2024-01-01T00:00:00"
    }
  }
  ```
- **Error**: Returns 401 Unauthorized if signature invalid
- **Error**: Returns 400 Bad Request if init_data format invalid
- **Error**: Returns 500 Internal Server Error if auth service fails

### 4. Telegram Signature Verification
- **File**: `app/utils/telegram_security.py`
- **Function**: `verify_telegram_data()`
- **Algorithm**: HMAC-SHA256
- **Secret**: `SHA256(bot_token)` → digest (binary)
- **Message**: All init_data params except "hash", sorted by key, joined by `\n`
- **Timing-Safe**: Uses `hmac.compare_digest()` to prevent timing attacks
- **Logging**: Logs verification failures with WARNING level

### 5. User Extraction
- **Source**: Verified init_data
- **Extract**:
  - `telegram_id = user_data.get("id")` → integer
  - `telegram_username = user_data.get("username")`
  - `first_name`, `last_name` for full_name computation
- **No Fallbacks**: Always uses REAL values from Telegram, never mock/dev users
- **Attach**: Stores as `request.state.telegram_user` for dependency injection

### 6. Database Access
- **Dependency**: `get_telegram_user_from_request()` - validates signature & returns user
- **Used By**: All protected endpoints: `/web-app/user`, `/web-app/wallets`, `/web-app/nfts`, `/web-app/mint`, etc.
- **Returns**: `dict` with `user_id`, `telegram_id`, `user_obj`
- **Validates**: Extracts telegram_id from init_data, verifies signature
- **Errors**: Returns 401 on any auth failure

## 🔧 CONFIGURATION CHECKLIST

### .env Settings
```bash
ENVIRONMENT=development          # (or 'production' for Railway)
DEBUG=true                       # (false in production)
TELEGRAM_BOT_TOKEN=...          # REAL bot token from @BotFather
TELEGRAM_WEBHOOK_URL=http://localhost:8000/api/v1/telegram/webhook
TELEGRAM_WEBHOOK_SECRET=dev-webhook-secret-secure-2024
TELEGRAM_AUTO_SETUP_WEBHOOK=false  # Don't auto-setup in development
TELEGRAM_WEBAPP_URL=http://localhost:8000/web-app/
```

### Production.env Settings
```bash
ENVIRONMENT=production
DEBUG=false
TELEGRAM_BOT_TOKEN=...          # REAL bot token
TELEGRAM_WEBHOOK_URL=https://your-domain.com/api/v1/telegram/webhook
TELEGRAM_WEBHOOK_SECRET=your-secure-secret-key-here
TELEGRAM_AUTO_SETUP_WEBHOOK=true   # Auto-register with Telegram
TELEGRAM_WEBAPP_URL=https://your-domain.com/web-app/
```

## 📡 API ENDPOINTS - CORRECT PATHS

### Telegram Webhook (Bot Integration)
```bash
POST /api/v1/telegram/webhook HTTP/1.1
X-Telegram-Bot-Api-Secret-Token: dev-webhook-secret-secure-2024
Content-Type: application/json

{
  "update_id": 12345,
  "message": {
    "message_id": 1,
    "date": 1234567890,
    "chat": {"id": 123456789, ...},
    "from": {"id": 123456789, "username": "testuser", ...},
    "text": "/start"
  }
}

Response (200 OK):
{"ok": true}
```

### WebApp Init (Authentication)
```bash
GET /api/v1/telegram/web-app/init?init_data=user%3D%7B%22id%22%3A123...

Response (200 OK):
{
  "success": true,
  "user": {
    "id": "uuid",
    "telegram_id": 123456789,
    "telegram_username": "username",
    ...
  }
}

Response (401 Unauthorized):
{
  "detail": "Invalid Telegram data signature"
}
```

### WebApp User Info (Authenticated)
```bash
GET /api/v1/telegram/web-app/user?user_id=uuid&init_data=...

Headers:
- init_data in query parameter (required for signature verification)

Response (200 OK):
{
  "success": true,
  "user": { ... }
}

Response (401 Unauthorized):
{
  "detail": "Missing init_data - authentication failed"
}
```

## 🐛 COMMON ISSUES & FIXES

### Issue: POST /telegram/webhook returns 404
**Root Cause**: Telegram posting to `/telegram/webhook` instead of `/api/v1/telegram/webhook`  
**Fix**: Add `http://localhost:8000/api/v1/telegram/webhook` to environment  
**Fallback**: We added explicit 404 handler at `/telegram/webhook` that logs the issue

### Issue: Telegram signature verification fails
**Root Cause**: 
1. Wrong bot token in .env
2. init_data modified/tampered
3. Server time out of sync

**Fix**:
1. Verify TELEGRAM_BOT_TOKEN is correct (from @BotFather)
2. Ensure init_data is passed exactly as received from Telegram SDK
3. Check server time with `timedatectl` (NTP sync required)

### Issue: User ID not resolved
**Root Cause**: init_data not being sent or signature verification failing  
**Fix**: Ensure frontend sends fresh init_data from Telegram.WebApp.initData  
**Debug**: Check logs for "Telegram signature verification failed"

### Issue: Frontend hitting wrong paths
**Root Cause**: CONFIG.API_BASE not aligned with backend mount points  
**Frontend**: `/api/v1/telegram` prefix defined in app.js line 71
**Backend**: `/api/v1/telegram` prefix in main.py line 175-178  
**Payments**: `/api/v1/payments/*` (absolute paths)

### Issue: External image URLs routed through API
**Root Cause**: Would create paths like `/api/v1/nft/https://external.com/image`  
**Fix**: Verified frontend uses direct URLs in `<img src="">` tags  
**Status**: Frontend is correct - uses direct URLs for NFT images

## 🔑 KEY DIFFERENCES FROM PREVIOUS VERSIONS

### Before
- Webhook at `/webhook` (root)
- No fallback handler
- Limited error logging
- Unclear telegram_id extraction

### After
- Webhook at `/api/v1/telegram/webhook` (correct mount point)
- Fallback handler at `/telegram/webhook` (logs and rejects)
- Comprehensive logging at each auth step
- Clear telegram_id extraction from verified init_data
- HMAC-SHA256 verification with timing-safe comparison
- 401 errors on auth failure (visible to frontend)
- 200 OK always on webhook (prevents Telegram retries)

## ✅ VERIFICATION STEPS

1. **Check Environment**
   ```bash
   python verify_telegram_setup.py
   ```

2. **Start Backend**
   ```bash
   python -m uvicorn app.main:app --reload
   ```

3. **Check Logs**
   ```
   INFO: Telegram signature verification PASSED
   INFO: Extracted telegram_id: 123456789
   INFO: User authenticated: id=..., telegram_id=...
   ```

4. **Test Endpoints**
   ```bash
   # Get test user (development only)
   curl http://localhost:8000/api/v1/telegram/web-app/test-user
   
   # Try webhook (manual)
   curl -X POST http://localhost:8000/api/v1/telegram/webhook \
     -H "X-Telegram-Bot-Api-Secret-Token: dev-webhook-secret-secure-2024" \
     -H "Content-Type: application/json" \
     -d '{"update_id": 1, "message": {"message_id": 1, "date": 1234567890, "chat": {"id": 123}, "from": {"id": 123, "username": "test"}, "text": "/start"}}'
   ```

5. **Test from Telegram**
   - Open bot in Telegram
   - Send `/start` command
   - WebApp button should open
   - Should authenticate successfully
   - Should show user's real telegram_id

## 📝 FINAL CHECKLIST

- ✅ Webhook endpoint at `/api/v1/telegram/webhook`
- ✅ Webhook validates secret token
- ✅ WebApp init endpoint at `/api/v1/telegram/web-app/init`
- ✅ Signature verification using HMAC-SHA256
- ✅ telegram_id extracted from verified init_data
- ✅ User created/updated in database
- ✅ All WebApp endpoints require init_data
- ✅ 401 Unauthorized on auth failure
- ✅ 200 OK on webhook success
- ✅ Comprehensive logging at each step
- ✅ Fallback handler for old `/telegram/webhook` path
- ✅ .env has correct webhook URL
- ✅ ENVIRONMENT set to development/production correctly
- ✅ TELEGRAM_AUTO_SETUP_WEBHOOK=false in local dev

## 🚀 PRODUCTION DEPLOYMENT

For Railway or similar:

1. Set environment to `production`
2. Update webhook URL to your domain
3. Set `TELEGRAM_AUTO_SETUP_WEBHOOK=true`
4. Backend will auto-register webhook on startup
5. Bot will send messages to your domain
6. WebApp will open from your domain

All request auth, logging, and error handling is production-ready.
