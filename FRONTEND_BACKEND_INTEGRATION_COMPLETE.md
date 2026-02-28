# GiftedForge Frontend-Backend Complete Integration Guide

## Overview

The frontend is now fully integrated with the backend API, providing a complete Telegram Mini App experience. All dashboard data, marketplace functionality, wallet operations, and user management are connected through a comprehensive API client layer.

---

## Architecture

### State Management Pattern

**AppManager IIFE (Immediately Invoked Function Expression)**
- Encapsulates all application state
- Provides private state with controlled access through public API
- Closure-based pattern prevents global variable pollution
- Single source of truth for all UI updates

**State Structure:**
```javascript
{
  currentUser: { username, email, avatar_url, ... },
  isAuthenticated: boolean,
  authToken: string (from localStorage),
  currentPage: 'dashboard' | 'market' | 'wallet' | 'profile',
  viewMode: 'grid' | 'list',
  sortMode: 'newest' | 'price_asc' | 'price_desc' | 'popular',
  
  marketplace: {
    items: [],        // All NFT listings
    filtered: [],     // Filtered results
    creators: Map(),  // Creator ID → Name mapping
    filters: { priceMin, priceMax, creators[], availability[] },
    loading: boolean
  },
  
  dashboard: {
    balance: number,       // USD balance
    nftCount: number,      // Total NFTs owned
    listingCount: number,  // Active listings
    walletBalance: string, // ETH/USDT balance
    totalProfit: number,   // USD profit
    activity: [],          // Activity feed
    collections: [],       // User collections
    loading: boolean
  },
  
  wallet: {
    address: string,       // Blockchain address
    stars: number,         // Telegram Stars balance
    balance: number,       // Wallet balance
    connected: boolean,    // Wallet connection status
    loading: boolean
  },
  
  profile: {
    username: string,
    email: string,
    avatar: string,
    totalSales: number,
    totalEarnings: number,
    loading: boolean
  },
  
  UI: { sortMenuOpen, filterPanelOpen }
}
```

---

## API Client Layer

### Configuration

```javascript
const api = {
  baseURL: '/api',
  async request(endpoint, options = {}) {
    // Automatic request handler with:
    // - Content-Type: application/json
    // - Authorization: Bearer {token}
    // - 401 auto-logout on expired auth
    // - Error handling & user feedback
  }
}
```

### Request Flow

1. **Request Construction**
   - Headers: `Content-Type: application/json`
   - Auth: `Authorization: Bearer ${state.authToken}` (if logged in)
   - Options: Method, body, additional headers

2. **Response Handling**
   - 200-299: Parse JSON & return data
   - 401: Clear auth, logout user
   - Other errors: Log & display to user
   - Network errors: Graceful error message

3. **Error Management**
   - Console logging for debugging
   - User-facing alert for critical errors
   - Null returns on failure (prevents crashes)

---

## Endpoint Integration

### Authentication

#### Login/Register
```javascript
api.getProfile() → GET /api/auth/me
```
- **When Called:** App initialization, page refresh
- **Response:** Current user data
- **State Update:** Sets `currentUser`, `isAuthenticated`
- **UI Impact:** Updates header with username/avatar

#### Profile Update
```javascript
api.updateProfile(data) → PUT /api/auth/profile
```
- **Data:** `{ username, email, bio, avatar_url }`
- **When Called:** User updates profile
- **State Update:** Updates `profile` object
- **UI Impact:** Refreshes profile page display

---

### Dashboard

#### Dashboard Summary
```javascript
api.getDashboardData() → GET /api/dashboard
```
- **Response Fields:**
  ```json
  {
    "total_balance": 12450.50,      // USD
    "nft_count": 16,
    "listing_count": 3,
    "wallet_balance": 1.24,         // ETH
    "total_profit": 450.00
  }
  ```
- **When Called:** Page load, navigate to dashboard, after transaction
- **State Update:**
  - `dashboard.balance` ← total_balance
  - `dashboard.nftCount` ← nft_count
  - `dashboard.listingCount` ← listing_count
  - `dashboard.walletBalance` ← wallet_balance
  - `dashboard.totalProfit` ← total_profit
- **UI Elements Updated:**
  - `#totalBalance` → formatted currency
  - `#nftCount` → count display
  - `#listingCount` → padded display (03)
  - `#walletBalance` → decimal display
  - `#totalProfit` → USD format

