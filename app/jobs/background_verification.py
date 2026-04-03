"""
Background job for verifying blockchain transactions
Runs periodically to update transaction confirmation status
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.database.base import async_session
from app.models.blockchain_transaction import BlockchainTransaction, BlockchainTransactionStatus
from app.services.transaction_verifier import TransactionVerifier
from app.services.toncenter_client import get_toncenter_client

logger = logging.getLogger(__name__)


class TransactionVerificationJob:
    """Background job for verifying pending transactions"""
    
    # Scheduling thresholds
    PENDING_RETRY_INTERVAL = timedelta(seconds=10)      # Check pending every 10s
    PENDING_MAX_AGE = timedelta(minutes=2)              # Stop checking after 2 minutes
    IN_PROGRESS_RETRY_INTERVAL = timedelta(seconds=30)  # Check in-progress every 30s
    IN_PROGRESS_MAX_AGE = timedelta(hours=1)            # Stop checking after 1 hour
    
    def __init__(self):
        """Initialize the verification job"""
        self.is_running = False
        self.verifier = TransactionVerifier()
        logger.info("TransactionVerificationJob initialized")
    
    async def start(self) -> None:
        """Start the background job"""
        if self.is_running:
            logger.warning("Job already running")
            return
        
        self.is_running = True
        logger.info("Starting transaction verification job")
        
        try:
            while self.is_running:
                await self.run_verification_cycle()
                # Run every 5 seconds
                await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Transaction verification job crashed: {e}", exc_info=True)
            self.is_running = False
            raise
    
    async def stop(self) -> None:
        """Stop the background job"""
        logger.info("Stopping transaction verification job")
        self.is_running = False
    
    async def run_verification_cycle(self) -> None:
        """Run a single verification cycle"""
        try:
            async with async_session() as session:
                # Find transactions that need verification
                transactions_to_verify = await self._get_transactions_to_verify(session)
                
                if transactions_to_verify:
                    logger.debug(f"Verifying {len(transactions_to_verify)} transactions")
                    
                    for tx in transactions_to_verify:
                        try:
                            await self._verify_and_update_transaction(session, tx)
                        except Exception as e:
                            logger.error(f"Failed to verify tx {tx.transaction_hash}: {e}")
                    
                    await session.commit()
                    logger.debug(f"Verification cycle completed, updated {len(transactions_to_verify)} transactions")
        
        except Exception as e:
            logger.error(f"Verification cycle failed: {e}", exc_info=True)
    
    async def _get_transactions_to_verify(self, session: AsyncSession) -> list:
        """
        Find transactions that need verification
        
        Returns pending/in-progress transactions that are ready for retry
        """
        now = datetime.utcnow()
        pending_cutoff = now - self.PENDING_MAX_AGE
        in_progress_cutoff = now - self.IN_PROGRESS_MAX_AGE
        
        # Find pending transactions ready for retry
        query = select(BlockchainTransaction).where(
            and_(
                BlockchainTransaction.status == BlockchainTransactionStatus.PENDING,
                BlockchainTransaction.created_at >= pending_cutoff,
                # Either never verified or needs retry
                (
                    (BlockchainTransaction.verified_at.is_(None)) |
                    (BlockchainTransaction.next_verification_at <= now)
                )
            )
        )
        
        result = await session.execute(query)
        pending_transactions = result.scalars().all()
        
        # Find in-progress transactions ready for retry
        query = select(BlockchainTransaction).where(
            and_(
                BlockchainTransaction.status == BlockchainTransactionStatus.IN_PROGRESS,
                BlockchainTransaction.created_at >= in_progress_cutoff,
                # Next verification is due
                (BlockchainTransaction.next_verification_at <= now)
            )
        )
        
        result = await session.execute(query)
        in_progress_transactions = result.scalars().all()
        
        logger.debug(f"Found {len(pending_transactions)} pending, {len(in_progress_transactions)} in-progress transactions to verify")
        
        return pending_transactions + in_progress_transactions
    
    async def _verify_and_update_transaction(
        self,
        session: AsyncSession,
        transaction: BlockchainTransaction
    ) -> None:
        """
        Verify a single transaction and update its status
        
        Args:
            session: Database session
            transaction: Transaction to verify
        """
        try:
            # Get TonCenter client
            toncenter_client = await get_toncenter_client()
            
            # Check confirmation status
            result = await toncenter_client.check_transaction_confirmation(
                tx_hash=transaction.transaction_hash,
                address=transaction.wallet_address
            )
            
            # Update transaction record
            confirmations = result.get("confirmations", 0)
            status_str = result.get("status", "pending").lower()
            
            # Map status string to enum
            status_map = {
                "pending": BlockchainTransactionStatus.PENDING,
                "in_progress": BlockchainTransactionStatus.IN_PROGRESS,
                "confirmed": BlockchainTransactionStatus.CONFIRMED,
                "failed": BlockchainTransactionStatus.FAILED,
            }
            new_status = status_map.get(status_str, BlockchainTransactionStatus.PENDING)
            
            # Calculate trust level based on confirmations
            trust_level = self.verifier.calculate_trust_level(confirmations)
            
            # Determine next verification time
            next_verification_at = self._calculate_next_verification(new_status)
            
            # Update transaction
            transaction.confirmations = confirmations
            transaction.trust_level = trust_level
            transaction.status = new_status
            transaction.verified_at = datetime.utcnow()
            transaction.next_verification_at = next_verification_at
            transaction.verification_attempts += 1
            
            logger.info(
                f"Updated tx {transaction.transaction_hash}: "
                f"status={new_status.value}, confirmations={confirmations}, trust_level={trust_level}"
            )
            
        except Exception as e:
            logger.error(f"Error verifying transaction {transaction.transaction_hash}: {e}")
            
            # Mark for retry with exponential backoff
            transaction.verification_attempts += 1
            max_retries = 30 if transaction.status == BlockchainTransactionStatus.PENDING else 20
            
            if transaction.verification_attempts >= max_retries:
                transaction.status = BlockchainTransactionStatus.FAILED
                logger.warning(f"Transaction {transaction.transaction_hash} exceeded max retries, marking as FAILED")
            else:
                # Schedule retry with exponential backoff (1s, 2s, 4s, 8s, etc.)
                delay_seconds = min(2 ** min(transaction.verification_attempts, 10), 300)
                transaction.next_verification_at = datetime.utcnow() + timedelta(seconds=delay_seconds)
    
    def _calculate_next_verification(self, status: BlockchainTransactionStatus) -> datetime:
        """
        Calculate when to next verify this transaction
        
        Returns: datetime of next verification, or None if no more verification needed
        """
        now = datetime.utcnow()
        
        if status == BlockchainTransactionStatus.PENDING:
            return now + self.PENDING_RETRY_INTERVAL
        elif status == BlockchainTransactionStatus.IN_PROGRESS:
            return now + self.IN_PROGRESS_RETRY_INTERVAL
        elif status == BlockchainTransactionStatus.CONFIRMED:
            # Confirmed transactions don't need further verification
            return now + timedelta(days=365)
        elif status == BlockchainTransactionStatus.FAILED:
            # Failed transactions don't need further verification
            return now + timedelta(days=365)
        else:
            return now + self.PENDING_RETRY_INTERVAL


class SessionCleanupJob:
    """Background job for cleaning up expired sessions"""
    
    CLEANUP_INTERVAL = timedelta(hours=1)  # Run cleanup every hour
    SESSION_EXPIRY = timedelta(hours=24)   # Sessions expire after 24 hours
    
    def __init__(self):
        """Initialize the cleanup job"""
        self.is_running = False
        logger.info("SessionCleanupJob initialized")
    
    async def start(self) -> None:
        """Start the background job"""
        if self.is_running:
            logger.warning("Cleanup job already running")
            return
        
        self.is_running = True
        logger.info("Starting session cleanup job")
        
        try:
            while self.is_running:
                await self.run_cleanup_cycle()
                await asyncio.sleep(self.CLEANUP_INTERVAL.total_seconds())
        except Exception as e:
            logger.error(f"Session cleanup job crashed: {e}", exc_info=True)
            self.is_running = False
            raise
    
    async def stop(self) -> None:
        """Stop the background job"""
        logger.info("Stopping session cleanup job")
        self.is_running = False
    
    async def run_cleanup_cycle(self) -> None:
        """Run a single cleanup cycle"""
        try:
            from app.models.ton_wallet_session import TONWalletSession
            
            async with async_session() as session:
                now = datetime.utcnow()
                cutoff_time = now - self.SESSION_EXPIRY
                
                # Find expired active sessions
                query = select(TONWalletSession).where(
                    and_(
                        TONWalletSession.is_active == True,
                        TONWalletSession.last_activity_at < cutoff_time
                    )
                )
                
                result = await session.execute(query)
                expired_sessions = result.scalars().all()
                
                if expired_sessions:
                    for session_record in expired_sessions:
                        session_record.is_active = False
                        session_record.updated_at = now
                    
                    await session.commit()
                    logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
                else:
                    logger.debug("No expired sessions to clean up")
        
        except Exception as e:
            logger.error(f"Cleanup cycle failed: {e}", exc_info=True)


# Global job instances
_verification_job: Optional[TransactionVerificationJob] = None
_cleanup_job: Optional[SessionCleanupJob] = None


async def start_background_jobs() -> None:
    """Start all background jobs"""
    global _verification_job, _cleanup_job
    
    logger.info("Starting background jobs")
    
    _verification_job = TransactionVerificationJob()
    _cleanup_job = SessionCleanupJob()
    
    # Start jobs as background tasks
    asyncio.create_task(_verification_job.start())
    asyncio.create_task(_cleanup_job.start())
    
    logger.info("Background jobs started")


async def stop_background_jobs() -> None:
    """Stop all background jobs"""
    global _verification_job, _cleanup_job
    
    logger.info("Stopping background jobs")
    
    if _verification_job:
        await _verification_job.stop()
    if _cleanup_job:
        await _cleanup_job.stop()
    
    logger.info("Background jobs stopped")


def get_verification_job() -> Optional[TransactionVerificationJob]:
    """Get the verification job instance"""
    return _verification_job


def get_cleanup_job() -> Optional[SessionCleanupJob]:
    """Get the cleanup job instance"""
    return _cleanup_job
