from app.routers.auth_router import router as auth_router
from app.routers.unified_auth_router import router as unified_auth_router
from app.routers.wallet_router import router as wallet_router
from app.routers.nft_router import router as nft_router
from app.routers.notification_router import router as notification_router
from app.routers.marketplace_router import router as marketplace_router
from app.routers.attestation_router import router as attestation_router
from app.routers.telegram_mint_router import router as telegram_mint_router
from app.routers.admin_router import router as admin_router
from app.routers.payment_router import router as payment_router
from app.routers.referrals import router as referrals_router
from app.routers.stars_payment import router as stars_payment_router
from app.routers.dashboard_router import router as dashboard_router
from app.routers.user_router import router as user_router
from app.routers.ton_wallet_router import router as ton_wallet_router
from app.routers.stars_marketplace_router import router as stars_marketplace_router
from app.routers.me_router import router as me_router
__all__ = [
    "auth_router",
    "unified_auth_router",
    "wallet_router",
    "nft_router",
    "notification_router",
    "marketplace_router",
    "attestation_router",
    "telegram_mint_router",
    "admin_router",
    "payment_router",
    "referrals_router",
    "stars_payment_router",
    "dashboard_router",
    "me_router",
    "user_router",
    "ton_wallet_router",
    "stars_marketplace_router",
]
