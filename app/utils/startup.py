import logging
import os
import sys
import asyncio
from pathlib import Path
from asyncio.subprocess import PIPE
from sqlalchemy import text
from app.config import get_settings
from app.utils.telegram_webhook import TelegramWebhookManager
logger = logging.getLogger(__name__)
settings = get_settings()
async def auto_migrate():
    import asyncio
    import os
    import sys
    from pathlib import Path
    project_root = Path(__file__).resolve().parents[2]
    cmd = [sys.executable, "-m", "alembic", "upgrade", "head"]
    sub_env = os.environ.copy()
    sub_env["DATABASE_URL"] = settings.database_url
    logger.info("Running Alembic migrations...")
    logger.info(f"Command: {' '.join(cmd)}")
    logger.info(f"Working directory: {project_root}")
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=str(project_root),
        env=sub_env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    stdout_text = stdout.decode() if stdout else ""
    stderr_text = stderr.decode() if stderr else ""
    logger.info(f"Alembic stdout:\n{stdout_text}")
    if proc.returncode == 0:
        logger.info("✓ Alembic migrations completed successfully")
    else:
        logger.error(f"Alembic migration failed with return code {proc.returncode}")
        logger.error(f"Alembic stderr:\n{stderr_text}")
        raise RuntimeError(f"Alembic migration failed: {stderr_text}")
async def setup_telegram_webhook() -> bool:
    if not settings.telegram_bot_token:
        logger.info("Telegram bot token not configured, skipping Telegram webhook setup")
        return True
    is_production = settings.environment.lower() == "production" and not settings.debug
    if not is_production:
        logger.info(
            f"Local development detected (ENVIRONMENT={settings.environment}, DEBUG={settings.debug}) "
            "- skipping Telegram webhook setup (using polling mode)"
        )
        return True
    if not settings.telegram_auto_setup_webhook:
        logger.info("Telegram auto-setup webhook disabled - skipping setup")
        return True
    if not settings.telegram_webhook_url:
        logger.warning("Telegram webhook URL not configured - skipping setup. Set TELEGRAM_WEBHOOK_URL to enable.")
        return True
    logger.info("Setting up Telegram webhook for production...")
    webhook_url = settings.telegram_webhook_url
    try:
        manager = TelegramWebhookManager(settings.telegram_bot_token)
        current_info = await manager.get_webhook_info()
        if current_info:
            current_url = current_info.get("url")
            logger.info(f"Current Telegram webhook on Telegram servers: {current_url}")
            if current_url == webhook_url:
                logger.info(f"✓ Telegram webhook already correctly configured: {webhook_url}")
                return True
            else:
                logger.info(f"Updating Telegram webhook from {current_url} to {webhook_url}")
        logger.info(f"Registering Telegram webhook: {webhook_url}")
        success = await manager.set_webhook(
            webhook_url,
            secret_token=settings.telegram_webhook_secret,
        )
        if success:
            logger.info(f"✓ Telegram webhook registered successfully: {webhook_url}")
            return True
        else:
            logger.warning(f"⚠ Telegram webhook registration returned False - this may indicate a network issue")
            logger.warning("  The app will continue, and the webhook may register on next restart")
            return True
    except Exception as e:
        logger.warning(f"⚠ Telegram webhook setup failed (non-fatal): {str(e)}")
        logger.warning(
            "  The app will continue with polling mode. "
            "Webhook will retry on next restart if settings are correct."
        )
        return True
