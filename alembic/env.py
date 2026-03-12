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
import sys
import os
from logging.config import fileConfig
from sqlalchemy import pool
from alembic import context

# Add app to sys.path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))

from app.database.base import Base
import app.models  # Ensures all models are imported

config = context.config
fileConfig(config.config_file_name)

def get_url():
    return os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))

target_metadata = Base.metadata

def run_migrations_offline():
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = context.engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
    
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

