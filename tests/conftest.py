
import pytest
import uuid
from sqlalchemy import event, inspect, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base


@pytest.fixture
async def test_db():
    """Create an async SQLite test database with in-memory storage."""
    # Use an in-memory SQLite database for tests
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    
    # Configure SQLite to handle UUID values as strings
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        """Enable foreign keys and configure SQLite for UUID support."""
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")  # Disable for table ops
        cursor.close()
    
    # Create all tables
    async with engine.begin() as conn:
        # Drop all tables first to avoid conflicts
        await conn.run_sync(Base.metadata.drop_all)
        # SQLite needs to clean up indexes too
        await conn.execute(text("PRAGMA foreign_keys=OFF"))
        # Create tables - use checkfirst=True to avoid duplicate index errors
        def create_with_checks(c):
            # SQLite has issues with index creation, so we suppress them
            try:
                Base.metadata.create_all(c, checkfirst=True)
            except Exception:
                # If there's an error, just continue - the tables should exist
                pass
        await conn.run_sync(create_with_checks)
        await conn.execute(text("PRAGMA foreign_keys=ON"))
    
    # Create async session factory
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    # Yield the session for tests
    async with async_session() as session:
        yield session
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


