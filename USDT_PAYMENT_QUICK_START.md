# USDT Payment System - Quick Start Guide

## Overview
The NFT Platform now supports complete USDT payment integration with:
- ✓ Real-time deposits from Binance, Kraken, Coinbase, and other exchanges
- ✓ Instant withdrawals to any external blockchain wallet
- ✓ 2% platform commission on all NFT purchases
- ✓ Commission automatically deducted and awarded to platform
- ✓ Support for all major blockchains (Ethereum, Polygon, Solana, TON, etc.)

---

## Getting Started

### For End Users

#### Depositing USDT (Exchange → Platform)
1. Open the NFT Platform in Telegram
2. Click **Payments** in the sidebar
3. Select **Deposit** tab
4. Choose a blockchain (Ethereum, Solana, TON, etc.)
5. Enter the amount of USDT you want to deposit
6. Select your wallet (click "Get Deposit Address")
7. Platform will display a deposit address
8. Copy the address
9. Go to your exchange (Binance, Kraken, Coinbase, etc.)
10. Initiate USDT withdrawal
11. Paste the platform address as the destination
12. Complete the withdrawal
13. Wait for blockchain confirmation (1-5 minutes typically)
14. Your balance updates automatically!

#### Withdrawing USDT (Platform → External Wallet)
1. Click **Payments** → **Withdraw** tab
2. Enter your recipient wallet address
3. Select the blockchain to use
4. Enter the amount to withdraw
5. Review the network fee and amount you'll receive
6. Click "Continue"
7. Review the withdrawal summary
8. Click "Confirm & Withdraw"
9. Approve the confirmation dialog
10. Your USDT will be sent to your wallet
11. Check transaction status in history

#### Buying NFTs with USDT
1. Deposit USDT into your platform account (steps above)
2. Click **Marketplace**
3. Browse available NFTs or make an offer
4. Your USDT balance is automatically deducted
5. Platform takes 2% commission automatically
6. Seller receives the rest (minus any collection royalty)
7. NFT transfers to your wallet

---

## For Developers

### API Integration

#### Check Balance
```bash
curl -X GET "http://localhost:8000/api/v1/payments/balance" \
  -H "Authorization: Bearer <token>"
```

#### Deposit Flow
```bash
# Step 1: Initiate deposit
curl -X POST "http://localhost:8000/api/v1/payments/web-app/deposit" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "uuid",
    "wallet_id": "uuid",
    "amount": 100.0,
    "blockchain": "ethereum"
  }'

# Response includes deposit_address where user sends USDT

# Step 2: Confirm deposit (after user sends USDT)
curl -X POST "http://localhost:8000/api/v1/payments/deposit/confirm" \
  -H "Content-Type: application/json" \
  -d '{
    "payment_id": "uuid",
    "transaction_hash": "0x..."
  }'
```

#### Withdrawal Flow
```bash
# Step 1: Initiate withdrawal
curl -X POST "http://localhost:8000/api/v1/payments/web-app/withdrawal" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "uuid",
    "wallet_id": "uuid",
    "amount": 50.0,
    "destination_address": "0x...",
    "blockchain": "ethereum"
  }'

# Response includes network_fee and amount user will receive

# Step 2: Approve withdrawal
curl -X POST "http://localhost:8000/api/v1/payments/withdrawal/approve" \
  -H "Content-Type: application/json" \
  -d '{
    "payment_id": "uuid"
  }'
```

#### Get Payment History
```bash
curl -X GET "http://localhost:8000/api/v1/payments/history?type=deposit&limit=10" \
  -H "Authorization: Bearer <token>"
```

### Commission System Implementation

The 2% commission is automatically handled in the marketplace:

```python
# When an offer is accepted or buy_now is executed:
royalty_amount = nft.royalty_percentage / 100 * price
platform_fee = price * 0.02  # 2% commission

# Escrow is created with these amounts:
escrow = Escrow(
    amount=price,
    commission_amount=platform_fee,
    royalty_amount=royalty_amount
)

# Seller receives:
seller_amount = price - platform_fee - royalty_amount
```

---

## Configuration

### Setting Commission Rate
Edit `app/config.py`:
```python
commission_rate: float = 0.02  # 2%
```

### Setting Platform Wallets (Receive Commissions)
Edit `app/config.py`:
```python
platform_wallets = {
    "ethereum": "0x1234567890123456789012345678901234567890",
    "polygon": "0x1234567890123456789012345678901234567890",
    "solana": "...",
    "ton": "...",
    # etc.
}
```

