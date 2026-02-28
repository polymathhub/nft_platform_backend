# Backend Integration Guide - GiftedForge Marketplace

## Overview
The frontend marketplace is now fully integrated into `app/static/webapp/index.html`. All backend API calls are ready to accept HTTP requests from JavaScript.

---

## Required API Endpoints

### 1. GET /api/marketplace/items
**Purpose:** Fetch all marketplace items for display

**Response Format:**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Genesis NFT",
      "description": "A rare genesis NFT",
      "price_stars": 100,
      "creator_id": "550e8400-e29b-41d4-a716-446655440001",
      "creator_name": "Creator Name",
      "created_at": "2026-02-27T10:00:00Z",
      "views": 250,
      "sales_count": 5,
      "availability": "available",
      "image_url": "https://example.com/image.jpg",
      "rarity": "LEGENDARY"
    }
  ]
}
```

**Frontend Code:**
```javascript
const response = await fetch('/api/marketplace/items');
const data = await response.json();
// state.marketplace.items = data.items
```

---

### 2. POST /api/marketplace/purchase/{itemId}
**Purpose:** Purchase a marketplace item

**Request Body:**
```json
{
  "payment_method": "stars"
}
```

**Response (Success):**
```json
{
  "success": true,
  "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Purchase successful"
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "Insufficient balance"
}
```

**Frontend Code:**
```javascript
const response = await fetch(`/api/marketplace/purchase/${itemId}`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ payment_method: 'stars' })
});
```

---

## Database Field Mapping

### NFT/Listing (Marketplace Items)
| Frontend Display | Database Field | Type | Example |
|---|---|---|---|
| Card title | `nft.title` | String | "Genesis Cube" |
| Price | `listing.price_stars` | Float | 100.0 |
| Creator | `user.username` (via creator_id) | String | "Artist Name" |
| Created date | `listing.created_at` | DateTime | 2026-02-27T10:00:00Z |
| Views | `nft.views` | Integer | 250 |
| Sales count | `nft.sales_count` | Integer | 5 |
| Availability | `listing.status` | Enum | "active" |
| Image | `nft.image_url` | String | "https://..." |
| Rarity | `nft.rarity_tier` | Enum | "legendary" |
| ID | `nft.id` | UUID | "550e8400..." |
| Creator ID | `listing.seller_id` | UUID | "550e8400..." |

---

## Sort Operations (Applied in JavaScript)

| Sort Option | Database Field | Order |
|---|---|---|
| Newest | `listing.created_at` | DESC |
| Price Low–High | `listing.price_stars` | ASC |
| Price High–Low | `listing.price_stars` | DESC |
| Popular | `nft.sales_count` | DESC |

**Note:** Sorting is done client-side in JavaScript after fetching all items. No need to add query parameters.

---

## Filter Operations (Applied in JavaScript)

| Filter Type | Database Field | Operation |
|---|---|---|
| Price Min | `listing.price_stars` | >= |
| Price Max | `listing.price_stars` | <= |
| Creator | `listing.seller_id` | IN (array) |
| Availability | `listing.status` | IN (array) |

**Note:** Filtering is done client-side. Send all items in initial fetch.

---

## Sample Response Data

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Liquid Oil #1",
      "description": "A vibrant abstract NFT",
      "price_stars": 50,
      "creator_id": "550e8400-e29b-41d4-a716-446655440001",
      "creator_name": "Artist Alice",
      "created_at": "2026-02-25T14:30:00Z",
      "views": 320,
      "sales_count": 8,
      "availability": "available",
      "image_url": "https://api.example.com/images/nft-01.jpg",
      "rarity": "EPIC"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "title": "Neon Dreams #42",
      "description": "Futuristic neon aesthetic",
      "price_stars": 150,
      "creator_id": "550e8400-e29b-41d4-a716-446655440003",
      "creator_name": "Creator Bob",
      "created_at": "2026-02-27T09:15:00Z",
      "views": 450,
      "sales_count": 12,
      "availability": "available",
      "image_url": "https://api.example.com/images/nft-02.jpg",
      "rarity": "LEGENDARY"
    }
  ]
}
```

---

## Frontend State Structure

The JavaScript maintains a private state object:

```javascript
state = {
  currentPage: 'dashboard',        // 'dashboard' | 'wallet' | 'mint' | 'market' | 'profile'
  viewMode: 'grid',                // 'grid' | 'list'
  sortMode: 'newest',              // 'newest' | 'price_asc' | 'price_desc' | 'popular'
  
  marketplace: {
    items: [],                      // All fetched items
    filtered: [],                   // After filters applied
    creators: new Map(),            // { creator_id → creator_name }
    
    filters: {
      priceMin: null,              // Number or null
      priceMax: null,              // Number or null
      creators: [],                // [creator_id, ...]
      availability: []             // ['available', 'sold', ...]
    }
  },
  
  sortMenuOpen: false,
  filterPanelOpen: false
}
```

---

## Implementation Checklist

### Backend Routes
- [ ] `GET /api/marketplace/items` - Returns all marketplace items
- [ ] `POST /api/marketplace/purchase/{itemId}` - Process purchase

