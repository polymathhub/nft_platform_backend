"""
Startup utilities for NFT Platform Backend.

Handles:
- Database async initialization
- Alembic migration execution
- Telegram webhook setup
"""

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
    """
    Run Alembic database migrations programmatically.
    
    This is the ONLY method for managing database schema.
    SQLAlchemy's metadata.create_all() is NOT used.
    
    Migrations are idempotent and safe to run multiple times.
    """
    from app.database.connection import engine
    
    if engine is None:
        raise RuntimeError("Database engine is not initialized. Call init_db() first.")

    logger.info("=" * 70)
    logger.info("Running Alembic database migrations...")
    logger.info("=" * 70)

    try:
        project_root = Path(__file__).resolve().parents[2]
        
        # Check if alembic_version table exists
        logger.info("Checking migration status...")
        async with engine.connect() as conn:
            try:
                result = await conn.execute(
                    text(
                        "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                        "WHERE table_schema='public' AND table_name='alembic_version')"
                    )
                )
                alembic_table_exists = bool(result.scalar())
            except Exception as e:
                # For non-PostgreSQL databases, just proceed
                logger.debug(f"Could not check alembic_version table: {e}")
                alembic_table_exists = False

        if alembic_table_exists:
            logger.info("✓ Alembic migration tracking table exists")
        else:
            logger.info("  Alembic migration tracking table will be created on first migration")

        # Run: alembic upgrade head
        cmd = [sys.executable, "-m", "alembic", "upgrade", "head"]
        logger.info(f"Executing: {' '.join(cmd)}")
        
        # CRITICAL: Pass environment variables to subprocess
        # alembic/env.py needs DATABASE_URL from environment
        # Pydantic loads from .env into memory, but subprocess needs actual env var
        sub_env = os.environ.copy()
        sub_env["DATABASE_URL"] = settings.database_url  # Ensure DATABASE_URL is set in subprocess
        
        logger.info(f"Subprocess DATABASE_URL: {settings.database_url[:50]}...")
        
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=PIPE,
            stderr=PIPE,
            cwd=str(project_root),
            env=sub_env  # Pass environment with explicit DATABASE_URL
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode == 0:
            logger.info("✓ Alembic migrations completed successfully")
            if stdout:
                out_text = stdout.decode(errors="ignore").strip()
                if out_text:
                    logger.info(f"Migration output:\n{out_text}")
            return
        else:
            # Alembic failed
            err_text = stderr.decode(errors="ignore") if stderr else ""
            out_text = stdout.decode(errors="ignore") if stdout else ""

            # Some errors are safe to ignore (objects already exist)
            if any(x in err_text.lower() for x in ["already exists", "duplicate", "constraint"]):
                logger.warning(f"⚠ Alembic warning (non-fatal): {err_text[:300]}")
                return
            
            # Critical error
            logger.error(f"✗ Alembic migration failed (exit code {proc.returncode})")
            logger.error(f"stderr: {err_text}")
            logger.error(f"stdout: {out_text}")
            raise RuntimeError(
                f"Alembic migration failed with exit code {proc.returncode}. "
                f"Database schema is not initialized. Error: {err_text}"
            )

    except Exception as e:
        logger.error(f"✗ Failed to run migrations: {e}", exc_info=True)
        raise RuntimeError(
            f"Database migration failed. Application cannot start. Error: {e}"
        ) from e




async def setup_telegram_webhook() -> bool:
    """
    Setup Telegram webhook on application startup.
    
    Webhook is set up in PRODUCTION mode only (ENVIRONMENT=production).
    Local development (debug=True or ENVIRONMENT=development) uses polling instead.
    Non-fatal - app will start even if webhook setup fails.
    """
    if not settings.telegram_bot_token:
        logger.info("Telegram bot token not configured, skipping Telegram webhook setup")
        return True

    # Determine if we're in production mode
    # Priority: settings.environment from config (loaded from Railway or .env)
    is_production = settings.environment.lower() == "production" and not settings.debug
    
    # Skip webhook setup for local development (use polling instead)
    if not is_production:
        logger.info(
            f"Local development detected (ENVIRONMENT={settings.environment}, DEBUG={settings.debug}) "
            "- skipping Telegram webhook setup (using polling mode)"
        )
        return True
    
    # Only set webhook if explicitly enabled in production mode
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
