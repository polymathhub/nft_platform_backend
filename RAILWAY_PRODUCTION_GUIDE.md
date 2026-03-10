# Production Deployment Guide - FastAPI on Railway

## Overview

Your NFT Platform Backend uses FastAPI with the following structure:
- **Entry point**: `app.main:app` (not `main:app`)
- **Working directory**: `/app` (inside container)
- **Database**: PostgreSQL with Alembic migrations
- **Health check**: `GET /health` endpoint

This guide provides production-ready Dockerfile and Railway configuration.

---

## Files Provided

### 1. **Dockerfile.production**
- Optimized for production FastAPI deployments
- Automatic module import validation
- Alembic migration execution before startup
- Non-root user for security
- Health checks with proper timeout handling
- Async-ready with uvloop support

### 2. **railway.production.json**
- Complete Railway service configuration
- PostgreSQL integration
- Environment variable management
- Health checks (startup + liveness + readiness)
- Auto-restart on failure

---

## Key Fixes Included

### ✅ Module Import Error Fix
**Problem**: `Could not import module "main"`

Your project structure:
```
nft_platform_backend/
├── app/
│   ├── main.py          ← FastAPI app is HERE
│   ├── config.py
│   ├── routers/
│   └── models/
├── requirements.txt
└── Dockerfile
```

**Solution**: Use `app.main:app` not `main:app`

The provided Dockerfile validates this:
```dockerfile
RUN python -c "from app.main import app; print('✓ app.main:app imported successfully')"
```

### ✅ Working Directory Handling
```dockerfile
WORKDIR /app
```
All imports resolve correctly from `/app` because Python can find `app/` package.

### ✅ Database Migrations
```dockerfile
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app ..."]
```
Runs migrations before starting the server.

### ✅ Health Check Compatibility
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=5).read()"
```

Matches your app's `/health` endpoint at line 192 of `app/main.py`.

### ✅ Async/Await Support
```dockerfile
uvicorn [...]
  --loop uvloop          ← Faster async loop
  --http h11             ← HTTP/1.1 support
```

### ✅ Environment Variable Defaults
```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    WORKERS=4
```

---

## Step-by-Step Deployment

### 1. Install Railway CLI

```bash
# Using npm
npm install -g @railway/cli

# Or using PowerShell (Windows)
irm railway.app/install.ps1 | iex

# Or using Scoop (Windows)
scoop install railway
```

### 2. Authenticate with Railway

```bash
railway login
```

Opens browser for authentication.

### 3. Create Railway Project

```bash
cd nft_platform_backend

# Initialize Railway project
railway init

# When prompted:
# - Project name: nft-platform
# - Environment: Production (or create new)
```

### 4. Add PostgreSQL Service

```bash
railway add
# Select: PostgreSQL from menu
# Railway auto-generates DATABASE_URL environment variable
```

### 5. Configure Environment Variables

```bash
# Set secret credentials (using Railway secrets)
railway variable add SECRET_KEY "your-secret-key-here"
railway variable add POSTGRES_PASSWORD "$(openssl rand -base64 32)"

# Set public environment variables
railway variable add ENVIRONMENT "production"
railway variable add LOG_LEVEL "info"
railway variable add WORKERS "4"

# Telegram Bot (if using)
railway variable add TELEGRAM_BOT_TOKEN "your-token-here"
railway variable add TELEGRAM_BOT_USERNAME "@your_bot"

# Web3 Integration (if using)
railway variable add ETHEREUM_RPC_URL "https://eth-mainnet.g.alchemy.com/v2/KEY"
railway variable add SOLANA_RPC_URL "https://api.mainnet-beta.solana.com"
```

View all variables:
```bash
railway variable list
```

### 6. Deploy Application

```bash
# Using Dockerfile.production
railway up

# Or specify Dockerfile explicitly
railway deploy --dockerfile Dockerfile.production
```

Monitor logs during deployment:
```bash
railway logs -f
```

### 7. Verify Deployment

```bash
# Check if running
railway status

# View URL
railway open

