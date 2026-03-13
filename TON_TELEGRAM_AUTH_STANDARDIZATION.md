# TON Wallet & Telegram Authentication - Standardization Guide

## Overview

This guide describes the standardized authentication system that unifies TON wallet connections and Telegram WebApp authentication for the NFT Platform backend.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Telegram/TON)                   │
└────────────────────┬────────────────────────────────────────┘
                     │
      ┌──────────────┴──────────────┐
      │                             │
      ▼                             ▼
  Telegram Auth             TON Connect
  (initData)                (TonConnect)
      │                             │
      └──────────────┬──────────────┘
                     │
                     ▼
        ┌────────────────────────────────┐
        │  Unified Security Service      │
        │  - verify_telegram_initdata()  │
        │  - verify_ton_wallet()         │
        │  - extract_identity()          │
        └────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────────┐
        │  Unified User Service          │
        │  - get_or_create_user()        │
        │  - link_wallet_to_user()       │
        └────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────────┐
        │  Unified Token Service         │
        │  - generate_tokens()           │
        │  - verify_access_token()       │
        │  - refresh_access_token()      │
        └────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────────┐
        │  Database                      │
        │  - Users                       │
        │  - TON Wallets                 │
        │  - Sessions (Redis)            │
        └────────────────────────────────┘
```

## New Services

### 1. UnifiedSecurityService
**Location:** `app/services/security_service.py`

Handles all security validation:
- Telegram initData HMAC verification
- TON wallet address validation
- TonConnect session validation
- Init data parsing
- Identity data extraction

**Usage Example:**
```python
from app.services.security_service import UnifiedSecurityService
from app.schemas.auth_unified import InitDataSource

# Verify Telegram
is_valid, error = UnifiedSecurityService.verify_telegram_initdata(init_data_str)

# Extract identity from Telegram
identity = UnifiedSecurityService.extract_telegram_identity(init_data_str)

# Extract identity from TON
identity = UnifiedSecurityService.extract_ton_identity(wallet_address)

# Verify TON wallet
is_valid, error = UnifiedSecurityService.verify_ton_wallet_address(wallet_address)
```

### 2. UnifiedUserService
**Location:** `app/services/unified_user_service.py`

Handles user and wallet creation:
- Create or get user from identity
- Link additional wallets to users
- Update user information

**Usage Example:**
```python
from app.services.unified_user_service import UnifiedUserService

# Get or create user from identity
user, error = await UnifiedUserService.get_or_create_user_from_identity(db, identity)

# Link additional TON wallet
wallet, error = await UnifiedUserService.link_ton_wallet_to_user(
    db, 
    user_id, 
    wallet_address,
    metadata
)
```

### 3. UnifiedTokenService
**Location:** `app/services/unified_token_service.py`

Handles JWT token operations:
- Generate access + refresh tokens
- Verify tokens
- Refresh access tokens
- Decode token claims

**Usage Example:**
```python
from app.services.unified_token_service import UnifiedTokenService

# Generate tokens
tokens = UnifiedTokenService.generate_tokens(user_id)

# Verify access token
user_id = UnifiedTokenService.verify_access_token(token)

# Refresh access token
new_tokens = UnifiedTokenService.refresh_access_token(refresh_token)
```

## Unified Schemas

**Location:** `app/schemas/auth_unified.py`

### Request Schemas
- `TelegramAuthRequest` - Telegram initData
- `TONWalletAuthRequest` - TON wallet connection
- `InitDataValidationRequest` - Generic init data validation

### Response Schemas
- `IdentityData` - Extracted identity from any source
- `AuthSuccessResponse` - Unified success response
- `AuthErrorResponse` - Standardized error response
- `TokenResponse` - Token response
- `UserIdentityResponse` - User information
- `WalletIdentityResponse` - TON wallet information

## Implementation Steps

### Step 1: Update Telegram Auth Endpoint

**Before:**
```python
@router.post("/telegram/login")
async def telegram_login(request_obj: Request, db: AsyncSession = Depends(get_db_session)):
    # Manual parsing and validation
    raw = await request_obj.json()
    if not verify_telegram_data(data):
        raise HTTPException(status_code=401)
    
    user, error = await AuthService.authenticate_telegram(db, telegram_id, ...)
    tokens = AuthService.generate_tokens(user.id)
    return {"user": ..., "tokens": ...}
```

**After:**
```python
from app.services.security_service import UnifiedSecurityService
from app.services.unified_user_service import UnifiedUserService
from app.services.unified_token_service import UnifiedTokenService
from app.schemas.auth_unified import TelegramAuthRequest, AuthSuccessResponse

@router.post("/telegram/login", response_model=AuthSuccessResponse)
async def telegram_login(
    request: TelegramAuthRequest,
    db: AsyncSession = Depends(get_db_session),
):
    # Validate initData
    is_valid, error = UnifiedSecurityService.verify_telegram_initdata(request.init_data)
    if not is_valid:
        raise HTTPException(status_code=401, detail=error)
    
    # Extract identity
    identity = UnifiedSecurityService.extract_telegram_identity(request.init_data)
    if not identity:
        raise HTTPException(status_code=400, detail="Failed to extract identity")
    
    # Get or create user
    user, error = await UnifiedUserService.get_or_create_user_from_identity(db, identity)
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    # Generate tokens
    tokens = UnifiedTokenService.generate_tokens(user.id)
    
    return AuthSuccessResponse(
        auth_method="telegram",
        user=UserIdentityResponse.model_validate(user),
        tokens=TokenResponse(**tokens),
    )
