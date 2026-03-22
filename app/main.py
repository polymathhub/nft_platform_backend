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
    me_v1_router,
)
from app.routers.telegram_mint_router import router as telegram_mint_router
from app.routers.walletconnect_router import router as walletconnect_router
from app.routers.image_router import router as image_router
from app.security_middleware import (
    RequestBodyCachingMiddleware,
    RequestSizeLimitMiddleware,
    RelaxedSecurityHeadersMiddleware,
    StaticFilesNoCacheMiddleware,
)
logger = logging.getLogger(__name__)
settings = get_settings()
try:
    configure_logging()
except Exception as e:
    logger.warning(f"Logging broke, but we keep rolling: {e}")
# Note: Uvicorn access logs are now configured in logger.py - keeping INFO level
# to capture API endpoint logs for debugging
@asynccontextmanager
async def lifespan(app: FastAPI):
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
                logger.info("Redis connected")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}")
                app.state.redis = None
        else:
            app.state.redis = None
    except Exception as e:
        logger.warning(f"Redis connection error: {e}")
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
        logger.error(f"Auto-migration failed: {e}", exc_info=True)
        raise
    logger.info("[Telegram] Setting up webhook...")
    await setup_telegram_webhook()
    logger.info("[Ready] App startup complete")
    yield
    logger.info("[Shutdown] Shutting down...")
    await close_db()
    try:
        r = getattr(app.state, "redis", None)
        if r:
            await r.close()
            logger.info("Redis closed")
    except Exception:
        pass
    logger.info("App shutdown complete")
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
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
    # SECURITY: Don't expose internal errors in production
    if settings.debug:
        # In debug mode, provide full error details for developers
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(exc),
                "status_code": 500,
            }
        )
    else:
        # In production, only log the error and return generic message
        logger.error(f"Unhandled exception: {type(exc).__name__}", exc_info=False)
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "status_code": 500,
            }
        )
app.add_middleware(RequestBodyCachingMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=500)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(StaticFilesNoCacheMiddleware)  # Ensure static files have no-cache headers
try:
    if getattr(settings, 'environment', '').lower() == 'production':
        app.add_middleware(RelaxedSecurityHeadersMiddleware)
        logger.info('RelaxedSecurityHeadersMiddleware enabled for production')
    else:
        logger.info('Skipping relaxed security headers in non-production')
except Exception:
    logger.warning('Unable to configure RelaxedSecurityHeadersMiddleware')
import os
webapp_path = os.path.join(os.path.dirname(__file__), "static", "webapp")
static_path = os.path.join(os.path.dirname(__file__), "static")
cors_origins = settings.allowed_origins.copy() if settings.allowed_origins else []
# SECURITY: Ensure no wildcard origins when credentials are allowed
# Wildcard + credentials = CORS vulnerability allowing credential theft
if "*" in cors_origins:
    logger.error("SECURITY: Wildcard CORS origin ('*') with credentials allowed - removing wildcard for security")
    cors_origins = [o for o in cors_origins if o != "*"]
if any("*" in origin for origin in cors_origins if isinstance(origin, str) and origin != "*"):
    logger.warning("SECURITY: Subdomain wildcard in CORS origins with credentials - review configuration for CORS attacks")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=settings.cors_allow_headers,
)

@app.get("/")
async def root_get():
    # Serve the dashboard HTML directly to avoid an extra redirect
    try:
        dashboard_path = os.path.join(webapp_path, 'dashboard.html')
        if os.path.isfile(dashboard_path):
            return FileResponse(dashboard_path, media_type='text/html')
    except Exception as e:
        logger.warning(f"Failed to serve dashboard.html for '/': {e}")

    # Fallback: return a minimal JSON response instead of redirecting
    return JSONResponse(status_code=200, content={"message": "NFT Platform - web UI available at /webapp/"})
@app.get("/app.js", include_in_schema=False)
async def redirect_app_js():
    return RedirectResponse(url="/webapp/static/app.js", status_code=301)
@app.get("/vendor/tonconnect/tonconnect-ui.css", include_in_schema=False)
async def tonconnect_vendor_css():
    """Redirect vendor CSS requests to CDN to avoid 404 errors when TonConnect auto-loads CSS."""
    return RedirectResponse(url="https://unpkg.com/@tonconnect/ui@latest/dist/tonconnect-ui.min.css", status_code=302)
@app.get("/vendor/tonconnect/tonconnect-ui.min.css", include_in_schema=False)
async def tonconnect_vendor_min_css():
    """Redirect vendor minified CSS requests to CDN."""
    return RedirectResponse(url="https://unpkg.com/@tonconnect/ui@latest/dist/tonconnect-ui.min.css", status_code=302)