# Test health endpoint
curl https://your-railway-app.railway.app/health
```

---

## Railway Configuration Explained

### Build Configuration
```json
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfile": "Dockerfile.production"
  }
}
```

Uses your custom production Dockerfile instead of Railway buildpacks.

### Health Checks
Three types of health checks in `railway.production.json`:

```json
{
  "startupProbe": {
    "initialDelaySeconds": 60,      // Wait 60s before checking
    "periodSeconds": 10,             // Check every 10s
    "failureThreshold": 5            // Fail after 5 misses
  },
  "livenessProbe": {
    "initialDelaySeconds": 30,       // App is "live"
    "periodSeconds": 10,
    "failureThreshold": 3            // Restart after 3 failures
  },
  "readinessProbe": {
    "initialDelaySeconds": 20,       // App is "ready"
    "periodSeconds": 5,
    "failureThreshold": 2
  }
}
```

**Why three?**
- **Startup**: App is initializing (slow database/migrations)
- **Liveness**: App is running (restart if not)
- **Readiness**: App can handle requests (load balanced)

### Environment Variables
```json
{
  "environment": {
    "DATABASE_URL": "${{ Postgres.DATABASE_URL }}",
    "ENVIRONMENT": "production",
    "SECRET_KEY": "${{ Railway.Secret.SECRET_KEY }}"
  }
}
```

- `${{ Postgres.DATABASE_URL }}` - Auto-generated by PostgreSQL service
- `${{ Railway.Secret.SECRET_KEY }}` - Secret managed by Railway
- Others - Set via `railway variable add`

### Service Configuration
```json
{
  "services": {
    "postgres": {
      "type": "postgres",
      "version": "15",
      "environment": {
        "POSTGRES_USER": "nft_user",
        "POSTGRES_DB": "nft_platform"
      }
    }
  }
}
```

Creates PostgreSQL 15 service alongside your FastAPI app.

---

## Troubleshooting

### Issue: "Could not import module 'main'"

**Cause**: Using `main:app` instead of `app.main:app`

**Fix**: The provided Dockerfile uses correct path: `app.main:app`

Verify in Dockerfile:
```dockerfile
# ✓ CORRECT
CMD ["uvicorn", "app.main:app", ...]

# ✗ WRONG (don't do this)
CMD ["uvicorn", "main:app", ...]
```

### Issue: Health Check Failing

**Cause**: `/health` endpoint not responding or not implemented

**Check**:
```bash
# View logs
railway logs -f

# Should see 200 response:
# GET /health HTTP/1.1" 200 OK
```

**Ensure endpoint exists** in `app/main.py`:
```python
@app.get("/health")
async def health():
    return {"status": "healthy"}
```

Already exists in your code at line 192.

### Issue: Database Connection Error

**Cause**: `DATABASE_URL` not set or incorrect format

**Check**:
```bash
# View environment variables
railway variable list

# Should see:
# DATABASE_URL postgresql://user:pass@host:5432/nft_platform
```

**Fix**: Ensure PostgreSQL service is added:
```bash
railway add
# Select PostgreSQL
```

### Issue: Migrations Not Running

**Cause**: Alembic not executed or database locked

**Check logs**:
```bash
railway logs -f

# Should see:
# Running database migrations...
# INFO  [alembic.runtime.migration] Running upgrade...
# INFO  [alembic.runtime.migration] Running upgrade 000_initial_schema -> 001_add_collection_rarity
```

**If stuck**: Check for migration locks:
```bash
# Connect to DB and unlock
psql $DATABASE_URL -c "SELECT * FROM alembic_version;"
```

### Issue: Port Already in Use (Local Testing)

If testing locally before deployment:

```bash
# Change port in command (not needed in Railway)
uvicorn app.main:app --port 9000
```

### Issue: Module Not Found After Deployment

**Cause**: Dependencies not installed

**Check logs**:
```bash
railway logs -f

# Should show:
# Installing requirements...
# Successfully installed fastapi uvicorn sqlalchemy...
```

**If fails**: Verify `requirements.txt`:
```bash
# Check file exists
ls requirements.txt

# Test locally
pip install -r requirements.txt
python -c "from app.main import app"
```

---

## Local Testing Before Deployment

### 1. Build Docker Image Locally

```bash
# Build using production Dockerfile
docker build -f Dockerfile.production -t nft-platform:latest .

