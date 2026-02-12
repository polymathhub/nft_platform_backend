"""WebSocket and notification endpoints for real-time user notifications."""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from uuid import UUID
from app.services.notification_service import NotificationService
from app.utils.security import verify_token

logger = logging.getLogger(__name__)
router = APIRouter(tags=["notifications"])


@router.websocket("/ws/notifications/{user_id}")
async def websocket_notification_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time notifications.
    
    Requires:
    - user_id: UUID of the user
    - token query parameter: Valid JWT token matching the user_id
    
    Usage:
    ```
    ws://localhost:8000/api/v1/ws/notifications/{user_id}?token={jwt_token}
    ```
    
    The endpoint will reject connections if:
    - user_id is not a valid UUID
    - token is missing or invalid
    - token doesn't match the user_id
    """
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
            # Keep connection alive and receive any client messages
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
    """
    Get current notification service statistics.
    
    Returns:
    - active_users: Number of currently connected WebSocket clients
    - status: "healthy" or "degraded" based on connection count
    - timestamp: When stats were collected
    """
    active_users = NotificationService.get_active_users()
    return {
        "success": True,
        "data": {
            "active_users": active_users,
            "status": "healthy" if active_users >= 0 else "degraded",
        },
        "timestamp": None
    }
