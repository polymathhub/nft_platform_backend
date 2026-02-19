# Railway Deployment Guide - Complete Configuration

## Overview
This guide explains how to properly deploy the NFT Platform Backend to Railway with all required configurations.

---

## ✅ Prerequisites

1. **Railway Account**: Create one at https://railway.app
2. **GitHub Repository**: Push this code to GitHub
3. **Telegram Bot Token**: Get from @BotFather on Telegram
4. **PostgreSQL Database**: Available (Railway provides this)
5. **Redis Instance**: Available (Railway provides this)

---

## 🚀 Step 1: Create Railway Project & Connect Services

### 1. Create PostgreSQL Database
```bash
# In Railway Dashboard:
1. Click "New"
2. Select "Database"
3. Choose "PostgreSQL"
4. Railway creates: DATABASE_URL environment variable
```

### 2. Create Redis Cache
```bash
# In Railway Dashboard:
1. Click "New"
2. Select "Database"
3. Choose "Redis"
4. Railway creates: REDIS_URL environment variable
```

### 3. Connect GitHub Repository
```bash
1. Click "New"
2. Select "GitHub Repo"
3. Authorize and select your repo
4. Choose main branch
```

---

## 🔑 Step 2: Required Environment Variables

Set these in Railway Dashboard → Your Project → Your Service → Variables:

### **Critical - Must Have (App Won't Start Without These)**

| Variable | Value | How to Generate |
|----------|-------|-----------------|
| `ENVIRONMENT` | `production` | Just set to this |
| `DATABASE_URL` | Auto-filled by Railway PostgreSQL | Railway auto-provides |
| `REDIS_URL` | Auto-filled by Railway Redis | Railway auto-provides |
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token | From @BotFather |
| `JWT_SECRET_KEY` | 32+ char random string | `openssl rand -hex 32` |
| `MNEMONIC_ENCRYPTION_KEY` | Fernet encryption key | See below |

### **How to Generate `MNEMONIC_ENCRYPTION_KEY`:**
```bash
# Run this ONCE locally to generate the key:
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Output will be like:
# VJQ0Q1eL2e3eL2eL2eL2eL2eL2eL2eL2eL2eL2eL=

# Copy this value to Railway as MNEMONIC_ENCRYPTION_KEY
# ⚠️ NEVER generate a new one after setting - it will invalidate all encrypted data
```

### **Recommended - Strongly Suggested**

| Variable | Value | Purpose |
|----------|-------|---------|
| `DEBUG` | `false` | Disable debug mode in production |
| `LOG_LEVEL` | `INFO` | Normal logging level |
| `DATABASE_ECHO` | `false` | Don't log SQL queries (saves bandwidth) |

### **Optional - Telegram Webhook Setup**

| Variable | Value | Notes |
|----------|-------|-------|
| `TELEGRAM_WEBHOOK_URL` | `https://your-railway-domain.up.railway.app/api/v1/telegram/webhook` | Replace with your Railway URL |
| `TELEGRAM_WEBHOOK_SECRET` | Random string (32+ chars) | Optional but recommended |
| `TELEGRAM_AUTO_SETUP_WEBHOOK` | `true` | Auto-register webhook on startup |

### **Optional - CORS Configuration**

| Variable | Value | Example |
|----------|-------|---------|
| `ALLOWED_ORIGINS` | Comma-separated URLs | `https://app.example.com,https://web.example.com` |

Note: Defaults to `http://localhost:3000,http://localhost:8000,https://nftplatformbackend-production-b67d.up.railway.app`

---

## 🔧 Step 3: Configure Telegram Webhook

### **Option A: Auto-Setup (Recommended)**
Set `TELEGRAM_AUTO_SETUP_WEBHOOK=true` → App auto-registers webhook on startup

### **Option B: Manual Setup**
```bash
# Get your Railway domain from the Dashboard
# Format: https://<project-name>-production-xxxxx.up.railway.app

# Register webhook:
curl -X POST "https://api.telegram.org/bot<YOUR_TELEGRAM_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-railway-domain/api/v1/telegram/webhook",
    "secret_token": "your-secret-token"
  }'

# Verify it's set:
curl -X GET "https://api.telegram.org/bot<YOUR_TELEGRAM_BOT_TOKEN>/getWebhookInfo" \
  -H "Content-Type: application/json"
```

