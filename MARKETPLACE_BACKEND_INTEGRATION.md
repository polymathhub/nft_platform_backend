# GiftedForge Marketplace UI - Backend Integration Guide

**Audience**: Backend Engineers & DevOps  
**Status**: Implementation Ready  
**Updated**: Feb 27, 2026

---

## QUICK START

### 1. Serve the Marketplace HTML

#### FastAPI (Python)

```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/ui/marketplace", response_class=HTMLResponse)
async def marketplace():
    """Serve the marketplace UI page"""
    with open("app/ui/marketplace.html", "r", encoding="utf-8") as f:
        return f.read()
```

#### Flask (Python)

```python
from flask import Flask, render_template

app = Flask(__name__)

@app.route("/ui/marketplace")
def marketplace():
    """Serve the marketplace UI page"""
    return render_template("marketplace.html")
```

**File Path**: `app/ui/marketplace.html`

---

## API ENDPOINTS REQUIRED

### 1. Fetch Marketplace Items

**Endpoint**: `GET /api/v1/marketplace/items`

**Request**:
```bash
GET /api/v1/marketplace/items
Authorization: Bearer {telegram_auth_token}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "title": "Digital Art Collection #1",
        "price_stars": 50,
        "creator_id": 101,
        "created_at": "2026-02-27T10:00:00Z",
        "views": 234,
        "sales_count": 12,
        "image_url": "https://cdn.example.com/items/1.jpg",
        "is_featured": true
      },
      {
        "id": 2,
        "title": "Collectible Card Series",
        "price_stars": 25,
        "creator_id": 102,
        "created_at": "2026-02-26T15:30:00Z",
        "views": 567,
        "sales_count": 34,
        "image_url": "https://cdn.example.com/items/2.jpg",
        "is_featured": false
      }
    ],
    "creators": [
      {
        "id": 101,
        "name": "Artist Prime",
        "profile_image": "https://cdn.example.com/creators/101.jpg"
      },
      {
        "id": 102,
        "name": "Creator Guild",
        "profile_image": "https://cdn.example.com/creators/102.jpg"
      },
      {
        "id": 103,
        "name": "Legendary Labs",
        "profile_image": "https://cdn.example.com/creators/103.jpg"
      }
    ]
  }
}
```

**Response Fields**:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | integer | ✓ | Unique identifier |
| `title` | string | ✓ | Display name |
| `price_stars` | integer | ✓ | Price in Telegram Stars |
| `creator_id` | integer | ✓ | Foreign key to creators |
| `created_at` | ISO8601 | ✓ | UTC timestamp for sorting |
| `views` | integer | ✓ | View count statistic |
| `sales_count` | integer | ✓ | Number of units sold |
| `image_url` | string | ✗ | CDN URL (optional) |
| `is_featured` | boolean | ✗ | Featured badge flag |

---

### 2. Purchase Item

**Endpoint**: `POST /api/v1/marketplace/purchase`

**Request**:
```json
{
  "item_id": 1,
  "quantity": 1
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "transaction_id": "txn_abc123xyz",
    "item_id": 1,
    "amount": 50,
    "currency": "XTR",
    "status": "pending",
    "next_action": "confirm_payment"
  }
}
```

---

### 3. Get Item Details

**Endpoint**: `GET /api/v1/marketplace/items/{item_id}`

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "title": "Digital Art Collection #1",
    "description": "...",
    "price_stars": 50,
    "creator_id": 101,
    "created_at": "2026-02-27T10:00:00Z",
    "updated_at": "2026-02-27T12:00:00Z",
    "views": 234,
    "sales_count": 12,
    "image_url": "https://...",
    "is_featured": true,
    "availability": "in_stock"
  }
}
```

---

## UI STATE → API FLOW

### Loading Data

```javascript
// Inside MarketplaceApp.init()

