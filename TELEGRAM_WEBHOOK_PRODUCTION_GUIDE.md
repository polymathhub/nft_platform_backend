# 🚀 Telegram Webhook Production Setup Guide

## Overview

This guide covers the production-ready Telegram webhook setup for the NFT Platform Backend. The setup includes:

- ✅ **Automatic webhook registration** on app startup (production only)
- ✅ **Secure webhook route** with token validation
- ✅ **Method-specific handling** (POST for Telegram, GET for debugging)
- ✅ **Comprehensive error logging** without crashes
- ✅ **Async-safe operations** compatible with SQLAlchemy asyncpg
- ✅ **Railway environment configuration** with no hardcoded secrets

---

## 📋 Environment Configuration

### Railway Production Setup

Set these environment variables in your **Railway dashboard** → Service Variables:

#### Standard Variables
```bash
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=info
```

#### Required Secrets (Railway Dashboard → Variables → Add Secret)
```bash
JWT_SECRET_KEY={your-32+ char random string}
MNEMONIC_ENCRYPTION_KEY={your-44-char Fernet key}
TELEGRAM_BOT_TOKEN={your-bot-token-from-@BotFather}
TELEGRAM_WEBHOOK_SECRET={your-random-secure-string}
```

#### Telegram Configuration
```bash
TELEGRAM_WEBHOOK_URL=https://nftplatformbackend-production-9081.up.railway.app/api/v1/telegram/webhook
TELEGRAM_AUTO_SETUP_WEBHOOK=True
TELEGRAM_API_ID={your-api-id}
TELEGRAM_API_HASH={your-api-hash}
```

### Local Development Configuration

Your `.env` file (already configured):
```bash
ENVIRONMENT=development
DEBUG=false
TELEGRAM_WEBHOOK_URL=http://localhost:8000/api/v1/telegram/webhook
TELEGRAM_AUTO_SETUP_WEBHOOK=true
TELEGRAM_WEBHOOK_SECRET=dev-webhook-secret-secure-2024
TELEGRAM_AUTO_SETUP_WEBHOOK=true
```

---

## 🔄 Webhook Registration Flow

### On Railway Production (ENVIRONMENT=production)

**Startup logs:**
```
[1/3] Initializing database connection pool...
[2/3] Running database migrations...
[3/3] Setting up Telegram webhook...
Setting up Telegram webhook for production...
Registering Telegram webhook: https://nftplatformbackend-production-9081.up.railway.app/api/v1/telegram/webhook
✓ Telegram webhook registered successfully: https://nftplatformbackend-production-9081.up.railway.app/api/v1/telegram/webhook

Application startup complete.
Uvicorn running on http://0.0.0.0:8000
```

**What happens:**
1. Setting validation confirms `ENVIRONMENT=production`
2. Telegram webhook is registered with Telegram servers
3. Telegram API is called once at startup (idempotent)
4. If webhook already matches, registration is skipped
5. If registration fails, app continues (non-fatal)

### On Local Development (ENVIRONMENT=development)

**Startup logs:**
```
[1/3] Initializing database connection pool...
[2/3] Running database migrations...
[3/3] Setting up Telegram webhook...
Local development (ENVIRONMENT=development, DEBUG=false) - skipping Telegram webhook setup (using polling mode)

Application startup complete.
Uvicorn running on http://127.0.0.1:8000
```

**What happens:**
1. Webhook setup is skipped
2. Polling mode is used (local development)
3. Telegram updates come via polling, not webhooks

---

## 🔒 Webhook Security

### Token Validation

Every POST request to `/api/v1/telegram/webhook` must include:

```http
X-Telegram-Bot-Api-Secret-Token: {TELEGRAM_WEBHOOK_SECRET}
```

**Telegram automatically sends this header** when it calls your webhook. If the header is missing or invalid:
- Request is logged as a security issue
- Response returns 200 OK (to prevent retry loops)
- Request is not processed

### Example Security Check (in code)

```python
if settings.telegram_webhook_secret:
    header_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if header_secret != settings.telegram_webhook_secret:
        logger.warning("Webhook rejected: secret token mismatch")
        return {"ok": True, "error": "Invalid secret"}
```

---

## 📡 Webhook Route Behavior

### POST /api/v1/telegram/webhook (Production & Development)

