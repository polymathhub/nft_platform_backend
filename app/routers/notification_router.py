import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from datetime import datetime
from app.database import get_db_session
from app.models import Notification
from app.models.user import User
from app.services.notification_service import NotificationService
from app.utils.security import verify_token
from app.utils.telegram_auth_dependency import get_current_user
logger = logging.getLogger(__name__)
router = APIRouter(tags=["notifications"])
@router.get("/notifications", tags=["notifications"], summary="Get User Notifications")
async def get_notifications(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0,
):
    try:
        query = (
            select(Notification)
            .where(Notification.user_id == current_user.id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(query)
        notifications = result.scalars().all()
        notifications_data = [
            {
                "id": str(notif.id),
                "title": notif.title,
                "description": notif.description or "",
                "message": notif.message or notif.description or "",
                "subject": notif.subject or notif.title,
                "timestamp": notif.created_at.isoformat() if notif.created_at else None,
                "created_at": notif.created_at.isoformat() if notif.created_at else None,
                "read": notif.is_read,
                "is_read": notif.is_read,
                "type": notif.notification_type.value if notif.notification_type else "info",
                "action_url": notif.action_url,
            }
            for notif in notifications
        ]
        return {
            "success": True,
            "data": notifications_data,
        }
    except Exception as e:
        logger.error(f"Error getting notifications: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch notifications"
        )
@router.delete("/notifications/{notification_id}", tags=["notifications"], summary="Delete Notification")
async def delete_notification(
    notification_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    try:
        try:
            notif_uuid = UUID(notification_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid notification ID format"
            )
        query = select(Notification).where(
            (Notification.id == notif_uuid) & 
            (Notification.user_id == current_user.id)
        )
        result = await db.execute(query)
        notification = result.scalar_one_or_none()
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        await db.delete(notification)
        await db.commit()
        return {
            "success": True,
            "data": None,
            "message": "Notification deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting notification: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete notification"
        )
@router.put("/notifications/{notification_id}/read", tags=["notifications"], summary="Mark Notification as Read")
async def mark_notification_read(
    notification_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    try:
        try:
            notif_uuid = UUID(notification_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid notification ID format"
            )
        query = select(Notification).where(
            (Notification.id == notif_uuid) & 
            (Notification.user_id == current_user.id)
        )
        result = await db.execute(query)
        notification = result.scalar_one_or_none()
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        notification.is_read = True
        notification.read = True
        notification.read_at = datetime.utcnow()
        await db.commit()
        await db.refresh(notification)
        return {
            "success": True,
            "data": {
                "id": str(notification.id),
                "title": notification.title,
                "description": notification.description,
                "read": notification.is_read,
                "is_read": notification.is_read,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notification"
        )
@router.websocket("/ws/notifications/{user_id}")
async def websocket_notification_endpoint(websocket: WebSocket, user_id: str):
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid user ID format")
        logger.warning(f"Connection rejected: Invalid user ID format - {user_id}")
        return
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing authentication token")
        logger.warning(f"Connection rejected: Missing token for user {user_id}")
        return
    verified_user_id = verify_token(token)
    if not verified_user_id or verified_user_id != user_uuid:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid or expired token")
        logger.warning(f"Connection rejected: Invalid token for user {user_id}")
        return
    await websocket.accept()
    logger.info(f"WebSocket connected - user: {user_id}")
    await NotificationService.connect(user_uuid, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received message from {user_id}: {data}")
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected - user: {user_id}")
        await NotificationService.disconnect(user_uuid, websocket)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}", exc_info=True)
        await NotificationService.disconnect(user_uuid, websocket)
        try:
            await websocket.close(code=status.WS_1011_SERVER_ERROR, reason="Internal server error")
        except Exception:
            pass
@router.get("/notifications/stats", tags=["notifications"], summary="Get Notification Stats")
async def get_notification_stats():
    active_users = NotificationService.get_active_users()
    return {
        "success": True,
        "data": {
            "active_users": active_users,
            "status": "healthy" if active_users >= 0 else "degraded",
        },
        "timestamp": None
    }
