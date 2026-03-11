"""TON Wallet integration router - handles TonConnect integration and wallet management."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime
import uuid
import logging
from typing import Optional

from app.database import get_db
from app.models import User, TONWallet, TONWalletStatus, StarTransaction
from app.security.auth import get_current_user
from app.utils.logger import logger
from app.config import get_settings

router = APIRouter(prefix="/api/v1/wallet/ton", tags=["TON Wallet"])

# Simple in-memory session store for TonConnect demo/testing purposes.
# In production this should be persisted in a database or Redis and cleaned up appropriately.
_TON_SESSIONS: dict = {}

# ========== SCHEMAS ==========

class TONConnectRequest(BaseModel):
    """Request to initiate TON wallet connection."""
    manifest: Optional[dict] = None


class TONConnectCallback(BaseModel):
    """Callback data from TON Connect."""
    session_id: str
    wallet_address: str
    tonconnect_session: dict
    wallet_metadata: Optional[dict] = None


class TONWalletStatus(BaseModel):
    """Status of TON wallet connection."""
    is_connected: bool
    wallet_address: Optional[str] = None
    status: Optional[str] = None
    connected_at: Optional[datetime] = None


class TONWalletResponse(BaseModel):
    """Response with TON wallet details."""
    id: str
    user_id: str
    wallet_address: str
    status: str
    is_primary: bool
    connected_at: Optional[datetime] = None


class DisconnectTONWalletRequest(BaseModel):
    """Request to disconnect TON wallet."""
    wallet_id: str


# ========== ENDPOINTS ==========

@router.post("/connect-request")
async def initiate_ton_connection(
    request: TONConnectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Initiate TON Wallet connection using TonConnect.
    Returns connection URL for client to open.
    """
    try:
        settings = get_settings()

        # Generate unique session ID
        session_id = f"ton_{uuid.uuid4().hex[:12]}"

        # Build manifest URL using configured Telegram WebApp origin (or fallback to configured APP_URL)
        from urllib.parse import urlparse
        configured = getattr(settings, "telegram_webapp_url", None) or getattr(settings, "APP_URL", None)
        manifest_origin = None
        if configured:
            parsed = urlparse(configured)
            if parsed.scheme and parsed.netloc:
                manifest_origin = f"{parsed.scheme}://{parsed.netloc}"

        # Fallback to server settings host/port if no configured origin available
        if not manifest_origin:
            manifest_origin = f"https://{settings.host}:{settings.port}" if settings.host and settings.port else ""

        manifest_url = manifest_origin.rstrip("/") + "/tonconnect-manifest.json"

        # NOTE: Proper TonConnect integration requires creating a TonConnect session and returning
        # a protocol-compliant connect URL. Here we create a simple session record so the frontend
        # can poll for the connection result. Replace with production session management later.
        # Create a session entry so frontend can poll for updates
        _TON_SESSIONS[session_id] = {
            "status": "pending",
            "wallet_address": None,
            "created_at": datetime.utcnow().isoformat(),
        }

        return {
            "success": True,
            "session_id": session_id,
            "manifest": manifest_url,
            "connect_url": None,
            "message": "Initiated TON connection session. Use TonConnect UI on client to proceed."
        }
        
    except Exception as e:
        logger.error(f"Error initiating TON connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate TON wallet connection"
        )


