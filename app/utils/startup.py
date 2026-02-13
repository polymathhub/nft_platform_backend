"""
Startup utilities for Telegram integration and DB auto-migration.
Webhook-only mode (no polling).
"""

import logging

from app.config import get_settings
from app.utils.telegram_webhook import TelegramWebhookManager

logger = logging.getLogger(__name__)
settings = get_settings()

"""database auto migration"""

from app.database.connection import Base, engine as db_engine  # only for type hinting, optional
from app.database.connection import init_db

async def auto_migrate():
    from app.database.connection import engine  # import AFTER init_db()
    if engine is None:
        raise RuntimeError("Database engine is not initialized")

    # Prefer Alembic migrations when available (production-ready)
    try:
        from alembic.config import Config
        from alembic import command
        cfg = Config("alembic.ini")
        command.upgrade(cfg, "head")
        logger.info("Alembic migrations applied successfully")
        return
    except Exception as e:
        logger.warning(f"Alembic upgrade failed or not available: {e}. Falling back to create_all()")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)



async def setup_telegram_webhook() -> bool:
    """
    Setup Telegram webhook on application startup.
    """

    if not settings.telegram_bot_token:
        logger.warning("Telegram bot token not configured, skipping Telegram setup")
        return True

    logger.info("Initializing Telegram webhook integration...")

    webhook_url = (
        "https://nftplatformbackend-production-b67d.up.railway.app/api/v1/telegram/webhook"
    )

    try:
        manager = TelegramWebhookManager(settings.telegram_bot_token)

        current_info = await manager.get_webhook_info()

        if current_info:
            current_url = current_info.get("url")
            logger.info(f"Current Telegram webhook: {current_url}")

            if current_url == webhook_url:
                logger.info("Webhook already correctly configured ✅")
                return True

        logger.info("Setting Telegram webhook...")

        success = await manager.set_webhook(
            webhook_url,
            secret_token=settings.telegram_webhook_secret,
        )

        if success:
            logger.info("✅ Telegram webhook setup successful")
            return True

        logger.error("❌ Failed to setup Telegram webhook")
        return False

    except Exception as e:
        logger.exception(f"Error during webhook setup: {e}")
        return False
