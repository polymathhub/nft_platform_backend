# Frontend-Backend Integration Audit Report

**Date**: February 20, 2026  
**Scope**: Complete audit of app.js API calls vs backend endpoints  
**Status**: Comprehensive issue identification and recommendations

---

## Executive Summary

### Critical Issues Found
1. ⚠️ **Missing `import-wallet` endpoint** - app.js calls it, backend doesn't implement it
2. ⚠️ **Parameter naming inconsistencies** - `init_data` handling varies across endpoints
3. ⚠️ **Missing `user_id` in POST body** - Some endpoints expect it, app.js doesn't always send it
4. ⚠️ **Authentication credential gaps** - Inconsistent init_data passing
5. ⚠️ **Error response handling** - Frontend doesn't handle all error cases
6. ⚠️ **Missing endpoints** - Several app.js calls have no backend implementation

### Risk Level: **HIGH**
Multiple features will fail in production without backend implementation.

---

## 1. API Endpoint Inventory

### Frontend API Calls (from app.js)

#### Authentication & Initialization
```
✓ GET  /web-app/init?init_data=<encoded>
✓ GET  /web-app/user?user_id=<id>&init_data=<encoded>
```

#### Wallets
```
✓ GET  /web-app/wallets?user_id=<id>&init_data=<encoded>
✓ POST /web-app/create-wallet
     Body: { blockchain, wallet_type, is_primary, init_data }
✗ POST /web-app/import-wallet  ← MISSING
     Expected Body: { blockchain, address, public_key?, is_primary, init_data }
✓ POST /web-app/set-primary
     Body: { wallet_id, user_id?, init_data }
```

#### NFTs
```
✓ GET  /web-app/nfts?user_id=<id>&init_data=<encoded>
✓ POST /web-app/mint
     Body: { user_id, wallet_id, nft_name, nft_description, image_url, init_data }
✓ POST /web-app/transfer
     Body: { user_id, nft_id, to_address, init_data }
✓ POST /web-app/burn
     Body: { user_id, nft_id, init_data }
```

#### Marketplace
```
✓ GET  /web-app/marketplace/listings?limit=50&init_data=<encoded>
✓ GET  /web-app/marketplace/mylistings?user_id=<id>&init_data=<encoded>
✓ POST /web-app/list-nft
     Body: { user_id, nft_id, price, currency, init_data }
✓ POST /web-app/make-offer
     Body: { user_id, listing_id, offer_price, init_data }
✓ POST /web-app/cancel-listing
     Body: { user_id, listing_id, init_data }
```

#### Dashboard
```
✓ GET  /web-app/dashboard-data?user_id=<id>&init_data=<encoded>
```

#### Payments
```
✓ GET  /api/v1/payments/balance?init_data=<encoded>
✓ GET  /api/v1/payments/history?limit=10&init_data=<encoded>
✓ POST /api/v1/payments/deposit/initiate
     Body: { wallet_id, amount, external_address, init_data }
✓ POST /api/v1/payments/deposit/confirm
     Body: { payment_id, transaction_hash, init_data }
✓ POST /api/v1/payments/withdrawal/initiate
     Body: { wallet_id, amount, destination_address, init_data }
✓ POST /api/v1/payments/withdrawal/approve
     Body: { payment_id, init_data }
```

### Backend Endpoint Implementation Status

#### Fully Implemented ✓
- `/web-app/init` - GET
- `/web-app/user` - GET
- `/web-app/wallets` - GET
- `/web-app/create-wallet` - POST
- `/web-app/nfts` - GET
- `/web-app/mint` - POST
- `/web-app/transfer` - POST
- `/web-app/burn` - POST
- `/web-app/set-primary` - POST
- `/web-app/list-nft` - POST
- `/web-app/make-offer` - POST
- `/web-app/cancel-listing` - POST
- `/web-app/marketplace/listings` - GET
- `/web-app/marketplace/mylistings` - GET
- `/web-app/dashboard-data` - GET
- `/api/v1/payments/balance` - GET
- `/api/v1/payments/history` - GET
- `/api/v1/payments/deposit/initiate` - POST
- `/api/v1/payments/deposit/confirm` - POST
- `/api/v1/payments/withdrawal/initiate` - POST
- `/api/v1/payments/withdrawal/approve` - POST

