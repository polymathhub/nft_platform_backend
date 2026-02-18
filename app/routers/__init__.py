from app.routers.auth_router import router as auth_router
from app.routers.wallet_router import router as wallet_router
from app.routers.nft_router import router as nft_router
from app.routers.notification_router import router as notification_router
from app.routers.marketplace_router import router as marketplace_router
from app.routers.attestation_router import router as attestation_router
from app.routers.telegram_mint_router import router as telegram_mint_router
from app.routers.admin_router import router as admin_router
from app.routers.payment_router import router as payment_router

__all__ = [
    "auth_router",
    "wallet_router",
    "nft_router",
    "notification_router",
    "marketplace_router",
    "attestation_router",
    "telegram_mint_router",
    "admin_router",
    "payment_router",
]