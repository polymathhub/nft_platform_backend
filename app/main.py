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
import redis.asyncio as redis

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
    unified_auth_router,
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

try:
    configure_logging()
except Exception as e:
    logger.warning(f"Logging broke, but we keep rolling: {e}")
try:
    uvicorn_access_logger = logging.getLogger('uvicorn.access')
    uvicorn_access_logger.setLevel(logging.WARNING)
except Exception:
    pass  # Uvicorn logger is on vacation

@asynccontextmanager
async def lifespan(app: FastAPI):
    # This function runs when the app wakes up and goes to sleep. Like coffee, but for servers.
    logger.info("=" * 70)
    logger.info("NFT Platform Backend - Startup")
    logger.info("=" * 70)
    
    logger.info("[Wake up] Initializing DB pool...")
    await init_db()
    try:
        logger.info("[Redis] Trying to connect...")
        if getattr(settings, "redis_url", None):
            app.state.redis = redis.from_url(settings.redis_url, encoding='utf-8', decode_responses=True)
            try:
                await app.state.redis.ping()
                logger.info("Redis is alive! 🦄")
            except Exception as e:
                logger.warning(f"Redis is grumpy: {e}")
                app.state.redis = None
        else:
            app.state.redis = None
    except Exception as e:
        logger.warning(f"Redis totally bailed: {e}")
        app.state.redis = None
    logger.info("[Migrations] Running... (AUTO_MIGRATE toggle respected)")
    try:
        import os
        auto_flag = os.environ.get("AUTO_MIGRATE", "true").lower()
        if auto_flag in ("1", "true", "yes"):
            await auto_migrate()
        else:
            logger.info("AUTO_MIGRATE disabled via environment; skipping Alembic migrations on startup.")
    except Exception as e:
        logger.warning(f"Skipping auto_migrate due to error reading AUTO_MIGRATE: {e}")
    logger.info("[Telegram] Setting up webhook...")
    await setup_telegram_webhook()
    logger.info("[Ready] App startup complete! 🎉")
    yield
    logger.info("[Nap time] Shutting down...")
    await close_db()
    try:
        r = getattr(app.state, "redis", None)
        if r:
            await r.close()
            logger.info("Redis is napping.")
    except Exception:
        pass
    logger.info("App is now asleep. 💤")


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
# Keep only essential middleware for request handling; remove strict security
# middleware that interferes with Telegram WebApp environment. Retain
# request body caching and gzip compression. Add request size limiting.
app.add_middleware(RequestBodyCachingMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=500)  # Compress responses larger than 500 bytes
# Lightweight request size limiter to protect against very large uploads
from app.security_middleware import RequestSizeLimitMiddleware
app.add_middleware(RequestSizeLimitMiddleware)

"""Serve Telegram Web App static files at /webapp
Note: static mount moved after router registration so API endpoints under
`/webapp/*` (POST create/import/etc.) are matched first. If the static
directory is missing we log a warning and API paths remain available.
"""
import os
webapp_path = os.path.join(os.path.dirname(__file__), "static", "webapp")
static_path = os.path.join(os.path.dirname(__file__), "static")

"""CORS"""
""" Build allowed origins - include same-origin for web app"""
cors_origins = settings.allowed_origins.copy() if settings.allowed_origins else []

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=settings.cors_allow_headers,
)


