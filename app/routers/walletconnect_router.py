"""WalletConnect Router - REST API endpoints for external wallet connections."""

import logging
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db_session
from app.models import User
from app.services.walletconnect_service import WalletConnectService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/walletconnect", tags=["walletconnect"])


class WalletConnectRequest(BaseModel):
    """Request to connect a wallet via WalletConnect."""

    user_id: str
    wallet_address: str
    blockchain: str
    wallet_name: Optional[str] = None
    chain_id: Optional[str] = None
    signature: Optional[str] = None
    message: Optional[str] = None


class DisconnectWalletRequest(BaseModel):
    """Request to disconnect a wallet."""

    user_id: str
    wallet_id: str


@router.post("/initiate")
async def initiate_walletconnect(
    user_id: str,
    blockchain: str,
) -> dict:
    """
    Initiate a WalletConnect connection.
    Returns a connection URI for the client to scan.
    """
    try:
        uri = WalletConnectService.generate_connection_uri()

        # Store session data
        session_data = {
            "user_id": user_id,
            "blockchain": blockchain,
            "status": "pending",
            "uri": uri,
        }
        session_id = uri.split(":")[1].split("@")[0]
        WalletConnectService.store_session(session_id, session_data)

        return {
            "success": True,
            "session_id": session_id,
            "uri": uri,
            "blockchain": blockchain,
            "message": f"Please scan the QR code to connect your {blockchain} wallet",
        }
    except Exception as e:
        logger.error(f"Error initiating WalletConnect: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate connection: {str(e)}",
        )


@router.post("/connect")
async def connect_wallet(
    request: WalletConnectRequest,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Connect a wallet via WalletConnect.
    The wallet address is verified before creating the connection.
    """
    try:
        # Verify user exists
        from sqlalchemy import select

        result = await db.execute(select(User).where(User.id == UUID(request.user_id)))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Verify signature if provided
        if request.signature and request.message:
            is_valid = await WalletConnectService.verify_wallet_signature(
                wallet_address=request.wallet_address,
                message=request.message,
                signature=request.signature,
                blockchain=request.blockchain,
            )

            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Wallet signature verification failed",
                )

        # Create wallet from connection
        wallet, error = await WalletConnectService.create_wallet_from_connection(
            db=db,
            user_id=UUID(request.user_id),
            wallet_address=request.wallet_address,
            blockchain=request.blockchain,
            wallet_name=request.wallet_name,
            chain_id=request.chain_id,
        )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to connect wallet: {error}",
            )

        return {
            "success": True,
            "wallet": {
                "id": str(wallet.id),
                "address": wallet.address,
                "blockchain": wallet.blockchain.value,
                "name": wallet.name,
                "is_primary": wallet.is_primary,
            },
            "message": f"Successfully connected {request.blockchain} wallet!",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error connecting wallet: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect wallet: {str(e)}",
        )


@router.post("/disconnect")
async def disconnect_wallet(
    request: DisconnectWalletRequest,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Disconnect a wallet from the user's account."""
    try:
        success, error = await WalletConnectService.disconnect_wallet(
            db=db,
            user_id=UUID(request.user_id),
            wallet_id=UUID(request.wallet_id),
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error or "Failed to disconnect wallet",
            )

        return {
            "success": True,
            "message": "Wallet disconnected successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting wallet: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect wallet: {str(e)}",
        )


@router.get("/connected")
async def get_connected_wallets(
    user_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Get all connected wallets for a user."""
    try:
        # Verify user exists
        result = await db.execute(select(User).where(User.id == UUID(user_id)))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        wallets = await WalletConnectService.get_user_connected_wallets(
            db=db, user_id=UUID(user_id)
        )

        return {
            "success": True,
            "wallets": wallets,
            "count": len(wallets),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting connected wallets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get wallets: {str(e)}",
        )


@router.get("/chains")
async def get_connected_chains(
    user_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Check which blockchains the user has wallets connected to."""
    try:
        result = await db.execute(select(User).where(User.id == UUID(user_id)))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        chains = await WalletConnectService.list_connected_chains(
            db=db, user_id=UUID(user_id)
        )

        return {
            "success": True,
            "chains": chains,
            "available_blockchains": [
                "ethereum",
                "solana",
                "polygon",
                "bitcoin",
                "ton",
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting connected chains: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chains: {str(e)}",
        )


@router.post("/verify-connection")
async def verify_connection(
    session_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Verify if a WalletConnect session has been approved."""
    try:
        session = WalletConnectService.get_session(session_id)

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )

        return {
            "success": True,
            "session_id": session_id,
            "status": session.get("status"),
            "blockchain": session.get("blockchain"),
            "wallet_address": session.get("wallet_address"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify: {str(e)}",
        )