#### Activity Feed
```javascript
api.getActivity() → GET /api/dashboard/activity
```
- **Response Format:**
  ```json
  {
    "activities": [
      {
        "id": "uuid",
        "title": "Minted Genesis Cube",
        "type": "income|expense|transfer",
        "amount": 450,
        "timestamp": "2024-01-15T10:30:00Z"
      }
    ]
  }
  ```
- **When Called:** Dashboard load
- **State Update:** `dashboard.activity` array
- **UI Rendering:**
  - Activity icon (SVG with type indicator)
  - Title + timestamp
  - Amount with +/- prefix
  - Color coding: green (income), red (expense)

---

### Marketplace

#### Get All Items
```javascript
api.getMarketplaceItems(filters) → GET /api/marketplace/items?[params]
```
- **Query Params:**
  - `price_min`, `price_max`
  - `creator_id`
  - `availability` (available, sold_out)
  - Pagination: `page`, `limit`

- **Response Format:**
  ```json
  {
    "items": [
      {
        "id": "uuid",
        "title": "Genesis Cube",
        "description": "...",
        "image_url": "https://...",
        "price_stars": 500,
        "creator_id": "user_123",
        "creator_name": "Creator Name",
        "rarity": "LEGENDARY",
        "views": 1250,
        "sales_count": 42,
        "availability": "available",
        "created_at": "2024-01-10T00:00:00Z"
      }
    ]
  }
  ```

- **When Called:** 
  - Navigate to marketplace
  - Apply filters
  - Change sort
  - Change view mode (grid/list)

- **State Update:**
  - `marketplace.items` ← response items
  - `marketplace.filtered` ← copy of items
  - `marketplace.creators` ← build Map from unique creators

- **UI Rendering:**
  ```
  Card Layout:
  ├── Image + Rarity Badge
  ├── Title + Creator Name
  ├── Stats (Views, Sales Count)
  ├── Price (in Stars) + Buy Button
  ```

- **Client-Side Operations:**
  - Filtering: `applyFilters()` function
  - Sorting: `sortOperations[mode]()`
  - Rendering: `renderMarketplace()`

#### Get Item Details
```javascript
api.getItemDetails(itemId) → GET /api/marketplace/items/{itemId}
```
- **When Called:** User clicks marketplace card
- **Response:** Single item object with extended details
- **UI Impact:** Displays in modal overlay with full details

#### Purchase Item
```javascript
api.purchaseItem(itemId, paymentMethod) → POST /api/marketplace/purchase/{itemId}
```
- **Request Body:**
  ```json
  {
    "payment_method": "stars" | "wallet" | "card"
  }
  ```
- **Response:**
  ```json
  {
    "transaction_id": "uuid",
    "status": "success",
    "message": "Purchase completed"
  }
  ```
- **When Called:** User clicks "Buy" or "Purchase Now" button
- **State Updates:**
  - Reload marketplace items
  - Reload dashboard data
  - Update wallet balance

- **UI Feedback:**
  - Success message
  - Close modal
  - Refresh grid (item moved out of marketplace if sold out)
  - Update dashboard balance

---

### Wallet Operations

#### Get Wallet Info
```javascript
api.getWallet() → GET /api/wallet
```
- **Response:**
  ```json
  {
    "address": "0x742d35Cc6634C0532925a3b844Bc7e7d30E3E4F1",
    "balance": 1.24,
    "stars": 5000,
    "connected": true,
    "chain": "ethereum"
  }
  ```
- **When Called:** Dashboard load, navigate to wallet page
- **State Update:**
  - `wallet.address` ← address
  - `wallet.stars` ← stars
  - `wallet.balance` ← balance
  - `wallet.connected` ← true/false

- **UI Elements Updated:**
  - `#walletStatus` → address preview (first 6 + last 4 chars)
  - Button availability (disabled/enabled based on `connected`)
  - Inline color indicator (green if connected)

#### Create Wallet
```javascript
api.createWallet() → POST /api/wallet/create
```
- **Response:**
  ```json
  {
    "address": "0x...",
    "private_key": "0x..." // NEVER store client-side
  }
  ```
- **When Called:** User clicks "Create Wallet" button
- **State Update:** `wallet.connected = true`
- **UI Feedback:**
  - Show generated address (masked)
  - Disable "Create Wallet" button
  - Refresh wallet display

#### Connect Wallet
```javascript
api.connectWallet(address) → POST /api/wallet/connect
```
- **Request:**
  ```json
  {
    "address": "0xUserAddress"
  }
  ```