# Check image size (should be <500MB)
docker image ls nft-platform
```

### 2. Run Container Locally

```bash
# Create .env file for local testing
cat > .env.local << EOF
ENVIRONMENT=development
SECRET_KEY=test-key-for-local-only
DATABASE_URL=postgresql://user:pass@localhost:5432/nft_platform_test
LOG_LEVEL=debug
EOF

# Run container
docker run -p 8000:8000 \
  --env-file .env.local \
  -e DATABASE_URL="postgresql://user:pass@localhost:5432/nft_platform_test" \
  nft-platform:latest

# Or with docker-compose
docker-compose up -d
```

### 3. Test Health Endpoint

```bash
curl http://localhost:8000/health

# Should respond:
# {"status": "healthy"}
```

### 4. Test API Endpoints

```bash
# List users (example)
curl http://localhost:8000/api/users

# Create user (example)
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com"}'
```

---

## Production Recommendations

### 1. Use Environment Secrets

Never commit sensitive values:

```bash
# ✓ CORRECT - Use Railway secrets
railway variable add SECRET_KEY "..."
railway variable add TELEGRAM_BOT_TOKEN "..."

# ✗ WRONG - Don't do this
echo "SECRET_KEY=my-secret" >> .env
git add .env  # Never!
```

### 2. Monitor Logs

```bash
# View real-time logs
railway logs -f

# Search for errors
railway logs | grep -i error

# Export logs
railway logs > deployment.log
```

### 3. Scale Replicas

For high traffic:

```bash
# Edit railway.production.json
{
  "deploy": {
    "numReplicas": 3  # Run 3 instances
  }
}
```

Or in Railway dashboard: Project → Settings → Replicas

### 4. Set Up Monitoring

In Railway dashboard:
- Metrics → CPU, Memory, Network
- Logs → Errors and warnings
- Alerts → Notify on issues

### 5. Regular Backups

Railway PostgreSQL auto-backups, but:
```bash
# Manual backup
pg_dump $DATABASE_URL > backup.sql

# Store in S3/GitHub
```

### 6. Update Dependencies

```bash
# Check for updates
pip list --outdated

# Update in requirements.txt
pip-review --interactive

# Rebuild and redeploy
docker build -f Dockerfile.production -t nft-platform:latest .
railway up
```

---

## Quick Commands Reference

```bash
# Authentication
railway login
railway logout

# Project management
railway init              # Create new project
railway switch            # Switch project
railway status            # Show status

# Environment variables
railway variable add KEY value
railway variable delete KEY
railway variable list

# Deployment
railway up                # Deploy
railway down              # Stop deployment
railway redeploy          # Force redeploy

# Monitoring
railway logs -f           # Real-time logs
railway logs --lines 50   # Last 50 lines
railway open              # Open dashboard

# Services
railway add               # Add PostgreSQL, Redis, etc.
railway remove            # Remove service

# Debugging
railway shell             # SSH into container
railway status            # Check health
```

---

## Complete Deployment Example

```bash
# 1. Install Railway
npm install -g @railway/cli

# 2. Login
railway login

# 3. Initialize project
cd nft_platform_backend
railway init

# 4. Add PostgreSQL
railway add
# Select: PostgreSQL

# 5. Set secrets
railway variable add SECRET_KEY "$(openssl rand -base64 32)"
railway variable add POSTGRES_PASSWORD "$(openssl rand -base64 32)"

# 6. Set config
railway variable add ENVIRONMENT "production"
railway variable add LOG_LEVEL "info"
railway variable add WORKERS "4"

# 7. Deploy
railway up

# 8. Monitor
railway logs -f

# 9. Test
curl https://your-railway-app.railway.app/health
```

Done! Your FastAPI backend is now deployed to Railway. 🚀

---

## Support Resources

- **Railway Docs**: https://docs.railway.app/
- **FastAPI**: https://fastapi.tiangolo.com/
- **Uvicorn**: https://www.uvicorn.org/
- **SQLAlchemy**: https://docs.sqlalchemy.org/
- **Alembic**: https://alembic.sqlalchemy.org/

---

**Your application is production-ready.**
