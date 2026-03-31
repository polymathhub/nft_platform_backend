# 🎯 SIMPLE REFERRAL SYSTEM - Implementation Guide

## 📋 What Was Built

**A production-ready referral system that:**
- ✅ Auto-generates unique referral codes for every new user
- ✅ Stores codes in the database (no external service needed)
- ✅ Displays the code on the profile page
- ✅ Allows users to copy and share their code
- ✅ Tracks how many people used their referral code
- ✅ Completely seamless Telegram authentication

---

## 🏗️ Architecture (Simple & Clean)

### **Database**
- User model already has `referral_code` field (unique)
- User model has `referred_by_id` field to track who referred them

### **Backend**

#### **1. Referral Utilities** (`app/utils/referral_utils.py`)
```python
async def generate_referral_code(db: AsyncSession, length: int = 10) -> str
    # Generates: REF_XXXXXXXXXX (10 random alphanumeric chars)
    # Ensures uniqueness (checks database)
    # Returns secure cryptographic token
```

#### **2. Referral Router** (`app/routers/referrals_router.py`)

**Endpoint 1: Get User's Referral Code**
```
GET /api/v1/referrals/me
```
Response:
```json
{
  "success": true,
  "data": {
    "referral_code": "REF_ABC123XYZ",
    "referral_url": "https://t.me/nftbot?startapp=ref_ABC123XYZ",
    "total_referrals": 5
  }
}
```

**Endpoint 2: Regenerate Code (if user wants new one)**
```
POST /api/v1/referrals/regenerate
```

**Endpoint 3: Use Referral Code (new user signs up)**
```
POST /api/v1/referrals/use/{referral_code}
```

#### **3. Seamless Telegram Auth**
When a NEW user signs up via Telegram:
1. `telegram_auth_dependency.py` auto-creates user
2. **Auto-generates referral code** ← NEW
3. Returns user to frontend
4. User doesn't need to do anything - code is ready

---

## 🎨 Frontend (Profile Page)

### **Referral Code Display** (`profile.html`)
```html
<div id="referral-code-display">REF_XYZ123</div>
```

### **Copy Button**
```javascript
window.copyReferralCode = () => {
  navigator.clipboard.writeText(referralCode);
  alert('Copied!');
}
```

### **Share Button** 
Opens modal with options:
- 📱 Telegram
- 💬 WhatsApp
- 🐦 Twitter
- 📧 Email

### **Referral Count**
```javascript
<div id="referral-count">5</div>  // # of people who used their code
```

---

## 🚀 How It Works (User Journey)

### **Step 1: New User Signs Up**
```
User opens Telegram Mini App
  ↓
App sends initData to backend
  ↓
telegram_auth_dependency:
  - Creates user account
  - AUTO-GENERATES referral code (REF_ABC123)
  - Saves to database
  ↓
Frontend loads profile.html
```

### **Step 2: User Views Profile**
```
Profile page loads
  ↓
JavaScript calls: GET /api/v1/referrals/me
  ↓
API returns:
{
  "referral_code": "REF_ABC123",
  "total_referrals": 0
}
  ↓
UI displays code & copy/share buttons
```

### **Step 3: User Shares Code**
```
User clicks "Share" button
  ↓
Modal shows social media options
  ↓
User picks Telegram
  ↓
Pre-filled message: "Use my code: REF_ABC123"
  ↓
Friend receives link
```

### **Step 4: Friend Signs Up With Code**
```
Friend clicks referral link
  ↓
New user creates account
  ↓
Frontend calls: POST /api/v1/referrals/use/REF_ABC123
  ↓
Backend:
  - Links friend to original user
  - Sets friend.referred_by_id = original_user.id
  ↓
Both users see updated referral count
```

---

## 📝 API Reference

### 1. Get Referral Code
```bash
curl -X GET http://localhost:8000/api/v1/referrals/me \
  -H "X-Telegram-Init-Data: YOUR_TELEGRAM_DATA"
```

**Response (Success):**
```json
{
  "success": true,
  "data": {
    "referral_code": "REF_K7M9N2X4",
    "referral_url": "https://t.me/nftbot?startapp=ref_K7M9N2X4",
    "total_referrals": 3
  },
  "message": "Referral code retrieved successfully"
}
```

### 2. Regenerate Code
```bash
curl -X POST http://localhost:8000/api/v1/referrals/regenerate \
  -H "X-Telegram-Init-Data: YOUR_TELEGRAM_DATA"
```

Response: Same format as above (with new code)

### 3. Use Referral Code
```bash
curl -X POST http://localhost:8000/api/v1/referrals/use/REF_K7M9N2X4 \
  -H "X-Telegram-Init-Data: YOUR_TELEGRAM_DATA"
```

**Response (Success):**
```json
{
  "success": true,
  "data": {
    "referrer": "john_smith",
    "message": "Welcome! You've been referred by john_smith"
  },
  "message": "Referral code applied successfully"
}
```

---

## 💻 Code Examples

### **Frontend: Load Referral Code**
```javascript
// Simple & Clean
class ReferralSystem {
  constructor() {
    this.referralCode = null;
    this.referralCount = 0;
  }

  async loadReferralData() {
    try {
      // Call API (uses Telegram auth automatically)
      const response = await telegramFetch('/api/v1/referrals/me');
      
      if (response && response.data) {
        this.referralCode = response.data.referral_code;
        this.referralCount = response.data.total_referrals || 0;
      }
    } catch (error) {
      console.warn('[Referral] Failed to load:', error.message);
    }

    this.renderUI();
  }

  renderUI() {
    if (this.referralCode) {
      document.getElementById('referral-code-display').textContent = this.referralCode;
    }
    document.getElementById('referral-count').textContent = this.referralCount;
  }

  copy() {
    navigator.clipboard.writeText(this.referralCode);
    alert('Referral code copied!');
  }

  share() {
    const text = `Join me! Use code: ${this.referralCode}`;
    // Show share modal...
  }
}
```