- **When Called:** MetaMask/Web3 connection
- **State Update:** `wallet.address`, `wallet.connected`
- **UI Feedback:** Wallet connection status display

#### Get Wallet Balance
```javascript
api.getWalletBalance() → GET /api/wallet/balance
```
- **Response:** `{ "balance": 1.24, "usd_value": 2480.00 }`
- **When Called:** Periodic refresh, after transaction
- **State Update:** `dashboard.walletBalance`

---

### NFT Operations

#### Get My NFTs
```javascript
api.getNFTs() → GET /api/nft/my-nfts
```
- **Response:**
  ```json
  {
    "nfts": [
      {
        "id": "uuid",
        "title": "NFT Title",
        "collection_id": "uuid",
        "image_url": "https://...",
        "created_at": "2024-01-10T00:00:00Z"
      }
    ]
  }
  ```
- **When Called:** Dashboard load, collections view
- **State Update:** `dashboard.nftCount`

#### Mint NFT
```javascript
api.mintNFT(data) → POST /api/nft/mint
```
- **Request:**
  ```json
  {
    "title": "My New NFT",
    "description": "NFT description",
    "image_url": "https://...",
    "collection_id": "uuid"
  }
  ```
- **Response:**
  ```json
  {
    "id": "uuid",
    "tx_hash": "0x...",
    "status": "pending|success"
  }
  ```
- **When Called:** User clicks "Mint NFT" button
- **Flow:**
  1. Prompt user for title
  2. Prompt for description
  3. Call API
  4. Show success message
  5. Reload dashboard & collections

---

### Collections

#### Get Collections
```javascript
api.getCollections() → GET /api/collections
```
- **Response:**
  ```json
  {
    "collections": [
      {
        "id": "uuid",
        "name": "Collection Name",
        "description": "...",
        "image_url": "https://...",
        "items_count": 5,
        "owner_id": "user_123"
      }
    ]
  }
  ```
- **When Called:** Dashboard collections section load
- **State Update:** `dashboard.collections`
- **UI Rendering:** Collection cards display in collections grid

---

### Transactions

#### Get Transaction History
```javascript
api.getTransactionHistory() → GET /api/transactions
```
- **Response:**
  ```json
  {
    "transactions": [
      {
        "id": "uuid",
        "type": "purchase|sale|transfer|mint",
        "amount": 500,
        "currency": "STARS|ETH|USD",
        "status": "completed|pending|failed",
        "timestamp": "2024-01-15T10:30:00Z",
        "details": { ... }
      }
    ]
  }
  ```
- **When Called:** Transaction history page load
- **State Update:** Used for transaction history page display

---

## Data Flow Diagrams

### Authentication Flow
```
User Opens App
     ↓
DOMContentLoaded Event
     ↓
AppManager.init()
     ↓
loadUserData() → api.getProfile()
     ↓
Response received?
├─ YES: Set currentUser, isAuthenticated = true
└─ NO: Show login prompt
     ↓
loadDashboardData()
     ↓
Update UI with user data
     ↓
initEventListeners()
     ↓
App Ready
```

### Purchase Flow
```
User clicks "Buy" → purchaseItem(itemId)
     ↓
api.purchaseItem(itemId) → POST /api/marketplace/purchase/{itemId}
     ↓
Response success?
├─ YES: 
│        showSuccess message
│        close modal
│        loadMarketplaceData() [refresh items]
│        loadDashboardData() [refresh balance]
│        Update UI
└─ NO: showError message
```

### Marketplace Filtering Flow
```
User applies filters
     ↓
Store filter values in state.marketplace.filters
     ↓
applyFilters() function
     ↓
Filter items client-side
     ↓
applySorting() function
     ↓
renderMarketplace()
     ↓
Update grid display
```

### Dashboard Auto-Refresh Flow
```
Every page load / navigation
     ↓
Check if data already loaded?
├─ YES: Reuse cached data
└─ NO: Call loadDashboardData()
     ↓
Fetch from api.getDashboardData()
     ↓
Fetch from api.getActivity()
     ↓
Update all UI elements
     ↓
Display on page
```

---

## Error Handling Strategy

### API Error Handling
```javascript
api.request() handles:
- 401 Unauthorized → Clear token, logout
- Network errors → Catch & display message
- Invalid responses → Try JSON parse, fallback
- Non-OK responses → Extract error message from response
```

### User-Facing Errors
```javascript
AppManager.showError(message) → alert(message)
AppManager.showSuccess(message) → alert(message)
```

