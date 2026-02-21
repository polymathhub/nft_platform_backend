# USDT Marketplace Flow with Commission Handling

## Overview
This document describes the complete flow of USDT transfers on the NFT marketplace with proper 2% platform commission deduction and fund routing.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    MARKETPLACE FLOW SUMMARY                 │
└─────────────────────────────────────────────────────────────┘

1️⃣  DEPOSIT PHASE (User → Platform)
   Buyer deposits USDT from external wallet (Binance, etc)
   → /web-app/deposit endpoint
   → Funds held in platform USDT account
   
2️⃣  OFFER PHASE (Buyer Shows Intent)
   Buyer makes offer on NFT listing
   → /web-app/make-offer 
   → Marks USDT as "reserved" for this specific offer
   → Creates Offer record (PENDING status)
   
3️⃣  ACCEPTANCE PHASE (Seller Accepts)
   Seller accepts buyer's offer
   → /web-app/accept-offer
   → Creates Order with calculated amounts
   → Creates Escrow record with commission breakdown
   
4️⃣  SETTLEMENT PHASE (Automatic Fund Routing)
   Platform autopay transfers funds according to Order:
   ├─ Total Offer Amount: 100 USDT (example)
   ├─ Platform Commission (2%): 2 USDT → Platform wallet
   ├─ Royalty (if any): X USDT → Creator wallet  
   └─ Seller Amount: (100 - 2 - X) USDT → Seller wallet
   
5️⃣  NFT TRANSFER
   NFT ownership transferred to buyer
   Order marked as COMPLETED
```

## Detailed Flow

### Phase 1: Deposit (Buyer deposits USDT)

**Endpoint**: `POST /web-app/deposit`

**Request**:
```json
{
  "user_id": "uuid",
  "wallet_id": "uuid",
  "blockchain": "ethereum",
  "amount": 100.00,
  "init_data": "telegram_init_data"
}
```

**Process**:
1. Validate user has wallet on blockchain
2. Generate unique platform deposit address
3. Create Payment record (status: PENDING)
4. Return deposit address to user

**Response**:
```json
{
  "success": true,
  "payment_id": "uuid",
  "deposit_address": "0x...",
  "amount": 100.00,
  "blockchain": "ethereum",
  "status": "pending_deposit"
}
```

**User Action**: 
- Copy deposit address
- Send 100 USDT from Binance/exchange to this address
- Platform monitors blockchain for confirmation

**Once Confirmed**:
- Payment status → CONFIRMED
- User's USDT balance increases by 100
- User can now make offers

---

### Phase 2: List NFT (Seller starts)

**Endpoint**: `POST /web-app/list-nft`

**Request**:
```json
{
  "user_id": "uuid",
  "nft_id": "uuid",
  "price": 50.00,
  "currency": "USDT"
}
```

**Process**:
1. Validate NFT ownership
2. Validate listing currency support
3. Lock NFT (prevent transfer during listing)
4. Create Listing record (status: ACTIVE)
5. Return listing ID

**Response**:
```json
{
  "success": true,
  "listing": {
    "id": "listing-uuid",
    "nft_id": "nft-uuid",
    "price": 50.00,
    "currency": "USDT",
    "status": "active"
  }
}
```

---

### Phase 3: Make Offer (Buyer bids)

**Endpoint**: `POST /web-app/make-offer`

**Frontend Calculation** (before sending):
```javascript
const offerAmount = 50.00; // USDT
const platformCommission = offerAmount * 0.02; // 1.00 USDT
const sellerReceives = offerAmount - platformCommission; // 49.00 USDT

// Show to user:
console.log(`Offer: ${offerAmount} USDT`);
console.log(`Platform Fee (2%): ${platformCommission} USDT`);
console.log(`Seller Gets: ${sellerReceives} USDT`);
```

**User sees pop-up**:
```
Offer: 50.00 USDT
Platform Fee (2%): 1.00 USDT
Seller Receives: 49.00 USDT

