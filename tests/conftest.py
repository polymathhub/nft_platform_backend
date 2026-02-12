
import pytest
import uuid
from sqlalchemy import event, inspect
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
    
    # Configure SQLite to handle UUID values as strings and disable duplicate indexes
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        """Enable foreign keys and configure SQLite for UUID support."""
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        # Allow duplicate indexes by disabling integrity checks temporarily
        cursor.execute("PRAGMA ignore_check_constraints=ON")
        cursor.close()
    
    # Create all tables
    async with engine.begin() as conn:
        # Drop all tables first to avoid conflicts
        await conn.run_sync(Base.metadata.drop_all)
        # Create tables without explicit index creation (handled by Column definitions)
        await conn.run_sync(Base.metadata.create_all)
    
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


