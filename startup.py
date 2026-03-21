import asyncio
import logging
import sys
import subprocess
from pathlib import Path
from sqlalchemy import text, event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import NullPool
from sqlalchemy.exc import (
    OperationalError,
    ProgrammingError,
    IntegrityError,
)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
ENUM_TYPES = {
    "notificationtype": [
        "PAYMENT_RECEIVED",
        "PAYMENT_FAILED",
        "COLLECTION_CREATED",
        "NFT_LISTED",
        "NFT_UNLISTED",
        "OFFER_RECEIVED",
        "OFFER_ACCEPTED",
        "OFFER_REJECTED",
        "AUCTION_STARTED",
        "AUCTION_ENDED",
        "BID_PLACED",
        "BID_CANCELLED",
        "PURCHASE_COMPLETED",
        "REFERRAL_BONUS",
        "WALLET_CONNECTED",
        "WALLET_DISCONNECTED",
        "ESCROW_CREATED",
        "ESCROW_RELEASED",
        "ESCROW_FAILED",
    ],
}
async def check_database_connection(database_url: str) -> bool:
    if not database_url.startswith("postgresql+asyncpg://"):
        logger.error(
            f"✗ Invalid DATABASE_URL format: {database_url}"
        )
        logger.error(
            "  Expected format: postgresql+asyncpg://user:password@host:port/database"
        )
        logger.error(
            "  Example: postgresql+asyncpg://nft_user:password@localhost:5432/nft_db"
        )
        return False
    try:
        engine = create_async_engine(
            database_url,
            echo=False,
            poolclass=NullPool,
        )
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"✓ Database connection successful: {version[:50]}...")
        await engine.dispose()
        return True
    except OperationalError as e:
        logger.error(f"✗ Database connection failed: {str(e)}")
        if "peer authentication failed" in str(e).lower():
            logger.error(
                "  Check DATABASE_URL credentials and PostgreSQL auth settings"
            )
        elif "could not connect" in str(e).lower():
            logger.error(
                "  Check DATABASE_URL host and port are correct, and PostgreSQL is running"
            )
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected database error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False
async def ensure_enum_types(database_url: str) -> bool:
    engine = create_async_engine(
        database_url,
        echo=False,
        poolclass=NullPool,
    )
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            logger.info(f"  Connected to PostgreSQL database: {db_name}")
            for enum_name, enum_values in ENUM_TYPES.items():
                try:
                    # Check if enum type already exists
                    result = await conn.execute(
                        text(
                            "SELECT EXISTS(SELECT 1 FROM pg_type WHERE typname = :enum_name AND typtype = 'e')"
                        ),
                        {"enum_name": enum_name},
                    )
                    if result.scalar():
                        logger.info(f"✓ Enum type '{enum_name}' already exists")
                        continue
                    enum_values_str = ", ".join(f"'{val}'" for val in enum_values)
                    create_enum_sql = f"CREATE TYPE {enum_name} AS ENUM ({enum_values_str})"
                    logger.info(f"  Creating enum type '{enum_name}'...")
                    await conn.execute(text(create_enum_sql))
                    logger.info(f"✓ Created enum type '{enum_name}'")
                except ProgrammingError as e:
                    if "already exists" in str(e).lower():
                        logger.info(f"✓ Enum type '{enum_name}' already exists")
                    else:
                        logger.error(f"✗ Error with enum '{enum_name}': {str(e)}")
                        return False
                except Exception as e:
                    logger.error(f"✗ Unexpected error creating enum '{enum_name}': {str(e)}")
                    import traceback
                    logger.debug(traceback.format_exc())
                    return False
        logger.info("✓ All enum types are ready")
        return True
    except OperationalError as e:
        logger.error(f"✗ Connection error while ensuring enums: {str(e)}")
        return False
    except ProgrammingError as e:
        logger.error(f"✗ PostgreSQL error while ensuring enums: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error ensuring enums: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        await engine.dispose()
async def run_alembic_migrations() -> bool:
    try:
        logger.info("Starting Alembic migrations...")
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            logger.info("✓ Alembic migrations completed successfully")
            if result.stdout:
                logger.debug(f"Migration output:\n{result.stdout}")
            return True
        else:
            logger.error(f"✗ Alembic migrations failed with code {result.returncode}")
            if result.stderr:
                logger.error(f"Migration error:\n{result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        logger.error("✗ Alembic migrations timed out after 120 seconds")
        return False
    except FileNotFoundError:
        logger.error("✗ alembic command not found. Ensure alembic is installed.")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error running migrations: {str(e)}")
        return False
async def start_fastapi_server() -> None:
    try:
        logger.info("Starting FastAPI server...")
        logger.info("Server running on http://0.0.0.0:8000")
        logger.info("API documentation available at http://0.0.0.0:8000/docs")
        import subprocess
        subprocess.run(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
            ],
            cwd=Path(__file__).parent,
        )
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"✗ Error starting FastAPI server: {str(e)}")
        sys.exit(1)
async def main() -> int:
    import os
    from dotenv import load_dotenv
    load_dotenv()
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        logger.error("✗ DATABASE_URL environment variable not set")
        logger.error("  Add DATABASE_URL to your .env file")
        logger.error("  Example: DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/nft_db")
        return 1
    logger.info("=" * 60)
    logger.info("NFT Platform Backend - Startup Process")
    logger.info("=" * 60)
    logger.info(f"Database URL: {database_url.split('@')[0]}@...")
    logger.info("")
    logger.info("[1/4] Checking database connection...")
    if not await check_database_connection(database_url):
        logger.error("✗ Cannot proceed without database connection")
        logger.error("  Troubleshooting:")
        logger.error("  1. Ensure PostgreSQL is running on localhost:5432")
        logger.error("  2. Verify DATABASE_URL format: postgresql+asyncpg://user:password@host:port/db")
        logger.error("  3. Check username and password are correct")
        logger.error("  4. Create database if it doesn't exist: createdb nft_db -U nft_user")
        return 1
    logger.info("\n[2/4] Ensuring PostgreSQL enum types exist...")
    if not await ensure_enum_types(database_url):
        logger.error("✗ Failed to ensure enum types")
        return 1
    logger.info("\n[3/4] Running Alembic migrations...")
    if not await run_alembic_migrations():
        logger.error("✗ Migrations failed - database may be in inconsistent state")
        return 1
    logger.info("\n[4/4] Starting FastAPI application...")
    logger.info("=" * 60)
    await start_fastapi_server()
    return 0
if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
