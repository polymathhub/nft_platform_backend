import os
import sys
from logging.config import fileConfig
from sqlalchemy import pool, create_engine
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
    
    # Convert async URL to sync URL for Alembic
    # postgresql+asyncpg:// -> postgresql+psycopg2://
    if url.startswith('postgresql+asyncpg://'):
        url = url.replace('postgresql+asyncpg://', 'postgresql+psycopg2://')
        print(f"✓ Converted async URL to sync for Alembic")
    
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
def run_migrations_online():
    url = get_url()
    try:
        # Use sync engine for migrations
        engine = create_engine(url, poolclass=pool.NullPool, echo=False)
        with engine.begin() as connection:
            do_run_migrations(connection)
        engine.dispose()
    except Exception as e:
        # If connection fails and we're using a remote database, fall back to SQLite
        if 'interchange.proxy.rlwy.net' in url or 'railway' in url:
            print(f"⚠  Remote database connection failed ({type(e).__name__})")
            print("📝 Falling back to SQLite for local testing...")
            url = "sqlite:///./test_migrations.db"
            engine = create_engine(url, poolclass=pool.NullPool, echo=False)
            with engine.begin() as connection:
                do_run_migrations(connection)
            engine.dispose()
            print("✓ Migrations applied to local SQLite database")
            print("⚠  WARNING: Production migrations should run against Railway database!")
        else:
            raise


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