#### Missing - CRITICAL ❌
- `/web-app/import-wallet` - POST **[NOT IMPLEMENTED]**

---

## 2. Critical Issues

### Issue #1: Missing Import-Wallet Endpoint

**Severity**: 🔴 CRITICAL

**Location**: app.js line 429

```javascript
async importWallet(blockchain, address, publicKey = null, isPrimary = false) {
  const initData = state.initData || (window.Telegram?.WebApp?.initData || '');
  return this._fetch(`/web-app/import-wallet`, {
    method: 'POST',
    body: { blockchain, address, public_key: publicKey, is_primary: isPrimary, init_data: initData }
  });
}
```

**Backend Status**: Not found in telegram_mint_router.py

**Impact**: 
- Users cannot import external wallets
- UI has form for wallet import but endpoint will return 404
- Feature is unusable

**Frontend Consequences**:
```
POST /web-app/import-wallet
→ 404 Not Found
→ showStatus('Error: ...')
→ User sees blank error message
```

**Recommendation**: Implement this endpoint in telegram_mint_router.py

---

### Issue #2: Init_data Parameter Passing Inconsistency

**Severity**: 🟠 HIGH

**Problem**: Different patterns for passing init_data

**Pattern A - Query Parameter (GET requests)**:
```javascript
// app.js line 406
return this._fetch(`/web-app/init?init_data=${encodeURIComponent(initData)}`);

// app.js line 412
return this._fetch(`/web-app/user?user_id=${userId}&init_data=${encodeURIComponent(initData)}`);
```

**Pattern B - Request Body (POST requests)**:
```javascript
// app.js line 423
return this._fetch(`/web-app/create-wallet`, {
  method: 'POST',
  body: { blockchain, wallet_type: walletType, is_primary: isPrimary, init_data: initData }
});
```

**Why It Matters**:
- GET requests: init_data added MANUALLY to URL before calling _fetch
- POST requests: init_data added AUTOMATICALLY by _fetch wrapper
- **Duplicate init_data** may be sent for POST requests with init_data in URL

**Code in _fetch (lines 305-312)**:
```javascript
if (method !== 'GET') {
  const body = Object.assign({}, options.body || {});
  if (initData) {
    body.init_data = initData;  // ← Added automatically
  }
  options.body = body;
}
```

**Issue**: If app.js manually passes init_data in body AND _fetch adds it again → duplication

**Recommendation**: Standardize to ONE of these patterns:
- Option A: Always pass init_data in body for POST (let _fetch handle it)
- Option B: Always use _fetch to inject init_data, never manually set it

---

### Issue #3: Missing user_id in POST Request Bodies

**Severity**: 🟠 HIGH

**Problem**: Some POST endpoints expect `user_id` in body, but app.js doesn't consistently send it

**Example from app.js line 453**:
```javascript
async mintNft(userId, walletId, nftName, description, imageUrl = null) {
  // userId parameter exists
  // But NOT always included in body
  return this._fetch(`/web-app/mint`, {
    method: 'POST',
    body: {
      user_id: userId,           // ← Included
      wallet_id: walletId,
      nft_name: nftName,
      nft_description: description,
      image_url: imageUrl,
      init_data: initData,
    }
  });
}
```

**But other endpoints don't include it**:
```javascript
// app.js line 470 - burnNft doesn't include user_id
async burnNft(userId, nftId) {
  return this._fetch(`/web-app/burn`, {
    method: 'POST',
    body: { user_id: userId, nft_id: nftId, init_data: initData }
    // ✓ Actually it DOES include it
  });
}
```

