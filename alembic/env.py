import asyncio
import os
import sys
import logging
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from app.database.base import Base
    import app.models
    logger.info("✓ Successfully imported app models and database base")
except ImportError as e:
    logger.error(f"✗ Failed to import app models: {e}", exc_info=True)
    raise

config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

def get_url():
    """
    Intelligently determine database URL for migrations.
    
    Priority:
    1. ALEMBIC_SQLALCHEMY_URL env var (explicit override)
    2. DATABASE_URL env var (primary)
    3. SQLite fallback (development only)
    """
    # Try explicit ALEMBIC_SQLALCHEMY_URL first
    url = os.getenv("ALEMBIC_SQLALCHEMY_URL")
    if url:
        logger.info(f"Using ALEMBIC_SQLALCHEMY_URL")
        return url
    
    # Try DATABASE_URL
    url = os.getenv("DATABASE_URL")
    if url:
        if "postgresql" in url or "asyncpg" in url:
            logger.info(f"✓ Using DATABASE_URL (PostgreSQL detected)")
            return url
        else:
            logger.warning(f"DATABASE_URL is set but doesn't look like PostgreSQL: {url[:50]}")
            return url
    
    # Fallback to SQLite for local development
    logger.warning(f"⚠ DATABASE_URL not set - using local SQLite for development")
    logger.warning(f"  (For production, set DATABASE_URL environment variable)")
    url = "sqlite:///./test_migrations.db"
    logger.info(f"  Using: {url}")
    return url

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """
    Run migrations in offline mode (e.g., for generating migration scripts).
    """
    try:
        url = get_url()
        context.configure(
            url=url,
            target_metadata=target_metadata,
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
        )
        
        with context.begin_transaction():
            context.run_migrations()
            logger.info("✓ Offline migrations completed")
    except Exception as e:
        logger.error(f"✗ Offline migrations failed: {e}", exc_info=True)
        raise


def do_run_migrations(connection):
    """
    Execute migrations given an active connection.
    """
    try:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=False,
        )
        
        with context.begin_transaction():
            context.run_migrations()
        
        # Log result
        logger.info("✓ Migrations executed successfully")
            
    except Exception as e:
        logger.error(f"✗ Migration execution failed: {e}", exc_info=True)
        raise


async def run_migrations_online():
    """
    Run migrations in online mode (async-first with graceful degradation).
    
    Strategy:
    - Try async PostgreSQL (asyncpg) for production
    - Fall back to sync SQLite for local development
    - Log all steps clearly
    """
    try:
        url = get_url()
        
        # Determine if we should use async or sync based on URL and drivers
        use_async = "postgresql" in url or "asyncpg" in url
        is_local_sqlite = url.startswith("sqlite")
        
        if use_async and not is_local_sqlite:
            # Production: Use async PostgreSQL engine
            logger.info("=" * 70)
            logger.info("Run migrations ONLINE (async mode)")
            logger.info("=" * 70)
            logger.info(f"Database: PostgreSQL (asyncpg)")
            
            try:
                engine = create_async_engine(
                    url,
                    poolclass=pool.NullPool,
                    echo=False,
                    future=True,
                )
                
                async with engine.begin() as connection:
                    await connection.run_sync(do_run_migrations)
                
                await engine.dispose()
                logger.info("=" * 70)
                logger.info("✓ Async migrations completed successfully")
                logger.info("=" * 70)
                
            except Exception as e:
                logger.error("=" * 70)
                logger.error(f"✗ Async migrations failed: {e}")
                logger.error("=" * 70)
                logger.error(f"Details: {type(e).__name__}: {str(e)}", exc_info=True)
                raise
        else:
            # Development: Use sync SQLite engine
            logger.info("=" * 70)
            logger.info("Run migrations ONLINE (sync mode - SQLite, local development)")
            logger.info("=" * 70)
            logger.info(f"Database: SQLite (local development)")
            logger.info(f"For production, set DATABASE_URL with PostgreSQL connection string")
            
            try:
                from sqlalchemy import create_engine as create_sync_engine
                
                sync_url = "sqlite:///./test_migrations.db"
                engine = create_sync_engine(
                    sync_url,
                    poolclass=pool.NullPool,
                    echo=False,
                )
                
                with engine.begin() as connection:
                    do_run_migrations(connection)
                
                engine.dispose()
                logger.info("=" * 70)
                logger.info("✓ Sync migrations completed successfully")
                logger.info("=" * 70)
                
            except Exception as e:
                logger.error("=" * 70)
                logger.error(f"✗ Sync migrations failed: {e}")
                logger.error("=" * 70)
                logger.error(f"Details: {type(e).__name__}: {str(e)}", exc_info=True)
                raise
                
    except Exception as e:
        logger.error(f"✗ Migration process failed: {e}")
        raise


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if context.is_offline_mode():
    logger.info("Running Alembic in OFFLINE mode")
    run_migrations_offline()
else:
    logger.info("Running Alembic in ONLINE mode")
    asyncio.run(run_migrations_online())
