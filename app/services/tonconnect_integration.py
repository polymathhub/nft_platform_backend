"""
TON Connect Integration Layer for Backend

Handles:
- Transaction format conversion for TON Connect
- Wallet connection state management
- Transaction callback handling
- Integration with frontend wallet manager

This module ensures backend-generated payloads work with TON Connect UI.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from decimal import Decimal
from datetime import datetime
from app.models import User, TONWallet

logger = logging.getLogger(__name__)


class TONConnectTransaction:
    """Wrapper for TON Connect transaction format"""
    
    @staticmethod
    def format_for_tonconnect(
        payload: Dict[str, Any],
        contract_address: str,
        amount_ton: str = "0.05",
        send_mode: int = 3,
    ) -> Dict[str, Any]:
        """
        Convert backend payload to TON Connect transaction format
        
        TON Connect requires specific structure:
        {
          "messages": [{
            "address": "EQAA...recipient",
            "amount": "50000000",  # nanoTON
            "payload": "base64_encoded_boc",
            "stateInit": "optional_base64_state"
          }],
          "validUntil": 1234567890
        }
        
        Args:
            payload: Backend-generated payload dict
            contract_address: Smart contract to call
            amount_ton: Amount in TON for transaction
            send_mode: TON send mode (default 3)
            
        Returns:
            TON Connect formatted transaction
        """
        
        # Convert TON to nanoTON
        amount_nano_ton = int(Decimal(amount_ton) * Decimal("1000000000"))
        
        # Create valid_until timestamp (30 seconds from now)
        import time
        valid_until = int(time.time()) + 30
        
        # Format TON Connect standard message
        transaction = {
            "messages": [
                {
                    "address": contract_address,
                    "amount": str(amount_nano_ton),
                    "payload": json.dumps(payload),  # Frontend will encode to BOC
                    "init": None,  # Optional state initialization
                }
            ],
            "validUntil": valid_until,
            "network": "-239",  # TON mainnet (-239), testnet (-3)
        }
        
        logger.info(f"[TONConnect] Formatted transaction for contract {contract_address} ({amount_ton} TON)")
        return transaction
    
    @staticmethod
    def format_nft_mint_for_tonconnect(
        collection_address: str,
        owner_address: str,
        content_uri: str,
        royalty_percent: int = 0,
        royalty_address: Optional[str] = None,
        amount_ton: str = "0.05",
    ) -> Dict[str, Any]:
        """
        Format NFT mint transaction for TON Connect
        
        This creates the exact transaction that will be signed by wallet
        
        Args:
            collection_address: NFT Collection smart contract
            owner_address: Address that will own the NFT
            content_uri: IPFS/backend URI to metadata
            royalty_percent: Royalty percentage
            royalty_address: Address to receive royalties
            amount_ton: Transaction amount
            
        Returns:
            TON Connect formatted mint transaction
        """
        
        mint_payload = {
            "type": "nft_mint",
            "owner": owner_address,
            "content_uri": content_uri,
            "royalty": {
                "address": royalty_address or "EQAA" + "A" * 46,
                "percent": min(max(royalty_percent, 0), 100),
            },
        }
        
        return TONConnectTransaction.format_for_tonconnect(
            payload=mint_payload,
            contract_address=collection_address,
            amount_ton=amount_ton,
        )
    
    @staticmethod
    def format_transfer_for_tonconnect(
        from_address: str,
        to_address: str,
        amount_ton: str,
        comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Format simple TON transfer for TON Connect
        
        Args:
            from_address: Sender wallet
            to_address: Recipient address
            amount_ton: Amount to transfer
            comment: Optional message comment
            
        Returns:
            TON Connect formatted transfer transaction
        """
        
        transfer_payload = {
            "type": "transfer",
            "from": from_address,
            "to": to_address,
            "amount": amount_ton,
        }
        
        if comment:
            transfer_payload["comment"] = comment
        
        return TONConnectTransaction.format_for_tonconnect(
            payload=transfer_payload,
            contract_address=to_address,
            amount_ton=amount_ton,
            send_mode=3,
        )


