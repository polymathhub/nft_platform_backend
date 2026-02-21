# USDT Payment System Integration Guide

## Overview
This document provides a comprehensive guide to the USDT payment system integrated into the NFT Platform, including deposits, withdrawals, and NFT purchases with real-time exchange integration and 2% platform commission.

---

## System Architecture

### Components
1. **Frontend (Telegram WebApp)**: `app/static/webapp/index-fixed.html`
2. **Payment Router**: `app/routers/payment_router.py`
3. **Marketplace Service**: `app/services/marketplace_service.py`
4. **Wallet Service**: `app/services/wallet_service.py`
5. **Database Models**: Payment, Escrow, Order, Listing, Offer, NFT

### Supported Blockchains
- Ethereum (ERC20-USDT)
- Polygon (ERC20-USDT)
- Arbitrum (ERC20-USDT)
- Optimism (ERC20-USDT)
- Avalanche (ERC20-USDT)
- Base (ERC20-USDT)
- Solana (SPL-USDT)
- TON (Native USDT)
- Bitcoin (BTC as fallback)

---

## Flow Diagrams

### 1. DEPOSIT FLOW (Exchange → Platform)
```
User at Binance/Exchange
       ↓
Frontend: Initiate Deposit (blockchain, amount, wallet_id)
       ↓
POST /api/v1/payments/web-app/deposit
       ↓
PaymentService.initiate_deposit()
       ↓
Create Payment record (status=pending)
       ↓
Return: platform_address (where user should send USDT)
       ↓
User sends USDT from exchange to platform address
       ↓
Backend poll/webhook detects transaction
       ↓
PaymentService.confirm_deposit(payment_id, tx_hash)
       ↓
Update Payment status=confirmed
       ↓
User's balance updated automatically
       ↓
Frontend shows "Deposit Complete" with transaction details
```

### 2. WITHDRAWAL FLOW (Platform → Exchange/Wallet)
```
User inputs: destination_address, amount, blockchain
       ↓
Frontend: Initiate Withdrawal
       ↓
POST /api/v1/payments/web-app/withdrawal
       ↓
PaymentService.initiate_withdrawal()
       ↓
Create Payment record (status=pending, type=withdrawal)
       ↓
Frontend shows: withdrawal summary with network fee
       ↓
User confirms withdrawal
       ↓
POST /api/v1/payments/withdrawal/approve
       ↓
PaymentService.approve_withdrawal(payment_id)
       ↓
Execute blockchain transfer of USDT to destination_address
       ↓
Update Payment status=approved
       ↓
User receives USDT at destination
```

### 3. NFT PURCHASE WITH COMMISSION FLOW
```
Buyer browses marketplace, finds listing
       ↓
Buyer has deposited USDT into platform account
       ↓
Buyer makes offer OR clicks buy_now
       ↓
Frontend: makeOffer() OR purchase_nft()
       ↓
Marketplace.make_offer() OR Marketplace.buy_now()
       ↓
Calculate amounts:
    - royalty_amount = price × (nft.royalty_percentage / 100)
    - platform_fee = price × 0.02   [2% commission]
    - seller_receives = price - royalty_amount - platform_fee
       ↓
Create Order record with:
    - amount: full price
    - platform_fee: 2%
    - royalty_amount: collection royalty
    - status: pending/confirmed
       ↓
Create Escrow record:
    - Hold platform_fee (commission) in escrow
    - Schedule seller payment: seller_receives amount
    - Schedule collection creator payment: royalty_amount
       ↓
Transfer funds:
    1. Platform fee → platform_wallets[blockchain]
    2. Royalty → collection_creator_wallet
    3. Seller amount → seller_wallet
       ↓
Transfer NFT ownership:
    - nft.owner_address = buyer_address
    - nft.status = TRANSFERRED
       ↓
Order status = COMPLETED
```

---

## API Endpoints Reference

### Balance Check
```http
GET /api/v1/payments/balance
Headers: Authorization: Bearer <token>
Response: {
    "balance": 1000.50,
    "currency": "USDT",
    "blockchain_balances": {
        "ethereum": 500.25,
        "solana": 300.00,
        "ton": 200.25
    }
}
```

