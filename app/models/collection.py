from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Integer, JSON, Index
from datetime import datetime
import uuid
from app.database import Base
from app.database.types import GUID


class Collection(Base):
    __tablename__ = "collections"

    id = Column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    creator_id = Column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False, index=True)
    description = Column(String(500), nullable=True)
    blockchain = Column(String(50), nullable=False)
    contract_address = Column(String(255), nullable=True, unique=True)
    
    floor_price = Column(Float, nullable=True, default=None)
    average_price = Column(Float, nullable=True, default=None)
    ceiling_price = Column(Float, nullable=True, default=None)
    total_volume = Column(Float, default=0, nullable=False)
    total_sales = Column(Integer, default=0, nullable=False)
    
    # Rarity weights for valuation (JSON)
    rarity_weights = Column(JSON, nullable=True, default={})  # {'attribute_name': weight}
    
    # Metadata
    collection_metadata = Column(JSON, nullable=True, default={})
    image_url = Column(String(500), nullable=True)
    banner_url = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_collections_creator", "creator_id"),
        Index("ix_collections_blockchain", "blockchain"),
        Index("ix_collections_floor_price", "floor_price"),
    )

    def __repr__(self) -> str:
        return f"<Collection(id={self.id}, name={self.name}, floor_price={self.floor_price})>"