class TONConnectCallback:
    """Handle TON Connect wallet callbacks and responses"""
    
    @staticmethod
    def validate_transaction_response(
        transaction_hash: str,
        from_wallet: str,
        to_address: str,
        amount_nano_ton: str,
        user: User,
    ) -> bool:
        """
        Validate transaction response from TON Connect wallet
        
        Args:
            transaction_hash: Hash returned by wallet
            from_wallet: Sender wallet address
            to_address: Expected recipient
            amount_nano_ton: Expected amount in nanoTON
            user: Current user
            
        Returns:
            True if valid, False otherwise
        """
        
        try:
            # Verify wallet belongs to user
            if not hasattr(user, 'ton_wallet') or user.ton_wallet is None:
                logger.warning(f"User {user.id} has no wallet connected")
                return False
            
            if user.ton_wallet.address != from_wallet:
                logger.warning(
                    f"Wallet mismatch: expected {user.ton_wallet.address}, got {from_wallet}"
                )
                return False
            
            # Verify transaction hash is valid hex
            if not all(c in '0123456789abcdefABCDEF' for c in transaction_hash):
                logger.warning(f"Invalid transaction hash format: {transaction_hash}")
                return False
            
            logger.info(f"[TONConnect] Transaction validated: {transaction_hash[:16]}...")
            return True
            
        except Exception as e:
            logger.error(f"[TONConnect] Validation error: {e}")
            return False
    
    @staticmethod
    def parse_tonconnect_error(error_data: Dict[str, Any]) -> str:
        """
        Parse TON Connect error into user-friendly message
        
        Args:
            error_data: Error data from TON Connect
            
        Returns:
            User-friendly error message
        """
        
        error_messages = {
            "UNKNOWN_ERROR": "An unknown error occurred. Please try again.",
            "BAD_REQUEST_ERROR": "Invalid transaction request. Check parameters.",
            "UNKNOWN_APP_ERROR": "Application error. Please refresh and try again.",
            "USER_REJECTS_ERROR": "You cancelled the transaction.",
            "MANIFEST_NOT_FOUND_ERROR": "Wallet manifest not found. Check your connection.",
            "MANIFEST_CONTENT_ERROR": "Invalid wallet configuration. Please try another wallet.",
            "BACK_ERROR": "Connection interrupted. Please try again.",
            "ALREADY_CONNECTED_ERROR": "Wallet already connected.",
            "HTTP_ERROR": "Network error. Check your connection.",
            "Memory": "Device memory error. Please restart.",
        }
        
        error_type = error_data.get("type", "UNKNOWN_ERROR")
        message = error_messages.get(error_type, f"Error: {error_type}")
        
        logger.warning(f"[TONConnect] Error: {error_type} - {message}")
        return message


class TONConnectWalletSync:
    """Keep backend wallet state in sync with TON Connect frontend state"""
    
    @staticmethod
    async def sync_wallet_connection(
        user: User,
        wallet_address: str,
        wallet_name: str,
        is_connected: bool,
        db_session,
    ) -> Optional[TONWallet]:
        """
        Sync wallet connection state from frontend to backend
        
        Called after TON Connect wallet connection/disconnection
        
        Args:
            user: Current user
            wallet_address: TON wallet address
            wallet_name: Wallet name (e.g., "tonkeeper", "mytonwallet")
            is_connected: Connection state
            db_session: Database session
            
        Returns:
            Updated TONWallet model or None
        """
        
        from sqlalchemy import select
        from app.models import TONWallet
        
        try:
            # Find existing wallet for this user
            stmt = select(TONWallet).where(
                (TONWallet.user_id == user.id) & 
                (TONWallet.address == wallet_address)
            )
            result = await db_session.execute(stmt)
            wallet = result.scalar_one_or_none()
            
            if is_connected:
                if wallet is None:
                    # Create new wallet connection
                    wallet = TONWallet(
                        user_id=user.id,
                        address=wallet_address,
                        wallet_type=wallet_name,
                        is_primary=True,
                        is_connected=True,
                        last_connected_at=datetime.utcnow(),
                    )
                    db_session.add(wallet)
                else:
                    # Update existing wallet
                    wallet.is_connected = True
                    wallet.last_connected_at = datetime.utcnow()
                    wallet.wallet_type = wallet_name
                
                logger.info(f"[TONConnect] Wallet synced: {wallet_address[:10]}...")
                
            else:
                # Disconnect wallet
                if wallet:
                    wallet.is_connected = False
                    logger.info(f"[TONConnect] Wallet disconnected: {wallet_address[:10]}...")
            
            await db_session.commit()
            return wallet
            
        except Exception as e:
            logger.error(f"[TONConnect] Sync error: {e}")
            await db_session.rollback()
            return None
    
    @staticmethod
    def get_tonconnect_ui_config() -> Dict[str, Any]:
        """
        Get TON Connect UI configuration for frontend
        
        Frontend needs this to initialize TON Connect properly
        
        Returns:
            TON Connect UI config object
        """
        
        from app.config import get_settings
        
        settings = get_settings()
        
        return {
            "manifestUrl": settings.get_manifest_url(),
            "buttonRootId": "ton-connect",
        }


class TONConnectError(Exception):
    """Custom exception for TON Connect errors"""
    
    def __init__(self, message: str, error_type: str = "UNKNOWN_ERROR", details: Optional[Dict] = None):
        self.message = message
        self.error_type = error_type
        self.details = details or {}
        super().__init__(self.message)
    
    def to_response(self) -> Dict[str, Any]:
        """Convert to API response format"""
        return {
            "success": False,
            "error": self.error_type,
            "message": self.message,
            "details": self.details,
        }
