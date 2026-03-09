"""
Test fixtures for NFT Platform Backend.

NOTE: Tests use SQLite in-memory database with metadata.create_all()
because Alembic migrations are for PostgreSQL production only.

For production, all schema changes MUST go through Alembic migrations.
"""

import pytest
import uuid
from sqlalchemy import event, inspect, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base


@pytest.fixture
async def test_db():
    """
    Create an async SQLite in-memory test database.
    
    Uses SQLAlchemy metadata.create_all() for test schema creation.
    Production code uses Alembic migrations exclusively.
    """
    # Use in-memory SQLite for tests
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    
    # Configure SQLite for foreign keys and UUID
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        """Enable foreign keys in SQLite."""
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    # Create test schema using metadata (test-only approach)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    # Create async session factory
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    # Yield session for test
    async with async_session() as session:
        yield session
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()
    await engine.dispose()


