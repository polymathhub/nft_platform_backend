"""Admin service for managing platform settings and audit logs."""

import logging
import json
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models import User, UserRole, AdminLog, AdminLogAction, AdminSettings
from app.config import get_settings

logger = logging.getLogger(__name__)


class AdminService:
    """Service for admin operations and auditing."""

    @staticmethod
    async def get_or_create_admin_settings(db: AsyncSession) -> AdminSettings:
        """Get or create singleton admin settings."""
        result = await db.execute(select(AdminSettings))
        settings = result.scalars().first()
        
        if not settings:
            settings = AdminSettings(
                commission_rate=Decimal("2.0"),
                commission_wallet="",
                commission_blockchain="ethereum",
            )
            db.add(settings)
            await db.commit()
            await db.refresh(settings)
        
        return settings

    @staticmethod
    async def log_admin_action(
        db: AsyncSession,
        admin_id: UUID,
        action: AdminLogAction,
        description: str,
        target_user_id: UUID | None = None,
        target_resource_id: str | None = None,
        resource_type: str | None = None,
        old_value: dict | None = None,
        new_value: dict | None = None,
        ip_address: str | None = None,
    ) -> AdminLog:
        """Log an admin action for audit trail."""
        log = AdminLog(
            admin_id=admin_id,
            action=action,
            target_user_id=target_user_id,
            target_resource_id=target_resource_id,
            resource_type=resource_type,
            description=description,
            old_value=json.dumps(old_value) if old_value else None,
            new_value=json.dumps(new_value) if new_value else None,
            ip_address=ip_address,
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        logger.info(f"Admin action logged: {action.value} by {admin_id}")
        return log

    @staticmethod
    async def get_audit_logs(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        admin_id: UUID | None = None,
        action: AdminLogAction | None = None,
    ) -> tuple[list[AdminLog], int]:
        """Get audit logs with optional filters."""
        query = select(AdminLog)
        
        if admin_id:
            query = query.where(AdminLog.admin_id == admin_id)
        if action:
            query = query.where(AdminLog.action == action)
        
        count_result = await db.execute(select(len(query)))
        
        logs = await db.execute(
            query.order_by(desc(AdminLog.created_at)).offset(skip).limit(limit)
        )
        return logs.scalars().all(), count_result.scalar()

    @staticmethod
    async def update_commission_rate(
        db: AsyncSession,
        admin_id: UUID,
        new_rate: Decimal,
        ip_address: str | None = None,
    ) -> AdminSettings:
        """Update platform commission rate (0-100%)."""
        if not 0 <= new_rate <= 100:
            raise ValueError("Commission rate must be between 0 and 100")
        
        settings = await AdminService.get_or_create_admin_settings(db)
        old_rate = settings.commission_rate
        
        settings.commission_rate = new_rate
        settings.updated_by = admin_id
        settings.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(settings)
        
        # Log action
        await AdminService.log_admin_action(
            db=db,
            admin_id=admin_id,
            action=AdminLogAction.COMMISSION_RATE_UPDATED,
            description=f"Commission rate changed from {old_rate}% to {new_rate}%",
            old_value={"rate": float(old_rate)},
            new_value={"rate": float(new_rate)},
            ip_address=ip_address,
        )
        
        logger.info(f"Commission rate updated to {new_rate}% by admin {admin_id}")
        return settings

    @staticmethod
    async def update_commission_wallet(
        db: AsyncSession,
        admin_id: UUID,
        new_wallet: str,
        blockchain: str = "ethereum",
        ip_address: str | None = None,
    ) -> AdminSettings:
        """Update commission wallet address."""
        if not new_wallet or len(new_wallet) < 20:
            raise ValueError("Invalid wallet address")
        
        settings = await AdminService.get_or_create_admin_settings(db)
        old_wallet = settings.commission_wallet
        old_blockchain = settings.commission_blockchain
        
        settings.commission_wallet = new_wallet
        settings.commission_blockchain = blockchain
        settings.updated_by = admin_id
        settings.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(settings)
        
        # Log action
        await AdminService.log_admin_action(
            db=db,
            admin_id=admin_id,
            action=AdminLogAction.COMMISSION_WALLET_UPDATED,
            description=f"Commission wallet changed from {old_blockchain} to {blockchain}",
            old_value={"wallet": old_wallet, "blockchain": old_blockchain},
            new_value={"wallet": new_wallet, "blockchain": blockchain},
            ip_address=ip_address,
        )
        
        logger.info(f"Commission wallet updated to {new_wallet} on {blockchain}")
        return settings

    @staticmethod
    async def promote_user_to_admin(
        db: AsyncSession,
        admin_id: UUID,
        user_id: UUID,
        ip_address: str | None = None,
    ) -> User:
        """Promote a user to admin role."""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValueError("User not found")
        
        if user.user_role == UserRole.ADMIN:
            raise ValueError("User is already an admin")
        
        old_role = user.user_role
        user.user_role = UserRole.ADMIN
        
        await db.commit()
        await db.refresh(user)
        
        # Log action
        await AdminService.log_admin_action(
            db=db,
            admin_id=admin_id,
            action=AdminLogAction.ADMIN_ADDED,
            description=f"User {user.username} promoted to admin",
            target_user_id=user_id,
            old_value={"role": old_role.value},
            new_value={"role": UserRole.ADMIN.value},
            ip_address=ip_address,
        )
        
        logger.info(f"User {user.username} promoted to admin by {admin_id}")
        return user

    @staticmethod
    async def demote_admin_to_user(
        db: AsyncSession,
        admin_id: UUID,
        user_id: UUID,
        ip_address: str | None = None,
    ) -> User:
        """Demote an admin to regular user role."""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValueError("User not found")
        
        if user.user_role != UserRole.ADMIN:
            raise ValueError("User is not an admin")
        
        old_role = user.user_role
        user.user_role = UserRole.USER
        
        await db.commit()
        await db.refresh(user)
        
        # Log action
        await AdminService.log_admin_action(
            db=db,
            admin_id=admin_id,
            action=AdminLogAction.ADMIN_REMOVED,
            description=f"Admin {user.username} demoted to user",
            target_user_id=user_id,
            old_value={"role": old_role.value},
            new_value={"role": UserRole.USER.value},
            ip_address=ip_address,
        )
        
        logger.info(f"Admin {user.username} demoted to user by {admin_id}")
        return user

    @staticmethod
    async def suspend_user(
        db: AsyncSession,
        admin_id: UUID,
        user_id: UUID,
        reason: str,
        ip_address: str | None = None,
    ) -> User:
        """Suspend a user account."""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValueError("User not found")
        
        if not user.is_active:
            raise ValueError("User is already suspended")
        
        user.is_active = False
        await db.commit()
        await db.refresh(user)
        
        # Log action
        await AdminService.log_admin_action(
            db=db,
            admin_id=admin_id,
            action=AdminLogAction.USER_SUSPENDED,
            description=f"User {user.username} suspended. Reason: {reason}",
            target_user_id=user_id,
            new_value={"reason": reason, "is_active": False},
            ip_address=ip_address,
        )
        
        logger.info(f"User {user.username} suspended by {admin_id}. Reason: {reason}")
        return user

    @staticmethod
    async def activate_user(
        db: AsyncSession,
        admin_id: UUID,
        user_id: UUID,
        ip_address: str | None = None,
    ) -> User:
        """Reactivate a suspended user account."""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValueError("User not found")
        
        if user.is_active:
            raise ValueError("User is already active")
        
        user.is_active = True
        await db.commit()
        await db.refresh(user)
        
        # Log action
        await AdminService.log_admin_action(
            db=db,
            admin_id=admin_id,
            action=AdminLogAction.USER_ACTIVATED,
            description=f"User {user.username} reactivated",
            target_user_id=user_id,
            new_value={"is_active": True},
            ip_address=ip_address,
        )
        
        logger.info(f"User {user.username} reactivated by {admin_id}")
        return user

    @staticmethod
    async def get_system_stats(db: AsyncSession) -> dict:
        """Get platform statistics."""
        from app.models import NFT, Listing, Offer, Order, Wallet
        
        # Count users
        users_result = await db.execute(select(len(select(User))))
        users_count = users_result.scalar()
        
        # Count admins
        admins_result = await db.execute(
            select(len(select(User).where(User.user_role == UserRole.ADMIN)))
        )
        admins_count = admins_result.scalar()
        
        # Count NFTs
        nfts_result = await db.execute(select(len(select(NFT))))
        nfts_count = nfts_result.scalar()
        
        # Count listings
        listings_result = await db.execute(select(len(select(Listing))))
        listings_count = listings_result.scalar()
        
        # Count wallets
        wallets_result = await db.execute(select(len(select(Wallet))))
        wallets_count = wallets_result.scalar()
        
        # Count orders
        orders_result = await db.execute(select(len(select(Order))))
        orders_count = orders_result.scalar()
        
        return {
            "users": users_count or 0,
            "admins": admins_count or 0,
            "nfts": nfts_count or 0,
            "listings": listings_count or 0,
            "wallets": wallets_count or 0,
            "orders": orders_count or 0,
        }

    @staticmethod
    async def get_all_admins(db: AsyncSession) -> list[User]:
        """Get all admin users."""
        result = await db.execute(
            select(User).where(User.user_role == UserRole.ADMIN)
        )
        return result.scalars().all()
    @staticmethod
    async def export_backup_data(db: AsyncSession) -> dict:
        """Export platform data for backup purposes."""
        from app.models import NFT, Listing, Offer, Order, Wallet, Escrow
        
        try:
            # Get all users
            users_result = await db.execute(select(User))
            users = users_result.scalars().all()
            
            # Get all NFTs
            nfts_result = await db.execute(select(NFT))
            nfts = nfts_result.scalars().all()
            
            # Get all listings
            listings_result = await db.execute(select(Listing))
            listings = listings_result.scalars().all()
            
            # Get all wallets
            wallets_result = await db.execute(select(Wallet))
            wallets = wallets_result.scalars().all()
            
            # Get all orders
            orders_result = await db.execute(select(Order))
            orders = orders_result.scalars().all()
            
            # Get all escrows
            escrows_result = await db.execute(select(Escrow))
            escrows = escrows_result.scalars().all()
            
            # Get settings
            settings = await AdminService.get_or_create_admin_settings(db)
            
            backup_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "summary": {
                    "users": len(users),
                    "nfts": len(nfts),
                    "listings": len(listings),
                    "wallets": len(wallets),
                    "orders": len(orders),
                    "escrows": len(escrows),
                },
                "users": [
                    {
                        "id": str(u.id),
                        "username": u.username,
                        "email": u.email,
                        "role": u.user_role.value,
                        "is_active": u.is_active,
                        "created_at": u.created_at.isoformat(),
                    }
                    for u in users
                ],
                "settings": {
                    "commission_rate": float(settings.commission_rate),
                    "commission_wallet": settings.commission_wallet,
                    "commission_blockchain": settings.commission_blockchain,
                },
                "stats": await AdminService.get_system_stats(db),
            }
            
            logger.info(f"Backup exported successfully with {len(users)} users")
            return backup_data
        except Exception as e:
            logger.error(f"Backup export failed: {e}", exc_info=True)
            raise