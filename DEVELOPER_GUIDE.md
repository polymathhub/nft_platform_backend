# 🧑‍💻 DEVELOPER'S QUICK REFERENCE

**NFT Platform Backend** - Production-Ready  
**Last Updated**: March 31, 2026  
**Status**: ✅ All Systems Operational

---

## 🚀 Quick Start

### Prerequisites
```bash
# Python 3.10+
python --version

# PostgreSQL
psql --version

# Node.js (optional, for frontend tools)
node --version
```

### Setup
```bash
# 1. Clone and navigate
cd nft_platform_backend-main

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\Activate  # Windows
source .venv/bin/activate  # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your values

# 5. Run migrations
alembic upgrade head

# 6. Start server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📁 Project Structure

```
app/
├── main.py                 # FastAPI app entry point
├── config.py              # Settings & environment
├── database.py            # Database setup
├── models/                # SQLAlchemy models
│   ├── user.py           # User model with referral_code
│   ├── nft.py
│   └── ...
├── routers/               # API endpoints
│   ├── user_router.py
│   ├── referrals_router.py  # NEW - Referral system
│   ├── dashboard_router.py
│   └── ...*.py
├── schemas/               # Request/response schemas
├── services/              # Business logic
├── security/              # Auth & security
└── static/webapp/         # Frontend
    ├── dashboard.html
    ├── profile.html
    ├── wallet.html
    ├── js/
    │   ├── auth-system.js
    │   ├── page-init.js    # FIXED - Navigate function
    │   └── ...
    └── css/