### Initiate Deposit
```http
POST /api/v1/payments/web-app/deposit
Body: {
    "user_id": "uuid",
    "wallet_id": "uuid",
    "amount": 100.00,
    "blockchain": "ethereum",
    "init_data": "telegram_init_data"
}
Response: {
    "success": true,
    "payment_id": "uuid",
    "deposit_address": "0x1234...",
    "amount": 100.00,
    "currency": "USDT",
    "blockchain": "ethereum"
}
```

### Confirm Deposit
```http
POST /api/v1/payments/deposit/confirm
Body: {
    "payment_id": "uuid",
    "transaction_hash": "0xabcd..."
}
Response: {
    "success": true,
    "payment_id": "uuid",
    "status": "confirmed"
}
```

### Initiate Withdrawal
```http
POST /api/v1/payments/web-app/withdrawal
Body: {
    "user_id": "uuid",
    "wallet_id": "uuid",
    "amount": 50.00,
    "destination_address": "0x5678...",
    "blockchain": "ethereum",
    "init_data": "telegram_init_data"
}
Response: {
    "success": true,
    "payment_id": "uuid",
    "network_fee": 2.50,
    "you_receive": 47.50,
    "status": "pending"
}
```

### Approve Withdrawal
```http
POST /api/v1/payments/withdrawal/approve
Body: {
    "payment_id": "uuid"
}
Response: {
    "success": true,
    "status": "approved",
    "transaction_hash": "0xdef0..."
}
```

### Payment History
```http
GET /api/v1/payments/history?type=deposit&limit=10
Response: {
    "payments": [
        {
            "payment_id": "uuid",
            "type": "deposit",
            "amount": 100.00,
            "status": "confirmed",
            "blockchain": "ethereum",
            "created_at": "2024-01-15T10:30:00Z"
        }
    ]
}
```

---

## Frontend Integration

### Payments Page Features

#### Deposit Tab
- **Wallet Selection**: Choose which wallet receives the deposit
- **Blockchain Selection**: ERC20, TON, SPL, or Bitcoin
- **Amount Input**: USDT amount to deposit
- **Address Display**: Shows platform's deposit address in that blockchain
- **Instructions**: Clear step-by-step guide to send from exchange
- **Transaction History**: Shows recent deposit transactions with status

#### Withdrawal Tab
- **Wallet Selection**: Choose wallet to withdraw from
- **Address Input**: Recipient wallet address (minimum 26 characters)
- **Amount Input**: USDT amount to withdraw
- **Fee Display**: Shows network fee (blockchain-dependent)
- **Summary**: Shows exact amount user receives = amount - fee
- **Confirmation**: Two-step confirmation (review + confirm)
- **Transaction History**: Shows recent withdrawals with status

#### Balance Display
- Shows current USDT balance in real-time
- Updates after successful deposit/withdrawal
- Reflects balance changes from NFT purchases

### Key Functions
```javascript
// Load current balance
loadBalance()

// Show deposit/withdrawal section
showPaymentSection('deposit' | 'withdraw')

// Initiate deposit
initiateDeposit()

// Copy deposit address to clipboard
copyDepositAddress()

// Initiate withdrawal
initiateWithdrawal()

// Confirm withdrawal
confirmWithdrawal()

// Refresh wallet selectors
refreshPaymentWallets(type)

// Load transaction history
loadDepositHistory()
loadWithdrawalHistory()
```

---

## Commission System

### 2% Platform Commission Structure

```
Purchase Price: $100.00 USDT
├─ Platform Commission (2%): $2.00 USDT
│  └─ Sent to: platform_wallets[blockchain]
├─ Collection Royalty (variable %): $5.00 USDT
│  └─ Sent to: collection_creator_wallet
└─ Seller Receives: $93.00 USDT
   └─ Sent to: seller_wallet
```

### Commission Configuration

**Location**: `app/config.py`
```python
commission_rate: float = 0.02  # 2% - can be configured per blockchain
commission_wallet: dict = {
    "ethereum": "0x...",
    "ton": "EQ...",
    "solana": "...",
    "erc20": "0x...",
    "trc20": "..."
}
```

### Commission Calculation (Code)
```python
# In marketplace_service.py accept_offer() and buy_now()
royalty_amount = offer.offer_price * (nft.royalty_percentage / 100)
platform_fee = offer.offer_price * 0.02
seller_receives = offer.offer_price - platform_fee - royalty_amount

# Create escrow with commission tracking
escrow = Escrow(
    listing_id=listing_id,
    offer_id=offer_id,
    buyer_id=buyer_id,
    seller_id=seller_id,
    amount=offer_price,
    commission_amount=platform_fee,
    royalty_amount=royalty_amount,
    status="pending"
)
```

