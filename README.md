# NFT Platform Backend

This repository contains the backend for the NFT platform and a Netlify Function to receive Telegram webhooks.

Quick steps to push to GitHub and deploy:

1. Create a GitHub repository and add it as a remote, for example:

```bash
git init
git add .
git commit -m "Initial commit: prepare for deployment"
git remote add origin git@github.com:<your-org-or-username>/<repo>.git
git branch -M main
git push -u origin main
```

2. On Railway (or Netlify) set environment variables (do NOT commit `.env`):
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_WEBHOOK_SECRET`
- `TELEGRAM_AUTO_SETUP_WEBHOOK=true`
- `TELEGRAM_WEBHOOK_URL=https://<your-site>.netlify.app/.netlify/functions/telegram_webhook/api/v1/telegram/webhook`

3. After deploy, manually set Telegram webhook:

```bash
curl -X POST "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook" \
	-H "Content-Type: application/json" \
	-d '{"url":"https://<your-site>.netlify.app/.netlify/functions/telegram_webhook/api/v1/telegram/webhook","secret_token":"<TELEGRAM_WEBHOOK_SECRET>"}'
```

If you want, I can create a GitHub remote and push from this machine — confirm and provide the remote URL (or authorize), or run the commands locally and push.
# NFT Platform Backend

FastAPI backend for NFT management across 9 blockchains (TON, Solana, Ethereum, Polygon, Arbitrum, Optimism, Base, Avalanche, Bitcoin).

## Stack

- Python 3.11+ async
- FastAPI
- SQLAlchemy 2.0 + AsyncPG
- Redis  
- IPFS
- JWT auth
- WebSocket notifications
- Docker

## Setup

```bash
git clone <repo>
cd nft_platform_backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` for API docs.

Or use Docker: `docker-compose up -d`

## Project Structure

```
app/
├── main.py      
├── config.py    
├── database/    
├── models/      
├── schemas/     
├── services/    
├── routers/     
├── blockchain/  
└── utils/       
tests/
```

## API

All endpoints under `/api/v1`. Protected endpoints need JWT in `Authorization: Bearer <token>` header.

**Auth:** register, login, refresh, me

**Wallets:** create, import, list, set-primary, delete

**NFTs:** mint, transfer, burn, list, get, upload metadata

**Notifications:** WebSocket real-time events, stats

## Configuration

Copy `.env.example` to `.env`:

**Required:**
- `DATABASE_URL` - PostgreSQL with asyncpg
- `JWT_SECRET_KEY` - 32+ chars
- Blockchain RPC URLs

**Optional:**
- Redis URL
- IPFS settings
- Telegram OAuth

## Development

```bash
pytest tests/
black app/
mypy app/
alembic upgrade head
```

## Production

Set `DEBUG=False`, use production DB, real RPC endpoints, secrets manager.

```bash
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

Or Docker: `docker build -t nft-backend . && docker run -p 8000:8000 --env-file .env nft-backend`
