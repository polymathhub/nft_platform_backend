from app.database.base_class import Base
# Import all models so Base.metadata is populated for Alembic and SQLAlchemy
import app.models  # noqa: F401

__all__ = ["Base"]
