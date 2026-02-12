from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db, close_db
from app.utils.startup import setup_telegram_webhook,auto_migrate


from app.routers import (
    auth_router,
    wallet_router,
    nft_router,
    notification_router,
    marketplace_router,
    attestation_router,
)
from app.routers.telegram_mint_router import router as telegram_mint_router
from app.routers.walletconnect_router import router as walletconnect_router

# Middleware
from app.security_middleware import (
    SecurityHeadersMiddleware,
    RequestSizeLimitMiddleware,
    HTTPSEnforcementMiddleware,
)

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()           # 1️⃣ Initialize engine
    from app.utils.startup import auto_migrate
    await auto_migrate()      # 2️⃣ Migrate tables
    from app.utils.startup import setup_telegram_webhook
    await setup_telegram_webhook()  # 3️⃣ Telegram

    yield

    from app.database.connection import close_db
    await close_db()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

"""
Security & request middleware
"""
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(HTTPSEnforcementMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=settings.cors_allow_headers,
)


# Root endpoints
@app.get("/")
async def root_get():
    return {"message": "Server is running", "status": "ok"}


@app.post("/")
async def root_post(data: dict):
    return {"message": "POST received", "data": data}


# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "telegram_bot_token": bool(settings.telegram_bot_token),
        "database_url": "configured" if settings.database_url else "not configured",
    }

# Include routers
app.include_router(
    telegram_mint_router,
    prefix="/api/v1/telegram",
    tags=["telegram"]
)

# ======================
# ROUTERS
# ======================

app.include_router(auth_router, prefix="/api/v1")
app.include_router(wallet_router, prefix="/api/v1")
app.include_router(nft_router, prefix="/api/v1")
app.include_router(notification_router, prefix="/api/v1")
app.include_router(marketplace_router, prefix="/api/v1")
app.include_router(attestation_router, prefix="/api/v1")