---

## 📋 Step 4: Set All Variables in Railway Dashboard

### Quickstart Copy-Paste Template

```
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
DATABASE_ECHO=false
TELEGRAM_AUTO_SETUP_WEBHOOK=true
ALLOWED_ORIGINS=https://your-railway-domain/api/v1

DATABASE_URL=[Auto-filled by Railway PostgreSQL]
REDIS_URL=[Auto-filled by Railway Redis]

TELEGRAM_BOT_TOKEN=[Your Telegram bot token from @BotFather]
TELEGRAM_WEBHOOK_URL=https://your-railway-domain/api/v1/telegram/webhook
TELEGRAM_WEBHOOK_SECRET=[Generate: openssl rand -hex 16]

JWT_SECRET_KEY=[Generate: openssl rand -hex 32]
MNEMONIC_ENCRYPTION_KEY=[Generate using Python command above]
```

---

## 🌐 Step 5: Get Your Railway Domain

1. Deploy the app (Railway auto-deploys on git push)
2. Go to Dashboard → Your Service → Settings → Domains
3. Railway generates a domain like: `nftplatformbackend-production-xxxxx.up.railway.app`
4. Use this for `TELEGRAM_WEBHOOK_URL` and `ALLOWED_ORIGINS`

---

## ✅ Verify Deployment

### 1. Check App is Running
```bash
curl https://your-railway-domain/health
# Should return: {"status": "ok", "telegram_bot_token": true, ...}
```

### 2. Check Telegram Webhook
```bash
curl -X GET "https://api.telegram.org/bot<YOUR_TOKEN>/getWebhookInfo"
# Should show: "url": "https://your-railway-domain/api/v1/telegram/webhook"
```

### 3. Test API Endpoint
```bash
curl https://your-railway-domain/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"test","password":"Test123!","full_name":"Test User"}'
```

---

## 🐛 Troubleshooting

### App Won't Start - Check Logs
```bash
# In Railway Dashboard:
1. Select your service
2. Go to "Logs" tab
3. Look for error messages
```

### 404 on Endpoints That Should Exist
**Cause**: Router not properly mounted
**Fix**: Restart the service (git push triggers restart)

### Telegram Webhook Returns 401
**Cause**: Missing or wrong `TELEGRAM_WEBHOOK_SECRET`
**Fix**: Verify the secret matches in both Railway variables and Telegram API

### Database Connection Timeout
**Cause**: Database URL is wrong
**Fix**: Verify `DATABASE_URL` format: `postgresql+asyncpg://user:password@host:5432/dbname`

### Redis Connection Failed
**Cause**: Redis URL is wrong
**Fix**: Verify `REDIS_URL` format: `redis://user:password@host:port/0`

### Endpoints Work Locally But Not on Railway
**Common Causes**:
- Environment variables not set in Railway
- Database/Redis not connected
- CORS blocking requests (check browser console)

**Solution**: 
1. Verify all variables are set: `echo $DATABASE_URL` (won't work in Railway, check Dashboard)
2. Check Rails logs for connection errors
3. Check browser Network tab for CORS errors

---

## 🔄 Deploying Changes

```bash
git add .
git commit -m "Your changes"
git push origin main

# Railway automatically redeploys on push
# Check deployment status in Dashboard → Deployments tab
```

---

## 📚 API Documentation

Once deployed, access:
- **Swagger UI**: https://your-railway-domain/docs
- **ReDoc**: https://your-railway-domain/redoc
- **Health Check**: https://your-railway-domain/health

---

## 🔐 Security Best Practices

1. **Never commit `.env` file** to git
2. **Rotate `JWT_SECRET_KEY`** regularly
3. **Use strong `MNEMONIC_ENCRYPTION_KEY`** (44+ characters)
4. **Enable `TELEGRAM_WEBHOOK_SECRET`** for webhook validation
5. **Set `DEBUG=false`** in production
6. **Use HTTPS URLs** for all webhooks (Railway provides automatic HTTPS)

---

## 📞 Support

- **Railway Docs**: https://docs.railway.app
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **SQLAlchemy Async**: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html

