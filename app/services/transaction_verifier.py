"""
Production-Grade Blockchain Transaction Verification

Handles:
- On-chain transaction verification
- Confirmation tracking (secp blocks)
- Trust level calculation
- Event listener integration
"""

import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)


class TransactionVerifier:
    """Verify transactions on TON blockchain"""
    
    # Confirmation thresholds
    MIN_CONFIRMATIONS_PENDING = 1
    MIN_CONFIRMATIONS_PROGRESS = 51
    MIN_CONFIRMATIONS_CONFIRMED = 101
    
    @staticmethod
    async def verify_transaction(
        transaction_hash: str,
        ton_center_client: Any,  # TonCenter API client
    ) -> Dict[str, Any]:
        """
        Verify a transaction on TON blockchain
        
        Args:
            transaction_hash: Transaction hash to verify
            ton_center_client: TonCenter API client
            
        Returns:
            {
                "found": bool,
                "status": "pending|in_progress|confirmed|failed|not_found",
                "confirmations": int,
                "block_time": datetime,
                "exit_code": int or None,
                "error": str or None,
            }
        """
        
        try:
            logger.info(f"[TransactionVerifier] Verifying {transaction_hash}")
            
            # Query TonCenter for transaction
            tx_data = await ton_center_client.get_transaction(transaction_hash)
            
            if not tx_data:
                logger.warning(f"[TransactionVerifier] Transaction not found: {transaction_hash}")
                return {
                    "found": False,
                    "status": "not_found",
                    "confirmations": 0,
                    "error": "Transaction not found in mempool or blockchain"
                }
            
            # Determine confirmation status
            confirmations = tx_data.get("confirmations", 0)
            
            if confirmations >= TransactionVerifier.MIN_CONFIRMATIONS_CONFIRMED:
                status = "confirmed"
            elif confirmations >= TransactionVerifier.MIN_CONFIRMATIONS_PROGRESS:
                status = "in_progress"
            else:
                status = "pending"
            
            # Check for execution failure
            exit_code = tx_data.get("exit_code")
            if exit_code is not None and exit_code != 0:
                status = "failed"
                logger.warning(f"[TransactionVerifier] Transaction failed with exit code {exit_code}")
            
            result = {
                "found": True,
                "status": status,
                "confirmations": confirmations,
                "block_time": tx_data.get("block_time"),
                "block_number": tx_data.get("block_number"),
                "exit_code": exit_code,
                "error": None,
            }
            
            logger.info(f"[TransactionVerifier] {transaction_hash} status: {status} ({confirmations} confirmations)")
            return result
            
        except Exception as e:
            logger.error(f"[TransactionVerifier] Error verifying transaction: {e}")
            return {
                "found": False,
                "status": "error",
                "confirmations": 0,
                "error": str(e),
            }
    
    @staticmethod
    def calculate_trust_level(confirmations: int) -> int:
        """
        Calculate trust level (0-10) based on confirmation count
        
        Trust increases with confirmations:
        - 0-50 confirmations: 0-2 (pending)
        - 51-100 confirmations: 3-7 (in progress)
        - 101+ confirmations: 8-10 (confirmed)
        """
        
        if confirmations < TransactionVerifier.MIN_CONFIRMATIONS_PROGRESS:
            return min(2, confirmations // 25)
        elif confirmations < TransactionVerifier.MIN_CONFIRMATIONS_CONFIRMED:
            # 51-100 maps to 3-7
            return 3 + min(4, (confirmations - 51) // 13)
        else:
            # 101+ maps to 8-10
            return min(10, 8 + (confirmations - 101) // 100)
    
    @staticmethod
    def needs_verification(
        last_verified_at: Optional[datetime],
        status: str,
        verification_attempts: int,
    ) -> bool:
        """
        Determine if transaction needs another verification attempt
        
        Strategy:
        - Pending: verify every 10 seconds (up to 2 minutes)
        - In progress: verify every 30 seconds
        - Confirmed: verify once
        - Failed: verify once, no retry
        """
        
        if status == "confirmed":
            return False  # No need to verify confirmed transactions
        
        if status == "failed":
            return False  # No need to retry failed transactions
        
        if last_verified_at is None:
            return True  # First verification
        
        time_since_verification = (datetime.utcnow() - last_verified_at).total_seconds()
        
        if status == "pending":
            # Re-verify every 10 seconds, max 2 minutes (12 attempts)
            if verification_attempts >= 12:
                return False
            return time_since_verification > 10
        
        elif status == "in_progress":
            # Re-verify every 30 seconds
            return time_since_verification > 30
        
        return False
