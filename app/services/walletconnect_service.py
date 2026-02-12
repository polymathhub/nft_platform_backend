"""WalletConnect service for managing external wallet connections via WalletConnect protocol."""

import logging
import hashlib
from typing import Optional, Dict, Any, Tuple, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User, Wallet
from app.models.wallet import BlockchainType
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class WalletConnectService:
    """Service for managing WalletConnect integrations."""

    # WalletConnect session storage (in production, use Redis/DB)
    _sessions: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def generate_connection_uri() -> str:
        """Generate a unique WalletConnect connection URI."""
        import uuid
        session_id = str(uuid.uuid4())
        return f"wc:{session_id}@2?relay-protocol=irn&symKey={hashlib.sha256(session_id.encode()).hexdigest()}"

    @staticmethod
    async def create_wallet_from_connection(
        db: AsyncSession,
        user_id: UUID,
        wallet_address: str,
        blockchain: str,
        wallet_name: Optional[str] = None,
        chain_id: Optional[str] = None,
    ) -> Tuple[Optional[Wallet], Optional[str]]:
        """Create a wallet from WalletConnect connection."""
        try:
            from app.services.wallet_service import WalletService

            # Validate blockchain
            try:
                blockchain_type = BlockchainType(blockchain.lower())
            except ValueError:
                return None, f"Unsupported blockchain: {blockchain}"

            # Check if wallet already exists
            result = await db.execute(
                select(Wallet).where(
                    (Wallet.user_id == user_id)
                    & (Wallet.address == wallet_address)
                    & (Wallet.blockchain == blockchain_type)
                )
            )
            existing_wallet = result.scalar_one_or_none()

            if existing_wallet:
                return existing_wallet, None

            # Create new wallet
            wallet_name = wallet_name or f"{blockchain.capitalize()} Wallet"

            wallet, error = await WalletService.import_wallet(
                db=db,
                user_id=user_id,
                blockchain=blockchain,
                address=wallet_address,
                name=wallet_name,
                private_key="",  # No private key for WalletConnect
                metadata={"source": "walletconnect", "chain_id": chain_id},
            )

            return wallet, error

        except Exception as e:
            logger.error(f"Error creating wallet from WalletConnect: {e}")
            return None, str(e)

    @staticmethod
    async def verify_wallet_signature(
        wallet_address: str,
        message: str,
        signature: str,
        blockchain: str,
    ) -> bool:
        """Verify wallet ownership via signature."""
        try:
            if blockchain.lower() == "ethereum":
                from eth_account.messages import encode_defunct
                from eth_account import Account

                message_hash = encode_defunct(text=message)
                recovered_address = Account.recover_message(message_hash, signature=signature)
                return recovered_address.lower() == wallet_address.lower()

            elif blockchain.lower() == "solana":
                # Solana signature verification
                from nacl.signing import VerifyKey
                from nacl.exceptions import BadSignatureError

                try:
                    verify_key = VerifyKey(wallet_address)
                    verify_key.verify(message.encode(), bytes.fromhex(signature))
                    return True
                except BadSignatureError:
                    return False

            else:
                logger.warning(f"Signature verification not implemented for {blockchain}")
                return True

        except Exception as e:
            logger.error(f"Error verifying wallet signature: {e}")
            return False

    @staticmethod
    async def get_user_connected_wallets(
        db: AsyncSession, user_id: UUID
    ) -> List[Dict[str, Any]]:
        """Get all WalletConnect-connected wallets for a user."""
        result = await db.execute(
            select(Wallet).where(Wallet.user_id == user_id)
        )
        wallets = result.scalars().all()

        return [
            {
                "id": str(wallet.id),
                "address": wallet.address,
                "blockchain": wallet.blockchain.value,
                "name": wallet.name,
                "is_primary": wallet.is_primary,
                "source": wallet.metadata.get("source") if wallet.metadata else None,
                "created_at": wallet.created_at.isoformat(),
            }
            for wallet in wallets
        ]

    @staticmethod
    async def disconnect_wallet(
        db: AsyncSession, user_id: UUID, wallet_id: UUID
    ) -> Tuple[bool, Optional[str]]:
        """Disconnect a WalletConnect wallet."""
        try:
            from app.services.wallet_service import WalletService

            result = await db.execute(
                select(Wallet).where(
                    (Wallet.id == wallet_id) & (Wallet.user_id == user_id)
                )
            )
            wallet = result.scalar_one_or_none()

            if not wallet:
                return False, "Wallet not found"

            # Delete wallet
            await db.delete(wallet)
            await db.commit()

            return True, None

        except Exception as e:
            logger.error(f"Error disconnecting wallet: {e}")
            return False, str(e)

    @staticmethod
    def store_session(session_id: str, data: Dict[str, Any]) -> None:
        """Store WalletConnect session data."""
        WalletConnectService._sessions[session_id] = data

    @staticmethod
    def get_session(session_id: str) -> Optional[Dict[str, Any]]:
        """Get WalletConnect session data."""
        return WalletConnectService._sessions.get(session_id)

    @staticmethod
    def remove_session(session_id: str) -> None:
        """Remove WalletConnect session."""
        if session_id in WalletConnectService._sessions:
            del WalletConnectService._sessions[session_id]

    @staticmethod
    async def list_connected_chains(
        db: AsyncSession, user_id: UUID
    ) -> Dict[str, bool]:
        """Get list of blockchains user has connected wallets for."""
        result = await db.execute(
            select(Wallet).where(Wallet.user_id == user_id)
        )
        wallets = result.scalars().all()

        connected = {}
        for blockchains in ["ethereum", "solana", "polygon", "bitcoin", "ton"]:
            connected[blockchains] = any(
                w.blockchain.value == blockchains for w in wallets
            )

        return connected
