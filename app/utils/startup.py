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

# ==================================================================================
# SAFE MIGRATION FUNCTION
# Handles errors gracefully without crashing the app
# ==================================================================================

async def auto_migrate_safe():
    """
    Run Alembic migrations with comprehensive error handling.
    
    Returns:
        (bool, str): (success: bool, message: str)
    
    Errors are logged but not raised - migrations should not crash the app.
    """
    try:
        logger.info("=" * 70)
        logger.info("DATABASE MIGRATION - Starting")
        logger.info("=" * 70)
        
        project_root = Path(__file__).resolve().parents[2]
        cmd = [sys.executable, "-m", "alembic", "upgrade", "head"]
        sub_env = os.environ.copy()
        sub_env["DATABASE_URL"] = settings.database_url
        
        logger.info(f"Command: {' '.join(cmd)}")
        logger.info(f"Working directory: {project_root}")
        logger.info(f"Database URL: {settings.database_url[:50]}..." if settings.database_url else "Not set")
        
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(project_root),
            env=sub_env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        # Wait for process to complete with timeout
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120.0)
        except asyncio.TimeoutError:
            logger.error("Migration timed out after 120 seconds")
            try:
                proc.kill()
            except:
                pass
            return (False, "Migration timeout")
        
        stdout_text = stdout.decode() if stdout else ""
        stderr_text = stderr.decode() if stderr else ""
        
        # Log output
        if stdout_text:
            logger.info(f"Alembic stdout:\n{stdout_text}")
        if stderr_text:
            logger.warning(f"Alembic stderr:\n{stderr_text}")
        
        # Check result
        if proc.returncode == 0:
            logger.info("=" * 70)
            logger.info("✓ DATABASE MIGRATION - Completed Successfully")
            logger.info("=" * 70)
            return (True, "Migrations completed successfully")
        else:
            logger.error("=" * 70)
            logger.error(f"✗ DATABASE MIGRATION - Failed with return code {proc.returncode}")
            logger.error("=" * 70)
            logger.error(f"Error details:\n{stderr_text}")
            return (False, f"Migration failed with code {proc.returncode}")
            
    except Exception as e:
        logger.error("=" * 70)
        logger.error(f"✗ DATABASE MIGRATION - Exception occurred")
        logger.error("=" * 70)
        logger.error(f"Exception: {type(e).__name__}: {str(e)}", exc_info=True)
        return (False, f"Migration exception: {str(e)}")


# Keep the old function for backward compatibility, but marked as deprecated
async def auto_migrate():
    """
    DEPRECATED: Use auto_migrate_safe() instead.
    This version raises exceptions and will crash the app on migration failure.
    """
    logger.warning("auto_migrate() is deprecated - use auto_migrate_safe() for non-fatal migrations")
    success, message = await auto_migrate_safe()
    if not success:
        raise RuntimeError(f"Migration failed: {message}")
    return True


# ==================================================================================
# TELEGRAM WEBHOOK SETUP
# ==================================================================================

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