const loadMarketplaceData = async () => {
  try {
    const response = await fetch('/api/v1/marketplace/items', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${getTelegramToken()}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const { data } = await response.json();
    
    // Populate state
    state.items = data.items;
    
    // Cache creator names
    data.creators?.forEach(creator => {
      state.creators.set(creator.id, creator.name);
    });

    // Apply initial filters & render
    applyFilters();
    renderMarketplaceGrid();
    
  } catch (error) {
    console.error('Failed to load marketplace:', error);
    displayEmptyState('Unable to load marketplace. Please try again.');
  }
};

const getTelegramToken = () => {
  if (window.Telegram?.WebApp?.initData) {
    return window.Telegram.WebApp.initData;
  }
  // Fallback for development
  return localStorage.getItem('auth_token');
};
```

---

### Purchase Flow

```javascript
// In rendered HTML
document.addEventListener('click', async (e) => {
  if (e.target.classList.contains('card-action')) {
    const itemId = parseInt(e.target.dataset.itemId);
    await handlePurchaseClick(itemId);
  }
});

const handlePurchaseClick = async (itemId) => {
  const item = state.items.find(i => i.id === itemId);
  
  try {
    // Show loading state
    const btn = event.target;
    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = 'Processing...';
    
    // Call purchase endpoint
    const response = await fetch('/api/v1/marketplace/purchase', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getTelegramToken()}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        item_id: itemId,
        quantity: 1
      })
    });

    const { data } = await response.json();
    
    // Navigate to payment confirmation
    if (window.Telegram?.WebApp) {
      window.Telegram.WebApp.openLink(`/checkout/${data.transaction_id}`);
    } else {
      window.location.hash = `#/checkout/${data.transaction_id}`;
    }
    
  } catch (error) {
    console.error('Purchase failed:', error);
    alert('Failed to start purchase. Please try again.');
    btn.disabled = false;
    btn.textContent = originalText;
  }
};
```

---

## FILTER OPERATIONS (DATABASE QUERY MAPPING)

### Filter State → SQL WHERE Clause

```javascript
// UI State
state.activeFilters = {
  priceMin: 25,
  priceMax: 100,
  creators: [101, 102],          // Multi-select
  availability: ['in_stock']
};

state.activeSort = 'price_asc';
```

### Maps to SQL:

```sql
SELECT 
  id, title, price_stars, creator_id, created_at, 
  views, sales_count, image_url, is_featured
FROM gifts
WHERE 
  price_stars >= 25
  AND price_stars <= 100
  AND creator_id IN (101, 102)
  AND sales_count > 0  -- in_stock
ORDER BY 
  price_stars ASC
LIMIT 50;
```

### Backend Implementation

```python
# FastAPI endpoint (optional server-side filtering)
@app.get("/api/v1/marketplace/items")
async def get_marketplace_items(
    price_min: int = Query(None),
    price_max: int = Query(None),
    creators: list[int] = Query(None),
    availability: str = Query(None),
    sort_by: str = Query("newest"),
    limit: int = Query(50),
    db: Session = Depends(get_db)
):
    """Get marketplace items with filtering & sorting"""
    
    query = db.query(Gift)
    
    # Filters
    if price_min is not None:
        query = query.filter(Gift.price_stars >= price_min)
    if price_max is not None:
        query = query.filter(Gift.price_stars <= price_max)
    if creators:
        query = query.filter(Gift.creator_id.in_(creators))
    if availability == "in_stock":
        query = query.filter(Gift.sales_count > 0)
    elif availability == "sold_out":
        query = query.filter(Gift.sales_count == 0)
    
    # Sorting
    if sort_by == "newest":
        query = query.order_by(Gift.created_at.desc())
    elif sort_by == "price_asc":
        query = query.order_by(Gift.price_stars.asc())
    elif sort_by == "price_desc":
        query = query.order_by(Gift.price_stars.desc())
    elif sort_by == "popular":
        query = query.order_by(Gift.sales_count.desc())
    
    items = query.limit(limit).all()
    
    # Get creators
    creator_ids = {item.creator_id for item in items}
    creators_data = db.query(Creator).filter(
        Creator.id.in_(creator_ids)
    ).all()
    
    return {
        "status": "success",
        "data": {
            "items": [item.to_dict() for item in items],
            "creators": [c.to_dict() for c in creators_data]
        }
    }
```

---

## AUTHENTICATION & AUTHORIZATION

### Telegram Mini App Auth Flow

```python
# Verify Telegram init data
import hashlib
import hmac
import json
from urllib.parse import parse_qs

def verify_telegram_web_app_data(init_data: str, bot_token: str) -> dict:
    """Verify Telegram WebApp init data signature"""
    
    parsed_data = parse_qs(init_data)
    signature = parsed_data.get('hash', [''])[0]
    
    # Remove hash from data for verification
    data_check_string = '\n'.join(
        f'{k}={v[0]}'
        for k, v in sorted(parsed_data.items())
        if k != 'hash'
    )
    
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    computed_signature = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    if signature != computed_signature:
        raise ValueError("Invalid signature")
    
    # Extract user data
    user_data = json.loads(parsed_data['user'][0])
    return user_data