tests/                      # Test files
alembic/                   # Database migrations
requirements.txt          # Python dependencies
.env                       # Environment variables
```

---

## 🔑 Key Files & What They Do

| File | Purpose | Edit When |
|------|---------|-----------|
| `app/main.py` | FastAPI app, routes, CORS | Adding new routers |
| `app/config.py` | Settings from environment | Changing configuration |
| `app/models/user.py` | User database model | Modifying user schema |
| `app/routers/user_router.py` | User API endpoints | Changes user endpoints |
| `app/routers/referrals_router.py` | Referral endpoints | **NEW** - Don't modify |
| `app/utils/referral_utils.py` | Referral code generation | **NEW** - Don't modify |
| `app/security/auth.py` | Authentication logic | Changing auth |
| `app/utils/telegram_auth_dependency.py` | Telegram verification | Changing Telegram auth |
| `static/webapp/dashboard.html` | Home page | Adding dashboard features |
| `static/webapp/profile.html` | User profile | User profile changes |
| `static/webapp/js/auth-system.js` | Frontend auth | Frontend auth changes |
| `static/webapp/js/page-init.js` | Page initialization | **FIXED** - Navigation handling |
| `alembic/versions/*.py` | Database migrations | Creating migrations |

---

## 🌐 API Reference

### Core Endpoints

**Authentication** (Stateless)
```bash
# Get current user (requires X-Telegram-Init-Data header)
GET /api/v1/me
Returns: User object with all fields

# Check if authenticated
GET /api/auth/check
Returns: { authenticated: true }
```

**Referrals** (NEW)
```bash
# Get my referral code
GET /api/v1/referrals/my-code
Returns: { referral_code: "ABC12345", referral_count: 0, earned_rewards: 0 }

# Get referral stats
GET /api/v1/referrals/stats
Returns: { total_referrals: 0, total_earned: 0 }
```

**Dashboard**
```bash
# Get stats
GET /api/v1/dashboard/stats
Returns: { nfts_owned: 0, active_listings: 0, wallet_balance: 0, profit_24h: 0 }

# Get user NFTs
GET /api/v1/dashboard/nfts?limit=6
Returns: { nfts: [...] }

# Get transactions
GET /api/v1/dashboard/transactions/recent
Returns: { transactions: [...] }
```

**Wallet**
```bash
# Create wallet
POST /api/v1/wallets/create
Body: { blockchain: "ton", wallet_type: "custodial", is_primary: false }

# Import wallet
POST /api/v1/wallets/import
Body: { mnemonic: "...", blockchain: "ton", wallet_type: "imported" }
```

**Trending**
```bash
# Get trending NFTs
GET /api/v1/trending/nfts

# Get trending collections
GET /api/v1/trending/collections

# Get volume data
GET /api/v1/trending/volume
```

**TON Connect**
```bash
# Connect wallet
POST /api/v1/walletconnect/connect
Body: { wallet_address: "...", init_data: "..." }
```

---

## 🔐 Authentication Pattern

**Every Frontend API Call Should**:
```javascript
// CORRECT - Modern pattern (implemented)
const { telegramFetch } = await import('./telegram-fetch.js');
response = await telegramFetch('/api/v1/endpoint');

// FALLBACK - If module import fails
const initData = window.Telegram?.WebApp?.initData || '';
response = await fetch('/api/v1/endpoint', {
  headers: {
    'Content-Type': 'application/json',
    ...(initData && { 'X-Telegram-Init-Data': initData })
  }
});
```

**Backend Verification**:
```python
from app.utils.telegram_auth_dependency import get_current_user

@router.get("/endpoint")
async def my_endpoint(current_user: User = Depends(get_current_user)):
    # User is already verified here
    return { "data": current_user.name }
```

---

## 📊 Database Tables

### User Table
```sql
-- Key fields
id: UUID primary_key
telegram_id: Int (unique)
username: String
first_name: String
last_name: String
telegram_username: String
photo_url: String
referral_code: String (unique, auto-generated)  -- NEW
created_at: DateTime

-- Generated on user creation:
-- referral_code = generate_referral_code()
```

### Referral Table
```sql
id: UUID primary_key
referrer_id: UUID (foreign key to User)
referred_user_id: UUID (foreign key to User)
reward_amount: Decimal
created_at: DateTime
```

### NFT Table
```sql
id: UUID primary_key
owner_id: UUID
name: String
description: String
image_url: String
collection_name: String
blockchain: String (e.g., "ton")
contract_address: String
token_id: String
created_at: DateTime
```

---

## 🛠️ Common Tasks

### Adding a New API Endpoint

**1. Create Schema** (`app/schemas/my_schema.py`)
```python
from pydantic import BaseModel

class MyRequest(BaseModel):
    field1: str
    field2: int

class MyResponse(BaseModel):
    success: bool
    data: dict
```

**2. Create Router** (`app/routers/my_router.py`)
```python
from fastapi import APIRouter
from app.utils.telegram_auth_dependency import get_current_user

router = APIRouter()

@router.post("/endpoint")
async def my_endpoint(
    request: MyRequest,
    current_user: User = Depends(get_current_user)
):
    # Your logic here
    return { "success": True, "data": {...} }
```

**3. Register in main.py**
```python
from app.routers.my_router import router as my_router

app.include_router(my_router, prefix="/api/v1")
```

**4. Frontend Call**
```javascript
const { telegramFetch } = await import('./telegram-fetch.js');
const response = await telegramFetch('/api/v1/endpoint', {
  method: 'POST',
  body: JSON.stringify({ field1: "value", field2: 123 })
});
```

### Creating a Database Migration

```bash
# Auto-generate from model changes
alembic revision --autogenerate -m "Add new field"

# Edit alembic/versions/xxxx_add_new_field.py if needed

# Apply
alembic upgrade head

# Downgrade if needed
alembic downgrade -1
```

### Fixing Navigation Issues

**In `page-init.js`, the navigate function handles:**
- `/webapp/page.html` → works as-is
- `/page` → converts to `/webapp/page.html`
- `page.html` → converts to `/webapp/page.html`
- `page` → converts to `/webapp/page.html`
- Full URLs → passes through

No need to worry about path format!

### Testing an Endpoint

```bash
# With real Telegram auth
curl -X GET http://localhost:8000/api/v1/me \
  -H "X-Telegram-Init-Data: YOUR_TELEGRAM_DATA"

# Check health
curl http://localhost:8000/health

# Check manifest
curl http://localhost:8000/tonconnect-manifest.json
```

---

## ⚠️ Common Pitfalls

| Mistake | Problem | Solution |
|---------|---------|----------|
| Hardcoded URLs | Fails on different domains | Use environment variables |
| Raw fetch without auth | 401 Unauthorized | Use telegramFetch wrapper |
| Missing X-Telegram-Init-Data | Backend rejects request | Include header on all API calls |
| Wrong path in navigate() | 404 Not Found | Use smart navigate function |
| Not awaiting AuthSystem init | User data not ready | Wait for AuthSystem.isInitialized |
| Modifying referral_utils.py | Changes code generation | Don't modify - it's locked |
| Hardcoded TON SDK calls | Mock data only | Document with ⚠️ markers |

---

## 🧪 Testing

### Run Tests
```bash
# All tests
pytest

# Specific test file
pytest tests/test_user_routes.py

# With coverage
pytest --cov=app tests/
```

### Test Auth Locally
The Telegram SDK doesn't work in localhost browser testing. Use:
```bash
# 1. Create test init data
# 2. Include in manual curl request
# 3. Backend validates signature

# OR use Telegram Bot API test mode:
python scripts/test_telegram_auth.py
```

---

## 📚 Documentation Files

- `claude.md` - Development history & decisions
- `PRODUCTION_DIAGNOSTIC_REPORT.md` - Comprehensive audit
- `FIXES_APPLIED_SUMMARY.md` - What was fixed
- `README.md` - Project overview
- `DOCUMENTATION_INDEX.md` - All docs

---

## 🚀 Deployment

### Railway.app
```bash
# Push to main branch
git push origin main

# Railway auto-deploys
# Check: https://nftplatformbackend-production-ee5f.up.railway.app/health
```

### Docker
```bash
# Build
docker build -t nft-platform .

# Run
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e TELEGRAM_BOT_TOKEN=... \
  nft-platform
```

### Environment for Production
```env
ENVIRONMENT=production
APP_URL=https://nftplatformbackend-production-ee5f.up.railway.app
TELEGRAM_WEBHOOK_URL=https://nftplatformbackend-production-ee5f.up.railway.app/webhook
AUTO_MIGRATE=true
```

---

## 📞 Troubleshooting

### "Module not found" error
```
Check: pip install -r requirements.txt
Verify: pip list
```

### "Database connection failed"
```
Check: DATABASE_URL in .env
Verify: alembic upgrade head
Test: psql $DATABASE_URL
```

### "401 Unauthorized"
```
Check: X-Telegram-Init-Data header present
Verify: Telegram bot token correct in .env
Ensure: initData from actual Telegram mini app (not browser)
```

### "404 Not Found on navigation"
```
The navigate() function in page-init.js now handles all formats
If still 404:
1. Check browser console for JavaScript errors
2. Verify file exists in /webapp/ directory
3. Check /health endpoint (should be 200 OK)
```

### "User name not displaying"
```
Check: window.AuthSystem exists in console
Verify: AuthSystem.isInitialized is true
Ensure: displayTelegramUserInfo() was called
Check: User fields: first_name, username, telegram_username
```

---

## ✅ Pre-Deployment Checklist

- [ ] All env vars set (.env file)
- [ ] Database migrations run (alembic upgrade head)
- [ ] No Python syntax errors (py_compile all files)
- [ ] GET /health returns 200
- [ ] TON Connect manifest loads
- [ ] Authentication works with real Telegram
- [ ] User name displays correctly
- [ ] Referral code shows in profile
- [ ] All navigation links work (no 404s)
- [ ] No console errors in DevTools

---

## 🎓 Learning Resources

- **FastAPI**: https://fastapi.tiangolo.com
- **SQLAlchemy**: https://docs.sqlalchemy.org
- **Telegram SDK**: https://core.telegram.org/bots/webapps
- **TON**: https://ton.org
- **TON Connect**: https://docs.ton.org/develop/wallets/tonconnect
- **Alembic**: https://alembic.sqlalchemy.org

---

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes following patterns in codebase
3. Test thoroughly
4. Commit with clear message
5. Push and create pull request
6. Team reviews and merges

---

**Last Updated**: March 31, 2026  
**Next Review**: When Phase 2 features added  
**Status**: ✅ Production-Ready  
**Contact**: Your team Slack channel
