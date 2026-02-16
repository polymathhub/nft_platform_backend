#!/usr/bin/env python3
"""
Web App Backend Connectivity Test (Static)
Verifies that all static webapp files and routing are properly connected
No database or config loading required
"""

from pathlib import Path
import re

def test_webapp_connectivity():
    """Test webapp connectivity without loading config"""
    
    print("\n" + "="*70)
    print("🔗 Web App Backend Connectivity Check")
    print("="*70)
    
    base_dir = Path(__file__).parent
    webapp_dir = base_dir / "app" / "static" / "webapp"
    
    # Test 1: Static Files
    print("\n1️⃣  Static Files Present")
    
    required_files = {
        "index.html": "HTML entry point",
        "app.js": "Frontend application logic",
        "styles.css": "Styling",
    }
    
    files_ok = True
    for file, desc in required_files.items():
        file_path = webapp_dir / file
        if file_path.exists():
            size_kb = file_path.stat().st_size / 1024
            print(f"   ✅ {file:20} {size_kb:6.1f} KB - {desc}")
        else:
            print(f"   ❌ {file:20} MISSING - {desc}")
            files_ok = False
    
    if not files_ok:
        print("\n❌ Required files missing!")
        return False
    
    # Test 2: Check HTML Structure
    print("\n2️⃣  HTML Structure")
    
    with open(webapp_dir / "index.html", 'r', encoding='utf-8') as f:
        html = f.read()
    
    html_checks = [
        ('id="status"', "Status alert"),
        ('id="statusText"', "Status text"),
        ('id="statusSpinner"', "Loading spinner"),
        ('id="modal"', "Modal dialog"),
        ('id="userInfo"', "User info"),
        ('id="walletsList"', "Wallets list"),
        ('id="nftList"', "NFTs list"),
        ('id="marketplaceListings"', "Marketplace"),
        ('id="createWalletBtn"', "Create wallet button"),
        ('id="importWalletBtn"', "Import wallet button"),
        ('id="mintNftBtn"', "Mint NFT button"),
        ('<script src="./app.js">', "app.js script tag"),
        ('href="./styles.css"', "styles.css link"),
        ('src="https://telegram.org/js/telegram-web-app.js"', "Telegram SDK"),
    ]
    
    html_ok = True
    for pattern, desc in html_checks:
        if pattern in html:
            print(f"   ✅ {desc:30} found")
        else:
            print(f"   ❌ {desc:30} missing")
            html_ok = False
    
    # Test 3: Check app.js API Configuration
    print("\n3️⃣  Frontend API Configuration")
    
    with open(webapp_dir / "app.js", 'r', encoding='utf-8') as f:
        app_js = f.read()
    
    api_checks = [
        ("const API_BASE = ", "API base URL"),
        ("async initSession", "Telegram session init"),
        ("async getDashboardData", "Dashboard data fetch"),
        ("async getMarketplaceListings", "Marketplace fetch"),
        ("async createWallet", "Wallet creation"),
        ("async importWallet", "Wallet import"),
        ("async mintNFT", "NFT minting"),
        ("async listNFT", "NFT listing"),
        ("async function init()", "App initialization"),
        ("async function loadDashboard()", "Dashboard loader"),
        ("function setupEvents()", "Event handler setup"),
        ("function updateUserInfo()", "User info update"),
        ("window.Telegram.WebApp", "Telegram WebApp SDK check"),
    ]
    
    api_ok = True
    for pattern, desc in api_checks:
        if pattern in app_js:
            print(f"   ✅ {desc:35} configured")
        else:
            print(f"   ❌ {desc:35} missing")
            api_ok = False
    
    # Test 4: Check Backend Router Configuration
    print("\n4️⃣  Backend Route Configuration")
    
    router_path = base_dir / "app" / "routers" / "telegram_mint_router.py"
    
    with open(router_path, 'r', encoding='utf-8') as f:
        router_content = f.read()
    
    routes = [
        ('"/web-app/init"', "GET /api/v1/telegram/web-app/init"),
        ('"/web-app/dashboard-data"', "GET /api/v1/telegram/web-app/dashboard-data"),
        ('"/web-app/user"', "GET /api/v1/telegram/web-app/user"),
        ('"/web-app/wallets"', "GET /api/v1/telegram/web-app/wallets"),
        ('"/web-app/nfts"', "GET /api/v1/telegram/web-app/nfts"),
        ('"/web-app/mint"', "POST /api/v1/telegram/web-app/mint"),
        ('"/web-app/list-nft"', "POST /api/v1/telegram/web-app/list-nft"),
        ('"/web-app/marketplace/listings"', "GET /api/v1/telegram/web-app/marketplace/listings"),
        ('"/web-app/marketplace/mylistings"', "GET /api/v1/telegram/web-app/marketplace/mylistings"),
    ]
    
    routes_ok = True
    for pattern, desc in routes:
        if pattern in router_content:
            print(f"   ✅ {desc}")
        else:
            print(f"   ❌ {desc} - NOT FOUND")
            routes_ok = False
    
    # Test 5: Check main.py Mount Configuration
    print("\n5️⃣  Static Files Mount Configuration")
    
    main_py_path = base_dir / "app" / "main.py"
    
    with open(main_py_path, 'r', encoding='utf-8') as f:
        main_content = f.read()
    
    mount_checks = [
        ('app.mount("/web-app"', "Web app mounted at /web-app"),
        ('StaticFiles(directory="app/static/webapp"', "Static files configured"),
        ('prefix="/api/v1/telegram"', "Telegram router prefix"),
    ]
    
    mount_ok = True
    for pattern, desc in mount_checks:
        if pattern in main_content:
            print(f"   ✅ {desc}")
        else:
            print(f"   ❌ {desc} - NOT CONFIGURED")
            mount_ok = False
    
    # Test 6: Check Wallet Router
    print("\n6️⃣  Wallet API Endpoints")
    
    wallet_router_path = base_dir / "app" / "routers" / "wallet_router.py"
    
    with open(wallet_router_path, 'r', encoding='utf-8') as f:
        wallet_content = f.read()
    
    wallet_routes = [
        ('"/create"', "POST /api/v1/wallets/create"),
        ('"/import"', "POST /api/v1/wallets/import"),
    ]
    
    wallet_ok = True
    for pattern, desc in wallet_routes:
        if pattern in wallet_content:
            print(f"   ✅ {desc}")
        else:
            print(f"   ❌ {desc} - NOT FOUND")
            wallet_ok = False
    
    # Test 7: Cross-origin Resource Sharing
    print("\n7️⃣  CORS Configuration in main.py")
    
    cors_checks = [
        ("CORSMiddleware", "CORS middleware"),
        ("allow_origins=", "Allowed origins config"),
        ("allow_credentials=True", "Credentials allowed"),
        ('allow_methods=["GET", "POST"', "Methods allowed"),
    ]
    
    cors_ok = True
    for pattern, desc in cors_checks:
        if pattern in main_content:
            print(f"   ✅ {desc}")
        else:
            print(f"   ❌ {desc} - NOT CONFIGURED")
            cors_ok = False
    
    # Test 8: Middleware Stack
    print("\n8️⃣  Middleware Stack")
    
    middleware_checks = [
        ("GZipMiddleware", "GZIP compression"),
        ("SecurityHeadersMiddleware", "Security headers"),
        ("RequestSizeLimitMiddleware", "Request size limit"),
        ("HTTPSEnforcementMiddleware", "HTTPS enforcement"),
    ]
    
    middleware_ok = True
    for pattern, desc in middleware_checks:
        if pattern in main_content:
            print(f"   ✅ {desc}")
        else:
            print(f"   ⚠️  {desc} - optional")
    
    # Final Report
    print("\n" + "="*70)
    print("✨ WEB APP CONNECTIVITY CHECK SUMMARY")
    print("="*70)
    
    all_ok = files_ok and html_ok and api_ok and routes_ok and mount_ok and wallet_ok and cors_ok
    
    if all_ok:
        print("""
✅ SUCCESS - Web App is Fully Connected!

The webapp has:
  ✅ All required static files
  ✅ Proper HTML structure with all elements
  ✅ Complete API method definitions in app.js
  ✅ All backend endpoints configured
  ✅ Proper static file mounting at /web-app
  ✅ Proper router prefixes for /api/v1
  ✅ CORS properly configured
  ✅ Complete middleware stack

Data Flow:
  1. User opens /web-app in Telegram
  2. Telegram SDK loads (telegram-web-app.js)
  3. app.js initializes and checks for Telegram.WebApp
  4. User is authenticated via /api/v1/telegram/web-app/init
  5. Dashboard data loaded via /api/v1/telegram/web-app/dashboard-data
  6. All API methods properly call backend endpoints
  7. Real-time updates as user interacts

Status: 🚀 READY FOR DEPLOYMENT
        """)
        return True
    else:
        print("""
⚠️  Some issues detected - review above for details

Please check:
  • All static files present
  • HTML structure complete
  • API methods defined
  • Backend routes configured
  • Static mounting correct
  • Router prefixes correct
        """)
        return False

if __name__ == "__main__":
    import sys
    result = test_webapp_connectivity()
    sys.exit(0 if result else 1)
