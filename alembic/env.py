import asyncio
import os
import sys
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from app.database.base import Base
import app.models
config = context.config
fileConfig(config.config_file_name)
def get_url(): 
    url = ( 
        os.getenv("ALEMBIC_SQLALCHEMY_URL") 
        or os.getenv("DATABASE_URL") 
        or config.get_main_option("sqlalchemy.url") 
    )
    if not url:
        raise ValueError(
            "DATABASE_URL is required for migrations. "
            "Set it in .env file or as environment variable."
        )
    masked_url = url
    if '@' in url:
        scheme, rest = url.split('://', 1)
        creds, host = rest.rsplit('@', 1)
        masked_url = f"{scheme}://***@{host}"
    print(f"[Alembic] Using database URL: {masked_url}")
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
    engine = create_async_engine(url, poolclass=pool.NullPool)
    async with engine.begin() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()
if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