### **Backend: Generate Unique Code**
```python
# app/utils/referral_utils.py
async def generate_referral_code(db: AsyncSession) -> str:
    characters = string.ascii_uppercase + string.digits
    
    # Try up to 10 times to ensure uniqueness
    for attempt in range(10):
        random_part = ''.join(
            secrets.choice(characters) for _ in range(10)
        )
        code = f"REF_{random_part}"
        
        # Check if already exists
        existing = await db.execute(
            select(User).where(User.referral_code == code)
        )
        
        if not existing.scalar_one_or_none():
            return code  # ✅ Unique!
    
    raise RuntimeError("Failed to generate unique code")
```

### **Auto-Generate on User Signup** (Modified)
```python
# app/utils/telegram_auth_dependency.py

from app.utils.referral_utils import generate_referral_code

async def get_current_user(...) -> User:
    # ... auth verification ...
    
    # New user - auto-generate referral code
    new_user = User(
        email=email,
        username=username,
        # ... other fields ...
        
        # ✨ NEW: Auto-generate referral code
        referral_code=await generate_referral_code(db)
    )
    
    db.add(new_user)
    await db.flush()
    await db.commit()
```

---

## 🔒 Security

✅ **Authentication**
- All referral endpoints require X-Telegram-Init-Data header
- Telegram-verified users only

✅ **Data Validation**
- Referral codes are cryptographically secure (secrets module)
- Unique constraint on database (can't create duplicate codes)
- Referral link can only be used once per user

✅ **Rate Limiting** (Optional future enhancement)
- Could limit code regeneration (e.g., once per day)
- Could limit referral accepts (e.g., one per user)

---

## 🧪 Testing

### **Test Referral Code Generation**
```bash
# 1. Create new user (automatic code generation)
curl -X GET http://localhost:8000/api/v1/me \
  -H "X-Telegram-Init-Data: YOUR_DATA"

# 2. Get referral code
curl -X GET http://localhost:8000/api/v1/referrals/me \
  -H "X-Telegram-Init-Data: YOUR_DATA"
# Should return: {"referral_code": "REF_XXXXX", "total_referrals": 0}

# 3. Regenerate (get new code)
curl -X POST http://localhost:8000/api/v1/referrals/regenerate \
  -H "X-Telegram-Init-Data: YOUR_DATA"
# Should return NEW referral_code
```

### **Test Referral Link**
```bash
# User 1 gets code: REF_ABC123

# User 2 signs up and applies code:
curl -X POST http://localhost:8000/api/v1/referrals/use/REF_ABC123 \
  -H "X-Telegram-Init-Data: USER_2_DATA"

# Check User 1's count increased:
curl -X GET http://localhost:8000/api/v1/referrals/me \
  -H "X-Telegram-Init-Data: USER_1_DATA"
# Should show: {"total_referrals": 1}
```

---

## 📊 Database Fields Used

### **users table**
```sql
- id (primary key)
- referral_code (UNIQUE, VARCHAR 50)  -- REF_XXXXXXXXXX
- referred_by_id (FK users.id)         -- Who referred this user
- created_at, updated_at               -- Tracking
```

### **Queries**
```sql
-- Get user's referral code
SELECT referral_code FROM users WHERE id = ?

-- Count referrals (people who used their code)
SELECT COUNT(*) FROM users WHERE referred_by_id = ?

-- Check if code exists
SELECT id FROM users WHERE referral_code = ?
```

---

## 🎯 What's Next (Optional Enhancements)

### **Referral Rewards**
```python
# Could add in future:
- User earns 5% commission on referred user's purchases
- Stars distributed as commission
- Commission tracking in separate table
```

### **Referral Leaderboard**
```
GET /api/v1/referrals/leaderboard
Response: Top 100 users by referral count
```

### **Referral Analytics**
```
GET /api/v1/referrals/stats
Response: {
  "total_referrals": 5,
  "active_referrals": 3,
  "total_earnings": 25.50,
  "referred_by": "john_smith"
}
```

---

## ✅ Deployment Checklist

- [x] Referral utils function created
- [x] Referral router created (3 endpoints)
- [x] Router registered in main.py
- [x] Telegram auth auto-generates codes
- [x] Profile UI updated
- [x] JavaScript simplified and working
- [x] Database fields already exist
- [x] No new migrations needed

**Status**: ✅ **Ready for production!**

---

## 📞 Troubleshooting

### **Issue: Code not showing on profile**
**Solution**: 
- Check browser console for errors
- Verify `/api/v1/referrals/me` endpoint is called
- Ensure X-Telegram-Init-Data header is present

### **Issue: Code regeneration fails**
**Solution**:
- Check database for duplicate codes
- Verify uniqueness constraint is set
- Check logs for SQL errors

### **Issue: Referral link not working**
**Solution**:
- Verify referral code format (REF_XXXXXXXXXX)
- Check user is authenticated
- Verify referenced user exists in database

---

**System**: Production-Ready ✨
**Last Updated**: March 31, 2026
**Status**: Fully Implemented