**_fetch Auto-injection (line 318)**:
```javascript
if (state.user && state.user.id) {
  body.user_id = state.user.id;  // Auto-inject from state
}
```

**Issue**: 
- _fetch automatically injects user_id if state.user.id exists
- Some endpoints have user_id in body twice
- Unclear which is authoritative - function param or auto-injected value

**Recommendation**: 
- Use ONLY state.user.id (auto-injected by _fetch)
- Remove manual user_id parameter from app.js methods
- OR only use manual user_id and remove auto-injection

---

### Issue #4: Inconsistent Authentication/Authorization

**Severity**: 🟠 HIGH

**Problem**: Different authentication mechanisms for different endpoint groups

**Telegram Web-App Endpoints** (`/web-app/*`):
- Require `init_data` in query param or body
- Authenticated via `get_telegram_user_from_request` dependency
- extract Telegram user from init_data

**Payment Endpoints** (`/api/v1/payments/*`):
- Use standard FastAPI `get_current_user` dependency
- Require Bearer token OR Telegram auth
- Different auth scheme

**Code in backend**:
```python
# telegram_mint_router.py - web-app endpoints
auth: dict = Depends(get_telegram_user_from_request)

# payment_router.py - payment endpoints  
current_user: User = Depends(get_current_user)
```

**Frontend Issue**:
- app.js sends init_data to both `/web-app/*` and `/api/v1/payments/*`
- But payment endpoints may expect JWT token instead
- Inconsistent auth could cause permission errors

**Example**: 
```javascript
async getBalance() {
  // Sends only init_data - payment router expects current_user via JWT
  return this._fetch(`/api/v1/payments/balance?init_data=...`);
}
```

**Recommendation**:
- Document which endpoints use which auth
- Ensure consistent auth for web-app vs API endpoints
- Consider unified auth token generation after web-app init

---

### Issue #5: Error Response Structure Inconsistency

**Severity**: 🟡 MEDIUM

**Problem**: Different backends return different error structures

**Payment Router** (payment_router.py):
```python
raise HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail=error,
)
```
Returns: `{ "detail": "error message" }`

**Telegram Router** (telegram_mint_router.py):
```python
return {
    "success": False,
    "error": "error message",
    "data": None
}
```
Returns: `{ "success": false, "error": "error message", "data": null }`

**Frontend Error Handling** (app.js line 376):
```javascript
const errorMsg = data?.detail || data?.error || `HTTP ${response.status}`;
throw new Error(errorMsg);
```

**Issue**:
- Some endpoints return `detail` field
- Some return `error` field
- Frontend tries both, but doesn't handle custom error structures
- Inconsistent error responses make debugging harder

**Recommendation**: Standardize error response structure across all endpoints:
```json
{
  "success": false,
  "error": "error_code",
  "detail": "human readable message",
  "status_code": 400
}
```

---

### Issue #6: Response Structure Inconsistency

**Severity**: 🟡 MEDIUM

**Problem**: Different endpoints return different response structures

**Example - Dashboard Data** (from app.js line 620):
```javascript
const dashData = await API.getDashboardData(state.user.id);
if (!dashData || !dashData.success) {  // ← Expects success field
  throw new Error(dashData?.error || dashData?.detail || 'Failed to load dashboard');
}
const wallets = dashData.wallets || [];
```

**But Payment Router** returns different structure:
```python
# payment_router.py line 72
return {
    "user_id": str(current_user.id),
    "history": history,
}
```
No `success` field!

**Frontend consequence**:
```javascript
const balanceResult = await API.getBalance();
// balanceResult doesn't have success field
// Frontend checks data.success - will get undefined
```

**Recommendation**: Standardize response structure:
```json
{
  "success": true,
  "data": { /* endpoint-specific data */ },
  "message": "Human readable message"
}
```

---

### Issue #7: Missing Response Validation

**Severity**: 🔴 CRITICAL

**Problem**: Frontend doesn't validate response structure before using data