### Database Queries
For `/api/marketplace/items`:
```sql
SELECT 
  n.id, n.title, n.description, n.views, n.sales_count, n.rarity_tier, n.image_url,
  l.id as listing_id, l.price_stars, l.status as availability, l.created_at, l.seller_id,
  u.id as creator_id, u.username as creator_name
FROM nfts n
LEFT JOIN listings l ON n.id = l.nft_id
LEFT JOIN users u ON l.seller_id = u.id
WHERE l.status = 'ACTIVE'
ORDER BY l.created_at DESC
```

For `/api/marketplace/purchase/{itemId}`:
1. Verify user has sufficient balance (stars)
2. Create transaction record
3. Update listing status
4. Transfer stars to seller
5. Return success/error

### Frontend Features (Already Implemented)
- [x] Marketplace grid (2 columns)
- [x] List view toggle
- [x] Sort functionality
- [x] Filter panel with price range
- [x] Creator filter (dynamic list)
- [x] Availability filter
- [x] Item details modal on click
- [x] Purchase button
- [x] Dark floating navbar
- [x] Navigation between pages

### Error Handling
Frontend expects HTTP status codes:
- `200 OK` - Success
- `400 Bad Request` - Invalid request
- `401 Unauthorized` - Not authenticated
- `404 Not Found` - Item not found
- `500 Internal Server Error` - Server error

The frontend will:
- Show error alerts
- Log errors to console
- Allow user to retry

---

## Testing Guide

### 1. Test Marketplace Loading
```
1. Navigate to app in browser
2. Click "Markets" button or Market nav item
3. Verify API call to /api/marketplace/items
4. Verify grid displays items
```

### 2. Test Sorting
```
1. Click sort button (top right of marketplace)
2. Select "Price Low–High"
3. Verify grid re-sorts by price ascending
4. Repeat for other sort options
```

### 3. Test Filtering
```
1. Click filter button
2. Enter price range (min: 50, max: 200)
3. Click Apply
4. Verify only items in range display
5. Click Reset to clear
```

### 4. Test Purchase
```
1. Click any marketplace card
2. Verify white modal appears with item details
3. Click "Purchase Now"
4. Verify POST to /api/marketplace/purchase/{id}
5. Verify success/error handling
```

### 5. Test View Toggle
```
1. Click grid icon (default)
2. Verify 2-column grid layout
3. Click list icon
4. Verify 1-column list layout with horizontal cards
5. Verify images are properly sized
```

---

## API Implementation Template

### Python/FastAPI Example
```python
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/marketplace")

@router.get("/items")
async def get_marketplace_items(db: Session = Depends(get_db)):
    """Fetch all active marketplace items"""
    try:
        items = db.query(
            NFT.id,
            NFT.title,
            NFT.description,
            NFT.views,
            NFT.sales_count,
            NFT.rarity_tier,
            NFT.image_url,
            Listing.price_stars,
            Listing.status,
            Listing.created_at,
            User.id.label('creator_id'),
            User.username.label('creator_name')
        ).join(
            Listing, NFT.id == Listing.nft_id
        ).join(
            User, Listing.seller_id == User.id
        ).filter(
            Listing.status == ListingStatus.ACTIVE
        ).all()
        
        return {
            "items": [
                {
                    "id": str(item.id),
                    "title": item.title,
                    "description": item.description,
                    "price_stars": float(item.price_stars),
                    "creator_id": str(item.creator_id),
                    "creator_name": item.creator_name,
                    "created_at": item.created_at.isoformat(),
                    "views": item.views,
                    "sales_count": item.sales_count,
                    "availability": item.status.value,
                    "image_url": item.image_url,
                    "rarity": item.rarity_tier.value.upper()
                }
                for item in items
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/purchase/{item_id}")
async def purchase_item(
    item_id: str,
    body: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process marketplace item purchase"""
    try:
        # Validate item exists
        listing = db.query(Listing).filter(Listing.nft_id == item_id).first()
        if not listing:
            raise HTTPException(status_code=404, detail="Item not found")
        
        # Check balance
        user_wallet = current_user.wallet
        if user_wallet.stars < listing.price_stars:
            raise HTTPException(status_code=400, detail="Insufficient balance")
        
        # Process transaction
        transaction = Transaction(
            user_id=current_user.id,
            nft_id=item_id,
            transaction_type=TransactionType.TRANSFER,
            status=TransactionStatus.CONFIRMED,
            # ... additional fields
        )
        db.add(transaction)
        
        # Update balances
        user_wallet.stars -= listing.price_stars
        seller_wallet = listing.seller.wallet
        seller_wallet.stars += listing.price_stars
        
        # Update listing
        listing.status = ListingStatus.COMPLETED
        
        db.commit()
        
        return {
            "success": True,
            "transaction_id": str(transaction.id),
            "message": "Purchase successful"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Important Notes

1. **No Pagination:** Current implementation fetches all items at once. For scale, add pagination.
2. **Caching:** Consider caching marketplace items for performance.
3. **Real-time Updates:** Consider WebSocket for live price/availability updates.
4. **Rate Limiting:** Implement rate limiting on purchase endpoint.
5. **Authentication:** All endpoints should verify user authentication.

---

## Support & Debugging

**Check Browser Console for:**
- API response logs
- JavaScript errors
- State mutations
- Network requests

**Common Issues:**
- CORS errors: Configure CORS on backend
- 404 errors: Verify endpoint paths
- TypeError: Check API response format matches expected structure
- State not updating: Check filter/sort logic

---

**Status:** Ready for backend integration  
**Frontend Version:** 1.0.0  
**Last Updated:** February 27, 2026
