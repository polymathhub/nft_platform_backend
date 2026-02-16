# NFT Platform Web App - Complete Setup Guide

## Overview

The NFT Platform is a comprehensive Telegram WebApp for managing digital assets across multiple blockchains. The application features a modern, mobile-first interface with full backend integration for wallet management, NFT minting, and marketplace trading.

**Latest Version:** 2.0 (Complete Overhaul - Feb 16, 2026)

## Architecture

### Frontend Stack
- **Framework:** Vanilla JavaScript (ES6+) with async/await
- **Styling:** CSS3 with gradients, animations, and responsive design
- **SDK:** Telegram WebApp SDK for authentication and user data
- **Features:** Real-time data loading, modal system, error handling, retry logic

### Backend Stack
- **API:** FastAPI (Python)
- **Database:** PostgreSQL with async SQLAlchemy
- **Authentication:** Telegram WebApp signature verification
- **Services:** Wallet, NFT, Marketplace, Admin, Dashboard services
- **Routers:** Organized by functionality (telegram_mint_router.py, wallet_router.py, etc.)

## Features Implemented

### Dashboard
- Portfolio value overview
- Wallet count and NFT statistics
- Recent wallets and NFTs
- Listing count and activity summary

### Wallet Management
- **Create Wallets:** Generate new wallets on supported blockchains
- **Import Wallets:** Add existing wallet addresses
- **Set Primary:** Mark a wallet as primary for operations
- **View Details:** See wallet address and creation date
- **Supported Chains:** Bitcoin, Ethereum, Solana, TON, Polygon, Avalanche, Arbitrum, Optimism, Base

### NFT Operations
- **Mint NFTs:** Create new NFTs with name, description, and image
- **View Collection:** Browse all owned NFTs with blockchain info
- **NFT Details:** See comprehensive NFT information
- **List for Sale:** Put NFTs on the marketplace with price and currency
- **Transfer NFTs:** Send NFTs to other addresses
- **Burn NFTs:** Remove NFTs from circulation

### Marketplace
- **Browse Listings:** View all active NFT listings
- **Seller Information:** See who is selling each NFT
- **Make Offers:** Submit offers on available NFTs
- **Search & Filter:** Find NFTs by name or criteria
- **Sort Options:** Order by newest, price, or popularity
- **My Listings:** View and manage your own listings
- **Cancel Listings:** Remove NFTs from marketplace

### User Profile
- **Account Info:** View Telegram username, ID, email, verification status
- **Statistics:** Portfolio stats including wallets, NFTs, and listings
- **User Role:** See your role in the system (user, admin, etc.)
- **Join Date:** Account creation date
- **Verification Status:** Verified or unverified account status

## Backend Endpoints

All endpoints are prefixed with `/api/v1/telegram`

### Authentication
- `GET /web-app/init` - Initialize session with init_data

### User
- `GET /web-app/user` - Get user profile info
- `GET /web-app/dashboard-data` - Get complete dashboard data

### Wallets
- `GET /web-app/wallets` - List user wallets
- `POST /web-app/create-wallet` - Create new wallet
- `POST /web-app/import-wallet` - Import existing wallet
- `POST /web-app/set-primary` - Set primary wallet

### NFTs
- `GET /web-app/nfts` - List user NFTs
- `POST /web-app/mint` - Mint new NFT
- `POST /web-app/transfer` - Transfer NFT
- `POST /web-app/burn` - Burn NFT

### Marketplace
- `GET /web-app/marketplace/listings` - Get all listings
- `GET /web-app/marketplace/mylistings` - Get your listings
- `POST /web-app/list-nft` - List NFT for sale
- `POST /web-app/make-offer` - Make offer on listing
- `POST /web-app/cancel-listing` - Cancel listing

## How to Deploy

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost/nft_db
TELEGRAM_BOT_TOKEN=your_bot_token_here
SECRET_KEY=your_secret_key
```

### 3. Run Database Migrations
```bash
alembic upgrade head
```

### 4. Start the Server
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Access Web App
The app is served at: `http://localhost:8000/web-app/`

## File Structure