### Silent Failures
```javascript
- Failed data loads → UI shows placeholder
- Purchase failure → User notified, modal remains open
- Marketplace empty → Show empty state
```

---

## Performance Optimizations

### Data Caching
- Dashboard data loaded once on init (not on every navigation)
- Marketplace items cached until refresh
- Creator list built once during marketplace load

### Client-Side Operations
- Sorting: Done client-side (no API call)
- Filtering: Done client-side (no API call)
- View mode toggle: Pure UI change (no API call)

### Lazy Loading
- Only fetch data when entering section
- Don't preload all pages simultaneously
- Reuse data if already loaded

---

## HTTP Headers & Auth

### Standard Request Headers
```
Content-Type: application/json
Authorization: Bearer {authToken}
```

### Token Management
- Stored in `localStorage.getItem('auth_token')`
- Sent on every authenticated request
- Automatically cleared on 401 response
- Retrieved on app initialization

---

## Telegram WebApp Integration

```javascript
if (window.Telegram?.WebApp) {
  const tg = window.Telegram.WebApp;
  tg.ready();           // Notify Telegram app is ready
  tg.expand();          // Expand to full screen
  tg.enableClosingConfirmation(); // Warn on back
}
```

---

## Implementation Checklist

- [x] API client with automatic token management
- [x] User authentication flow
- [x] Dashboard data binding
- [x] Activity feed integration
- [x] Marketplace items fetching
- [x] Marketplace filtering (client-side)
- [x] Marketplace sorting (client-side)
- [x] Purchase flow with backend
- [x] Wallet operations
- [x] NFT minting
- [x] Collection management
- [x] Transaction history
- [x] Error handling & user feedback
- [x] State management with closure pattern
- [x] Telegram WebApp ready

---

## Testing Endpoints with cURL

### Get Dashboard Data
```bash
curl -X GET "http://localhost:8000/api/dashboard" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json"
```

### Purchase Item
```bash
curl -X POST "http://localhost:8000/api/marketplace/purchase/{itemId}" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"payment_method": "stars"}'
```

### Get Marketplace Items
```bash
curl -X GET "http://localhost:8000/api/marketplace/items?price_min=0&price_max=1000" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json"
```

### Create Wallet
```bash
curl -X POST "http://localhost:8000/api/wallet/create" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json"
```

---

## Frontend-Backend Alignment

### Database Models Used

**User Model**
```python
- id (UUID)
- username (string)
- email (string)
- avatar_url (string)
- total_sales (int)
- total_earnings (decimal)
```

**NFT Model**
```python
- id (UUID)
- title (string)
- description (string)
- image_url (string)
- creator_id (UUID → User)
- collection_id (UUID → Collection)
- views (int)
- created_at (datetime)
```

**Listing Model**
```python
- id (UUID)
- nft_id (UUID → NFT)
- price_stars (int)
- availability (enum: available, sold_out)
- sales_count (int)
```

**Transaction Model**
```python
- id (UUID)
- buyer_id (UUID → User)
- seller_id (UUID → User)
- amount (decimal)
- currency (string)
- type (enum: purchase, sale, transfer, mint)
- status (enum: completed, pending, failed)
- timestamp (datetime)
```

**Wallet Model**
```python
- id (UUID)
- user_id (UUID → User)
- address (string)
- balance (decimal)
- stars (int)
- connected (bool)
```

**Collection Model**
```python
- id (UUID)
- name (string)
- description (string)
- image_url (string)
- owner_id (UUID → User)
- items_count (int)
```

---

## Next Steps

1. **Backend Validation**
   - Ensure all endpoints return expected JSON structures
   - Verify JWT token validation on all protected routes
   - Test error responses (401, 404, 500)

2. **Frontend Testing**
   - Test each API call manually via browser DevTools
   - Verify state updates correctly
   - Test error scenarios

3. **Production Deployment**
   - Set correct `api.baseURL` for production
   - Enable HTTPS for all API calls
   - Configure CORS headers on backend

---

## Support & Debugging

### Enable Debug Logging
All API errors log to console with full stack traces.
```javascript
// In browser console:
AppManager.getState() // View current app state
```

### Common Issues

**401 Unauthorized**
- Clear localStorage
- Re-login
- Check token expiration

**CORS Errors**
- Verify backend CORS headers
- Check API endpoint URLs

**Empty Marketplace**
- Verify NFT data in database
- Check API response format
- Enable browser DevTools Network tab
