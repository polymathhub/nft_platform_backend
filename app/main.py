from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, RedirectResponse, FileResponse
from fastapi.exceptions import HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

from app.config import get_settings
from app.database import init_db, close_db
from app.utils.logger import configure_logging
from app.utils.startup import setup_telegram_webhook, auto_migrate

from app.routers import (
    auth_router,
    wallet_router,
    nft_router,
    notification_router,
    marketplace_router,
    attestation_router,
    admin_router,
    payment_router,
    referrals_router,
    stars_payment_router,
    dashboard_router,
    user_router,
    ton_wallet_router,
    stars_marketplace_router,
)
from app.routers.telegram_mint_router import router as telegram_mint_router
from app.routers.walletconnect_router import router as walletconnect_router
from app.routers.image_router import router as image_router

"""Middleware"""

from app.security_middleware import (
    RequestBodyCachingMiddleware,
    SecurityHeadersMiddleware,
    DirectoryListingBlockMiddleware,
)

logger = logging.getLogger(__name__)
settings = get_settings()

# Configure detailed logging after settings are loaded
# Wrap in try-except to ensure app boots even if logging config fails
try:
    configure_logging()
except Exception as e:
    logger.warning(f"Failed to configure detailed logging: {e}. Continuing with bootstrap logger.")

# Reduce noisy access logs from uvicorn in production/dev previews
try:
    uvicorn_access_logger = logging.getLogger('uvicorn.access')
    uvicorn_access_logger.setLevel(logging.WARNING)
