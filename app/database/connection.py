from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy.pool import NullPool, QueuePool
from app.config import get_settings
from app.database.base_class import Base

engine: Optional[AsyncEngine] = None
AsyncSessionLocal: Optional[async_sessionmaker] = None

async def init_db():
    global engine, AsyncSessionLocal
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


async def close_db():
    global engine
    if engine:
        await engine.dispose()
    engine = None


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    if not AsyncSessionLocal:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


get_db = get_db_session


async def create_tables_if_missing():
    if not engine:
        raise RuntimeError("Engine not initialized. Call init_db() first.")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
