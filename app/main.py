from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
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

"""Middleware"""

from app.security_middleware import (
    RequestBodyCachingMiddleware,
    SecurityHeadersMiddleware,
    RequestSizeLimitMiddleware,
    HTTPSEnforcementMiddleware,
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
    """
    Custom HTTP exception handler to log suspicious requests.
    Detects and logs potential security issues like URL injection in paths.
    """
    path = request.url.path
    method = request.method
    
    # Check for suspicious patterns in path
    suspicious_patterns = [
        "https://", "http://",  # URLs in path
        "%3A", "%2F",  # Encoded : and /
        "../../",  # Path traversal
        "..%2F",  # Encoded path traversal
        "%00",  # Null byte injection
        "eval(", "exec(",  # Code injection attempts
        "<script>", "<iframe>",  # XSS attempts
    ]
    
    is_suspicious = any(pattern in path for pattern in suspicious_patterns)
    
    # Log suspicious requests at WARNING level
    if is_suspicious:
        logger.warning(
            f"SUSPICIOUS REQUEST: {method} {path} | "
            f"Status: {exc.status_code} | "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )
    elif exc.status_code == 404:
        # Log 404s for debugging (mostly for development)
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
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(HTTPSEnforcementMiddleware)

"""Serve Telegram Web App static files at /web-app"""
app.mount("/web-app", StaticFiles(directory="app/static/webapp", html=True), name="webapp")

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

# Mount again at root to catch /telegram/webhook and /web-app endpoints
app.include_router(
    telegram_mint_router,
    prefix="",
    tags=["telegram"]
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
app.include_router(payment_router)
 