**Accept:** ONLY POST requests from Telegram

**Request:**
```json
{
  "update_id": 123456789,
  "message": {
    "message_id": 1,
    "date": 1704067200,
    "chat": {"id": -1001234567890, "type": "private"},
    "from": {"id": 987654321, "first_name": "User"},
    "text": "/start"
  }
}
```

**Response (always 200 OK):**
```json
{"ok": true}
```

**Logs:**
```
INFO: Telegram webhook: update_type=message from IP=123.45.67.89
INFO: Processing message: chat_id=-1001234567890, user_id=987654321
INFO: Message processed successfully
```

---

### GET /api/v1/telegram/webhook

**Production Mode (ENVIRONMENT=production):**
- Returns: **405 Method Not Allowed**
- Logs: Debug message about rejected GET
- Why: Telegram only sends POST; GET is not allowed

```
$ curl http://nftplatformbackend-production-9081.up.railway.app/api/v1/telegram/webhook
{
  "detail": "Method not allowed. Use POST to send Telegram updates."
}
```

**Local Development Mode (ENVIRONMENT=development):**
- Returns: **200 OK** with status info
- Logs: Info message showing development mode
- Why: Allows safe testing/debugging without real Telegram data

```
$ curl http://localhost:8000/api/v1/telegram/webhook
{
  "status": "webhook_running",
  "environment": "development",
  "webhook_url": "http://localhost:8000/api/v1/telegram/webhook",
  "message": "Webhook is running and ready to receive Telegram updates. Use POST method.",
  "debug_mode": true
}
```

---

## 🧪 Testing Instructions

### 1. Test Webhook Health (Local Development)

```bash
# GET request - should return 200 OK with status info
curl -X GET http://localhost:8000/api/v1/telegram/webhook

# Expected output:
{
  "status": "webhook_running",
  "environment": "development",
  "webhook_url": "http://localhost:8000/api/v1/telegram/webhook",
  "message": "Webhook is running and ready to receive Telegram updates. Use POST method.",
  "debug_mode": true
}
```

### 2. Test Webhook Health (Production)

```bash
# GET request - should return 405 Method Not Allowed
curl -X GET https://nftplatformbackend-production-9081.up.railway.app/api/v1/telegram/webhook

# Expected output:
{
  "detail": "Method not allowed. Use POST to send Telegram updates."
}

# Check HTTP status code:
curl -i -X GET https://nftplatformbackend-production-9081.up.railway.app/api/v1/telegram/webhook
# HTTP/1.1 405 Method Not Allowed
```

### 3. Test Webhook with Mock Telegram Update (Development)

```bash
# Send a mock message update with secret token
curl -X POST http://localhost:8000/api/v1/telegram/webhook \
  -H "Content-Type: application/json" \
  -H "X-Telegram-Bot-Api-Secret-Token: dev-webhook-secret-secure-2024" \
  -d '{
    "update_id": 12345,
    "message": {
      "message_id": 1,
      "date": 1704067200,
      "chat": {
        "id": 123456789,
        "type": "private"
      },
      "from": {
        "id": 987654321,
        "is_bot": false,
        "first_name": "TestUser"
      },
      "text": "/start"
    }
  }'

# Expected response:
{"ok": true}

# Check logs for:
# INFO: Telegram webhook: update_type=message from IP=127.0.0.1
# INFO: Processing message: chat_id=123456789, user_id=987654321
# INFO: Message processed successfully
```

### 4. Test Webhook without Secret Token (Security Test)

```bash
# Missing secret token header
curl -X POST http://localhost:8000/api/v1/telegram/webhook \
  -H "Content-Type: application/json" \
  -d '{"update_id": 12345, "message": {...}}'

# Expected response (still 200 to prevent retries):
{"ok": true, "error": "Missing secret token"}

# Check logs for:
# WARNING: Webhook rejected: missing secret token header
```

### 5. Test with Python Requests (Development)