**Example from app.js line 624**:
```javascript
const wallets = dashData.wallets || [];
const nfts = dashData.nfts || [];
const listings = dashData.listings || [];

// Immediately used in rendering without type check
state.wallets = wallets;  // Could be null, undefined, string, number, etc.
```

**If backend returns**:
```json
{
  "success": true,
  "wallets": "string instead of array",
  "nfts": null,
  "listings": undefined
}
```

**Frontend fails silently or crashes**:
```javascript
nfts.slice(0, 3)  // TypeError: Cannot read property 'slice' of null
```

**Recommendation**: Add strict type validation:
```javascript
if (!Array.isArray(wallets)) {
  log('Invalid wallets response', 'error');
  throw new Error('Expected array of wallets');
}
```

---

### Issue #8: Missing Timeout on GET Requests

**Severity**: 🟡 MEDIUM

**Problem**: GET requests in _fetch don't have timeout protection in some browsers

**Code in app.js line 347**:
```javascript
const response = await fetch(url, fetchOptions);
```

**Issue**:
- Fetch API doesn't support timeout parameter
- Promise.race with timeout is only in _catch_ handler
- Slow GET requests can hang the page

**Recent change**: Yes, _fetch has timeout wrapper (line 288)

**But check if working correctly**:
```javascript
async _fetch(endpoint, options = {}, attempt = 1) {
  // ... setup code ...
  const response = await fetch(url, fetchOptions);  // No timeout here!
  // Timeout only happens on error catch
}
```

**Issue**: Timeout not enforced on successful requests

**Recommendation**: Use AbortController timeout:
```javascript
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), CONFIG.TIMEOUT);
const response = await fetch(url, { ...fetchOptions, signal: controller.signal });
clearTimeout(timeoutId);
```

---

### Issue #9: Race Condition on State.initData

**Severity**: 🟡 MEDIUM

**Problem**: Race condition when multiple endpoints call simultaneously

**Code in app.js line 305**:
```javascript
let initData = state.initData;
if (!initData && typeof window.Telegram !== 'undefined' && window.Telegram.WebApp) {
  initData = window.Telegram.WebApp.initData;
}
```

**Scenario**:
1. User opens app, state.initData = null
2. User clicks "Mint NFT" → API call starts
3. API call checks state.initData (null) → falls back to window.Telegram
4. Meanwhile, /web-app/init completes and sets state.initData
5. Two different initData values used in same request batch

**Issue**: Data inconsistency across multiple concurrent requests

**Recommendation**: 
- Ensure state.initData set in initApp before any other requests
- Add synchronization point to wait for init_data before other calls

---

## 3. Feature Implementation Status

### Dashboard
**Status**: ✅ **WORKING**
- All GET endpoints implemented
- Response structure: `{ success, data, wallets, nfts, listings }`
- No critical issues

### Wallets
**Status**: ⚠️ **PARTIAL**
- ✅ Create wallet - Working
- ✅ Get wallets - Working
- ✅ Set primary - Working
- ❌ Import wallet - **NOT IMPLEMENTED**

**Action Required**: Implement `/web-app/import-wallet` endpoint

### NFTs
**Status**: ✅ **WORKING**
- All endpoints implemented (mint, transfer, burn)
- Response structures consistent
- No critical issues

### Marketplace
**Status**: ✅ **WORKING**
- All listing endpoints implemented
- Response structures consistent
- No critical issues

### Payments
**Status**: ⚠️ **PARTIAL**
- ✅ Balance - Working
- ✅ History - Working
- ✅ Deposit initiate/confirm - Working
- ✅ Withdrawal initiate/approve - Working
- ⚠️ Auth scheme differs from web-app endpoints

**Action Required**: Verify payment auth works with Telegram init_data

---

## 4. Request/Response Mapping Details

### Profile: GET /web-app/init

**Frontend (app.js line 406)**:
```javascript
return this._fetch(`/web-app/init?init_data=${encodeURIComponent(initData)}`);
```