---

## Real-Time Exchange Integration

### Supported Exchanges
1. **Binance**
   - Send USDT to provided deposit address
   - Platform address varies by blockchain
   - Confirmation within 1-5 minutes (Ethereum/Polygon) or up to 15 minutes (other chains)

2. **Kraken**
   - Use USDT withdrawal feature
   - Select blockchain (ERC20, Polygon, etc.)
   - Send to platform address provided in deposit form

3. **Coinbase**
   - Withdraw USDT
   - Select network (Ethereum, Polygon, etc.)
   - Use platform deposit address

4. **Other Exchanges**
   - Use USDT withdrawal feature
   - Select correct blockchain
   - Send to platform address

### Deposit Flow Steps
1. User clicks "Payments" → "Deposit" tab
2. Selects blockchain and amount
3. Frontend shows platform's deposit address for that blockchain
4. User copies address
5. User goes to exchange (Binance, Kraken, etc.)
6. Initiates USDT withdrawal
7. Pastes platform address as destination
8. Sends USDT
9. Backend confirms deposit transaction
10. User's balance updates automatically

---

## Testing Checklist

### Deposit Testing
- [ ] Create wallet for each blockchain
- [ ] Initiate deposit with various amounts
- [ ] Verify deposit address displays correctly
- [ ] Check transaction appears in history
- [ ] Verify balance updates after confirmation
- [ ] Test with different blockchains (Ethereum, Solana, TON)
- [ ] Verify UI shows pending status → confirmed status

### Withdrawal Testing
- [ ] Check available balance before withdrawal
- [ ] Initiate withdrawal to external address
- [ ] Verify fee calculation is correct
- [ ] Verify user receives amount minus fee
- [ ] Confirm withdrawal requires two-step confirmation
- [ ] Check transaction appears in history
- [ ] Verify external wallet receives USDT
- [ ] Test with different blockchains

### NFT Purchase with Commission Testing
- [ ] Deposit USDT into platform account
- [ ] Browse marketplace listing
- [ ] Make offer below asking price
- [ ] Verify seller receives: offer_price - commission(2%) - royalty(%)
- [ ] Verify platform receives 2% commission
- [ ] Verify collection creator receives royalty
- [ ] Check order status transitions (pending → completed)
- [ ] Verify NFT ownership transfers to buyer
- [ ] Verify seller's wallet receives payment

### Balance Integrity Testing
- [ ] Initial balance = 0
- [ ] After deposit: balance = deposit_amount
- [ ] After purchase: balance = previous - purchase_price
- [ ] After partial withdrawal: balance = previous - withdraw_amount - network_fee
- [ ] Multiple transactions: balance remains consistent

---

## Error Handling

### Common Error Scenarios

#### Insufficient Funds
```
User tries to withdraw 100 USDT but balance is 50 USDT
Error: "Insufficient balance. Available: 50.00 USDT"
Frontend: Shows error in red banner, clears form
```

#### Invalid Address
```
User enters address with < 26 characters
Error: "Invalid address format. Minimum 26 characters required."
Frontend: Prevents form submission, shows error message
```

#### Network Issues
```
Backend cannot reach blockchain to confirm deposit
Status: Remains "pending" until backend confirms transaction
Retry: Automatic retry with exponential backoff (1s, 2s, 4s, 8s)
```

#### Expired Listing
```
User tries to buy on expired listing
Error: "This listing has expired"
Frontend: Disables buy button, shows expiration date
```

---

## Blockchain Network Fees

### Approximate Network Fees (subject to change)
```
Ethereum:  $5.00 - $50.00 (depends on gas)
Polygon:   $0.10 - $1.00
Arbitrum:  $0.20 - $2.00
Optimism:  $0.30 - $3.00
Avalanche: $0.50 - $5.00
Base:      $0.20 - $2.00
Solana:    $0.001 - $0.01
TON:       $0.10 - $1.00
Bitcoin:   $2.00 - $20.00 (depends on network congestion)
```

