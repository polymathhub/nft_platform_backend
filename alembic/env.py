import asyncio
import os
import sys
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from app.database.base import Base
import app.models
config = context.config
fileConfig(config.config_file_name)
def get_url(): 
    # Priority: explicit ALEMBIC var > DATABASE_URL env > fallback to local SQLite
    url = (
        os.getenv("ALEMBIC_SQLALCHEMY_URL") 
        or os.getenv("DATABASE_URL") 
    )
    
    if not url:
        # Fallback to local SQLite for development/testing
        print("WARNING: DATABASE_URL not set, using local SQLite for testing")
        url = "sqlite:///./test_migrations.db"
    
    print(f"✓ Using database: {url.split('@')[1] if '@' in url else url[:30]}...")
    
    return url 
target_metadata = Base.metadata
def run_migrations_offline():
    url = get_url()
    context.configure(
        url=url,
        target_metadata=None,
        literal_binds=True,
        compare_type=False,
    )
    with context.begin_transaction():
        context.run_migrations()
def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=None,
        compare_type=False,
    )
    with context.begin_transaction():
        context.run_migrations()
async def run_migrations_online():
    url = get_url()
    
    # If using Railway (remote), try asyncpg first
    if 'asyncpg' in url and 'railway' not in url and 'interchange' not in url:
        # Local/dev asyncpg - use async
        engine = create_async_engine(url, poolclass=pool.NullPool, echo=False)
        try:
            async with engine.begin() as connection:
                await connection.run_sync(do_run_migrations)
        finally:
            await engine.dispose()
    else:
        # Remote database or fallback - use sync SQLite
        print(f"⚠  Using local SQLite for testing (Railway accessed via CI/CD only)")
        from sqlalchemy import create_engine as create_sync_engine
        url = "sqlite:///./test_migrations.db"
        sync_engine = create_sync_engine(url, poolclass=pool.NullPool, echo=False)
        try:
            with sync_engine.begin() as connection:
                do_run_migrations(connection)
        finally:
            sync_engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
