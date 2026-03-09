"""Alembic environment configuration for async SQLAlchemy + asyncpg."""
import asyncio
import os
import sys
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine

from alembic import context

# ============================================================================
# DATABASE URL CONFIGURATION
# ============================================================================
# Load DATABASE_URL from environment variables with priority order:
# 1. ALEMBIC_SQLALCHEMY_URL (explicit Alembic config, if set)
# 2. DATABASE_URL (FastAPI config from .env)

sqlalchemy_url = (
    os.getenv("ALEMBIC_SQLALCHEMY_URL") 
    or os.getenv("DATABASE_URL")
)

if not sqlalchemy_url:
    raise RuntimeError(
        "Database URL not found. Set one of these environment variables:\n"
        "  - DATABASE_URL (FastAPI config)\n"
        "  - ALEMBIC_SQLALCHEMY_URL (explicit Alembic config)\n"
        "Example:\n"
        "  export DATABASE_URL='postgresql+asyncpg://user:password@localhost:5432/dbname'"
    )

# ============================================================================
# DATABASE URL CONVERSION
# ============================================================================

def _ensure_asyncpg(url: str) -> str:
    """
    Ensure the database URL uses the asyncpg driver for async operations.
    
    Converts:
      postgres://... -> postgresql+asyncpg://...
      postgresql://... -> postgresql+asyncpg://...
    
    Args:
        url: SQLAlchemy database URL
        
    Returns:
        URL with postgresql+asyncpg:// scheme
        
    Raises:
        ValueError: If URL format is invalid
    """
    if not url:
        raise ValueError("Database URL is empty")
    
    # Already has asyncpg
    if "+asyncpg" in url:
        return url
    
    # Convert old postgres:// to postgresql+asyncpg://
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    
    # Convert postgresql:// to postgresql+asyncpg://
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    # Unknown format
    raise ValueError(
        f"Invalid database URL format: {url[:50]}...\n"
        f"Expected: postgresql+asyncpg://user:password@host:port/dbname"
    )

# Convert to async URL
async_url = _ensure_asyncpg(sqlalchemy_url)

# ============================================================================
# ALEMBIC CONFIGURATION
# ============================================================================

config = context.config

# Setup logging if configured in alembic.ini
if config.config_file_name is not None:
    try:
        fileConfig(config.config_file_name)
    except Exception:
        pass

# Metadata is not used by this template (set to None)
target_metadata = None


# ============================================================================
# MIGRATION RUNNERS
# ============================================================================

def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    
    This mode doesn't require a live database connection.
    Useful for generating migration SQL scripts.
    
    Usage:
        alembic upgrade head --sql
    """
    context.configure(
        url=async_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """Execute migrations using an active connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    
    Creates an async engine, applies migrations, and cleans up.
    
    Requirements:
      - asyncpg driver installed
      - DATABASE_URL with postgresql+asyncpg:// scheme
      - PostgreSQL database accessible
    """
    # Create async engine with NullPool (no connection pooling for migrations)
    engine = create_async_engine(
        async_url,
        poolclass=pool.NullPool,
    )

    async with engine.begin() as connection:
        await connection.run_sync(do_run_migrations)

    await engine.dispose()


# ============================================================================
# EXECUTE MIGRATIONS
# ============================================================================

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())