# Development helper: prevent aggressive caching of static assets so frontend changes
# appear immediately. In production you may want to remove or relax these headers.
@app.middleware("http")
async def disable_static_caching(request: Request, call_next):
    response = await call_next(request)
    try:
        path = request.url.path or ""
        if path.startswith("/webapp/") or path.startswith("/static/"):
            # Force browsers to always revalidate during development
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
    except Exception:
        # Don't let caching logic break the app
        pass
    return response


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
async def tonconnect_manifest(request: Request):
    """
    Serve a TonConnect manifest generated at runtime using the configured
    `settings.APP_URL` so the manifest `url` and icon URLs match the deployed
    origin. This avoids mismatch issues when the static `tonconnect-manifest.json` was
    authored for a different domain.
    
    Priority for origin determination:
    1. APP_URL from settings (Railway environment variable)
    2. Derived from X-Forwarded-Proto/X-Forwarded-Host headers (Railway/proxy)
    3. Request origin
    """
    import json
    manifest_path = os.path.join(os.path.dirname(__file__), "static", "tonconnect-manifest.json")
    if not os.path.isfile(manifest_path):
        raise HTTPException(status_code=404, detail="TonConnect manifest not found")

    try:
        with open(manifest_path, "r", encoding="utf-8") as fh:
            manifest = json.load(fh)

        from urllib.parse import urlparse

        # Method 1: Check for configured APP_URL (Railway environment or explicit config)
        origin = ""
        if settings.app_url:
            origin = settings.app_url.rstrip('/')
        
        # Method 1b: If APP_URL not set, try to derive from TELEGRAM_WEBAPP_URL
        if not origin and settings.telegram_webapp_url:
            parsed = urlparse(settings.telegram_webapp_url)
            if parsed.scheme and parsed.netloc:
                origin = f"{parsed.scheme}://{parsed.netloc}"
        
        # Method 2: Derive from X-Forwarded headers (Railway/proxy setup)
        if not origin or origin == "https://localhost:8000":
            forwarded_proto = request.headers.get("x-forwarded-proto", "").lower()
            forwarded_host = request.headers.get("x-forwarded-host", "").strip()
            
            if forwarded_proto and forwarded_host:
                origin = f"{forwarded_proto}://{forwarded_host}"
        
        # Method 3: Derive from incoming request
        if not origin:
            scheme = request.url.scheme or "https"
            host = request.url.hostname or ""
            port = request.url.port
            if host:
                origin = f"{scheme}://{host}"
                if port and port not in (80, 443):
                    origin = f"{origin}:{port}"
        
        # Fallback for local/invalid origins - use production URL
        if not origin or origin.startswith("http://localhost"):
            origin = "https://nftplatformbackend-production-9081.up.railway.app"
        
        logger.info(f"TonConnect manifest origin: {origin}")
        
        if origin:
            manifest["url"] = origin
            # Normalize icons to absolute URLs
            if isinstance(manifest.get("icons"), list):
                for ico in manifest["icons"]:
                    src = ico.get("src") or ''
                    if src and not src.startswith("http"):
                        ico["src"] = origin.rstrip("/") + "/" + src.lstrip("/")

        from fastapi.responses import JSONResponse
        return JSONResponse(content=manifest, media_type="application/json")
    except Exception as e:
        logger.error(f"Failed to load tonconnect-manifest: {e}")
        raise HTTPException(status_code=500, detail="Failed to load TonConnect manifest")


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


@app.get("/health/tonconnect", include_in_schema=False)
async def health_tonconnect(request: Request):
    """Check presence of vendored TonConnect assets and manifest availability.
    Returns JSON with boolean flags: vendor_js, vendor_css, manifest_ok
    """
    import os
    from urllib.request import urlopen
    result = {"vendor_js": False, "vendor_css": False, "manifest_ok": False}

    vendor_dir = os.path.join(os.path.dirname(__file__), "static", "vendor", "tonconnect")
    # Support both minified and non-minified filenames
    possible_js = ["tonconnect-ui.js", "tonconnect-ui.min.js"]
    possible_css = ["tonconnect-ui.css", "tonconnect-ui.min.css"]
    result["vendor_js"] = any(os.path.isfile(os.path.join(vendor_dir, p)) for p in possible_js)
    result["vendor_css"] = any(os.path.isfile(os.path.join(vendor_dir, p)) for p in possible_css)

    # Try manifest endpoint (fast 3s timeout)
    try:
        scheme = request.url.scheme or "https"
        host = request.url.hostname or (settings.app_url.split('://')[-1] if settings.app_url else '')
        origin = f"{scheme}://{host}" if host else (settings.app_url or "")
        manifest_url = origin.rstrip('/') + '/tonconnect-manifest.json'
        try:
            with urlopen(manifest_url, timeout=3) as resp:
                result["manifest_ok"] = (getattr(resp, 'status', None) == 200)
        except Exception:
            result["manifest_ok"] = False
    except Exception:
        result["manifest_ok"] = False

    return JSONResponse(content=result)


@app.get('/redis-ping', include_in_schema=False)
async def redis_ping():
    """Simple Redis connectivity check that uses the shared async client on app.state."""
    r = getattr(app.state, "redis", None)
    if not r:
        return {"status": "no_redis", "available": False}
    try:
        pong = await r.ping()
        return {"status": "ok", "available": True, "pong": pong}
    except Exception as e:
        return {"status": "error", "available": False, "error": str(e)}

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
app.include_router(unified_auth_router)  # Unified TON & Telegram auth - prefix included in router
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
    
    # Mount static directory at /static for tonconnect-manifest.json and other assets
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