### Fee Configuration
**Location**: `app/config.py` or `app/models/admin.py`
```python
blockchain_fees = {
    "ethereum": 0.02,  # in USDT
    "polygon": 0.001,
    "solana": 0.0001,
    "ton": 0.10,
    # ... other blockchains
}
```

---

## Database Schema

### Payment Model
```python
class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, ForeignKey("users.id"))
    wallet_id = Column(UUID, ForeignKey("wallets.id"), nullable=True)
    type = Column(String, enum=["deposit", "withdrawal"])
    amount = Column(Numeric(18, 8))
    status = Column(String, enum=["pending", "confirmed", "approved", "failed"])
    blockchain = Column(String)
    platform_address = Column(String, nullable=True)  # For deposits
    destination_address = Column(String, nullable=True)  # For withdrawals
    transaction_hash = Column(String, nullable=True)
    network_fee = Column(Numeric(18, 8), default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
```

### Order Model (In Marketplace)
```python
class Order(Base):
    __tablename__ = "orders"
    
    id = Column(UUID, primary_key=True)
    listing_id = Column(UUID, ForeignKey("listings.id"))
    nft_id = Column(UUID, ForeignKey("nfts.id"))
    seller_id = Column(UUID, ForeignKey("users.id"))
    buyer_id = Column(UUID, ForeignKey("users.id"))
    amount = Column(Numeric(18, 8))  # Full purchase price
    currency = Column(String, default="USDT")
    platform_fee = Column(Numeric(18, 8))  # 2% commission
    royalty_amount = Column(Numeric(18, 8))  # Collection royalty
    status = Column(String, enum=["pending", "completed", "failed"])
    transaction_hash = Column(String)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## Deployment Checklist

- [ ] Configure platform wallet addresses for each blockchain in `config.py`
- [ ] Set commission rate (default 2%) in `config.py`
- [ ] Deploy payment_router.py endpoint
- [ ] Deploy marketplace_service.py with commission logic
- [ ] Update frontend WebApp with payment UI
- [ ] Set up blockchain RPC endpoints for transaction confirmation
- [ ] Configure webhook/polling for deposit confirmation
- [ ] Test with testnet first (Goerli, Mumbai, etc.)
- [ ] Verify all blockchain wallets are funded for withdrawal processing
- [ ] Enable monitoring/alerts for payment transactions
- [ ] Document support procedures for manual intervention

---

## Security Considerations

1. **Address Validation**: All addresses validated for minimum length (26 characters)
2. **Amount Validation**: All amounts must be > 0 and within safe limits
3. **User Authentication**: All operations require valid Telegram WebApp auth
4. **Transaction Hashing**: All transactions verified with blockchain transaction hash
5. **Escrow Protection**: Commission held in escrow until order completes
6. **Rate Limiting**: Payment endpoints rate-limited to prevent abuse
7. **Audit Logging**: All payment operations logged with timestamp and user ID

---

## Support & Troubleshooting

### "Deposit address not showing"
1. Ensure wallet is selected in dropdown
2. Refresh page and try again
3. Check Telegram WebApp authentication

### "Balance not updating"
1. Wait 2-3 minutes for blockchain confirmation
2. Check transaction status on blockchain explorer
3. Verify transaction hash in browser console

### "Withdrawal stuck as pending"
1. Check destination address is correct
2. Verify user has sufficient balance
3. Check blockchain network status
4. Contact support with transaction ID

### "NFT purchase failed"
1. Verify buyer has sufficient USDT balance
2. Confirm listing is still active
3. Check network status for blockchain
4. Retry the purchase after waiting 30 seconds

---

## Future Enhancements

1. **Multi-currency Support**: Add USDC, DAI support
2. **Staking**: Allow users to stake USDT for rewards
3. **Lending**: Collateralized lending with NFT as collateral
4. **Cross-chain Bridge**: Enable deposits from multiple blockchains
5. **Mobile App**: Native iOS/Android app with same payment system
6. **Advanced Analytics**: Payment dashboard with charts and insights
7. **Recurring Payments**: Subscription-based NFT purchases
8. **Payment Splitting**: Distribute payments among multiple creators

---

## Contact & Support

For payment system issues or feature requests:
- GitHub Issues: [...link...]
- Email Support: [...email...]
- Telegram Support Group: [...link...]

---

**Last Updated**: 2024-01-15
**Version**: 1.0.0
**Status**: Production Ready ✓
