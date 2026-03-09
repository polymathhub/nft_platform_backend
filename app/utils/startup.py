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
            await ensure_enum_types()
            return
        else:
            # Alembic failed
            err_text = stderr.decode(errors="ignore") if stderr else ""
            out_text = stdout.decode(errors="ignore") if stdout else ""

            # Some errors are safe to ignore (objects already exist)
            if any(x in err_text.lower() for x in ["already exists", "duplicate", "constraint"]):
                logger.warning(f"⚠ Alembic warning (non-fatal): {err_text[:300]}")
                await ensure_enum_types()
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


async def ensure_enum_types():
    """
    Safely ensure all required PostgreSQL enum types exist.
    
    This is called AFTER migrations run to ensure enums are created
    in the correct order for PostgreSQL.
    """
    from app.database.connection import engine
    
    if engine is None:
        return

    # Only for PostgreSQL
    if "postgresql" not in settings.database_url:
        return

    enum_types = {
        "notificationtype": [
            "PAYMENT_RECEIVED", "PAYMENT_FAILED", "COLLECTION_CREATED", "NFT_LISTED",
            "NFT_UNLISTED", "OFFER_RECEIVED", "OFFER_ACCEPTED", "OFFER_REJECTED",
            "AUCTION_STARTED", "AUCTION_ENDED", "BID_PLACED", "BID_CANCELLED",
            "PURCHASE_COMPLETED", "REFERRAL_BONUS", "WALLET_CONNECTED",
            "WALLET_DISCONNECTED", "ESCROW_CREATED", "ESCROW_RELEASED", "ESCROW_FAILED",
        ],
        "userrole": ["user", "admin"],
    }

    try:
        async with engine.connect() as conn:
            for enum_name, enum_values in enum_types.items():
                try:
                    # Check if enum exists
                    result = await conn.execute(
                        text(
                            "SELECT 1 FROM pg_type WHERE typname = :enum_name"
                        ),
                        {"enum_name": enum_name},
                    )
                    if result.scalar():
                        logger.debug(f"✓ Enum type '{enum_name}' exists")
                        continue

                    # Create enum if missing
                    enum_values_str = ", ".join(f"'{val}'" for val in enum_values)
                    create_sql = f"CREATE TYPE {enum_name} AS ENUM ({enum_values_str})"
                    await conn.execute(text(create_sql))
                    await conn.commit()
                    logger.info(f"✓ Created enum type '{enum_name}'")

                except Exception as e:
                    if "already exists" in str(e).lower():
                        logger.debug(f"Enum type '{enum_name}' already exists")
                    else:
                        logger.warning(f"Could not ensure enum '{enum_name}': {e}")
    except Exception as e:
        logger.warning(f"Could not check/create enum types: {e}")
        # Non-fatal - migrations already handle this


async def setup_telegram_webhook() -> bool:
    """
    Setup Telegram webhook on application startup.
    
    SKIPPED for local development (localhost, debug mode).
    Non-fatal - app will start even if webhook setup fails.
    """
    if not settings.telegram_bot_token:
        logger.info("Telegram bot token not configured, skipping Telegram webhook setup")
        return True

    # Skip webhook setup for local development (use polling instead)
    if settings.debug or os.getenv("ENVIRONMENT", "").lower() == "development":
        logger.info("Local development detected - skipping Telegram webhook setup (polling mode)")
        return True
    
    # Only set webhook if explicitly enabled in non-debug mode
    if not settings.telegram_auto_setup_webhook:
        logger.info("Telegram auto-setup webhook disabled - skipping setup")
        return True

    if not settings.telegram_webhook_url:
        logger.warning("Telegram webhook URL not configured - skipping setup. Set TELEGRAM_WEBHOOK_URL to enable.")
        return True

    logger.info("Initializing Telegram webhook integration...")
    webhook_url = settings.telegram_webhook_url

    try:
        manager = TelegramWebhookManager(settings.telegram_bot_token)
        current_info = await manager.get_webhook_info()

        if current_info:
            current_url = current_info.get("url")
            logger.info(f"Current Telegram webhook: {current_url}")
            if current_url == webhook_url:
                logger.info("✓ Webhook already correctly configured")
                return True

        logger.info(f"Setting Telegram webhook to: {webhook_url}")
        success = await manager.set_webhook(
            webhook_url,
            secret_token=settings.telegram_webhook_secret,
        )

        if success:
            logger.info("✓ Telegram webhook setup successful")
            return True
        else:
            logger.warning("⚠ Telegram webhook setup failed - continuing startup")
            return True

    except Exception as e:
        logger.warning(f"⚠ Telegram webhook setup error (non-fatal): {e}")
        return True
