import logging
from datetime import timedelta
from typing import Optional, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import User
from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AuthService:
    """Service for authentication operations."""

    @staticmethod
    async def register_user(
        db: AsyncSession,
        email: str,
        username: str,
        password: str,
        full_name: Optional[str] = None,
    ) -> Tuple[Optional[User], Optional[str]]:
        existing_user = await db.execute(
            select(User).where((User.email == email) | (User.username == username))
        )
        if existing_user.scalar_one_or_none():
            return None, "User with this email or username already exists"

        new_user = User(
            email=email,
            username=username,
            hashed_password=hash_password(password),
            full_name=full_name,
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user, None

    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        email: str,
        password: str,
    ) -> Tuple[Optional[User], Optional[str]]:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.hashed_password):
            return None, "Invalid email or password"

        if not user.is_active:
            return None, "User account is disabled"

        return user, None

    @staticmethod
    async def authenticate_telegram(
        db: AsyncSession,
        telegram_id: int,
        telegram_username: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> Tuple[Optional[User], Optional[str]]:
        result = await db.execute(
            select(User).where(User.telegram_id == str(telegram_id))
        )
        user = result.scalar_one_or_none()

        if user:
            if not user.is_active:
                return None, "User account is disabled"
            return user, None

        email = f"telegram_{telegram_id}@nftplatform.local"
        username = telegram_username or f"user_{telegram_id}"
        full_name = f"{first_name or ''} {last_name or ''}".strip()

        counter = 1
        original_username = username
        while True:
            existing = await db.execute(
                select(User).where(User.username == username)
            )
            if not existing.scalar_one_or_none():
                break
            username = f"{original_username}_{counter}"
            counter += 1

        new_user = User(
            email=email,
            username=username,
            telegram_id=str(telegram_id),
            telegram_username=telegram_username,
            full_name=full_name,
            hashed_password=hash_password(""),
            is_verified=True,
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user, None

    @staticmethod
    def generate_tokens(user_id: UUID) -> dict:
        access_token = create_access_token(
            subject=user_id,
            expires_delta=timedelta(hours=settings.jwt_expiration_hours),
            secret_key=settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        refresh_token = create_refresh_token(
            subject=user_id,
            expires_delta=timedelta(days=settings.refresh_token_expiration_days),
            secret_key=settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.jwt_expiration_hours * 3600,
        }

    @staticmethod
    def verify_token(token: str) -> Optional[UUID]:
        payload = decode_token(
            token,
            secret_key=settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        if payload:
            try:
                return UUID(payload.get("sub"))
            except (ValueError, TypeError):
                return None
        return None

    @staticmethod
    async def refresh_access_token(
        db: AsyncSession,
        refresh_token: str,
    ) -> Tuple[Optional[str], Optional[str]]:
        payload = decode_token(
            refresh_token,
            secret_key=settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        if not payload or payload.get("type") != "refresh":
            return None, "Invalid refresh token"

        try:
            user_id = UUID(payload.get("sub"))
        except (ValueError, TypeError):
            return None, "Invalid token payload"

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            return None, "User not found or inactive"

        new_access_token = create_access_token(
            subject=user_id,
            expires_delta=timedelta(hours=settings.jwt_expiration_hours),
            secret_key=settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        return new_access_token, None
