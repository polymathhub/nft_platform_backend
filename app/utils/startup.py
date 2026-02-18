"""
Startup utilities for Telegram integration and DB auto-migration.
Webhook-only mode (no polling).
"""

import logging
import os

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

    auto_flag = os.getenv("AUTO_MIGRATE", "false").lower() in ("1", "true", "yes")
    if not auto_flag:
        logger.info("AUTO_MIGRATE is not enabled; attempting fallback table creation. Set AUTO_MIGRATE=true to enable Alembic migrations.")
        # Fallback: create tables using SQLAlchemy metadata (safe, uses checkfirst=True)
        from app.database.connection import Base
        async with engine.begin() as conn:
            await conn.run_sync(lambda c: Base.metadata.create_all(c, checkfirst=True))
        logger.info("Tables created/verified via SQLAlchemy metadata")
        return

    try:
        import sys
        import asyncio
        from asyncio.subprocess import PIPE
        from pathlib import Path

        project_root = Path(__file__).resolve().parents[2]

        # If database has application tables but no alembic_version, stamp instead of upgrading
        from sqlalchemy import text
        async with engine.connect() as conn:
            result = await conn.execute(
                text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='alembic_version')")
            )
            alembic_table_exists = bool(result.scalar())

            if not alembic_table_exists:
                check_tables = ["collections", "users", "nfts", "wallets", "transactions", "listings", "offers", "orders"]
                in_clause = ",".join([f"'{t}'" for t in check_tables])
                res = await conn.execute(
                    text(f"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name IN ({in_clause}))")
                )
                some_tables_exist = bool(res.scalar())

                if some_tables_exist:
                    logger.info("Database contains application tables but no alembic_version. Proceeding to run idempotent migrations (upgrade head).")

        # Run alembic current (diagnostic) then upgrade head
        cmd_current = [sys.executable, "-m", "alembic", "current"]
        proc_cur = await asyncio.create_subprocess_exec(
            *cmd_current, stdout=PIPE, stderr=PIPE, cwd=str(project_root)
        )
        cur_out, cur_err = await proc_cur.communicate()
        logger.info("Alembic current: %s", cur_out.decode(errors="ignore") if cur_out else cur_err.decode(errors="ignore"))

        cmd_upgrade = [sys.executable, "-m", "alembic", "upgrade", "head"]
        proc = await asyncio.create_subprocess_exec(
            *cmd_upgrade, stdout=PIPE, stderr=PIPE, cwd=str(project_root)
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            err = stderr.decode(errors="ignore") if stderr else ""
            out = stdout.decode(errors="ignore") if stdout else ""
            # Ignore "already exists" errors for indexes/tables that were previously created
            if "already exists" in err.lower() or "duplicate" in err.lower():
                logger.warning("Alembic: Some objects already exist in database (safe to ignore): %s", err[:200])
            else:
                logger.error("Alembic upgrade failed (exit %s). stdout=%s stderr=%s", proc.returncode, out, err)
                raise RuntimeError(f"Alembic upgrade failed. Exit {proc.returncode}: {err}")

        logger.info("Alembic migrations applied successfully")
        
        # After Alembic migrations, ensure user_role column exists (for backward compatibility)
        await ensure_user_role_column()
        return
    except Exception as e:
        logger.error("Alembic migrations failed: %s", e)
        raise RuntimeError(f"Database migrations failed. Application cannot start. Error: {e}") from e


async def ensure_user_role_column():
    """
    Safely check if user_role column exists on users table.
    If missing, add it with default value 'user' and create the enum type if needed.
    This is a safeguard for deployments where migrations haven't fully applied.
    """
    from app.database.connection import engine
    from sqlalchemy import text
    
    if engine is None:
        logger.warning("Database engine not initialized; skipping user_role column check")
        return
    
    try:
        async with engine.connect() as conn:
            # Check if user_role column exists
            result = await conn.execute(
                text("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_schema='public' AND table_name='users' AND column_name='user_role'
                    )
                """)
            )
            column_exists = bool(result.scalar())
            
            if column_exists:
                logger.info("user_role column already exists on users table")
                return
            
            logger.info("user_role column missing; adding it now")
            
            # Add the enum type if it doesn't exist
            await conn.execute(text(
                "CREATE TYPE IF NOT EXISTS userrole AS ENUM ('user', 'admin')"
            ))
            
            # Add the column with default value
            await conn.execute(text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS user_role userrole DEFAULT 'user' NOT NULL"
            ))
            
            await conn.commit()
            logger.info("user_role column added successfully")
            
    except Exception as e:
        logger.warning(f"Failed to ensure user_role column (non-fatal): {e}")
        # Don't raise; this is an exception we can stay with if it happensas the column will be added 



async def setup_telegram_webhook() -> bool:
    """
    Setup Telegram webhook on application startup.
    Non-fatal - app will start even if webhook setup fails.
    """

    if not settings.telegram_bot_token:
        logger.info("Telegram bot token not configured, skipping Telegram webhook setup")
        return True

    logger.info("Initializing Telegram webhook integration...")

    webhook_url = (
        settings.telegram_webhook_url or "https://nftplatformbackend-production-b67d.up.railway.app/api/v1/telegram/webhook"
    )

    try:
        manager = TelegramWebhookManager(settings.telegram_bot_token)

        current_info = await manager.get_webhook_info()

        if current_info:
            current_url = current_info.get("url")
            logger.info(f"Current Telegram webhook: {current_url}")

            if current_url == webhook_url:
                logger.info("Webhook already correctly configured")
                return True

        logger.info("Attempting to set Telegram webhook...")

        success = await manager.set_webhook(
            webhook_url,
            secret_token=settings.telegram_webhook_secret,
        )

        if success:
            logger.info("Telegram webhook setup successful")
            return True
        else:
            logger.warning("Failed to setup Telegram webhook - continuing startup anyway")
            return True

    except Exception as e:
        logger.warning(f"Telegram webhook setup failed (non-fatal): {e}")
        return True
