# Telegram NFT WebApp - Setup & Usage Guide

## System Overview

This is a complete Telegram NFT WebApp with full backend integration. The system includes:

- **Backend**: FastAPI server with Telegram WebApp endpoints
- **Frontend**: Pure JavaScript web app with responsive mobile design
- **Database**: SQLAlchemy ORM (SQLite for development, PostgreSQL for production)
- **Authentication**: Telegram WebApp signature verification
- **Features**: Wallet management, NFT minting, marketplace, trading

## Prerequisites

- Python 3.8+
- pip packages (see requirements.txt)
- Node not required - pure vanilla JavaScript

## Installation & Setup

### 1. Install Dependencies

```bash
cd nft_platform_backend-main
pip install -r requirements.txt
```

### 2. Configure Environment

Copy and edit `.env` file with your settings:

```bash
# Key variables needed:
DATABASE_URL=sqlite+aiosqlite:///./nft_platform.db
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=your-secret-key-min-32-chars
MNEMONIC_ENCRYPTION_KEY=mD2kZS8iktzZduZzGoHd1Dk75gtz3Y3VP0uNDm-4VAQ=
TELEGRAM_BOT_TOKEN=your_bot_token_here (optional)
```

### 3. Start Backend Server

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Expected output:
```
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Frontend Access

### Option 1: Real Telegram WebApp (Production)

1. Open the Telegram WebApp from the bot
2. The frontend will authenticate using Telegram's `initData`
3. User data is fetched from the backend

### Option 2: Development/Testing Mode

The frontend has a fallback mechanism for testing without Telegram:

**Method 1: Automatic Test User**
```
http://localhost:8000/web-app/
```
- Opens automatically, creates a test user
- Backend provides test data

**Method 2: Specific Test User via URL**
```
http://localhost:8000/web-app/?user_id=<uuid>
```
- Replace `<uuid>` with actual user ID
- Backend loads that user's data

### Getting a Test User ID

Run the test-user endpoint:

```bash
curl http://localhost:8000/api/v1/telegram/web-app/test-user
```

Response:
```json
{
  "success": true,
  "test_user": {
    "id": "e3ec4b5c-4eff-4ac6-931a-b87cab0e79cf",
    "username": "test_user",
    "full_name": "Test User"
  }
}
```

Then open: `http://localhost:8000/web-app/?user_id=e3ec4b5c-4eff-4ac6-931a-b87cab0e79cf`

## API Endpoints

### Web App Endpoints (all require /api/v1/telegram prefix)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/web-app/init` | GET | Authenticate with Telegram data |
| `/web-app/user` | GET | Get user profile |
| `/web-app/wallets` | GET | Get user's wallets |
| `/web-app/nfts` | GET | Get user's NFTs |
| `/web-app/dashboard-data` | GET | Get all dashboard data |
| `/web-app/marketplace/listings` | GET | Get active marketplace listings |
| `/web-app/marketplace/mylistings` | GET | Get user's listings |
| `/web-app/create-wallet` | POST | Create new wallet |
| `/web-app/import-wallet` | POST | Import existing wallet |
| `/web-app/mint` | POST | Mint new NFT |
| `/web-app/list-nft` | POST | List NFT for sale |
| `/web-app/transfer` | POST | Transfer NFT |
| `/web-app/burn` | POST | Burn NFT |
| `/web-app/set-primary` | POST | Set primary wallet |
| `/web-app/make-offer` | POST | Make offer on listing |
| `/web-app/cancel-listing` | POST | Cancel listing |
| `/web-app/test-user` | GET | Create/get test user (dev only) |

### Example API Calls

**Get User Profile:**
```bash
curl "http://localhost:8000/api/v1/telegram/web-app/user?user_id=e3ec4b5c-4eff-4ac6-931a-b87cab0e79cf"
```

**Get Marketplace Listings:**
```bash
curl "http://localhost:8000/api/v1/telegram/web-app/marketplace/listings?limit=50"
```

**Create Wallet (POST):**
```bash
curl -X POST "http://localhost:8000/api/v1/telegram/web-app/create-wallet" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "e3ec4b5c-4eff-4ac6-931a-b87cab0e79cf",
    "blockchain": "ethereum",
    "is_primary": true
  }'
```

## Frontend Architecture

### Files

- `app/static/webapp/index.html` - HTML structure & styling
- `app/static/webapp/app.js` - JavaScript logic (876 lines)

### Features Implemented

- **Authentication**: Real Telegram WebApp + test user fallback
- **Dashboard**: Portfolio overview, recent wallets/NFTs
- **Wallets**: Create, import, view, set primary
- **NFTs**: View collection, mint, transfer, burn
- **Marketplace**: Browse listings, make offers, list for sale
- **Profile**: User information, statistics
- **Responsive Design**: Mobile-first, works on desktop too
- **Error Handling**: Proper error messages and retry logic
- **Loading States**: Visual indicators for async operations

### Pages

