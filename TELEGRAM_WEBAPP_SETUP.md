# Telegram Web App Setup Guide

## Overview

Your NFT Platform now has a fully functional web app that works inside Telegram. Users can open the app directly from the Telegram bot menu and manage their NFTs without leaving Telegram.

---

## Quick Start (Production)

### Step 1: Get Your Bot Token and Configure

Make sure you have:
- ✅ Bot Token (from @BotFather)
- ✅ Web App URL (e.g., `https://yourdomain.com/web-app/`)
- ✅ Webhook URL (e.g., `https://yourdomain.com/api/v1/telegram/webhook`)

These go in your `.env` file:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_WEBAPP_URL=https://yourdomain.com/web-app/
TELEGRAM_WEBHOOK_URL=https://yourdomain.com/api/v1/telegram/webhook
TELEGRAM_WEBHOOK_SECRET=your_secret_token
```

### Step 2: Run Setup Script

```bash
python setup_telegram_webapp.py
```

This will:
1. ✅ Verify bot token is valid
2. ✅ Set up the "Web App" menu button
3. ✅ Configure the webhook
4. ✅ Show instructions

**Output:**
```
🤖 Setting up Telegram Bot Menu Button
✅ Menu button set successfully!
   Button text: Web App
   Opens URL: https://yourdomain.com/web-app/

🔗 Setting up Telegram Webhook
✅ Webhook set successfully!
   Webhook URL: https://yourdomain.com/api/v1/telegram/webhook
```

### Step 3: Test in Telegram

1. Open your Telegram bot
2. Look for a "Web App" button at the bottom (might take 10-30 seconds to appear)
3. Click the button
4. Web app loads with your data

---

## Development Testing

If you're testing locally without a public URL:

### Option 1: Use Development Mode

```
http://localhost:8000/web-app/?user_id=550e8400-e29b-41d4-a716-446655440000
```

**Pros:**
- No Telegram required
- Works immediately
- Perfect for frontend testing

**Cons:**
- Can't test Telegram integration

### Option 2: Use Ngrok for Local Testing

```bash
# Install ngrok
# https://ngrok.com/

# Expose your local server
ngrok http 8000

# Example output:
# Forwarding: https://abc123.ngrok.io -> http://localhost:8000
```

Then update your `.env`:
```
TELEGRAM_WEBAPP_URL=https://abc123.ngrok.io/web-app/
TELEGRAM_WEBHOOK_URL=https://abc123.ngrok.io/api/v1/telegram/webhook
```

Run setup script again:
```bash
python setup_telegram_webapp.py
```

Now you can test the web app in Telegram while running locally!

---

## Architecture

### Data Flow

```
User Opens Telegram Bot
    ↓
Clicks "Web App" Button
    ↓
Browser opens: https://yourdomain.com/web-app/
    ↓
Telegram.WebApp.initData sent to frontend
    ↓
Frontend: app.js calls /api/v1/telegram/web-app/init
    ↓
Backend verifies Telegram signature
    ↓
Backend returns user ID and profile
    ↓
Frontend: app.js calls /api/v1/telegram/web-app/dashboard-data
    ↓
Backend returns: { wallets, nfts, listings }
    ↓
Web App displays user's data
```

### Key Endpoints

| Endpoint | Purpose | Auth |
|----------|---------|------|
| `GET /web-app/` | Serve web app HTML | None (static) |
| `GET /api/v1/telegram/web-app/init` | Authenticate via Telegram | Telegram signature |
| `GET /api/v1/telegram/web-app/dashboard-data` | Get user's data | User ID |
| `POST /api/v1/telegram/web-app/mint` | Mint NFT | User ID |
| `GET /api/v1/telegram/web-app/test-user` | Create test user | None |

---

## Features

### Available in Web App

✅ **Dashboard**
- View portfolio statistics
- See all your wallets, NFTs, listings
- Track activity

✅ **Wallet Management**
- Create new wallets (Ethereum, Polygon, Solana, TON)
- Import existing wallets
- Set primary wallet
- View wallet details

✅ **NFT Operations**
- Mint new NFTs
- List NFTs for sale
- Transfer NFTs
- Burn NFTs

✅ **Marketplace**
- Browse all active listings
- Make offers on NFTs
- View your listings
- Cancel listings

✅ **User Profile**
- View account information
- See statistics

---

## Telegram SDK Integration

### What Happens When App Loads

1. **Telegram SDK loaded** (from `https://telegram.org/js/telegram-web-app.js`)
2. **initData available** - Contains signed user information from Telegram
3. **Backend verifies** - Checks the cryptographic signature to ensure data came from Telegram
4. **User authenticated** - Backend returns authorized user profile

### Browser Console Logs

When the app loads in Telegram, you'll see:

```
🚀 NFT Platform App Starting...
ℹ️ Telegram SDK available: yes
ℹ️ Test user ID in URL: no
📱 Telegram mode: Using Telegram WebApp SDK
ℹ️ Telegram initData length: 450
Authenticating with Telegram...
✅ [TELEGRAM] User authenticated: username (550e8400...)
Loading dashboard for user: username (550e8400...)
  Wallets: 2
  NFTs: 5
  Own Listings: 1
Data loaded!
```

---

