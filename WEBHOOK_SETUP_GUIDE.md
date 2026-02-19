# Telegram Webhook Setup Guide

## Overview
This guide explains how to properly configure and test the Telegram webhook for the NFT Platform Backend.

---

## 🔧 Webhook Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/telegram/webhook` | POST | **Main webhook** - Telegram sends updates here |
| `/api/v1/telegram/webhook/set` | POST | Manual webhook registration |
| `/api/v1/telegram/webhook/delete` | POST | Delete webhook |
| `/api/v1/telegram/webhook/info` | GET | Check webhook status ✨ NEW |

---

## 📋 Configuration

### Step 1: Set Environment Variables

Update your `.env.production` or `.env` file:

```env
# ✅ Required
TELEGRAM_BOT_TOKEN=your-bot-token-from-botfather

# ✅ Required for webhook mode
TELEGRAM_WEBHOOK_URL=https://your-domain.com/api/v1/telegram/webhook

# ⭐ Recommended - adds security
TELEGRAM_WEBHOOK_SECRET=your-secret-token-here

# ✅ Optional - auto-setup on startup
TELEGRAM_AUTO_SETUP_WEBHOOK=true
```

### Step 2: Valid Bot Token Format
- Bot tokens start with numbers: `123456789:ABCdefGHIjklmnoPQRstuvwxy...`
- Get one from [@BotFather](https://t.me/botfather) on Telegram

---

## 🚀 Setting Up the Webhook

### Option A: Auto-Setup (Recommended)

Set `TELEGRAM_AUTO_SETUP_WEBHOOK=true` in your environment. The app will automatically register the webhook on startup.

**Verify it worked:**
```bash
curl https://your-domain.com/api/v1/telegram/webhook/info
```

Should return webhook status.

---

### Option B: Manual Setup

#### Step 1: Start Your Backend
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Step 2: Register Webhook via API

```bash
curl -X POST "https://your-domain.com/api/v1/telegram/webhook/set" \
  -H "Content-Type: application/json" \
  -d '{"webhook_url":"https://your-domain.com/api/v1/telegram/webhook","secret_token":"your-secret"}'
```

#### Step 3: Verify

```bash
curl https://your-domain.com/api/v1/telegram/webhook/info
```

Expected response:
```json
{
  "status": "ok",
  "webhook_url": "https://your-domain.com/api/v1/telegram/webhook",
  "webhook_secret": "***configured***",
  "auto_setup_enabled": true,
  "telegram_webhook_info": {
    "url": "https://your-domain.com/api/v1/telegram/webhook",
    "has_custom_certificate": false,
    "pending_update_count": 0,
    "last_error_date": 1234567890,
    "last_error_message": "..."
  }
}
```

---

## 🔍 Troubleshooting

### Problem: 404 on Webhook Endpoint

**Cause**: Router not properly registered or endpoint doesn't exist

**Fix**:
```bash
# Check if endpoint exists
curl https://your-domain.com/api/v1/telegram/webhook/info

# Should return 200, not 404
# If 404: Restart app and verify `app/main.py` has the router mounted
```

---

### Problem: 401 Unauthorized on Webhook

**Cause**: `TELEGRAM_WEBHOOK_SECRET` mismatch

**Solution**:
1. Check your secret token in `.env.production`:
   ```env
   TELEGRAM_WEBHOOK_SECRET=your-secret-here
   ```

2. Verify Telegram has the same secret:
   ```bash
   curl https://your-domain.com/api/v1/telegram/webhook/info
   # Check "webhook_secret": "***configured***"
   ```

3. Re-register if needed:
   ```bash
   curl -X POST "https://your-domain.com/api/v1/telegram/webhook/set" \
     -H "Content-Type: application/json" \
     -d '{"webhook_url":"https://your-domain.com/api/v1/telegram/webhook","secret_token":"your-new-secret"}'
   ```

---

### Problem: Webhook Not Registered with Telegram

**Cause**: Manual setup not completed or auto-setup failed

**Solution**:
1. Check logs for errors:
   ```bash
   # In your app logs, look for:
   # "Attempting to set Telegram webhook..."
   # "Telegram webhook setup successful"
   ```

2. Manually register:
   ```bash
   curl -X POST "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{
       "url":"https://your-domain.com/api/v1/telegram/webhook",
       "secret_token":"your-secret"
     }'
   ```

3. Verify:
   ```bash
   curl -X GET "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getWebhookInfo"
   ```

---

### Problem: "Webhook Failed" in Telegram

**Cause**: Telegram can't connect to your webhook URL

**Solution**:
1. Check URL is accessible:
   ```bash
   curl -X POST https://your-domain.com/api/v1/telegram/webhook \
     -H "Content-Type: application/json" \
     -d '{"update_id":1,"message":{"chat":{"id":123}}}'
   ```

2. Check firewall/DNS:
   - Ensure domain resolves: `nslookup your-domain.com`
   - Ensure port is open: `netstat -an | find "8000"` (or your port)
   - Railway domains are public by default

3. Check logs for errors:
   - Look for `400 Bad Request`, `500 Internal Server Error`
   - Check request format matches Telegram's expected format

---

### Problem: Webhook Returns 400 Bad Request

**Cause**: Invalid JSON or missing required fields

**Solution**: 
1. Verify request body format:
   ```bash
   # Test with minimal valid update
   curl -X POST https://your-domain.com/api/v1/telegram/webhook \
     -H "Content-Type: application/json" \
     -H "X-Telegram-Bot-Api-Secret-Token: your-secret" \
     -d '{
       "update_id": 1,
       "message": {
         "message_id": 1,
         "date": 1234567890,
         "chat": {"id": 123, "type": "private"},
         "from": {"id": 123, "first_name": "Test"},
         "text": "/start"
       }
     }'
   ```

---

## 🧪 Testing the Webhook

### Test 1: Health Check
```bash
curl https://your-domain.com/health
```
Expected: `{"status": "ok", ...}`

---

### Test 2: Webhook Info
```bash
curl https://your-domain.com/api/v1/telegram/webhook/info
```
Expected: Webhook status with URL

---

### Test 3: Send Test Message via Telegram

1. Start your bot: [@BotFather](https://t.me/botfather) `/start`
2. Send a message to your bot
3. Check app logs for:
   ```
   Processing message: /start
   handle_message completed
   ```

---

### Test 4: Test with curl (Advanced)

Simulate Telegram sending an update:

```bash
curl -X POST "https://your-domain.com/api/v1/telegram/webhook" \
  -H "Content-Type: application/json" \
  -H "X-Telegram-Bot-Api-Secret-Token: your-secret-here" \
  -d '{
    "update_id": 12345,
    "message": {
      "message_id": 1,
      "date": 1613000000,
      "chat": {
        "id": 123456789,
        "type": "private"
      },
      "from": {
        "id": 123456789,
        "is_bot": false,
        "first_name": "Test"
      },
      "text": "/start"
    }
  }'
```

Expected response: `{"ok": true}`

---

## 🚀 Production Deployment (Railway)

### Step 1: Set Environment Variables in Railway Dashboard

1. Go to Railway Dashboard → Your Service → Variables
2. Add:
   ```
   TELEGRAM_BOT_TOKEN=your-bot-token
   TELEGRAM_WEBHOOK_URL=https://your-railway-domain/api/v1/telegram/webhook
   TELEGRAM_WEBHOOK_SECRET=your-secret
   TELEGRAM_AUTO_SETUP_WEBHOOK=true
   ```

### Step 2: Get Your Railway Domain

1. Go to Settings → Domains
2. Copy the domain (e.g., `nftplatform-production-xxxxx.up.railway.app`)
3. Use in `TELEGRAM_WEBHOOK_URL`

### Step 3: Deploy

```bash
git add .
git commit -m "Configure webhook"
git push origin main
```

Railway auto-deploys. Check logs:
- Dashboard → Logs
- Look for "Telegram webhook setup successful"

---

## 📊 Webhook Info Response Example

```json
{
  "status": "ok",
  "webhook_url": "https://your-domain.com/api/v1/telegram/webhook",
  "webhook_secret": "***configured***",
  "auto_setup_enabled": true,
  "telegram_webhook_info": {
    "url": "https://your-domain.com/api/v1/telegram/webhook",
    "has_custom_certificate": false,
    "pending_update_count": 0,
    "ip_address": "1.2.3.4",
    "last_error_date": 0,
    "max_connections": 40
  }
}
```

**Fields Explained**:
- `pending_update_count`: 0 is good, >0 means webhook is failing
- `last_error_date`: 0 means no recent errors
- `max_connections`: How many concurrent requests Telegram will send

---

## 🔐 Security Notes

1. **Use HTTPS**: Telegram requires HTTPS for webhooks
2. **Set Secret Token**: Prevents unauthorized access:
   ```bash
   TELEGRAM_WEBHOOK_SECRET=your-random-secret
   ```
3. **Validate Requests**: App validates the secret token from `X-Telegram-Bot-Api-Secret-Token` header
4. **Never Commit Secrets**: Use Railway environment variables, not `.env` files

---

## 📚 Useful Commands

### Quick Status Check
```bash
curl https://your-domain.com/api/v1/telegram/webhook/info | jq
```

### Delete Webhook
```bash
curl -X POST https://your-domain.com/api/v1/telegram/webhook/delete
```

### Set Webhook with Secret
```bash
curl -X POST "https://your-domain.com/api/v1/telegram/webhook/set" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://your-domain.com/api/v1/telegram/webhook",
    "secret_token": "your-secret"
  }'
```

### View Bot Info
```bash
curl -X GET "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"
```

---

## 🎯 Summary Checklist

- [ ] `TELEGRAM_BOT_TOKEN` set in environment
- [ ] `TELEGRAM_WEBHOOK_URL` set to your domain
- [ ] `TELEGRAM_WEBHOOK_SECRET` set (optional but recommended)
- [ ] `TELEGRAM_AUTO_SETUP_WEBHOOK=true` (or manually register)
- [ ] `/api/v1/telegram/webhook/info` returns 200
- [ ] Webhook URL shows correct in webhook info response
- [ ] Send test message to bot and see it logged
- [ ] No "401 Unauthorized" or "404 Not Found" errors

---

## 📞 Debugging

If still having issues:
1. Check app logs for error messages
2. Verify endpoint exists: `curl https://your-domain.com/api/v1/telegram/webhook/info`
3. Test with `curl` to simulate Telegram update
4. Verify `TELEGRAM_BOT_TOKEN` format is correct
5. Ensure domain is publicly accessible (not localhost)

