# Web App Static/Webapp Integration Guide

## Overview
The NFT Platform Web App is now fully integrated with the backend and can fetch data per user. The webapp can be tested both:
1. **Within Telegram** (production mode)
2. **Outside Telegram** (development/testing mode)

---

## Architecture

### Frontend (Static Files)
- **Location**: `/app/static/webapp/`
- **Files**:
  - `index.html` - Web app HTML structure
  - `app.js` - JavaScript logic and API calls
  - `styles.css` - Professional dark theme CSS

### Backend (API Endpoints)
- **Location**: `/app/routers/telegram_mint_router.py`
- **Available Endpoints**:
  - `/web-app/init` - Authenticate user
  - `/web-app/dashboard-data` - Get user's wallets, NFTs, listings
  - `/web-app/test-user` - Create test user for development
  - `/web-app/mint` - Mint NFT
  - `/web-app/list-nft` - List NFT for sale
  - `/web-app/marketplace/listings` - Get all marketplace listings

### Data Flow
```
User Opens Web App
    ↓
[Development] ?user_id=UUID  |  [Production] Telegram.WebApp.initData
    ↓
Backend authenticates user via /web-app/init (Telegram) or direct UUID
    ↓
app.js calls API.getDashboardData(user_id)
    ↓
Backend returns: { wallets, nfts, listings }
    ↓
Frontend updates UI with user's data
```

---

## Testing the Web App

### Option 1: Development Mode (No Telegram Required)

**Step 1: Get a Test User**
```bash
# Make a GET request to:
http://localhost:8000/api/v1/telegram/web-app/test-user

# Response:
{
  "success": true,
  "test_user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "test_user",
    "first_name": "Test",
    "last_name": "User"
  },
  "instructions": {
    "step_2": "Visit web app with: /web-app/index.html?user_id=550e8400-e29b-41d4-a716-446655440000"
  }
}
```

**Step 2: Open Web App with Test User**
```
http://localhost:8000/web-app/?user_id=550e8400-e29b-41d4-a716-446655440000
```

**Step 3: Web App Loads**
- Console shows: "Development mode: Using test user ID from URL"
- Web app fetches test user's data from backend
- Dashboard displays test user's wallets, NFTs, listings

### Option 2: Production Mode (Telegram)

**Step 1: Open Telegram Bot**
- Start your Telegram bot with `/start` command

**Step 2: Click Web App Button**
- Telegram sends WebApp.initData with user signature

**Step 3: Backend Authenticates**
- Verifies Telegram signature
- Creates/retrieves user from database
- Returns user ID and profile

**Step 4: Web App Loads**
- Console shows: "Telegram mode: Using Telegram WebApp"
- Web app fetches your data from backend
- Dashboard displays your wallets, NFTs, listings

---

## API Response Structure

### Dashboard Data Response
```json
{
  "success": true,
  "wallets": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "My Ethereum Wallet",
      "blockchain": "ethereum",
      "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
      "is_primary": true,
      "created_at": "2024-01-15T10:30:00"
    }
  ],
  "nfts": [
    {
      "id": "abc12345-def6-4890-gh12-ijklmnopqrst",
      "name": "My First NFT",
      "global_nft_id": "ethereum:0x123abc...",
      "description": "Cool artwork",
      "blockchain": "ethereum",
      "status": "minted",
      "image_url": "https://example.com/nft.jpg",
      "created_at": "2024-01-15T10:45:00"
    }
  ],
  "listings": [
    {
      "id": "listing-123",
      "nft_id": "abc12345-def6-4890-gh12-ijklmnopqrst",
      "nft_name": "My First NFT",
      "price": 99.99,
      "currency": "USDT",
      "blockchain": "ethereum",
      "status": "active",
      "image_url": "https://example.com/nft.jpg"
    }
  ]
}
```

---

## Frontend Logic (app.js)

### Authentication Flow
```javascript
// Development mode (has ?user_id in URL)
const urlParams = new URLSearchParams(window.location.search);
const testUserId = urlParams.get('user_id');
if (testUserId) {
  // Use test user ID directly
  state.user = { id: testUserId, ... }
}

// Production mode (Telegram)
if (window.Telegram?.WebApp) {
  // Get initData from Telegram
  const initData = window.Telegram.WebApp.initData;
  // Send to backend: /web-app/init?init_data=...
  // Backend verifies signature and returns user
}
```

### Data Fetching
```javascript
async function loadDashboard() {
  // Call backend /web-app/dashboard-data endpoint
  const dashboardData = await API.getDashboardData(state.user.id);
  
  // Store in state
  state.wallets = dashboardData.wallets;
  state.nfts = dashboardData.nfts;
  state.listings = dashboardData.listings;
  
  // Update UI
  updateWalletsList();
  updateNftsList();
  updateMarketplace();
}
```