## Troubleshooting

### "Web App" Button Not Showing

**Problem:** Clicked /start but no Web App button appears

**Solution:**
1. Wait 10-30 seconds (Telegram updates menu slowly)
2. Try typing `/start` again
3. Run setup script again: `python setup_telegram_webapp.py`
4. Check bot token is correct in `.env`

### Web App Not Loading

**Problem:** Button opens but shows blank or error

**Solution:**
1. Check browser console (F12) for errors
2. Ensure web app URL is correct (HTTPS required)
3. Verify backend is running on correct port
4. Check CORS configuration

### "Error: Telegram auth not available"

**Problem:** App says Telegram auth not available

**Solution:**
1. Make sure you opened from Telegram bot (not direct URL)
2. Check Telegram WebApp SDK loaded: `window.Telegram` in console
3. For testing, use `?user_id=UUID` parameter

### Webhook Not Receiving Updates

**Problem:** Messages/callbacks not triggering bot

**Solution:**
1. Verify webhook URL is HTTPS
2. Check webhook URL is publicly accessible
3. Verify bot token is correct
4. Run setup script to reconfigure: `python setup_telegram_webapp.py`

---

## Environment Variables

### Required

```env
TELEGRAM_BOT_TOKEN=<your_bot_token>
```

### Recommended for Production

```env
TELEGRAM_WEBAPP_URL=https://yourdomain.com/web-app/
TELEGRAM_WEBHOOK_URL=https://yourdomain.com/api/v1/telegram/webhook
TELEGRAM_WEBHOOK_SECRET=<your_secret_token>
```

### Optional

```env
TELEGRAM_AUTO_SETUP_WEBHOOK=true  # Auto-configure webhook on startup
```

---

## Security Considerations

### Telegram Signature Verification

✅ **Backend verifies** every request from Telegram:
- Checks cryptographic signature
- Ensures data hasn't been tampered with
- Validates timestamp (24-hour window)

### Data Isolation

✅ **Each user only sees their own data:**
- Wallets filtered by `user_id`
- NFTs filtered by `user_id`
- Listings filtered by `seller_id`

### HTTPS Required

✅ **Web app URL must be HTTPS** (Telegram requirement)
- Development: Use ngrok to generate HTTPS tunnel
- Production: Use proper SSL certificate

---

## Deployment Checklist

Before deploying to production:

- [ ] Bot token configured in environment
- [ ] Web app URL is HTTPS
- [ ] Webhook URL is HTTPS and publicly accessible
- [ ] Database migrations applied
- [ ] Environment variables set correctly
- [ ] Setup script run successfully
- [ ] Bot menu button shows "Web App"
- [ ] Can open web app from Telegram
- [ ] Telegram signature verification working
- [ ] Per-user data isolation verified
- [ ] All endpoints returning correct data

---

## Testing Checklist

**Before Release:**

- [ ] Open app from Telegram mobile
- [ ] Dashboard loads (wallets, NFTs, listings)
- [ ] Create wallet from app
- [ ] Mint NFT from app
- [ ] List NFT on marketplace
- [ ] Make offer on listing
- [ ] Check data appears in dashboard
- [ ] Test on different user accounts
- [ ] Test with no wallets/NFTs (empty states)
- [ ] Test error scenarios
- [ ] Check keyboard adjustments work
- [ ] Verify slow network handling

---

## File Structure

```
app/
├── static/webapp/
│   ├── index.html          # Web app page
│   ├── app.js              # Frontend logic
│   └── styles.css          # Styling
├── routers/
│   └── telegram_mint_router.py  # Web app endpoints
└── utils/
    └── startup.py          # Webhook setup

setup_telegram_webapp.py    # Setup script (NEW)
```

---

## Support

### Browser Console for Debugging

Open browser DevTools (F12) and check:
- **Console tab** - See all logs and errors
- **Network tab** - Check API calls and responses
- **Application tab** - Check WebApp.initData

### Common Log Patterns

**Success:**
```
✅ User authenticated: username (id...)
```

**Error:**
```
❌ Failed to get user: [error message]
```

**Info:**
```
ℹ️ Telegram SDK available: yes
```

---

## API Integration Points

### Frontend Uses These Endpoints

```javascript
// Authenticate
GET /api/v1/telegram/web-app/init?init_data=...

// Get dashboard data
GET /api/v1/telegram/web-app/dashboard-data?user_id=UUID

// Mint NFT
POST /api/v1/telegram/web-app/mint
  { user_id, wallet_id, nft_name, nft_description, image_url }

// And more...
```

All endpoints require proper user authentication via Telegram signature verification.

---

## Next Steps

1. **Run Setup Script**
   ```bash
   python setup_telegram_webapp.py
   ```

2. **Test in Telegram**
   - Click "Web App" button
   - Verify data loads

3. **Monitor Logs**
   - Check browser console (F12)
   - Check server logs for API calls

4. **Create Sample Data**
   - Create wallets
   - Mint NFTs
   - List on marketplace

5. **Gather Feedback**
   - Test with real users
   - Refine based on feedback

---

**Status**: ✅ READY FOR TELEGRAM

The web app is fully integrated and ready to use inside Telegram. Set up the bot menu button and users can start managing NFTs directly from Telegram!