```

### Step 2: Update TON Wallet Auth Endpoint

**Before:**
```python
@router.post("/callback")
async def ton_connect_callback(request: Request, db: Session):
    body = await request.json()
    init_data = body.get('init_data')
    
    # Manual validation
    if not verify_telegram_initdata(init_data):
        raise HTTPException(status_code=401)
    
    # Manual user creation
    new_user = User(...)
    new_wallet = TONWallet(...)
    db.add(new_user)
    db.add(new_wallet)
    
    token = create_access_token(...)
    return {"token": token, ...}
```

**After:**
```python
from app.services.security_service import UnifiedSecurityService
from app.services.unified_user_service import UnifiedUserService
from app.services.unified_token_service import UnifiedTokenService

@router.post("/callback")
async def ton_connect_callback(
    request: TONWalletAuthRequest,
    db: AsyncSession = Depends(get_db_session),
):
    # Validate TON wallet address
    is_valid, error = UnifiedSecurityService.verify_ton_wallet_address(request.wallet_address)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)
    
    # Validate Telegram initData (extra security)
    if request.init_data:
        is_valid, error = UnifiedSecurityService.verify_telegram_initdata(request.init_data)
        if not is_valid:
            logger.warning(f"Telegram validation failed: {error}")
    
    # Extract TON identity
    identity = UnifiedSecurityService.extract_ton_identity(
        request.wallet_address,
        request.wallet_metadata
    )
    if not identity:
        raise HTTPException(status_code=400, detail="Invalid wallet identity")
    
    # Get or create user
    user, error = await UnifiedUserService.get_or_create_user_from_identity(db, identity)
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    # Generate tokens
    tokens = UnifiedTokenService.generate_tokens(user.id)
    
    return AuthSuccessResponse(
        auth_method="ton_wallet",
        user=UserIdentityResponse.model_validate(user),
        tokens=TokenResponse(**tokens),
    )
```

### Step 3: Add Token Refresh Endpoint

```python
@router.post("/refresh")
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token using refresh token."""
    tokens = UnifiedTokenService.refresh_access_token(request.refresh_token)
    if not tokens:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    return tokens
```

### Step 4: Update Authentication Dependency

```python
from app.services.unified_token_service import UnifiedTokenService

async def get_current_user(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """Extract and verify user from JWT token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    token = authorization.replace("Bearer ", "")
    user_id = UnifiedTokenService.verify_access_token(token)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user
```

## Configuration

Add to `.env` or Railway environment:
```
SECRET_KEY=<strong-random-key>
TELEGRAM_BOT_TOKEN=<your-bot-token>
TELEGRAM_WEBHOOK_URL=https://your-domain.com/api/v1/telegram/webhook
TELEGRAM_WEBHOOK_SECRET=<optional-secret>
```

## Error Handling

All standardized services use consistent error patterns:

```python
# All services return Tuple[result, error_message]
user, error = await UnifiedUserService.get_or_create_user_from_identity(db, identity)
if error:
    # error is a descriptive string
    raise HTTPException(status_code=400, detail=error)
```

## Testing

### Test Telegram Auth
```bash
curl -X POST http://localhost:8000/auth/telegram/login \
  -H "Content-Type: application/json" \
  -d '{"init_data":"id=123&hash=abc..."}'
```

### Test TON Connection
```bash
curl -X POST http://localhost:8000/api/v1/wallet/ton/callback \
  -H "Content-Type: application/json" \
  -d '{
    "wallet_address":"0:...",
    "init_data":"id=123&hash=abc...",
    "wallet_metadata":{...}
  }'
```

### Test Token Refresh
```bash
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<jwt-refresh-token>"}'
```

## Migration Checklist

- [ ] Create new services (already done)
- [ ] Update Telegram auth endpoint
- [ ] Update TON wallet endpoint
- [ ] Add token refresh endpoint
- [ ] Update auth dependency
- [ ] Remove old verify_telegram_data() function
- [ ] Update existing token generation calls
- [ ] Add tests for all endpoints
- [ ] Test in Railway staging environment
- [ ] Deploy to production

## Benefits

✅ **Consistency**: Single path for all auth types
✅ **Security**: Centralized validation logic
✅ **Maintainability**: Less code duplication
✅ **Scalability**: Easy to add new auth sources
✅ **Testability**: Isolated services easy to test
✅ **Logging**: Standardized error messages
✅ **Documentation**: Clear schemas for API

## Next Steps

1. Review and approve the standard services
2. Update Telegram auth endpoint to use UnifiedSecurityService + UnifiedUserService
3. Update TON wallet endpoint to use new services
4. Add token refresh endpoint
5. Test both flows end-to-end
6. Deploy to staging
7. Deploy to production