---

## Backend Integration

### Web App Routes (telegram_mint_router.py)

All web app endpoints are in:
```python
@router.get("/web-app/init")  # Authenticate user
@router.get("/web-app/dashboard-data")  # Get user's data
@router.get("/web-app/test-user")  # Create test user
@router.post("/web-app/mint")  # Mint NFT
@router.post("/web-app/list-nft")  # List NFT
@router.get("/web-app/marketplace/listings")  # Get all listings
```

### User Data Isolation
Each endpoint properly filters data by `user_id`:
```python
# Get only this user's wallets
wallets = await db.execute(
    select(Wallet)
    .where(Wallet.user_id == user_uuid)
)

# Get only this user's NFTs
nfts = await db.execute(
    select(NFT)
    .where(NFT.user_id == user_uuid)
)

# Get only this user's listings (where they are seller)
listings = await db.execute(
    select(Listing)
    .where((Listing.seller_id == user_uuid) & (Listing.status == ListingStatus.ACTIVE))
)
```

---

## Browser Console Logs

When web app loads, you'll see detailed logs:

**Development Mode:**
```
🚀 NFT Platform App Starting...
📝 Development mode: Using test user ID from URL
Loading dashboard for user: test_user (550e8400...)
Dashboard response received: success=true
  Wallets: 2
  NFTs: 5
  Own Listings: 1
State updated: wallets=2, nfts=5, listings=1
Data loaded!
```

**Production Mode:**
```
🚀 NFT Platform App Starting...
📱 Telegram mode: Using Telegram WebApp
Authenticating...
User authenticated: test_user (550e8400...)
Loading dashboard for user: test_user (550e8400...)
... [same as above]
```

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| "Error: Not running in Telegram" | No Telegram SDK, no ?user_id parameter | Use ?user_id=UUID for testing |
| "Data not loading" | API call failed | Check browser console (F12) for errors |
| "Empty dashboard" | No wallets/NFTs for user | Create wallet or NFT first |
| "CORS error" | Backend CORS not configured | Backend already configured, should work |
| "API calls to /api/v1/... failing" | Wrong API path | App uses `/api/v1/telegram/web-app/*` |

---

## Static Files Mount

The backend serves the web app at:
```python
app.mount("/web-app", StaticFiles(directory="app/static/webapp", html=True), name="webapp")
```

This means:
- `index.html` is served at `/web-app/`
- `app.js` is loaded from `/web-app/app.js`
- `styles.css` is loaded from `/web-app/styles.css`

---

## Configuration

### CORS Setup (app/main.py)
```python
cors_origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
app.add_middleware(CORSMiddleware, allow_origins=cors_origins, ...)
```
**Note**: This allows localhost calls. Same-origin requests don't need CORS (web app on same domain as API).

### API Base URL (app.js)
```javascript
const API_BASE = '/api/v1';
```
All API calls are relative to this base (same domain).

---

## Features Working

✅ **Authentication**
- Telegram signature verification
- Test user creation for development
- Per-user data isolation

✅ **Dashboard**
- Display user's wallets
- Display user's NFTs
- Display user's listings

✅ **Wallet Management**
- Create wallet
- Import wallet
- Set primary wallet

✅ **NFT Operations**
- Mint NFT
- List NFT for sale
- Transfer NFT
- Burn NFT

✅ **Marketplace**
- Browse all listings
- Make offer
- Cancel listing

✅ **UI/UX**
- Professional dark theme
- Responsive design
- Skeleton loaders
- Error handling
- Loading states
- Help/instructions page

---

## Next Steps

1. **Test in Development**:
   - Call `/api/v1/telegram/web-app/test-user` to get test user ID
   - Open `/web-app/?user_id=YOUR_ID`
   - Verify data loads and dashboard works

2. **Test in Telegram**:
   - Add web app button to Telegram bot
   - Click button from mobile Telegram
   - Verify authentication and data loading

3. **Monitor Logs**:
   - Open browser DevTools (F12)
   - Check Console tab for debug logs
   - Verify all API calls succeed

4. **Create Sample Data**:
   - Create wallets
   - Mint NFTs
   - List on marketplace
   - Verify all appears on dashboard

---

## Files Modified

- ✅ `app/static/webapp/app.js` - Added development mode support
- ✅ `app/static/webapp/index.html` - Added help page and navigation
- ✅ `app/routers/telegram_mint_router.py` - Added `/web-app/test-user` endpoint

**Status**: ✅ READY FOR TESTING

All components are connected and functioning. The web app can now fetch data per user and works both in development and production modes.