```python
import requests
import json

webhook_url = "http://localhost:8000/api/v1/telegram/webhook"
secret = "dev-webhook-secret-secure-2024"

# Prepare mock Telegram update
telegram_update = {
    "update_id": 12345,
    "message": {
        "message_id": 1,
        "date": 1704067200,
        "chat": {
            "id": 123456789,
            "type": "private"
        },
        "from": {
            "id": 987654321,
            "is_bot": False,
            "first_name": "TestUser"
        },
        "text": "/start"
    }
}

# Send POST with secret header
response = requests.post(
    webhook_url,
    json=telegram_update,
    headers={"X-Telegram-Bot-Api-Secret-Token": secret}
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
# Output: Status: 200, Response: {'ok': True}
```

---

## 📊 Webhook Log Examples

### Successful Message Processing

```
INFO:     Received http request [POST /api/v1/telegram/webhook]
INFO: Telegram webhook: update_type=message from IP=149.154.160.0
INFO: Processing message: chat_id=123456789, user_id=987654321
INFO: Message processed successfully
INFO:     "POST /api/v1/telegram/webhook HTTP/1.1" 200
```

### Successful Callback Query Processing

```
INFO: Telegram webhook: update_type=callback_query from IP=149.154.160.0
INFO: Processing callback: chat_id=987654321, callback_data=mint_nft
INFO: Callback processed successfully
```

### Security Issue - Missing Token

```
WARNING: Webhook rejected: missing secret token header from IP=192.168.1.100
```

### Security Issue - Invalid Token

```
WARNING: Webhook rejected: secret token mismatch from IP=192.168.1.100 (expected 24 chars)
```

### Processing Error (Non-Fatal)

```
ERROR: Webhook processing error from 149.154.160.0: ValueError: Invalid data format
Traceback (most recent call last):
  ...
```

---

## 🔧 Debugging Webhooks

### 1. Check Telegram Webhook Status

Use Telegram Bot API directly to verify current webhook:

```bash
curl https://api.telegram.org/bot{YOUR_BOT_TOKEN}/getWebhookInfo
```

**Output:**
```json
{
  "ok": true,
  "result": {
    "url": "https://nftplatformbackend-production-9081.up.railway.app/api/v1/telegram/webhook",
    "has_custom_certificate": false,
    "pending_update_count": 0,
    "ip_address": "149.154.160.0",
    "last_error_date": 0,
    "last_error_message": "",
    "last_synchronization_unix_time": 1710000000
  }
}
```

### 2. Check Application Logs

```bash
# Railway CLI
railway logs

# Look for:
# "Setting up Telegram webhook for production..."
# "✓ Telegram webhook registered successfully"
# "Telegram webhook: update_type=message"
```

### 3. Verify Settings Loaded Correctly

Check that `ENVIRONMENT` is correctly set:

```python
from app.config import get_settings
settings = get_settings()
print(f"Environment: {settings.environment}")
print(f"Debug: {settings.debug}")
print(f"Webhook URL: {settings.telegram_webhook_url}")
print(f"Auto setup: {settings.telegram_auto_setup_webhook}")
```

---

## 🚨 Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| "Local development detected - skipping webhook setup" | `ENVIRONMENT != production` | Set `ENVIRONMENT=production` on Railway |
| "Telegram webhook setup failed (non-fatal)" | Network/API issue | Check bot token, webhook URL, internet |
| "Method not allowed" on POST | Webhook rejected | Check `X-Telegram-Bot-Api-Secret-Token` header |
| No updates received | Webhook not registered | Check Telegram `getWebhookInfo()` output |
| GET returns 200 instead of 405 | Development mode | Set `ENVIRONMENT=production` for production |

---

## ✅ Production Checklist

- [ ] `ENVIRONMENT=production` on Railway
- [ ] `DEBUG=False` on Railway
- [ ] `TELEGRAM_BOT_TOKEN` set in Railway Secrets
- [ ] `TELEGRAM_WEBHOOK_SECRET` set in Railway Secrets
- [ ] `TELEGRAM_WEBHOOK_URL` points to production domain
- [ ] `TELEGRAM_AUTO_SETUP_WEBHOOK=True`
- [ ] Deployment logs show: `✓ Telegram webhook registered successfully`
- [ ] `GET /api/v1/telegram/webhook` returns 405 (Method Not Allowed)
- [ ] Test with real Telegram bot commands
- [ ] Monitor logs for "Telegram webhook: update_type="

---

## 📚 Additional Resources

- [Telegram Bot API Webhook Docs](https://core.telegram.org/bots/api#setwebhook)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [Railway Documentation](https://docs.railway.app/)