### Network Fee Configuration
Edit `app/config.py`:
```python
blockchain_fees = {
    "ethereum": 0.02,
    "polygon": 0.001,
    "solana": 0.0001,
    "ton": 0.10,
    # etc.
}
```

---

## Testing

### Run Payment System Tests
```bash
# All tests
python test_usdt_payment_system.py

# Against specific server
python test_usdt_payment_system.py --server http://production-server.com

# With custom user
python test_usdt_payment_system.py --user-id "your-uuid" --init-data "your-init-data"
```

### Manual Testing Checklist
- [ ] Deposit 10 USDT via Ethereum
- [ ] Withdraw 5 USDT to external wallet
- [ ] Verify balance updates correctly
- [ ] Make an offer on NFT with deposited USDT
- [ ] Verify 2% commission deducted
- [ ] Check Binance/exchange receives withdrawal
- [ ] Verify seller receives correct amount (minus 2% commission)

---

## Troubleshooting

### "Deposit address not showing"
- Make sure you selected a wallet
- Ensure wallet is created for the selected blockchain
- Check browser console for errors

### "Withdrawal fails with 'insufficient balance'"
- Check your balance first
- Remember network fees are deducted from withdrawal amount
- Withdraw less than available balance

### "NFT purchase says 'insufficient balance'"
- Deposit more USDT first
- Remember 2% of purchase price is platform fee
- Make sure balance includes the full purchase + 2%

### "Transaction not confirming after 10 minutes"
- Check blockchain explorer for transaction status
- On Ethereum, gas price might be high - wait for next block
- For Binance Smart Chain, confirmation is ~3-5 seconds
- For Solana, confirmation should be ~10-30 seconds

### "Can't connect to payment API"
- Ensure backend server is running
- Check server URL in configuration
- Verify network connectivity
- Check server logs for errors

---

## Fee Summary

### Platform Commission
- **NFT Purchases**: 2% of sale price
- **Where it goes**: To `platform_wallets[blockchain]` address
- **Automatic**: Deducted automatically, no user action needed

### Network Fees
- **Deposits**: User pays exchange withdrawal fee (typically $0-$5)
- **Withdrawals**: Varies by blockchain:
  - Ethereum: $5-$50 (gas-dependent)
  - Polygon: $0.10-$1
  - Solana: $0.001-$0.01
  - TON: $0.10-$1

---

## Security Notes

1. **Always verify addresses** - Copy/paste wallet addresses, don't type them
2. **Double-check receiver address** - You can't reverse a blockchain transfer
3. **Use HTTPS only** - Ensure you're on a secure connection
4. **Verify transaction hashes** - Check blockchain explorer after transfer
5. **Never share private keys** - The platform doesn't ask for private keys

---

## Supported Blockchains

| Blockchain | USDT Type | Min Deposit | Min Withdrawal | Typical Fee |
|-----------|-----------|-------------|----------------|------------|
| Ethereum  | ERC20     | $10        | $20            | $5-50      |
| Polygon   | ERC20     | $1         | $5             | $0.10-1    |
| Arbitrum  | ERC20     | $5         | $10            | $0.20-2    |
| Optimism  | ERC20     | $5         | $10            | $0.30-3    |
| Avalanche | ERC20     | $5         | $10            | $0.50-5    |
| Base      | ERC20     | $5         | $10            | $0.20-2    |
| Solana    | SPL       | $1         | $5             | $0.001-0.01|
| TON       | Native    | $5         | $10            | $0.10-1    |

---

## Key Files

- **Frontend UI**: `app/static/webapp/index-fixed.html`
- **Payment Router**: `app/routers/payment_router.py`
- **Marketplace Service**: `app/services/marketplace_service.py`
- **Wallet Service**: `app/services/wallet_service.py`
- **Database Models**: `app/models/payment.py`, `app/models/marketplace.py`
- **Tests**: `test_usdt_payment_system.py`
- **Documentation**: This file + `USDT_PAYMENT_SYSTEM_INTEGRATION.md`

---

## Support

For questions or issues:
1. Check this guide and the integration guide
2. Run the test suite to verify functionality
3. Check server logs for detailed error messages
4. Review blockchain explorer for transaction details
5. Contact support with payment ID and transaction hash

---

**Status**: Production Ready ✓
**Last Updated**: 2024-01-15
**Version**: 1.0.0
