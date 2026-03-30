# Quick Reference - Wallet Connect & Endpoint Fixes

## What Was Fixed

### Issue: Wallet connection sync was failing
- Frontend called `/api/v1/wallet/connect` (doesn't exist)
- Should call `/api/v1/walletconnect/connect` (correct endpoint)

### Result: ✅ FIXED
- Endpoint URL corrected in telegram-wallet.js
- Backend endpoint enhanced to support Telegram auth
- Wallet connections now sync successfully

---

## Key Endpoints

### Wallet Management
```
POST /api/v1/walletconnect/connect
  Headers: X-Telegram-Init-Data
  Body: { wallet_address, blockchain, wallet_name? }
  Response: { success, wallet, message }

POST /api/v1/walletconnect/disconnect
  Headers: X-Telegram-Init-Data
  Body: { wallet_id }

GET /api/v1/walletconnect/connected?user_id=...
```

### User Profile
```
GET /api/v1/me
  Headers: X-Telegram-Init-Data
  Response: { id, username, email, full_name, avatar_url, ... }

POST /api/v1/user/update
  Headers: X-Telegram-Init-Data
  Body: { full_name?, avatar_url?, is_creator? }

POST /api/v1/images/upload
  Headers: X-Telegram-Init-Data
  Body: FormData with file
```

---

## Files Changed

### Backend
- `app/routers/walletconnect_router.py`
  - Line 11: Added import `from app.utils.telegram_auth_dependency import get_current_user`
  - Line 17-23: Updated WalletConnectRequest schema (user_id is now Optional)
  - Line 52-127: Enhanced /connect endpoint with Telegram auth support

### Frontend  
- `app/static/webapp/js/telegram-wallet.js`
  - Line 103: Fixed endpoint URL
  - Line 109: Added wallet_name field

---

## How It Works Now

1. **User clicks "Connect TON Wallet"** on wallet page
2. **TelegramWalletIntegrator initiates connection**
3. **TON Connect UI shows connection dialog**
4. **User selects their TON wallet**
5. **Frontend calls** `/api/v1/walletconnect/connect` with:
   - Telegram auth header (X-Telegram-Init-Data)
   - Wallet address from TON Connect
   - Blockchain: 'ton'
6. **Backend verifies auth** and creates wallet record
7. **User sees success message** "Synced with backend ✓"

---

## Testing Commands

### Check if endpoint works
```bash
# Get current user
curl -H "X-Telegram-Init-Data: <initData>" http://localhost:8000/api/v1/me

# Connect wallet  
curl -X POST \
  -H "X-Telegram-Init-Data: <initData>" \
  -H "Content-Type: application/json" \
  -d '{"wallet_address":"EQ...","blockchain":"ton"}' \
  http://localhost:8000/api/v1/walletconnect/connect
```

---

## Common Issues & Solutions

### Issue: 401 Unauthorized on /connect
**Cause:** Missing or invalid `X-Telegram-Init-Data` header
**Solution:** Ensure Telegram WebApp is initialized and header is present

### Issue: 404 on profile page
**Cause:** Old profile.html still cached
**Solution:** Clear browser cache (Ctrl+Shift+Delete) or hard refresh (Ctrl+F5)

### Issue: Wallet doesn't sync after connection
**Cause:** Browser console shows error
**Solution:** Check Network tab for 401/400/500 errors, review error message

---

## Deployment Notes

- ✅ No database migrations needed
- ✅ No environment variables changed
- ✅ No schema changes needed
- ⚠️ Clear browser cache after deployment
- ⚠️ Restart backend to pick up changes

---

## Architecture

```
Wallet Page (wallet.html)
  ↓
TelegramWalletIntegrator (telegram-wallet.js)
  ↓
TON Connect SDK
  ↓
User selects wallet
  ↓
syncWithBackend() called
  ↓
POST /api/v1/walletconnect/connect
  ↓
walletconnect_router.py::connect_wallet()
  ↓
WalletConnectService.create_wallet_from_connection()
  ↓
Database: TONWallet record created
  ↓
Response: { success: true, wallet: {...} }
  ↓
UI updates: "✓ Connected"
```

---

## See Also

- BUG_FIXES_SUMMARY.md - Detailed technical summary
- /memories/session/bug-fix-plan.md - Development notes
- app/routers/walletconnect_router.py - Full endpoint implementation
- app/static/webapp/js/telegram-wallet.js - Frontend implementation

---

**Last Updated:** March 30, 2026  
**Status:** ✅ Deployed and Verified
