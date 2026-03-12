from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
from app.database.base_class import Base
import app.models  # Ensures all models are imported for Alembic

__all__ = ["Base"]
