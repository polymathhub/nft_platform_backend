import logging
import json
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Request, Body, Path
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from app.database import get_db_session
from app.utils.auth import get_current_user
from app.models import User, UserRole, AdminSettings
from app.services.admin_service import AdminService
from app.config import get_settings
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])
class AdminLoginRequest(BaseModel):
    password: str = Field(..., min_length=1)
class AdminLoginResponse(BaseModel):
    success: bool
    message: str
    token: str | None = None
class CommissionSettingsRequest(BaseModel):
    rate: Decimal = Field(..., ge=0, le=100)
    wallet: str = Field(..., min_length=20)
    blockchain: str = Field(default="ethereum")
class CommissionSettingsResponse(BaseModel):
    rate: Decimal
    wallet: str
    blockchain: str
    last_updated_at: str | None = None
class CommissionWalletRequest(BaseModel):
    blockchain: str
    wallet: str = Field(..., min_length=20)
class CommissionWalletResponse(BaseModel):
    blockchain: str
    wallet: str
    updated_at: str | None = None
class AdminUserRequest(BaseModel):
    user_id: UUID
class AdminActionRequest(BaseModel):
    user_id: UUID
    reason: str | None = None
class AuditLogResponse(BaseModel):
    id: str
    admin_id: str
    action: str
    target_user_id: str | None
    description: str
    created_at: str
class SystemStatsResponse(BaseModel):
    users: int
    admins: int
    nfts: int
    listings: int
    wallets: int
    orders: int
class BackupDataResponse(BaseModel):
    success: bool
    message: str
    backup_timestamp: str
    data: dict | None = None
async def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.user_role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user
def get_client_ip(request: Request) -> str:
    if request.client:
        return request.client.host
    return "unknown"
@router.post("/login")
async def admin_login(
    request: AdminLoginRequest,
    db: AsyncSession = Depends(get_db_session),
) -> AdminLoginResponse:
    settings = get_settings()
    if request.password != settings.admin_password:
        logger.warning(f"Failed admin login attempt with wrong password")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin password",
        )
    import hashlib
    token = hashlib.sha256(request.password.encode()).hexdigest()
    return AdminLoginResponse(
        success=True,
        message="Admin authenticated successfully",
        token=token,
    )
@router.get("/commission-settings")
async def get_commission_settings(
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(get_admin_user),
) -> dict:
    settings = get_settings()
    return {
        "rate": settings.commission_rate,
        "wallets": {
            "ton": settings.commission_wallet_ton,
            "trc20": settings.commission_wallet_trc20,
            "erc20": settings.commission_wallet_erc20,
            "solana": settings.commission_wallet_solana,
        },
    }
