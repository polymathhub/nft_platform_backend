import uuid
import logging
from typing import Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.models import User
from app.models.ton_wallet import TONWallet, TONWalletStatus
from app.schemas.auth_unified import IdentityData, InitDataSource
from app.utils.security import hash_password
logger = logging.getLogger(__name__)
class UnifiedUserService:
    @staticmethod
    async def get_or_create_user_from_identity(
        db: AsyncSession,
        identity: IdentityData,
    ) -> Tuple[Optional[User], Optional[str]]:
        try:
            if identity.source == InitDataSource.TELEGRAM:
                return await UnifiedUserService._get_or_create_telegram_user(db, identity)
            elif identity.source == InitDataSource.TON_CONNECT:
                return await UnifiedUserService._get_or_create_ton_user(db, identity)
            else:
                return None, f"Unsupported identity source: {identity.source}"
        except Exception as e:
            logger.error(f"Error getting/creating user from identity: {e}", exc_info=True)
            return None, f"User creation failed: {str(e)}"
    @staticmethod
    async def _get_or_create_telegram_user(
        db: AsyncSession,
        identity: IdentityData,
    ) -> Tuple[Optional[User], Optional[str]]:
        try:
            telegram_id = identity.telegram_id
            if not telegram_id:
                logger.error("Missing Telegram ID in identity")
                return None, "Missing Telegram ID"
            
            logger.info(f"[Telegram Auth] Looking up user by telegram_id={telegram_id}")
            result = await db.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                # Update existing user with latest Telegram data
                logger.info(f"[Telegram Auth] Found existing user: {existing_user.id}")
                updated = False
                
                # Update full_name if provided
                if identity.first_name or identity.last_name:
                    new_full_name = f"{identity.first_name or ''} {identity.last_name or ''}".strip()
                    if new_full_name and existing_user.full_name != new_full_name:
                        existing_user.full_name = new_full_name
                        logger.info(f"[Telegram Auth] Updated full_name to: {new_full_name}")
                        updated = True
                
                # Update telegram_username if changed
                if identity.telegram_username and existing_user.telegram_username != identity.telegram_username:
                    existing_user.telegram_username = identity.telegram_username
                    logger.info(f"[Telegram Auth] Updated telegram_username to: {identity.telegram_username}")
                    updated = True
                
                # Update avatar_url if provided
                if identity.avatar_url and existing_user.avatar_url != identity.avatar_url:
                    existing_user.avatar_url = identity.avatar_url
                    logger.info(f"[Telegram Auth] Updated avatar_url")
                    updated = True
                
                if updated:
                    existing_user.updated_at = datetime.utcnow()
                    db.add(existing_user)
                    await db.commit()
                    logger.info(f"[Telegram Auth] User updated: {existing_user.id}")
                
                return existing_user, None
            
            # Create new Telegram user
            user_id = uuid.uuid4()
            # USERNAME GENERATION FIX: Use telegram_username if available, else fallback to tg_ID
            username = identity.telegram_username.strip() if identity.telegram_username else f"tg_{telegram_id}"
            email = f"telegram_{telegram_id}@giftedforge.local"
            full_name = f"{identity.first_name or ''} {identity.last_name or ''}".strip()
            
            logger.warning(f"[Telegram Auth] Creating new user - username='{username}' (from_telegram={bool(identity.telegram_username)}) | telegram_id={telegram_id} | email={email} | full_name={full_name}")
            
            new_user = User(
                id=user_id,
                telegram_id=telegram_id,
                telegram_username=identity.telegram_username,
                username=username,
                email=email,
                hashed_password=hash_password(uuid.uuid4().hex),
                full_name=full_name or None,
                avatar_url=identity.avatar_url,  # Store avatar URL from Telegram
                user_role="user",
                is_verified=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)  # Refresh to ensure all fields loaded
            # VERIFICATION LOG: Confirm all user fields were saved correctly
            logger.warning(f"[Telegram Auth] ✓ User SAVED to DB - id={new_user.id} | telegram_id={new_user.telegram_id} | username='{new_user.username}' | email={new_user.email} | full_name='{new_user.full_name}' | verified={new_user.is_verified}")
            return new_user, None
        except Exception as e:
            await db.rollback()
            logger.error(f"[Telegram Auth] Error creating Telegram user: {e}", exc_info=True)
            return None, str(e)
    @staticmethod
    async def _get_or_create_ton_user(
        db: AsyncSession,
        identity: IdentityData,
    ) -> Tuple[Optional[User], Optional[str]]:
        try:
            wallet_address = identity.ton_wallet_address
            if not wallet_address:
                return None, "Missing TON wallet address"
            result = await db.execute(
                select(TONWallet).where(TONWallet.wallet_address == wallet_address)
            )
            existing_wallet = result.scalar_one_or_none()
            if existing_wallet:
                result = await db.execute(
                    select(User).where(User.id == existing_wallet.user_id)
                )
                user = result.scalar_one_or_none()
                if user:
                    existing_wallet.status = TONWalletStatus.CONNECTED
                    existing_wallet.connected_at = datetime.utcnow()
                    if identity.ton_wallet_metadata:
                        existing_wallet.wallet_metadata = {
                            **(existing_wallet.wallet_metadata or {}),
                            **identity.ton_wallet_metadata
                        }
                    db.add(existing_wallet)
                    await db.commit()
                    logger.info(f"TON wallet reconnected: {wallet_address} -> user {user.id}")
                    return user, None
            user_id = uuid.uuid4()
            wallet_short = wallet_address[:8]
            new_user = User(
                id=user_id,
                telegram_id=None,
                username=f"wallet_{wallet_short}",
                email=f"wallet_{wallet_short}@giftedforge.local",
                hashed_password=hash_password(uuid.uuid4().hex),
                user_role="user",
                is_verified=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(new_user)
            await db.flush()
            new_wallet = TONWallet(
                id=uuid.uuid4(),
                user_id=new_user.id,
                wallet_address=wallet_address,
                tonconnect_session_id="",
                status=TONWalletStatus.CONNECTED,
                is_primary=True,
                connected_at=datetime.utcnow(),
                wallet_metadata={
                    **(identity.ton_wallet_metadata or {}),
                    "connection_timestamp": datetime.utcnow().isoformat(),
                }
            )
            db.add(new_wallet)
            await db.commit()
            logger.info(
                f"New TON user created: {new_user.id} with wallet {wallet_address}"
            )
            return new_user, None
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating TON user: {e}", exc_info=True)
            return None, str(e)
    @staticmethod
    async def link_ton_wallet_to_user(
        db: AsyncSession,
        user_id: str,
        wallet_address: str,
        wallet_metadata: Optional[dict] = None,
    ) -> Tuple[Optional[TONWallet], Optional[str]]:
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                return None, f"User not found: {user_id}"
            result = await db.execute(
                select(TONWallet).where(TONWallet.wallet_address == wallet_address)
            )
            existing = result.scalar_one_or_none()
            if existing:
                if existing.user_id == user_id:
                    return existing, None
                else:
                    return None, f"Wallet already connected to another user"
            new_wallet = TONWallet(
                id=uuid.uuid4(),
                user_id=user_id,
                wallet_address=wallet_address,
                status=TONWalletStatus.CONNECTED,
                is_primary=False,
                connected_at=datetime.utcnow(),
                wallet_metadata=wallet_metadata or {},
            )
            db.add(new_wallet)
            await db.commit()
            logger.info(f"TON wallet linked to user {user_id}: {wallet_address}")
            return new_wallet, None
        except Exception as e:
            await db.rollback()
            logger.error(f"Error linking TON wallet: {e}", exc_info=True)
            return None, str(e)
