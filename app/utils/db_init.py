from app.database.engine import engine
from app.database.base_class import Base
async def create_tables_if_missing():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
