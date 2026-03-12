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
import json
import redis.asyncio as redis
import asyncio

router = APIRouter(prefix="/api/v1/wallet/ton", tags=["TON Wallet"])

# Simple in-memory session store for TonConnect demo/testing purposes.
# In production this should be persisted in a database or Redis and cleaned up appropriately.
_TON_SESSIONS: dict = {}
_REDIS_CLIENT = None

async def _get_redis():
    global _REDIS_CLIENT
    if _REDIS_CLIENT:
        return _REDIS_CLIENT
    settings = get_settings()
    try:
        # redis.asyncio.from_url returns a Redis client
        _REDIS_CLIENT = redis.from_url(settings.redis_url, encoding='utf-8', decode_responses=True)
        # Test connection (awaitable)
        await _REDIS_CLIENT.ping()
        return _REDIS_CLIENT
    except Exception:
        _REDIS_CLIENT = None
        return None

async def _persist_session(session_id: str, payload: dict, expire: int = 24 * 3600):
    r = await _get_redis()
    if not r:
        # fallback to in-memory
        _TON_SESSIONS[session_id] = payload
        return
    try:
        await r.set(f"ton_session:{session_id}", json.dumps(payload))
        if expire:
            await r.expire(f"ton_session:{session_id}", expire)
    except Exception:
        _TON_SESSIONS[session_id] = payload

async def _load_session(session_id: str):
    r = await _get_redis()
    if r:
        try:
            raw = await r.get(f"ton_session:{session_id}")
            if raw:
                return json.loads(raw)
        except Exception:
            pass
    return _TON_SESSIONS.get(session_id)

async def _update_session(session_id: str, update: dict):
    rec = await _load_session(session_id)
    if not rec:
        rec = {}
    rec.update(update)
    await _persist_session(session_id, rec)

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
        session_payload = {
            "status": "pending",
            "wallet_address": None,
            "created_at": datetime.utcnow().isoformat(),
            "user_id": str(current_user.id) if current_user else None,
        }

        # Persist session (Redis if available, otherwise in-memory)
        try:
            await _persist_session(session_id, session_payload)
        except Exception:
            _TON_SESSIONS[session_id] = session_payload

        # Provide common wallet deep-links that clients can open to trigger wallet app
        connect_links = {
            "tonkeeper": f"https://app.tonkeeper.com/ton-connect?request_id={session_id}",
            "tonwallet": f"ton://connect?request_id={session_id}",
            "telegram": f"https://wallet.tg/ton-connect?request_id={session_id}",
        }

        return {
            "success": True,
            "session_id": session_id,
            "manifest": manifest_url,
            "connect_links": connect_links,
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
    rec = await _load_session(session_id)
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
    Requires Telegram initData for authentication.
    """
    try:
        import hmac
        import hashlib
        import time
        from urllib.parse import parse_qsl

        # Get request body
        body = await request.json()
        wallet_address = body.get('wallet_address')
        tonconnect_session = body.get('tonconnect_session', {})
        wallet_metadata = body.get('wallet_metadata', {})
        init_data = body.get('init_data', '')

        if not wallet_address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Wallet address is required"
            )
        if not init_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Telegram initData is required"
            )

        # Validate wallet address format (TON addresses start with 0: or -1:)
        if not (wallet_address.startswith('0:') or wallet_address.startswith('-1:')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid TON wallet address format"
            )

        # --- Telegram initData verification (HMAC, expiry) ---
        settings = get_settings()
        bot_token = getattr(settings, 'telegram_bot_token', None)
        if not bot_token:
            raise HTTPException(status_code=500, detail="Telegram bot token not configured")

        # Parse initData
        try:
            parts = dict(parse_qsl(init_data, keep_blank_values=True))
            hash_received = parts.pop('hash', None)
            auth_date = int(parts.get('auth_date', '0'))
            data_check_string = '\n'.join(f"{k}={v}" for k, v in sorted(parts.items()))
            secret_key = hashlib.sha256(bot_token.encode()).digest()
            hmac_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(hmac_hash, hash_received):
                raise HTTPException(status_code=401, detail="Telegram initData HMAC verification failed")
            # Check expiry (allow max 1 day)
            if abs(time.time() - auth_date) > 86400:
                raise HTTPException(status_code=401, detail="Telegram initData expired")
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Invalid Telegram initData: {e}")

        # --- Wallet logic (unchanged) ---
        existing_wallet = db.execute(
            select(TONWallet).where(
                TONWallet.wallet_address == wallet_address
            )
        ).scalar_one_or_none()

        if existing_wallet:
            existing_wallet.status = "connected"
            existing_wallet.connected_at = datetime.utcnow()
            if wallet_metadata:
                existing_wallet.wallet_metadata.update(wallet_metadata)
            db.commit()
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
            from app.models import User
            from app.utils.security import create_access_token, hash_password
            user_id = uuid.uuid4()
            wallet_short = wallet_address[:8]
            new_user = User(
                id=user_id,
                telegram_id=None,
                username=f"wallet_{wallet_short}",
                email=f"wallet_{wallet_short}@giftedforge.local",
                hashed_password=hash_password(uuid.uuid4().hex),
                user_role="user",
                is_verified=False
            )
            db.add(new_user)
            db.commit()
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
        raise
    except Exception as e:
        logger.error(f"Error in TON wallet callback: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect TON wallet: {str(e)}"
        )


@router.get("/status")
async def get_ton_wallet_status(
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