@router.post("/commission-rate")
async def update_commission_rate(
    rate: Decimal = Body(..., ge=0, le=100),
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(get_admin_user),
    http_request: Request = None,
) -> dict:
    try:
        if not 0 <= rate <= 100:
            raise ValueError("Commission rate must be between 0 and 100")
        settings = await AdminService.update_commission_rate(
            db=db,
            admin_id=admin.id,
            new_rate=rate,
            ip_address=get_client_ip(http_request) if http_request else None,
        )
        logger.warning(f"Commission rate updated to {rate}% by admin {admin.username}")
        return {
            "success": True,
            "message": f"Commission rate updated to {float(rate)}%",
            "rate": float(settings.commission_rate),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
@router.post("/commission-wallet/{blockchain}")
async def update_commission_wallet_for_blockchain(
    blockchain: str = Path(...),
    wallet: str = Body(..., min_length=20),
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(get_admin_user),
    http_request: Request = None,
) -> dict:
    try:
        settings = await AdminService.update_commission_wallet(
            db=db,
            admin_id=admin.id,
            blockchain=blockchain.lower(),
            new_wallet=wallet,
            ip_address=get_client_ip(http_request) if http_request else None,
        )
        logger.warning(f"Commission wallet for {blockchain} updated to {wallet} by admin {admin.username}")
        return {
            "success": True,
            "message": f"Commission wallet for {blockchain} updated successfully",
            "blockchain": blockchain,
            "wallet": wallet,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
@router.post("/users/{user_id}/make-admin")
async def make_user_admin(
    user_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(get_admin_user),
    http_request: Request = None,
) -> dict:
    try:
        user = await AdminService.promote_user_to_admin(
            db=db,
            admin_id=admin.id,
            user_id=user_id,
            ip_address=get_client_ip(http_request) if http_request else None,
        )
        return {
            "success": True,
            "user_id": str(user.id),
            "username": user.username,
            "role": user.user_role.value,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
@router.post("/users/{user_id}/remove-admin")
async def remove_user_admin(
    user_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(get_admin_user),
    http_request: Request = None,
) -> dict:
    try:
        user = await AdminService.demote_admin_to_user(
            db=db,
            admin_id=admin.id,
            user_id=user_id,
            ip_address=get_client_ip(http_request) if http_request else None,
        )
        return {
            "success": True,
            "user_id": str(user.id),
            "username": user.username,
            "role": user.user_role.value,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
@router.post("/users/{user_id}/suspend")
async def suspend_user(
    user_id: UUID,
    reason: str = "No reason provided",
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(get_admin_user),
    http_request: Request = None,
) -> dict:
    try:
        user = await AdminService.suspend_user(
            db=db,
            admin_id=admin.id,
            user_id=user_id,
            reason=reason,
            ip_address=get_client_ip(http_request) if http_request else None,
        )
        return {
            "success": True,
            "user_id": str(user.id),
            "username": user.username,
            "is_active": user.is_active,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(get_admin_user),
    http_request: Request = None,
) -> dict:
    try:
        user = await AdminService.activate_user(
            db=db,
            admin_id=admin.id,
            user_id=user_id,
            ip_address=get_client_ip(http_request) if http_request else None,
        )
        return {
            "success": True,
            "user_id": str(user.id),
            "username": user.username,
            "is_active": user.is_active,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
@router.get("/admins")
async def get_all_admins(
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(get_admin_user),
) -> dict:
    admins = await AdminService.get_all_admins(db)
    return {
        "count": len(admins),
        "admins": [
            {
                "id": str(a.id),
                "username": a.username,
                "email": a.email,
                "created_at": a.created_at.isoformat(),
            }
            for a in admins
        ],
    }
@router.get("/stats")
async def get_system_stats(
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(get_admin_user),
) -> dict:
    stats = await AdminService.get_system_stats(db)
    return stats
@router.get("/audit-logs")
async def get_audit_logs(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(get_admin_user),
) -> dict:
    logs, total = await AdminService.get_audit_logs(
        db=db,
        skip=skip,
        limit=limit,
    )
    return {
        "total": total,
        "page": skip // limit + 1 if limit > 0 else 1,
        "per_page": limit,
        "logs": [
            {
                "id": str(log.id),
                "admin_id": str(log.admin_id),
                "action": log.action.value,
                "description": log.description,
                "target_user_id": str(log.target_user_id) if log.target_user_id else None,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
    }
@router.post("/backup/export")
async def export_backup(
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(get_admin_user),
) -> BackupDataResponse:
    try:
        backup_data = await AdminService.export_backup_data(db)
        return BackupDataResponse(
            success=True,
            message="Backup exported successfully",
            backup_timestamp=datetime.utcnow().isoformat(),
            data=backup_data,
        )
    except Exception as e:
        logger.error(f"Backup export failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backup export failed: {str(e)}",
        )
@router.post("/health-check")
async def admin_health_check(
    db: AsyncSession = Depends(get_db_session),
    admin: User = Depends(get_admin_user),
) -> dict:
    try:
        from sqlalchemy import text
        await db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed",
        )
