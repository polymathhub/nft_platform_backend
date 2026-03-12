from __future__ import annotations
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy.pool import NullPool, QueuePool
from app.config import get_settings
from app.database.base_class import Base

engine: AsyncEngine | None = None
AsyncSessionLocal: async_sessionmaker | None = None
async_engine: AsyncEngine | None = None  # Backwards compatibility

async def init_db():
    """Initialize the async database engine and sessionmaker."""
    global engine, AsyncSessionLocal, async_engine
    settings = get_settings()

    if "postgresql" in settings.database_url or "postgres" in settings.database_url:
        engine = create_async_engine(
            settings.database_url,
            echo=getattr(settings, "database_echo", False),
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600,
            pool_pre_ping=True,
        )
    else:
        engine = create_async_engine(
            settings.database_url,
            echo=getattr(settings, "database_echo", False),
            poolclass=NullPool,
        )

    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async_engine = engine

async def create_tables_if_missing():
    """Create all tables if they do not exist (useful for first deploy or dev)."""
    if not engine:
        raise RuntimeError("Engine not initialized. Call init_db() first.")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def close_db():
    """Dispose the async engine (for shutdown/cleanup)."""
    global engine, async_engine
    if engine:
        await engine.dispose()
    engine = None
    async_engine = None

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async SQLAlchemy session (use in FastAPI dependencies)."""
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

get_db = get_db_session  # Alias for FastAPI dependencies

        AsyncSessionLocal = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
        async_engine = engine

    async def create_tables_if_missing():
        """Create all tables if they do not exist (useful for first deploy or dev)."""
        if not engine:
            raise RuntimeError("Engine not initialized. Call init_db() first.")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close_db():
        """Dispose the async engine (for shutdown/cleanup)."""
        global engine, async_engine
        if engine:
            await engine.dispose()
        engine = None
        async_engine = None

    async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
        """Yield an async SQLAlchemy session (use in FastAPI dependencies)."""
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

    get_db = get_db_session  # Alias for FastAPI dependencies