except Exception:
    # Non-fatal: if uvicorn logger isn't present, continue
    pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.
    
    Startup:
    1. Initialize async database connection pool
    2. Run Alembic migrations
    3. Setup Telegram webhook (non-fatal if fails)
    
    Shutdown:
    1. Close database connections
    """
    logger.info("=" * 70)
    logger.info("NFT Platform Backend - Startup")
    logger.info("=" * 70)
    
    # Startup
    logger.info("\n[1/3] Initializing database connection pool...")
    await init_db()
    
    logger.info("\n[2/3] Running database migrations...")
    await auto_migrate()
    
    logger.info("\n[3/3] Setting up Telegram webhook...")
    await setup_telegram_webhook()
    
    logger.info("\n" + "=" * 70)
    logger.info("✓ Application startup complete")
    logger.info("=" * 70 + "\n")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    await close_db()
    logger.info("✓ Application shutdown complete")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# ==================== Global Exception Handlers ====================

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """HTTP exception handler."""
    path = request.url.path
    method = request.method
    
    if exc.status_code == 404:
        logger.debug(f"404 Not Found: {method} {path}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "path": path,
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Global catch-all for unexpected errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "status_code": 500,
        }
    )

"""
Security & request middleware
"""
# RequestBodyCachingMiddleware MUST be added first to cache bodies early
app.add_middleware(RequestBodyCachingMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=500)  # Compress responses larger than 500 bytes
app.add_middleware(SecurityHeadersMiddleware)  # Security headers with Telegram support
app.add_middleware(DirectoryListingBlockMiddleware)  # Block directory listing on static files

"""Serve Telegram Web App static files at /web-app
Note: static mount moved after router registration so API endpoints under
`/web-app/*` (POST create/import/etc.) are matched first. If the static
directory is missing we log a warning and API paths remain available.
"""
import os
webapp_path = os.path.join(os.path.dirname(__file__), "static", "webapp")
static_path = os.path.join(os.path.dirname(__file__), "static")

"""CORS"""
""" Build allowed origins - include same-origin for web app"""
cors_origins = settings.allowed_origins.copy() if settings.allowed_origins else []

"""Always allow same-origin requests (important for internal web app)"""

if "http://localhost" not in ",".join(cors_origins):
    cors_origins.extend([
        "http://localhost",
        "http://localhost:8000",
        "http://127.0.0.1",
        "http://127.0.0.1:8000",
        "https://nftplatformbackend-production-b67d.up.railway.app",
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=settings.cors_allow_headers,
)


"""Root endpoints"""

@app.get("/")
async def root_get():
    # Redirect root to webapp for now
    return RedirectResponse(url="/webapp/", status_code=301)


@app.get("/app.js", include_in_schema=False)
async def redirect_app_js():
    """Redirect legacy /app.js requests to the correct path"""
    return RedirectResponse(url="/webapp/static/app.js", status_code=301)


# Serve TonConnect manifest at root path for TonConnect clients
@app.get("/tonconnect-manifest.json", include_in_schema=False)
async def tonconnect_manifest():
    manifest_path = os.path.join(os.path.dirname(__file__), "static", "manifest.json")
    if os.path.isfile(manifest_path):
        return FileResponse(manifest_path, media_type="application/json")
    raise HTTPException(status_code=404, detail="TonConnect manifest not found")


# Serve a simple favicon to avoid browser 404 noise
@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    icon_path = os.path.join(os.path.dirname(__file__), 'static', 'icon.svg')
    if os.path.isfile(icon_path):
        return FileResponse(icon_path, media_type='image/svg+xml')
    raise HTTPException(status_code=404, detail='Favicon not found')


@app.post("/")
async def root_post(data: dict):
    return {"message": "POST received", "data": data}

""" Health check endpoint"""

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "telegram_bot_token": bool(settings.telegram_bot_token),
        "database_url": "configured" if settings.database_url else "not configured",
    }

"""Include routers"""

app.include_router(
    telegram_mint_router,
    prefix="/api/v1/telegram",
    tags=["telegram"]
)

# Also expose the web-app endpoints at the root so the frontend can call
app.include_router(
    telegram_mint_router,
    prefix="",
    tags=["telegram-root-compat"]
)

# Additional compatibility prefixes Telegram deployments sometimes use
app.include_router(
    telegram_mint_router,
    prefix="/telegram",
    tags=["telegram-compat"]
)

# Also support /api/telegram as some setups omit the v1 segment
app.include_router(
    telegram_mint_router,
    prefix="/api/telegram",
    tags=["telegram-compat-2"]
)

"""routers"""

app.include_router(auth_router, prefix="/api/v1")
app.include_router(wallet_router, prefix="/api/v1")
app.include_router(nft_router, prefix="/api/v1")
app.include_router(notification_router, prefix="/api/v1")
app.include_router(marketplace_router, prefix="/api/v1")
app.include_router(attestation_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(walletconnect_router, prefix="/api/v1")
app.include_router(image_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(ton_wallet_router)  # Router already has /api/v1/wallet/ton prefix
app.include_router(stars_marketplace_router)  # Router already has /api/v1/stars/marketplace prefix

# User router at /api prefix (for web app compatibility)
app.include_router(user_router, prefix="/api")

# Notification router at /api prefix (for web app compatibility)
app.include_router(notification_router, prefix="/api")

# Payment router already has /api/v1/payments prefix in its definition
app.include_router(payment_router)

# Referral router already has /api/v1/referrals prefix in its definition
app.include_router(referrals_router)

# Telegram Stars payment router already has /api/v1/stars prefix in its definition
app.include_router(stars_payment_router)

# Mount web app static files and HTML pages
# StaticFiles mounts the webapp directory at root, serving:
# - /webapp/css/*.css
# - /webapp/js/*.js
# - /webapp/index.html
# - Other static assets
logger.info(f"Checking web app static directory: {webapp_path}")
if os.path.isdir(webapp_path):
    # List files in the directory for debugging
    import glob
    css_files = glob.glob(os.path.join(webapp_path, "css", "*.css"))
    js_files = glob.glob(os.path.join(webapp_path, "js", "*.js"))
    html_files = glob.glob(os.path.join(webapp_path, "*.html"))
    
    logger.info(f"✓ Web app directory found: {webapp_path}")
    logger.info(f"  CSS files found: {len(css_files)} - {[os.path.basename(f) for f in css_files]}")
    logger.info(f"  JS files found: {len(js_files)}")
    logger.info(f"  HTML files found: {len(html_files)} - {[os.path.basename(f) for f in html_files]}")
    
    # Mount entire webapp directory at /webapp
    # html=True enables directory traversal and HTML fallback behavior
    app.mount("/webapp", StaticFiles(directory=webapp_path, html=True), name="webapp")
    logger.info(f"✓ Mounted web app static files at /webapp")
    
    # Mount static directory at /static for manifest.json and other assets
    try:
        if os.path.isdir(static_path):
            app.mount("/static", StaticFiles(directory=static_path), name="static")
            logger.info(f"✓ Mounted static assets at /static")
    except Exception as e:
        logger.warning(f"Failed to mount /static directory: {e}")

else:
    logger.error(f"✗ Web app static directory NOT FOUND at {webapp_path}")
    logger.error(f"  This will cause 404 errors for CSS/JS files")


# Fallback routes for root redirects (only if not served by StaticFiles)
@app.get("/", include_in_schema=False)
async def redirect_to_webapp():
    """Redirect root to /webapp"""
    return RedirectResponse(url="/webapp/", status_code=301)




