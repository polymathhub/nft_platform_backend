from sqlalchemy import Column, String, DateTime, Boolean, Index, Enum, ForeignKey, Float
from datetime import datetime
import uuid
from enum import Enum as PyEnum
from app.database import Base
from app.database.types import GUID


class UserRole(PyEnum):
    """User role enumeration."""
    ADMIN = "admin"
    USER = "user"


class User(Base):
    __tablename__ = "users"

    id = Column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    telegram_id = Column(String(50), unique=True, nullable=True)
    telegram_username = Column(String(100), nullable=True)
    full_name = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    user_role = Column(Enum(UserRole), default=UserRole.USER, nullable=False, index=True)
    
    # Creator mode fields
    is_creator = Column(Boolean, default=False, nullable=False, index=True)
    creator_name = Column(String(255), nullable=True)
    creator_bio = Column(String(1000), nullable=True)
    creator_avatar_url = Column(String(500), nullable=True)
    
    # Referral system fields
    referral_code = Column(String(50), unique=True, nullable=True, index=True)
    referred_by_id = Column(
        GUID(),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
    )
    referral_locked_at = Column(DateTime, nullable=True)  # When referral became permanent
    
    # Stars/payment balance fields
    stars_balance = Column(Float, default=0.0, nullable=False)
    total_stars_earned = Column(Float, default=0.0, nullable=False)
    total_stars_spent = Column(Float, default=0.0, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_users_username_active", "username", "is_active"),
        Index("ix_users_referral_code", "referral_code"),
        Index("ix_users_is_creator", "is_creator"),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"
