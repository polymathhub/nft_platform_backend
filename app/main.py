from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.exceptions import HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

from app.config import get_settings
from app.database import init_db, close_db
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
)
from app.routers.telegram_mint_router import router as telegram_mint_router
from app.routers.walletconnect_router import router as walletconnect_router
from app.routers.image_router import router as image_router

"""Middleware"""

from app.security_middleware import (
    RequestBodyCachingMiddleware,
)

logger = logging.getLogger(__name__)
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await auto_migrate()
    await setup_telegram_webhook()

    yield

    await close_db()


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

"""Serve Telegram Web App static files at /web-app
Note: static mount moved after router registration so API endpoints under
`/web-app/*` (POST create/import/etc.) are matched first. If the static
directory is missing we log a warning and API paths remain available.
"""
import os
webapp_path = os.path.join(os.path.dirname(__file__), "static", "webapp")

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
    # If the web app static directory is available, redirect root to the SPA
    try:
        if os.path.isdir(webapp_path):
            return RedirectResponse(url="/web-app/")
    except Exception:
        pass

    return {"message": "Server is running", "status": "ok"}


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
# `/web-app/*` (the web app expects API paths under the same prefix).
# These routes are duplicated intentionally as compatibility endpoints.
app.include_router(
    telegram_mint_router,
    prefix="",
    tags=["telegram-root-compat"]
)

# Additional compatibility prefixes Telegram deployments sometimes use
# (e.g., webhook configured to https://host/telegram/webhook)
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

# Payment router already has /api/v1/payments prefix in its definition
# DO NOT add another prefix to avoid double-prefixing
app.include_router(payment_router)
 
# Mount web app static files after routers so API endpoints under /web-app/*
# (POST create/import/etc.) are matched first. StaticFiles only serves GET/HEAD.
if os.path.isdir(webapp_path):
    app.mount("/web-app", StaticFiles(directory=webapp_path, html=True), name="webapp")
else:
    logger.warning(f"Web app static directory not found at {webapp_path} - /web-app static will not be available")