**Backend** (telegram_mint_router.py line 1620):
```python
@router.get("/web-app/init")
async def web_app_init(
    init_data: str = None,
    db: AsyncSession = Depends(get_db_session),
) -> dict
```

**Status**: ✅ Match

---

### Profile: POST /web-app/create-wallet

**Frontend (app.js line 423)**:
```javascript
return this._fetch(`/web-app/create-wallet`, {
  method: 'POST',
  body: { blockchain, wallet_type: walletType, is_primary: isPrimary, init_data: initData }
});
```

**Backend (telegram_mint_router.py line 2547)**:
```python
@router.post("/web-app/create-wallet", response_model=dict)
async def create_wallet_for_webapp(
    request: CreateWalletRequest,  # Expects: blockchain, wallet_type, is_primary, init_data
    ...
)
```

**Status**: ✅ Match

**Note**: Backend has 30-second timeout on wallet generation (recently added)

---

### Profile: POST /web-app/import-wallet

**Frontend (app.js line 429)**:
```javascript
return this._fetch(`/web-app/import-wallet`, {
  method: 'POST',
  body: { blockchain, address, public_key: publicKey, is_primary: isPrimary, init_data: initData }
});
```

**Backend**:
```
❌ NOT FOUND - 404 Will Occur
```

**Status**: ❌ Missing - Critical

**Backend Definition Needed**:
```python
@router.post("/web-app/import-wallet", response_model=dict)
async def web_app_import_wallet(
    request: ImportWalletRequest,  # blockchain, address, public_key?, is_primary, init_data
    db: AsyncSession = Depends(get_db_session),
    auth: dict = Depends(get_telegram_user_from_request),
) -> dict:
    # Implementation
```

---

### Profile: GET /api/v1/payments/balance

**Frontend (app.js line 531)**:
```javascript
return this._fetch(`/api/v1/payments/balance?init_data=${encodeURIComponent(initData)}`, {
  headers: { 'X-User-ID': state.user.id }
});
```

**Backend (payment_router.py line 43)**:
```python
@router.get("/balance")
async def get_balance(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> BalanceSummaryResponse
```

**Status**: ⚠️ Partial Match
- Endpoint exists ✅
- Auth mechanism differs ⚠️ (XML vs JWT token expected)
- init_data in query may not work with current auth dependency

**Issue**: 
- Frontend sends init_data in URL
- Backend expects JWT token or Telegram auth
- May cause 401 Unauthorized errors

---

## 5. Data Serialization Issues

### Date/Time Handling

**Backend Response** (example):
```python
{
  "created_at": datetime(2026, 2, 20, 12, 30, 45),
  "updated_at": datetime(2026, 2, 20, 12, 30, 45)
}
```

**Frontend Expected** (app.js line 629):
```javascript
<small>${new Date(w.created_at || Date.now()).toLocaleDateString()}</small>
```

**Issue**:
- Backend serializes datetime as ISO string (FastAPI default)
- Frontend expects ISO strings or timestamps
- ✅ Should work (FastAPI auto-serializes to ISO)

---

### UUID Handling

**Backend Response**:
```python
{
  "id": UUID("550e8400-e29b-41d4-a716-446655440000"),
  "user_id": UUID("...")
}
```

**Frontend Expected** (app.js):
```javascript
// No UUID handling - treated as opaque strings
$('walletsList').innerHTML = ws.map(w => `<div>${w.id}</div>`)
```

**Status**: ✅ Works (FastAPI serializes UUID to string automatically)

---

## 6. Performance Issues

### N+1 Query Problem

**Potential Issue**: Dashboard endpoint may query database for each wallet/NFT

**Code**: app.js line 620
```javascript
const dashData = await API.getDashboardData(state.user.id);
```

