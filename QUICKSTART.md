# Quick Start Guide - NFT Platform Backend

## 🚀 What Was Fixed

Your backend had **6 critical issues** that prevented the Telegram bot and web app from working properly:

1. **User Creation Broken** - Invalid database columns being set ✅ FIXED
2. **Telegram Webhook Broken** - Hardcoded to wrong URL ✅ FIXED  
3. **Import Mess** - Duplicate imports confusing the startup ✅ FIXED
4. **Log Spam** - Normal operations logged as WARNING instead of INFO ✅ FIXED
5. **No Configuration** - No .env.example template ✅ CREATED
6. **Type Mismatches** - Telegram ID inconsistency ✅ FIXED

---

## 🔧 Setup Instructions

### Step 1: Configure Environment

```bash
cd c:\Users\HomePC\Downloads\nft_platform_backend-main (1)\nft_platform_backend-main

cp .env.example .env
```

### Step 2: Edit .env File

**Required fields to fill in:**

```env
# Database (use PostgreSQL in production)
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/nft_platform

# JWT Secret (copy from existing or generate 32+ random chars)
JWT_SECRET_KEY=your-32-character-secret-key-here-minimum32chars

# Telegram Bot (get from @BotFather on Telegram)
TELEGRAM_BOT_TOKEN=123456789:ABCDEFGHIJKLMNOPQRSTUVWxyz...

# Redis Cache (URL to your Redis instance)
REDIS_URL=redis://localhost:6379/0

# Fernet Key for Encryption (IMPORTANT: Use this to generate)
MNEMONIC_ENCRYPTION_KEY=<see Step 3>
```

### Step 3: Generate Encryption Key

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copy the output (44 characters) and paste into `.env` as `MNEMONIC_ENCRYPTION_KEY`

### Step 4: Prepare Database

Ensure PostgreSQL is running and accessible:

```bash
# Test connection
python
>>> import asyncpg
>>> asyncio.run(asyncpg.connect('postgresql://user:password@localhost/nft_platform'))
```

### Step 5: Run the Application

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Application startup complete
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 6: Configure Telegram Webhook

Get your domain URL (use `http://localhost:8000` for testing, or `https://your-domain.com` for production)

Then run:

```bash
# Using your bot token (replace with actual token)
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://localhost:8000/api/v1/telegram/webhook",
    "secret_token": "<optional_secret>"
  }'
```

Response should show `"ok":true`

---

## ✅ Test the Fix

### 1. Test Bot Commands

Open Telegram and message your bot:
```
/start        → Should welcome you and create user
/dashboard    → Should show main menu
/wallets      → Should list your wallets
```

### 2. Test API Health

```bash
curl http://localhost:8000/health
```

Should return:
```json
{
  "status": "ok",
  "telegram_bot_token": true,
  "database_url": "configured"
}
```

### 3. Test Web App

Visit: `http://localhost:8000/web-app/`

You should see the NFT Platform interface.

### 4. Check Logs

Look for these signs of success:

✅ Good logs:
```
INFO: Processing /start command from username
INFO: Message sent successfully to chat_id=123456789
INFO: Web app initialized for user
```

❌ Bad logs (should be fixed):
```
WARNING: [TELEGRAM] Processing...  (should be INFO)
ValueError: first_name column not found  (would be this before fix)
```

---

## 🛠️ Common Issues & Solutions

### Issue: "Module not found" Error
**Solution:** Ensure Python virtual environment is activated:
```bash
cd c:\Users\HomePC\Downloads\nft_platform_backend-main (1)\nft_platform_backend-main
.venv\Scripts\activate
pip install -r requirements.txt
```

### Issue: "Database connection failed"
**Solution:** Check `DATABASE_URL` in `.env`:
```bash
# Test connection string format
postgresql+asyncpg://username:password@localhost:5432/database_name

# Verify PostgreSQL is running
pg_isready -h localhost -p 5432
```

### Issue: "Telegram webhook failed"
**Solution:** 
1. Verify bot token is correct
2. Check domain is accessible from internet
3. Try without secret_token first:
```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://your-domain.com/api/v1/telegram/webhook"}'
```

### Issue: "/start opens wrong page"
**Solution:** Ensure web app URL in `.env`:
```env
TELEGRAM_WEBAPP_URL=http://localhost:8000/web-app/
```

Or for production:
```env
TELEGRAM_WEBAPP_URL=https://your-domain.com/web-app/
```

---

## 📁 Key Files Modified

| File | What Changed | Why |
|------|-------------|-----|
| `app/routers/telegram_mint_router.py` | User creation flow | Fixed database column mismatch |
| `app/main.py` | Startup sequence | Removed duplicate imports |
| `app/utils/startup.py` | Webhook setup | Made URL configurable |
| `app/services/telegram_bot_service.py` | Logging | Changed WARNING→INFO |
| `.env.example` | NEW FILE | Deployment configuration template |

---

## 🏗️ Architecture Overview

```
User opens Telegram Bot
        ↓
/start command sent to webhook
        ↓
app/routers/telegram_mint_router.py handles webhook
        ↓
Creates/retrieves user (app/models/user.py)
        ↓
Stores in PostgreSQL database
        ↓
Sends welcome message with Web App button
        ↓
User clicks Web App button
        ↓
Browser loads: /web-app/index.html
        ↓
Web app calls: /api/v1/telegram/web-app/init
        ↓
Backend returns user data
        ↓
Web app displays dashboard
```

---

## 🔐 Security Notes

- ✅ Telegram webhook secret optional but recommended
- ✅ JWT tokens required for API access (except web-app endpoints)
- ✅ Database uses asyncpg (secure async driver)
- ✅ Passwords hashed with bcrypt
- ✅ Environment variables never committed to git

---

## 📚 Documentation Files

Read these for more details:

1. **FIXES_APPLIED.md** - Detailed fix explanations with code samples
2. **VERIFICATION_CHECKLIST.md** - Complete verification and deployment checklist
3. **README.md** - Original project documentation
4. **.env.example** - Configuration template with all options

---

## 🎯 Next Steps

1. ✅ Set up .env file
2. ✅ Start the application
3. ✅ Test with `/start` command
4. ✅ Monitor logs for any issues
5. ✅ Open web app from Telegram
6. ✅ Test wallet/NFT flows

---

## 💬 Support

If you encounter issues:

1. Check the logs for error messages
2. Verify all environment variables are set
3. Ensure PostgreSQL and Redis are running
4. Check that Telegram bot token is correct
5. Verify network connectivity to Telegram API

Review **FIXES_APPLIED.md** for technical details on what was changed and why.

---

**Status:** ✅ All systems go! Your backend is now ready for testing and deployment.