```
app/
├── main.py                    # FastAPI app setup
├── config.py                  # Configuration settings
├── models/                    # Database models
│   ├── user.py
│   ├── wallet.py
│   ├── nft.py
│   └── marketplace.py
├── routers/
│   ├── telegram_mint_router.py     # Web-app endpoints (2493 lines)
│   ├── wallet_router.py
│   ├── nft_router.py
│   ├── marketplace_router.py
│   └── ... (other routers)
├── services/
│   ├── wallet_service.py
│   ├── nft_service.py
│   ├── marketplace_service.py
│   └── ... (other services)
├── static/
│   └── webapp/
│       ├── app.js             # Main app (880+ lines)
│       ├── index.html         # Html structure
│       └── styles.css         # Styling
└── utils/
    ├── telegram_security.py   # Signature verification
    ├── telegram_utils.py
    └── ... (other utilities)
```

## Frontend Implementation Details

### App Initialization
1. Check for Telegram WebApp SDK
2. Get Telegram initData
3. Send initData to `/web-app/init` endpoint
4. Verify user and create session
5. Load dashboard data
6. Display main interface

### API Layer
The API object provides:
- Automatic retry logic (3 attempts)
- Exponential backoff for failed requests
- Proper error handling and logging
- Request timeout (20 seconds)
- JSON request/response handling

### State Management
Global state object tracks:
- Current user info
- Wallets list
- NFTs list
- Marketplace listings
- Current page

### Error Handling
- Try-catch blocks on all async operations
- User-friendly error messages
- Status bar notifications
- Console logging for debugging

### Mobile Responsiveness
- Flex-based layouts
- CSS media queries
- Touch-friendly buttons
- Responsive grid layouts

## Database Models

### User Model
- id (UUID)
- telegram_id (int)
- telegram_username (str)
- full_name (str)
- email (optional)
- avatar_url (optional)
- is_verified (bool)
- user_role (enum)
- created_at, updated_at, last_login (datetime)

### Wallet Model
- id (UUID)
- user_id (FK)
- blockchain (enum)
- address (str)
- public_key (optional)
- is_primary (bool)
- is_active (bool)
- created_at, updated_at (datetime)

### NFT Model
- id (UUID)
- user_id (FK)
- name (str)
- description (str)
- image_url (optional)
- blockchain (enum)
- blockchain_id (str)
- metadata (JSON)
- status (enum)
- created_at, updated_at (datetime)

### Listing Model
- id (UUID)
- nft_id (FK)
- seller_id (FK)
- price (decimal)
- currency (str)
- status (enum)
- created_at, updated_at (datetime)

## Key Features

1. **Telegram Integration**
   - Uses Telegram WebApp SDK for seamless integration
   - Automatic user authentication via initData
   - Telegram username and profile support

2. **Blockchain Support**
   - Bitcoin, Ethereum, Solana, TON
   - Polygon, Avalanche, Arbitrum, Optimism, Base

3. **Security**
   - Telegram signature verification
   - Secure session management
   - User authentication on every request
   - Database-backed user sessions

4. **Performance**
   - Async/await throughout
   - Connection pooling
   - Query optimization
   - Minimal JavaScript bundle
   - Responsive UI updates

5. **User Experience**
   - Intuitive navigation
   - Clear status messages
   - Modal dialogs for operations
   - Grid-based responsive layouts
   - Professional gradient design

## Troubleshooting

### Web app won't load
1. Check browser console (F12) for errors
2. Verify Telegram WebApp SDK is loaded
3. Ensure CORS is properly configured
4. Check environment variables

### API calls timing out
1. Verify backend is running (`python -m uvicorn app.main:app`)
2. Check database connection
3. Look for errors in server logs
4. Increase timeout value if needed

### Database errors
1. Verify PostgreSQL is running
2. Check DATABASE_URL is correct
3. Run migrations: `alembic upgrade head`
4. Check database permissions

## Next Steps

1. **Testing**
   - Run pytest for unit tests
   - Test in actual Telegram app
   - Verify all endpoints work
   - Test on different devices

2. **Deployment**
   - Use Railway, Heroku, or VPS
   - Configure production database
   - Set up SSL/TLS certificates
   - Configure DNS and domain

3. **Monitoring**
   - Set up logging
   - Monitor API performance
   - Track user activity
   - Alert on failures

## Support

For issues or questions:
1. Check browser console (F12) for errors
2. Review server logs
3. Check database connection
4. Verify all services are running
5. Ensure environment variables are set

## Version History

- **v2.0** (Feb 16, 2026): Complete overhaul with full backend integration
- **v1.0** (Initial): Basic web app structure

## License

This project is part of the Gifted Forge NFT Platform.