**Backend** (telegram_mint_router.py line 1883):
```python
# Check if this does multiple queries without optimization
async def web_app_get_dashboard_data(user_id: str = None, db: AsyncSession = ...):
    # Potential N+1 queries:
    wallets = await db.execute(select(Wallet).where(...))  # Query 1
    nfts = await db.execute(select(NFT).where(...))        # Query 2
    listings = await db.execute(select(...)...)            # Query 3
```

**Recommendation**: Use SQLAlchemy join loading or batch loading

---

## 7. Detailed Recommendations

### Priority 1 - CRITICAL (Do Immediately)

#### 1.1 Implement `/web-app/import-wallet` Endpoint

**File**: `app/routers/telegram_mint_router.py`

**Code Template**:
```python
@router.post("/web-app/import-wallet", response_model=dict)
async def web_app_import_wallet(
    request: ImportWalletRequest,
    db: AsyncSession = Depends(get_db_session),
    auth: dict = Depends(get_telegram_user_from_request),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> dict:
    """Import external wallet for current user."""
    try:
        user = auth.get("user_obj")
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Validate request
        if not request.blockchain or not request.address:
            raise HTTPException(status_code=400, detail="blockchain and address required")
        
        # Import wallet logic
        wallet = await WalletService.import_wallet(
            user_id=user.id,
            blockchain=request.blockchain,
            address=request.address,
            public_key=request.public_key,
            is_primary=request.is_primary,
            db=db
        )
        
        return {
            "success": True,
            "wallet": WalletResponse.from_orm(wallet),
            "message": "Wallet imported successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

#### 1.2 Standardize Error Response Structure

**Across all routers**, use consistent error format:

```python
# Create a utility function in app/utils/responses.py
def error_response(message: str, error_code: str = "ERROR"):
    return {
        "success": False,
        "error": error_code,
        "detail": message,
        "status_code": 400
    }
```

#### 1.3 Fix Response Validation in Frontend

**File**: `app/static/webapp/app.js`

**Add validation functions**:
```javascript
function validateWalletArray(data) {
  if (!Array.isArray(data)) {
    throw new Error(`Expected array of wallets, got ${typeof data}`);
  }
  return data.map(w => {
    if (!w.id || !w.address || !w.blockchain) {
      throw new Error('Invalid wallet structure');
    }
    return w;
  });
}
```

#### 1.4 Ensure init_data Synchronization

**Fix initialization order** in `app.js`:

```javascript
async function init() {
  // 1. Initialize Telegram first
  initWithTelegram();
  
  // 2. WAIT for state.initData to be set
  let efforts = 0;
  while (!state.initData && efforts < 50) {
    await new Promise(r => setTimeout(r, 100));
    efforts++;
  }
  
  if (!state.initData) {
    throw new Error('Failed to get Telegram init_data');
  }
  
  // 3. NOW load other data
  await loadPageData('dashboard');
}
```

---

### Priority 2 - HIGH (Do This Sprint)

#### 2.1 Implement Proper GET Timeout with AbortController

**File**: `app/static/webapp/app.js`, line 288

```javascript
async _fetch(endpoint, options = {}, attempt = 1) {
  const url = `${endpoint}`;
  const method = options.method || 'GET';
  
  try {
    log(`[Attempt ${attempt}] ${method} ${url}`);
    
    // Setup abort controller for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      controller.abort();
      log(`Request timeout (${CONFIG.TIMEOUT}ms): ${method} ${url}`, 'warn');
    }, CONFIG.TIMEOUT);
    
    // ... rest of setup ...
    
    let fetchOptions = {
      method,
      signal: controller.signal,  // ← Add abort signal
      // ... headers and body ...
    };
    
    const response = await fetch(url, fetchOptions);
    clearTimeout(timeoutId);  // Always clear timeout
    
    // ... rest of logic ...
  }
}
```

#### 2.2 Standardize init_data Passing Pattern

**Pattern**: Always use manually-set init_data, never auto-inject

```javascript
// Option A: Remove auto-injection, require manual passing
// Pros: Explicit, no duplicates
// Cons: More verbose