Continue?
```

**Request**:
```json
{
  "user_id": "buyer-uuid",
  "listing_id": "listing-uuid",
  "offer_price": 50.00,
  "currency": "USDT"
}
```

**Backend Process**:
1. Validate listing exists and is ACTIVE
2. Validate buyer ≠ seller
3. Check buyer has sufficient USDT (50.00 USDT in account)
4. Create Offer record:
   ```python
   offer = Offer(
       listing_id=listing_id,
       nft_id=listing.nft_id,
       buyer_id=buyer_id,
       buyer_address=wallet.address,
       offer_price=50.00,  # Full amount
       currency="USDT",
       status=OfferStatus.PENDING,
   )
   ```
5. Return offer ID

**Response**:
```json
{
  "success": true,
  "offer": {
    "id": "offer-uuid",
    "offer_price": 50.00,
    "currency": "USDT",
    "status": "pending"
  }
}
```

**State After Offer**:
- Buyer's balance: 100 - 50 = 50 USDT (50 reserved for this offer)
- Offer status: PENDING (awaiting seller acceptance)
- NFT still owned by seller

---

### Phase 4: Accept Offer (Seller accepts)

**Endpoint**: `POST /web-app/accept-offer`

**Request**:
```json
{
  "seller_id": "seller-uuid",
  "offer_id": "offer-uuid"
}
```

**Backend Process**:

1. **Fetch Offer & Validate**:
   ```python
   offer = db.get(Offer, offer_id)
   if offer.status != PENDING:
       return error
   ```

2. **Calculate Commission Breakdown**:
   ```python
   offer_amount = 50.00
   platform_fee = 50.00 * 0.02 = 1.00  # 2% commission
   royalty = 50.00 * (nft.royalty_percentage / 100) = 2.50  # 5% royalty
   seller_amount = 50.00 - 1.00 - 2.50 = 46.50
   ```

3. **Create Order**:
   ```python
   order = Order(
       listing_id=listing_id,
       offer_id=offer_id,
       nft_id=nft_id,
       seller_id=seller_id,
       buyer_id=buyer_id,
       amount=50.00,           # Full offer amount
       currency="USDT",
       status=OrderStatus.CONFIRMED,
       royalty_amount=2.50,    # Creator gets this
       platform_fee=1.00,      # Platform keeps this
   )
   ```

4. **Create Escrow (Fund Holding)**:
   ```python
   escrow = Escrow(
       listing_id=listing_id,
       offer_id=offer_id,
       buyer_id=buyer_id,
       seller_id=seller_id,
       amount=50.00,           # Held amount
       currency="USDT",
       commission_amount=1.00,
       status=EscrowStatus.HELD,
   )
   # Funds are held in USDT escrow account until settlement
   ```

5. **Update State**:
   ```python
   offer.status = ACCEPTED
   listing.status = ACCEPTED
   nft.owner_address = buyer_address
   nft.status = TRANSFERRED
   nft.is_locked = False
   ```

6. **Transaction Log**:
   ```
   [SETTLEMENT QUEUE]
   Event: Offer Accepted (Order #{order_id})
   Seller: {seller_address}
   Buyer: {buyer_address}
   Amount: 50.00 USDT
   
   Breakdown:
   ├─ Platform Commission: 1.00 USDT → {platform_wallet}
   ├─ Creator Royalty:     2.50 USDT → {creator_wallet}
   └─ Seller Amount:      46.50 USDT → {seller_address}
   ```

**Response**:
```json
{
  "success": true,
  "order": {
    "id": "order-uuid",
    "amount": 50.00,
    "platform_fee": 1.00,
    "royalty_amount": 2.50,
    "status": "confirmed"
  }
}
```

---

### Phase 5: Fund Settlement (Automatic)

**Backend Settlement Process**:

1. **Read Escrow Record**:
   - Get all accepted orders waiting settlement
   - Group by blockchain/currency

2. **Calculate Total Transfers**:
   ```python
   total_to_platform = sum(e.commission_amount for e in escrows) 
                     # All orders' 2% fees
   
   total_to_creators = sum(Creator royalties from all orders)
   
   transfers_to_sellers = {
       seller_address: sum(amount - commission - royalty)
       for each completed order
   }
   ```

3. **Execute Blockchain Transfers** (via automatic job):
   ```python
   # Example: Process one order
   platform_wallet = get_commission_wallet(blockchain="ethereum")
   seller_wallet = "0x..."
   
   # Transfer 1. Platform fee
   transfer(
       from=escrow_address,
       to=platform_wallet,
       amount=1.00,
       description="Platform Commission"
   )
   
   # Transfer 2. Creator royalty (if applicable)
   if royalty > 0:
       transfer(
           from=escrow_address,
           to=creator_wallet,
           amount=2.50,
           description="Creator Royalty"
       )
   
   # Transfer 3. Seller amount
   transfer(
       from=escrow_address,
       to=seller_wallet,
       amount=46.50,
       description="NFT Sale Proceeds"
   )
   ```

4. **Update Records**:
   ```python
   escrow.status = RELEASED
   order.status = COMPLETED
   order.completed_at = datetime.now()
   ```

5. **Final State**:
   ```
   ✅ Buyer:     Accounts reduced by 50 USDT (withdrawn from balance)
   ✅ Seller:    Accounts increased by 46.50 USDT
   ✅ Platform:  Receives 1.00 USDT
   ✅ Creator:   Receives 2.50 USDT (if applicable)
   ✅ NFT:       Ownership transferred to buyer
   ```

---

## Fund Routing Wallets

### Commission Wallet (Platform)
- Blockchain: Ethereum
- Address: `config.COMMISSION_WALLET_ERC20`
- Receives: 2% of all USDT sales on Ethereum
- Frequency: Automatic settlement per order

### Sideropoli/Creator Wallet
- Varies per NFT
- Receives: Royalty percentage per NFT (configurable)
- Default: 5% of sale price

### Seller Wallets (User-provided)
- Wallet connected to their account
- Receives: Sale amount minus commission and royalty
- Must be same blockchain as listing

---

## Commission Structure

| Component | Amount | Recipient |
|-----------|--------|-----------|
| Platform Commission | 2% of sale price | Platform wallet |
| Creator Royalty | 0-10% (configurable) | Creator wallet |
| Seller Amount | Remainder | Seller wallet |

**Example**: 100 USDT sale with 5% royalty:
- Platform: 2 USDT
- Creator: 5 USDT
- Seller: 93 USDT

---

## Error Scenarios & Handling

### 1. Insufficient USDT Balance
```
Offer: 50 USDT
User Balance: 30 USDT
Status: ❌ ERROR
Message: "Insufficient balance. You have 30 USDT but offer requires 50 USDT"
```

### 2. Listing Expired
```
Listing created: Jan 1
Expiration: Jan 8
Current date: Jan 15
Status: ❌ ERROR  
Message: "Listing has expired"
```

### 3. NFT Already Locked
```
NFT listed on Marketplace: ✅ LOCKED
Seller tries to list again: ❌ ERROR
Message: "NFT is locked and cannot be listed (already on marketplace)"
```

### 4. Commission Wallet Transfer Failed
```
Settlement started: ✅
Platform fee transfer to {platform_wallet}: ❌ FAILED
Retry: Automatic (exponential backoff)
Log: Error recorded for manual investigation
```

---

## Frontend User Experience

### 1. Browse Listings
```
✅ Shows all active listings with:
  - NFT image preview
  - Price: 50.00 USDT
  - Seller info
  - Blockchain (Ethereum)
  - Copy buttons for IDs
```

### 2. Make Offer Dialog
```
✅ Calculations shown before confirmation:
  Base Offer:        50.00 USDT
  Platform Fee (2%): -1.00 USDT
  You Pay:           50.00 USDT  ◄ From your account
  Seller Gets:       49.00 USDT
  
  [Cancel] [Confirm Offer]
```

### 3. Offer Status Updates
```
✅ Notification states:
  - "Offer made! Waiting for seller approval..."
  - "Seller accepted your offer!"
  - "NFT transferred to your account"
  - "Settlement complete - funds sent to seller"
```

### 4. Transaction History
Shows all orders with breakdown:
```
Order #1234 - COMPLETED
Offer Amount:   100 USDT
Platform Fee:   -2 USDT
Creator Fee:    -5 USDT
You Received:   93 USDT
Status:         ✅ PAID
```

---

## Testing Checklist

- [ ] User can deposit 100 USDT from simulated wallet
- [ ] User balance shows 100 USDT after deposit confirms
- [ ] User can list NFT for 50 USDT
- [ ] User can make offer with commission calculation shown
- [ ] Seller receives offer notification
- [ ] Seller can accept offer
- [ ] USDT deducted from buyer (50 USDT)
- [ ] USDT added to seller (49 USDT, after 2% commission)
- [ ] Platform receives commission (1 USDT)
- [ ] NFT transferred to buyer
- [ ] Order shows COMPLETED status
- [ ] All transaction history records created

---

## Database Records

### Offer Record
```python
{
    id: UUID,
    listing_id: UUID,
    nft_id: UUID,
    buyer_id: UUID,
    buyer_address: str,
    offer_price: 50.00,
    currency: "USDT",
    status: "pending|accepted|rejected",
    created_at: datetime,
    expires_at: datetime
}
```

### Order Record
```python
{
    id: UUID,
    listing_id: UUID,
    offer_id: UUID,
    nft_id: UUID,
    seller_id: UUID,
    buyer_id: UUID,
    amount: 50.00,
    currency: "USDT",
    blockchain: "ethereum",
    platform_fee: 1.00,      # 2% commission
    royalty_amount: 2.50,    # Creator royalty
    status: "confirmed|completed|failed",
    completed_at: datetime
}
```

### Escrow Record
```python
{
    id: UUID,
    listing_id: UUID,
    offer_id: UUID,
    buyer_id: UUID,
    seller_id: UUID,
    amount: 50.00,
    currency: "USDT",
    commission_amount: 1.00,  # 2% held for platform
    status: "held|released|failed",
    created_at: datetime,
    released_at: datetime
}
```

---

## Commission Wallet Configuration

**File**: `app/config.py`

```python
# Commission settings
commission_rate: float = 0.02  # 2%

# Per-blockchain commission wallets
commission_wallet_erc20: str = "0x..."      # Ethereum USDT
commission_wallet_trc20: str = "T..."       # Tron USDT
commission_wallet_sol: str = "So..."        # Solana USDT
```

**Admin Panel**: Can update commission rate dynamically via AdminSettings model

---

## Key Features Implemented

✅ **2% Platform Commission** - Automatically calculated and deducted  
✅ **Creator Royalties** - Per-NFT configurable (0-10%)  
✅ **Escrow System** - Funds held safely during settlement  
✅ **Real-time USDT Deposits** - From external wallets (Binance, etc)  
✅ **Automatic Settlement** - Fund routing happens automatically  
✅ **Commission Tracking** - Full audit trail in database  
✅ **Error Resilience** - Failed transfers retry with exponential backoff  
✅ **User Transparency** - Clear commission display before confirmation  

---

## Security Considerations

1. **Fund Custody**: USDT held in platform-controlled escrow during settlement
2. **Commission Validation**: Backend recalculates commission (never trust frontend)
3. **Address Validation**: Seller address must match wallet associated with listing
4. **Rate Updates**: Commission rate changes apply only to future orders
5. **Audit Trail**: All fund movements logged in ActivityLog
