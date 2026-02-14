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
        # Run Alembic CLI in a separate process to avoid event-loop issues.
        import sys
        import asyncio
        from asyncio.subprocess import PIPE
        from pathlib import Path
        from sqlalchemy import text

        project_root = Path(__file__).resolve().parents[2]

        # First, check current alembic revision
        cmd_current = [sys.executable, "-m", "alembic", "current"]
        proc_cur = await asyncio.create_subprocess_exec(
            *cmd_current, stdout=PIPE, stderr=PIPE, cwd=str(project_root)
        )
        cur_out, cur_err = await proc_cur.communicate()

        # If `alembic current` succeeded, proceed with upgrade
        if proc_cur.returncode == 0:
            logger.info("Alembic current: %s", cur_out.decode(errors="ignore"))
        else:
            # `alembic current` failed. Inspect DB: is `alembic_version` present?
            async with engine.connect() as conn:
                result = await conn.execute(
                    text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='alembic_version')")
                )
                alembic_table_exists = bool(result.scalar())

                if not alembic_table_exists:
                    # Check for presence of known application tables — if any exist,
                    # assume the DB schema was created outside Alembic. Do not mutate.
                    check_tables = ["collections", "users", "nfts"]
                    in_clause = ",".join([f"'{t}'" for t in check_tables])
                    res = await conn.execute(
                        text(f"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name IN ({in_clause}))")
                    )
                    some_tables_exist = bool(res.scalar())

                    if some_tables_exist:
                        msg = (
                            "Database already contains application tables but is not versioned by Alembic. "
                            "Automatic migrations are disabled to avoid duplicate-creation errors. "
                            "Please either run migrations manually or stamp the DB with the current head. "
                            "Example commands (run from project root):\n"
                            "  python -m alembic current\n"
                            "  python -m alembic upgrade head\n"
                            "  OR to mark DB as up-to-date without applying SQL (only when you're sure):\n"
                            "  python -m alembic stamp head\n"
                        )
                        logger.error(msg)
                        raise RuntimeError(msg)

        # Run upgrade now that sanity checks passed
        cmd_upgrade = [sys.executable, "-m", "alembic", "upgrade", "head"]
        proc = await asyncio.create_subprocess_exec(
            *cmd_upgrade, stdout=PIPE, stderr=PIPE, cwd=str(project_root)
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            err = stderr.decode(errors="ignore") if stderr else ""
            out = stdout.decode(errors="ignore") if stdout else ""
            logger.error("Alembic upgrade failed (exit %s). stdout=%s stderr=%s", proc.returncode, out, err)
            raise RuntimeError(f"Database migrations failed. Application cannot start. Exit {proc.returncode}: {err}")

        logger.info("Alembic migrations applied successfully")
        return
    except Exception as e:
        logger.error(f"Alembic migrations failed: {e}")
        raise RuntimeError(f"Database migrations failed. Application cannot start. Error: {e}") from e



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