@router.get('/verify')
async def verify_ton_session(session_id: str):
    """Verify session status for a TonConnect session (simple polling endpoint)."""
    rec = _TON_SESSIONS.get(session_id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Session not found')
    return {
        'success': True,
        'session_id': session_id,
        'status': rec.get('status'),
        'wallet_address': rec.get('wallet_address')
    }


@router.post("/callback")
async def ton_connect_callback(
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    """
    Handle callback from TON wallet apps (Tonkeeper, Ton Wallet, etc.).
    Works with or without authentication - creates user if needed.
    """
    try:
        # Get request body
        body = await request.json()
        wallet_address = body.get('wallet_address')
        tonconnect_session = body.get('tonconnect_session', {})
        wallet_metadata = body.get('wallet_metadata', {})
        
        if not wallet_address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Wallet address is required"
            )
        
        # Validate wallet address format (TON addresses start with 0: or -1:)
        if not (wallet_address.startswith('0:') or wallet_address.startswith('-1:')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid TON wallet address format"
            )
        
        # Check if wallet already connected
        existing_wallet = db.execute(
            select(TONWallet).where(
                TONWallet.wallet_address == wallet_address
            )
        ).scalar_one_or_none()
        
        if existing_wallet:
            # Update existing wallet connection
            existing_wallet.status = "connected"
            existing_wallet.connected_at = datetime.utcnow()
            if wallet_metadata:
                existing_wallet.wallet_metadata.update(wallet_metadata)
            db.commit()
            
            # Redirect to dashboard
            # Update session store if present
            for sid, rec in list(_TON_SESSIONS.items()):
                if rec.get("wallet_address") == wallet_address:
                    rec["status"] = "connected"
                    rec["wallet_address"] = wallet_address

            return {
                "success": True,
                "message": "TON wallet reconnected successfully",
                "wallet_address": wallet_address,
                "redirect_url": "/dashboard"
            }
        else:
            # Create new user if this is their first wallet
            from app.models import User
            from app.utils.security import create_access_token
            from app.utils.security import hash_password
            
            # Generate user account from wallet
            user_id = uuid.uuid4()
            wallet_short = wallet_address[:8]
            
            new_user = User(
                id=user_id,
                telegram_id=None,  # Will be linked later if they verify
                username=f"wallet_{wallet_short}",
                email=f"wallet_{wallet_short}@giftedforge.local",
                hashed_password=hash_password(uuid.uuid4().hex),  # Random password, not used for wallet auth
                user_role="user",
                is_verified=False
            )
            db.add(new_user)
            db.commit()
            
            # Create new wallet connection
            new_wallet = TONWallet(
                id=uuid.uuid4(),
                user_id=new_user.id,
                wallet_address=wallet_address,
                tonconnect_session_id=body.get('session_id', ''),
                status="connected",
                is_primary=True,
                connected_at=datetime.utcnow(),
                wallet_metadata={
                    **wallet_metadata,
                    "connection_timestamp": datetime.utcnow().isoformat(),
                    "wallet_type": tonconnect_session.get('wallet', 'unknown')
                }
            )
            db.add(new_wallet)
            db.commit()
            
            # Create JWT token for the user
            token = create_access_token(data={"sub": str(new_user.id)})
            
            return {
                "success": True,
                "message": "TON wallet connected successfully",
                "wallet_address": wallet_address,
                "token": token,
                "user_id": str(new_user.id),
                "redirect_url": "/dashboard"
            }
        
    except HTTPException:
            else:
    except Exception as e:
        logger.error(f"Error in TON wallet callback: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect TON wallet: {str(e)}"
        )


@router.get("/status")
async def get_ton_wallet_status(

            # Update in-memory session store if session_id present in body
            session_id = body.get('session_id')
            if session_id and session_id in _TON_SESSIONS:
                _TON_SESSIONS[session_id]['status'] = 'connected'
                _TON_SESSIONS[session_id]['wallet_address'] = wallet_address

            return {
                "success": True,
                "message": "TON wallet connected successfully",
                "wallet_address": wallet_address,
                "redirect_url": "/dashboard"
            }
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get current TON wallet connection status."""
    try:
        wallet = db.execute(
            select(TONWallet).where(
                (TONWallet.user_id == current_user.id) &
                (TONWallet.is_primary == True)
            )
        ).scalar_one_or_none()
        
        if not wallet:
            return {
                "is_connected": False,
                "wallet_address": None,
                "status": None
            }
        
        return {
            "is_connected": wallet.status == TONWalletStatus.CONNECTED,
            "wallet_address": wallet.wallet_address,
            "status": wallet.status,
            "connected_at": wallet.connected_at
        }
        
    except Exception as e:
        logger.error(f"Error getting TON wallet status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get wallet status"
        )


@router.get("/list")
async def list_ton_wallets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """List all connected TON wallets for the current user."""
    try:
        wallets = db.execute(
            select(TONWallet).where(TONWallet.user_id == current_user.id)
        ).scalars().all()
        
        return {
            "success": True,
            "wallets": [
                {
                    "id": str(w.id),
                    "wallet_address": w.wallet_address,
                    "status": w.status,
                    "is_primary": w.is_primary,
                    "connected_at": w.connected_at
                }
                for w in wallets
            ]
        }
        
    except Exception as e:
        logger.error(f"Error listing TON wallets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list wallets"
        )


@router.post("/disconnect/{wallet_id}")
async def disconnect_ton_wallet(
    wallet_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Disconnect a TON wallet."""
    try:
        wallet = db.execute(
            select(TONWallet).where(
                (TONWallet.id == uuid.UUID(wallet_id)) &
                (TONWallet.user_id == current_user.id)
            )
        ).scalar_one_or_none()
        
        if not wallet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Wallet not found"
            )
        
        wallet.status = TONWalletStatus.DISCONNECTED
        wallet.disconnected_at = datetime.utcnow()
        db.commit()
        
        return {
            "success": True,
            "message": "Wallet disconnected successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting TON wallet: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disconnect wallet"
        )
