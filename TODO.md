# TON Connect Fix - Implementation Steps

## Status: [0/8] In Progress

### 1. [x] Create this TODO.md ✅
### 2. [ ] Implement `app/static/webapp/js/tonconnect.js`
   - TON Connect UI v2 initialization
   - Connect/disconnect handlers
   - Session persistence (localStorage)
   - Custom events

### 3. [ ] Fix `app/static/webapp/wallet.html`
   - Add missing DOM: #connectBtn, #walletAddress, #status, #error
   - Replace broken inline script
   - Import tonconnect.js + telegram-wallet.js
   - Add loading/error states

### 4. [ ] Backend: Create `/api/v1/wallet/connect` endpoint
   - New `app/routers/ton_wallet_router.py` OR extend wallet_router.py
   - POST wallet_address + telegram_init_data
   - Verify initData → User → TONWallet upsert
   - Idempotent (handle duplicates)

### 5. [ ] Create `app/static/webapp/js/telegram-wallet.js`
   - Integrate TON Connect events + backend sync
   - Call /wallet/connect after successful connect
   - Handle reconnect on page load
   - Update UI states

### 6. [ ] DB Model verification
   - app/models/ton_wallet.py: Ensure unique wallet_address
   - Add last_connected_at timestamp (migration if needed)

### 7. [ ] UI Propagation
   - navbar.js: Show connected wallet
   - dashboard.html, marketplace.html: Display TON address

### 8. [ ] Testing & Completion
   - Manual test in Telegram Mini App
   - Verify TONWallet row in DB
   - Refresh test (reconnect)
   - attempt_completion

**Next Step: #2 - tonconnect.js**

