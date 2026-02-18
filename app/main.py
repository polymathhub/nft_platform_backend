from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

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
 