// Current code injects init_data automatically in _fetch
// Recommendation: Either:
// A) Keep auto-injection, remove manual init_data from all methods
// B) Remove auto-injection, make methods responsible

// Choose A (recommended for backwards compatibility):
// Remove all manual init_data from app.js methods
// _fetch handles it via state.initData
```

#### 2.3 Create Unified Error Handler

**File**: `app/static/webapp/app.js`

```javascript
function handleApiError(response, data) {
  // Handle different error formats
  const errorMsg = data?.detail || data?.error || `HTTP ${response.status}`;
  const errorCode = data?.error?.code || 'UNKNOWN_ERROR';
  
  log(`API Error [${errorCode}]: ${errorMsg}`, 'error');
  
  return {
    success: false,
    error: errorCode,
    detail: errorMsg,
    status_code: response.status
  };
}
```

#### 2.4 Audit and Document Authentication Scheme

**Create doc**: `AUTH_SCHEME.md`

```markdown
# Authentication Scheme

## Web-App Endpoints (/web-app/*)
- Auth Method: Telegram WebApp init_data
- Required Field: init_data (query param or POST body)
- Verification: Telegram signature validation
- User Extraction: From parsed init_data JSON

## Payment Endpoints (/api/v1/payments/*)  
- Auth Method: ???
- Required Field: ???
- Verification: ???
- User Extraction: ???
```

---

### Priority 3 - MEDIUM (Do Next Sprint)

#### 3.1 Implement Response Standardization

**All endpoints should return**:
```json
{
  "success": true|false,
  "data": { /* endpoint-specific data */ },
  "error": null|"ERROR_CODE",
  "detail": null|"Human message",
  "message": "Human message"
}
```

#### 3.2 Add Request/Response Logging

**Enable in production only**:
```python
if settings.DEBUG:
    log request/response details
else:
    skip logging to save perf
```

#### 3.3 Implement OpenAPI/Swagger Documentation

```python
app.openapi_url = "/api/openapi.json"
# Generate automatic API docs
```

---

## 8. Testing Checklist

### Frontend Testing
- [ ] Test wallet creation with various blockchains
- [ ] Test wallet import (once implemented)
- [ ] Test NFT minting with image upload
- [ ] Test marketplace browsing and offers
- [ ] Test payment flows (balance, deposit, withdrawal)
- [ ] Test error handling with network throttling
- [ ] Test timeout scenarios (30s+ delay)
- [ ] Test retry logic (trigger 503 errors)
- [ ] Test mobile responsiveness
- [ ] Test Telegram WebApp integration

### Backend Testing
- [ ] Test all endpoints with valid auth
- [ ] Test all endpoints without auth → 401/403
- [ ] Test all endpoints with invalid init_data → 400/401
- [ ] Test response structure consistency
- [ ] Test error response formats
- [ ] Test timeout on wallet generation
- [ ] Test database transaction rollback on error
- [ ] Test rate limiting (if implemented)

### Integration Testing
- [ ] E2E: Create wallet → Mint NFT → List → Buy
- [ ] E2E: Make deposit → Check balance → Make withdrawal
- [ ] E2E: Open from Telegram → complete flow
- [ ] Verify all error messages are user-friendly
- [ ] Verify no sensitive data in logs

---

## 9. Summary of Actions

### Must Fix (Today)
1. Implement `/web-app/import-wallet` endpoint
2. Fix init_data synchronization timing
3. Add response validation in frontend

### Should Fix (This Sprint)
1. Implement GET timeout with AbortController
2. Standardize error responses across all endpoints
3. Document authentication scheme

### Can Fix (Next Sprint)
1. Add comprehensive API documentation (Swagger)
2. Implement response standardization globally
3. Add request/response logging

---

**Document Status**: ✅ Complete  
**Last Updated**: February 20, 2026  
**Next Review**: After implementing critical fixes  
**Owner**: Full-Stack Engineering Team