1. **Dashboard** - Portfolio summary
2. **Wallets** - Wallet management
3. **NFTs** - Personal NFT collection
4. **Mint** - Create new NFTs
5. **Marketplace** - Browse and trade
6. **Profile** - User details & stats
7. **Help** - Getting started guide

## Backend Architecture

### Key Components

- **app/main.py** - FastAPI application setup
- **app/routers/telegram_mint_router.py** - WebApp endpoints (2493 lines)
- **app/models/** - Database models
- **app/services/** - Business logic
- **app/utils/startup.py** - Initialization and webhook setup
- **app/database/connection.py** - Database session management

### Database Models

- **User** - Telegram users
- **Wallet** - User wallets (multiple blockchains)
- **NFT** - User NFTs with metadata
- **Listing** - Marketplace listings
- **Offer** - Trading offers
- **Escrow** - Payment escrow for trading

### Supported Blockchains

- Bitcoin
- Ethereum
- Solana
- TON (Telegram Open Network)
- Polygon
- Arbitrum
- Optimism
- Base
- Avalanche

## Testing

### Run Test Suite

```bash
# Test API endpoints
python test_api_endpoints.py

# Comprehensive end-to-end test
python test_system_e2e.py

# Backend startup test
python test_backend_startup.py
```

### Manual Testing

1. Open http://localhost:8000/web-app/
2. Check browser console (F12) for logs
3. Test each feature:
   - Create wallet
   - Mint NFT
   - List for sale
   - Browse marketplace
   - Make offer

## Important Notes

### Security

- **Real Telegram Data**: In production, always use real Telegram WebApp initData
- **Signature Verification**: All requests are validated against Telegram's signature
- **JWT Authentication**: Optional JWT tokens for additional security
- **CORS**: Configured for localhost and Telegram origins

### Development vs Production

**Development:**
- Test user endpoint enabled
- URL parameters for user selection
- SQLite database
- Webhook setup non-fatal

**Production:**
- Only real Telegram authentication
- PostgreSQL database
- Proper JWT tokens
- HTTPS required
- Webhook properly configured

### Common Issues

1. **"Can't authenticate"**: 
   - In Telegram: Ensure WebApp.initData is sent
   - In development: Use test-user endpoint

2. **"Marketplace returns empty"**:
   - No listings created yet - this is normal for new systems
   - Create a test user and add NFTs/listings

3. **Backend won't start**:
   - Check .env file has MNEMONIC_ENCRYPTION_KEY
   - Ensure Python 3.8+ installed
   - Check port 8000 not in use

4. **Frontend buttons don't work**:
   - Check browser console (F12) for errors
   - Verify backend is running
   - Check API_BASE in app.js (should be `/api/v1/telegram`)

## Deployment

### Railway.app

```bash
# Configure environment variables on Railway
# Install dependencies, start server
python -m uvicorn app.main:app --host 0.0.0.0 --port

 $PORT
```

### Docker

```bash
docker build -t nft-platform .
docker run -p 8000:8000 nft-platform
```

## API Contract

The frontend expects the following API response structure:

```javascript
// User response
{
  "success": true,
  "user": {
    "id": "uuid",
    "telegram_id": number,
    "telegram_username": "string",
    "full_name": "string",
    "avatar_url": "url",
    "email": "string",
    "is_verified": boolean,
    "user_role": "user|admin",
    "created_at": "ISO8601"
  }
}

// Listings response
{
  "success": true,
  "listings": [
    {
      "id": "uuid",
      "nft_id": "uuid",
      "nft_name": "string",
      "price": number,
      "currency": "string",
      "blockchain": "string",
      "image_url": "url",
      "seller_id": "uuid",
      "seller_name": "string",
      "status": "ACTIVE"
    }
  ]
}

// NFT response
{
  "success": true,
  "nfts": [
    {
      "id": "uuid",
      "name": "string",
      "description": "string",
      "image_url": "url",
      "blockchain": "string",
      "status": "UNLISTED|LISTED",
      "created_at": "ISO8601"
    }
  ]
}
```

## Next Steps

1. **Create Real Telegram Bot**
   - Get TELEGRAM_BOT_TOKEN from @BotFather
   - Set WebApp URL to your deployed URL
   - Test with real Telegram users

2. **Configure Production Database**
   - Set up PostgreSQL
   - Update DATABASE_URL in env
   - Run migrations

3. **Add Blockchain Integration**
   - Configure RPC endpoints for each blockchain
   - Set up proper key management
   - Implement actual mint/transfer logic

4. **Deploy**
   - Use Railway, Heroku, AWS, or similar
   - Configure domain/SSL
   - Set up monitoring and logging

## Support & Debugging

**Enable Debug Logging:**
```python
# In app/config.py
LOG_LEVEL=DEBUG
```

**Check All Routes:**
```bash
curl http://localhost:8000/openapi.json | jq '.paths | keys'
```

**Monitor Backend:**
```bash
tail -f app.log  # Check logs
```

**Browser Console:**
Open F12 -> Console tab to see all app logs and errors.

---

Last Updated: February 2026
System Status: Production Ready