# Protect endpoints
@app.get("/api/v1/marketplace/items")
async def get_marketplace_items(
    request: Request,
    db: Session = Depends(get_db)
):
    """Authenticated marketplace endpoint"""
    
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Missing auth token")
    
    token = auth_header[7:]
    
    try:
        user_data = verify_telegram_web_app_data(token, BOT_TOKEN)
        user_id = user_data['id']
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
    
    # Fetch items
    items = db.query(Gift).limit(50).all()
    creators = db.query(Creator).all()
    
    return {
        "status": "success",
        "data": {
            "items": [item.to_dict() for item in items],
            "creators": [c.to_dict() for c in creators]
        }
    }
```

---

## CORS CONFIGURATION

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://web.telegram.org",
        "https://web-beta.telegram.org"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## DATABASE OPTIMIZATIONS

### Indexes Required

```sql
-- Speed up marketplace queries
CREATE INDEX idx_gifts_price_stars ON gifts(price_stars);
CREATE INDEX idx_gifts_creator_id ON gifts(creator_id);
CREATE INDEX idx_gifts_created_at ON gifts(created_at DESC);
CREATE INDEX idx_gifts_sales_count ON gifts(sales_count DESC);

-- Combined index for filtering
CREATE INDEX idx_gifts_filter ON gifts(
  price_stars, creator_id, sales_count
);
```

### Query Performance

```python
# Avoid N+1 queries - use eager loading
from sqlalchemy.orm import joinedload

@app.get("/api/v1/marketplace/items")
async def get_marketplace_items(db: Session = Depends(get_db)):
    items = db.query(Gift).options(
        joinedload(Gift.creator)
    ).limit(50).all()
    
    return {
        "status": "success",
        "data": {
            "items": [item.to_dict() for item in items],
            "creators": [
                { "id": item.creator.id, "name": item.creator.name }
                for item in items
            ]
        }
    }
```

---

## ERROR HANDLING

```python
# Global error handler
from fastapi import HTTPException

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "error": {
                "code": exc.status_code,
                "message": exc.detail
            }
        }
    )

# Business logic errors
class MarketplaceError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message

@app.exception_handler(MarketplaceError)
async def marketplace_error_handler(request: Request, exc: MarketplaceError):
    return JSONResponse(
        status_code=400,
        content={
            "status": "error",
            "error": {
                "code": exc.code,
                "message": exc.message
            }
        }
    )
```

---

## DEVELOPMENT SETUP

### 1. Server Setup

```bash
# Create folder
mkdir -p app/ui

# Copy marketplace.html to app/ui/
cp marketplace.html app/ui/

# Run server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Test Locally

```bash
# Access in browser
open http://localhost:8000/ui/marketplace
```

### 3. Test with Telegram Mini App

```python
# Add test endpoint (development only)
@app.get("/test/init-data")
async def get_test_init_data():
    """Generate test Telegram init data"""
    import time
    import hashlib
    import hmac
    
    test_user = {
        "id": 123456789,
        "is_bot": False,
        "first_name": "Test",
        "username": "testuser",
        "language_code": "en"
    }
    
    # Build data string
    import json
    user_json = json.dumps(test_user)
    auth_date = int(time.time())
    
    data_check_string = f"user={user_json}\nauth_date={auth_date}"
    
    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    signature = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return {
        "init_data": f"user={user_json}&auth_date={auth_date}&hash={signature}"
    }
```

---

## DEPLOYMENT CHECKLIST

- [ ] Database indexes created
- [ ] API endpoints implemented & tested
- [ ] CORS configured for Telegram domains
- [ ] Authentication working (Telegram WebApp)
- [ ] Error handling in place
- [ ] Marketplace HTML served correctly
- [ ] Images cached/CDN configured
- [ ] Rate limiting configured
- [ ] Monitoring/logging set up
- [ ] SSL/TLS certificates installed
- [ ] Bot webhook configured for payments
- [ ] Telegram WebApp declared in bot settings

---

## TROUBLESHOOTING

### Issue: "unable to load marketplace"

**Check**:
1. API endpoint `/api/v1/marketplace/items` returns 200 OK
2. Auth token is valid (verify with Telegram)
3. CORS headers allow request origin
4. Database connection working

### Issue: Images not loading

**Check**:
1. `image_url` fields populated in database
2. Image URLs are absolute (https://...)
3. Image server accessible and CORS enabled

### Issue: Filters not filtering

**Check**:
1. Filter state updates correctly (console.log activeFilters)
2. Database fields match filter logic (price_stars, creator_id, etc.)
3. `applyFilters()` called before `applySort()`

---

**Last Updated**: Feb 27, 2026  
**Backend Owner**: Engineering Team  
**Frontend Owner**: Senior Design Engineer
