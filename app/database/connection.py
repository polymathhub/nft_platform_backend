from __future__ import annotations

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool, QueuePool
from app.config import get_settings

# SQLAlchemy ORM base class
Base = declarative_base()

# Global engine and session factory
engine: AsyncEngine | None = None
AsyncSessionLocal: async_sessionmaker | None = None

# Backwards compatibility: some tests and modules expect `async_engine`
# Export `async_engine` alias that mirrors `engine` so imports remain stable.
async_engine: AsyncEngine | None = None


async def init_db():
    global engine, AsyncSessionLocal
    settings = get_settings()

    # Use connection pooling for production (PostgreSQL on Railway)
    # NullPool for SQLite/testing, QueuePool for PostgreSQL/production
    if "postgresql" in settings.database_url or "postgres" in settings.database_url:
        # Production PostgreSQL configuration with connection pooling
        engine = create_async_engine(
            settings.database_url,
            echo=settings.database_echo,
            poolclass=QueuePool,
            pool_size=10,  # Number of connections to keep in the pool
            max_overflow=20,  # Max additional connections beyond pool_size
            pool_recycle=3600,  # Recycle connections after 1 hour to avoid stale connections
            pool_pre_ping=True,  # Test connections before using them
        )
    else:
        # Development/test SQLite without pooling
        engine = create_async_engine(
            settings.database_url,
            echo=settings.database_echo,
            poolclass=NullPool,
        )
    
    # keep compatibility alias in sync
    global async_engine
    async_engine = engine
    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


"""Database connection management"""
async def close_db():
    global engine

    if engine:
        await engine.dispose()
    # ensure alias cleared as well
    global async_engine
    async_engine = None


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    if not AsyncSessionLocal:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()


# Alias for backwards compatibility with routers that use get_db
get_db = get_db_session