@app.get("/tonconnect-manifest.json", include_in_schema=False)
async def tonconnect_manifest(request: Request):
    import json
    manifest_path = os.path.join(os.path.dirname(__file__), "static", "tonconnect-manifest.json")
    if not os.path.isfile(manifest_path):
        raise HTTPException(status_code=404, detail="TonConnect manifest not found")
    try:
        with open(manifest_path, "r", encoding="utf-8") as fh:
            manifest = json.load(fh)
        from urllib.parse import urlparse
        origin = ""
        if settings.app_url:
            origin = settings.app_url.rstrip('/')
        if not origin and settings.telegram_webapp_url:
            parsed = urlparse(settings.telegram_webapp_url)
            if parsed.scheme and parsed.netloc:
                origin = f"{parsed.scheme}://{parsed.netloc}"
        if not origin or origin == "https://localhost:8000":
            forwarded_proto = request.headers.get("x-forwarded-proto", "").lower()
            forwarded_host = request.headers.get("x-forwarded-host", "").strip()
            if forwarded_proto and forwarded_host:
                origin = f"{forwarded_proto}://{forwarded_host}"
        if not origin:
            scheme = request.url.scheme or "https"
            host = request.url.hostname or ""
            port = request.url.port
            if host:
                origin = f"{scheme}://{host}"
                if port and port not in (80, 443):
                    origin = f"{origin}:{port}"
        if not origin or origin.startswith("http://localhost"):
            origin = "https://nftplatformbackend-production-9081.up.railway.app"
        logger.info(f"TonConnect manifest origin: {origin}")
        if origin:
            manifest["url"] = origin
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
@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    icon_path = os.path.join(os.path.dirname(__file__), 'static', 'icon.svg')
    if os.path.isfile(icon_path):
        return FileResponse(icon_path, media_type='image/svg+xml')
    raise HTTPException(status_code=404, detail='Favicon not found')
@app.post("/")
async def root_post(data: dict):
    return {"message": "POST received", "data": data}
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "telegram_bot_token": bool(settings.telegram_bot_token),
        "database_url": "configured" if settings.database_url else "not configured",
    }
@app.get("/health/tonconnect", include_in_schema=False)
async def health_tonconnect(request: Request):
    import os
    from urllib.request import urlopen
    result = {"vendor_js": False, "vendor_css": False, "manifest_ok": False}
    vendor_dir = os.path.join(os.path.dirname(__file__), "static", "vendor", "tonconnect")
    possible_js = ["tonconnect-ui.js", "tonconnect-ui.min.js"]
    possible_css = ["tonconnect-ui.css", "tonconnect-ui.min.css"]
    result["vendor_js"] = any(os.path.isfile(os.path.join(vendor_dir, p)) for p in possible_js)
    result["vendor_css"] = any(os.path.isfile(os.path.join(vendor_dir, p)) for p in possible_css)
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
    r = getattr(app.state, "redis", None)
    if not r:
        return {"status": "no_redis", "available": False}
    try:
        pong = await r.ping()
        return {"status": "ok", "available": True, "pong": pong}
    except Exception as e:
        return {"status": "error", "available": False, "error": str(e)}
app.include_router(
    telegram_mint_router,
    prefix="/api/v1/telegram",
    tags=["telegram"]
)
app.include_router(
    telegram_mint_router,
    prefix="",
    tags=["telegram-root-compat"]
)
app.include_router(
    telegram_mint_router,
    prefix="/telegram",
    tags=["telegram-compat"]
)
app.include_router(
    telegram_mint_router,
    prefix="/api/telegram",
    tags=["telegram-compat-2"]
)

# Legacy auth routers removed.  we are Using the stateless Telegram auth via `me_v1_router`.
app.include_router(me_v1_router, prefix="/api")  # telegram stateless login is here 
app.include_router(wallet_router, prefix="/api/v1")
app.include_router(nft_router, prefix="/api/v1")
app.include_router(notification_router, prefix="/api/v1")
app.include_router(marketplace_router, prefix="/api/v1")
app.include_router(attestation_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(walletconnect_router, prefix="/api/v1")
app.include_router(image_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(ton_wallet_router)
app.include_router(stars_marketplace_router)
app.include_router(user_router, prefix="/api/v1")
app.include_router(payment_router)
app.include_router(referrals_router)
app.include_router(stars_payment_router)

# Define route handlers BEFORE mounts so they have priority
# Serve dashboard at root; avoid redirect loops by not forcing a redirect here.
@app.get("/webapp/", include_in_schema=False)
async def webapp_root():
    # Serve dashboard directly for webapp root
    try:
        dashboard_path = os.path.join(webapp_path, 'dashboard.html')
        if os.path.isfile(dashboard_path):
            return FileResponse(dashboard_path, media_type='text/html')
    except Exception as e:
        logger.warning(f"Failed to serve dashboard.html for '/webapp/': {e}")

    return JSONResponse(status_code=200, content={"message": "Webapp root - dashboard not available"})

logger.info(f"Checking web app static directory: {webapp_path}")
if os.path.isdir(webapp_path):
    import glob
    css_files = glob.glob(os.path.join(webapp_path, "css", "*.css"))
    js_files = glob.glob(os.path.join(webapp_path, "js", "*.js"))
    html_files = glob.glob(os.path.join(webapp_path, "*.html"))
    logger.info(f"✓ Web app directory found: {webapp_path}")
    logger.info(f"  CSS files found: {len(css_files)} - {[os.path.basename(f) for f in css_files]}")
    logger.info(f"  JS files found: {len(js_files)}")
    logger.info(f"  HTML files found: {len(html_files)} - {[os.path.basename(f) for f in html_files]}")
    app.mount("/webapp", StaticFiles(directory=webapp_path, html=True), name="webapp")
    logger.info(f"Mounted web app static files at /webapp")
    try:
        if os.path.isdir(static_path):
            app.mount("/static", StaticFiles(directory=static_path), name="static")
            logger.info(f"Mounted static assets at /static")
            # Add /vendor mount for TonConnect auto-loading CSS from relative paths
            vendor_path = os.path.join(static_path, "vendor")
            if os.path.isdir(vendor_path):
                app.mount("/vendor", StaticFiles(directory=vendor_path), name="vendor")
                logger.info(f"Mounted vendor assets at /vendor")
    except Exception as e:
        logger.warning(f"Failed to mount /static directory: {e}")
else:
    logger.error(f"Web app static directory NOT FOUND at {webapp_path}")
    logger.error(f"  This will cause 404 errors for CSS/JS files")
    