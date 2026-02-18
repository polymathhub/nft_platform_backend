"""Payment service for deposit and withdrawal operations."""
import logging
from typing import Optional, Tuple
from uuid import UUID
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment, PaymentType, PaymentStatus
from app.models.wallet import Wallet
from app.models.user import User
from app.utils.blockchain_utils import USDTHelper
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class PaymentService:
    """Service for managing user deposits and withdrawals."""

    @staticmethod
    async def initiate_deposit(
        db: AsyncSession,
        user_id: UUID,
        wallet_id: UUID,
        amount: float,
        external_address: Optional[str] = None,
    ) -> Tuple[Optional[Payment], Optional[str]]:
        """
        Initiate a deposit to a user's wallet.
        Returns platform wallet address to deposit to.
        """
        try:
            # Verify wallet exists and belongs to user
            result = await db.execute(
                select(Wallet).where(
                    (Wallet.id == wallet_id) & (Wallet.user_id == user_id)
                )
            )
            wallet = result.scalar_one_or_none()
            if not wallet:
                return None, "Wallet not found"

            # Validate USDT amount
            valid, error = USDTHelper.validate_usdt_amount(amount, settings.usdt_min_transaction)
            if not valid:
                return None, error

            # Create payment record
            payment = Payment(
                user_id=user_id,
                wallet_id=wallet_id,
                payment_type=PaymentType.DEPOSIT,
                status=PaymentStatus.PENDING,
                blockchain=wallet.blockchain.value,
                amount=amount,
                currency="USDT",
                counterparty_address=external_address,
                description=f"Deposit {amount} USDT to {wallet.blockchain.value} wallet",
            )

            db.add(payment)
            await db.commit()
            await db.refresh(payment)

            logger.info(f"Deposit initiated: {payment.id} for user {user_id}, amount={amount} USDT")
            return payment, None

        except Exception as e:
            logger.error(f"Error initiating deposit: {e}", exc_info=True)
            await db.rollback()
            return None, str(e)

    @staticmethod
    async def confirm_deposit(
        db: AsyncSession,
        payment_id: UUID,
        tx_hash: str,
    ) -> Tuple[Optional[Payment], Optional[str]]:
        """
        Confirm a deposit by verifying the transaction on-chain.
        """
        try:
            result = await db.execute(
                select(Payment).where(Payment.id == payment_id)
            )
            payment = result.scalar_one_or_none()

            if not payment:
                return None, "Payment record not found"

            if payment.status != PaymentStatus.PENDING:
                return None, f"Payment is not pending: {payment.status}"

            if payment.payment_type != PaymentType.DEPOSIT:
                return None, "This payment is not a deposit"

            # Store the external transaction hash
            payment.transaction_hash_external = tx_hash

            # In production: verify tx_hash on-chain
            # For now, mark as confirmed after user provides hash
            payment.status = PaymentStatus.CONFIRMED
            payment.confirmed_at = __import__("datetime").datetime.utcnow()

            await db.commit()
            await db.refresh(payment)

            logger.info(f"Deposit confirmed: {payment.id}, tx_hash={tx_hash}")
            return payment, None

        except Exception as e:
            logger.error(f"Error confirming deposit: {e}", exc_info=True)
            await db.rollback()
            return None, str(e)

    @staticmethod
    async def initiate_withdrawal(
        db: AsyncSession,
        user_id: UUID,
        wallet_id: UUID,
        amount: float,
        destination_address: str,
        destination_blockchain: Optional[str] = None,
    ) -> Tuple[Optional[Payment], Optional[str]]:
        """
        Initiate a withdrawal from a user's wallet.
        """
        try:
            # Verify wallet exists and belongs to user
            result = await db.execute(
                select(Wallet).where(
                    (Wallet.id == wallet_id) & (Wallet.user_id == user_id)
                )
            )
            wallet = result.scalar_one_or_none()
            if not wallet:
                return None, "Wallet not found"

            # Validate USDT amount
            valid, error = USDTHelper.validate_usdt_amount(amount, settings.usdt_min_transaction)
            if not valid:
                return None, error

            # Validate destination address format
            if not destination_address or len(destination_address) < 20:
                return None, "Invalid destination address"

            # Use source wallet blockchain if destination not specified
            target_blockchain = destination_blockchain or wallet.blockchain.value

            # Check if USDT is supported on target blockchain
            from app.models.wallet import BlockchainType
            try:
                bc = BlockchainType(target_blockchain)
                if not USDTHelper.is_usdt_supported(bc):
                    return None, f"USDT not supported on {target_blockchain}"
            except ValueError:
                return None, f"Unknown blockchain: {target_blockchain}"

            # Calculate platform fee (2% default)
            platform_fee = amount * settings.commission_rate
            withdrawal_amount = amount - platform_fee

            # Create payment record
            payment = Payment(
                user_id=user_id,
                wallet_id=wallet_id,
                payment_type=PaymentType.WITHDRAWAL,
                status=PaymentStatus.PENDING,
                blockchain=target_blockchain,
                amount=withdrawal_amount,
                currency="USDT",
                counterparty_address=destination_address,
                platform_fee=platform_fee,
                description=f"Withdraw {withdrawal_amount} USDT (fee: {platform_fee}) to {destination_address}",
            )

            db.add(payment)
            await db.commit()
            await db.refresh(payment)

            logger.info(f"Withdrawal initiated: {payment.id} for user {user_id}, amount={withdrawal_amount} USDT, fee={platform_fee}")
            return payment, None

        except Exception as e:
            logger.error(f"Error initiating withdrawal: {e}", exc_info=True)
            await db.rollback()
            return None, str(e)

    @staticmethod
    async def approve_withdrawal(
        db: AsyncSession,
        payment_id: UUID,
    ) -> Tuple[Optional[Payment], Optional[str]]:
        """
        Approve a pending withdrawal for processing.
        In production, this would trigger the actual on-chain transfer.
        """
        try:
            result = await db.execute(
                select(Payment).where(Payment.id == payment_id)
            )
            payment = result.scalar_one_or_none()

            if not payment:
                return None, "Payment record not found"

            if payment.status != PaymentStatus.PENDING:
                return None, f"Payment is not pending: {payment.status}"

            if payment.payment_type != PaymentType.WITHDRAWAL:
                return None, "This payment is not a withdrawal"

            # In production: execute actual blockchain transaction here
            # For demo: mark as confirmed
            payment.status = PaymentStatus.CONFIRMED
            payment.confirmed_at = __import__("datetime").datetime.utcnow()
            # In real implementation, payment.transaction_hash would be set after on-chain tx

            await db.commit()
            await db.refresh(payment)

            logger.info(f"Withdrawal approved: {payment.id}, amount={payment.amount} USDT to {payment.counterparty_address}")
            return payment, None

        except Exception as e:
            logger.error(f"Error approving withdrawal: {e}", exc_info=True)
            await db.rollback()
            return None, str(e)

    @staticmethod
    async def get_user_balance(
        db: AsyncSession,
        user_id: UUID,
    ) -> Tuple[Optional[dict], Optional[str]]:
        """
        Get user's total USDT balance across all wallets.
        Includes pending deposits/withdrawals.
        """
        try:
            # Get all user wallets
            wallets_result = await db.execute(
                select(Wallet).where(Wallet.user_id == user_id)
            )
            wallets = wallets_result.scalars().all()

            if not wallets:
                return {
                    "user_id": user_id,
                    "total_balance_usdt": 0.0,
                    "pending_deposits_usdt": 0.0,
                    "pending_withdrawals_usdt": 0.0,
                    "available_balance_usdt": 0.0,
                    "wallets": [],
                }, None

            # Calculate total and pending balances
            total_confirmed = 0.0
            pending_deposits = 0.0
            pending_withdrawals = 0.0
            wallets_info = []

            for wallet in wallets:
                # Get confirmed deposits for this wallet
                deposits_result = await db.execute(
                    select(Payment).where(
                        (Payment.wallet_id == wallet.id) &
                        (Payment.payment_type == PaymentType.DEPOSIT) &
                        (Payment.status == PaymentStatus.CONFIRMED)
                    )
                )
                wallet_balance = sum(p.amount for p in deposits_result.scalars().all())

                # Get pending deposits
                pending_dep_result = await db.execute(
                    select(Payment).where(
                        (Payment.wallet_id == wallet.id) &
                        (Payment.payment_type == PaymentType.DEPOSIT) &
                        (Payment.status == PaymentStatus.PENDING)
                    )
                )
                wallet_pending_deposits = sum(p.amount for p in pending_dep_result.scalars().all())

                # Get pending withdrawals
                pending_with_result = await db.execute(
                    select(Payment).where(
                        (Payment.wallet_id == wallet.id) &
                        (Payment.payment_type == PaymentType.WITHDRAWAL) &
                        (Payment.status == PaymentStatus.PENDING)
                    )
                )
                wallet_pending_withdrawals = sum(p.amount for p in pending_with_result.scalars().all())

                total_confirmed += wallet_balance
                pending_deposits += wallet_pending_deposits
                pending_withdrawals += wallet_pending_withdrawals

                wallets_info.append({
                    "wallet_id": str(wallet.id),
                    "address": f"{wallet.address[:15]}...{wallet.address[-10:]}",
                    "blockchain": wallet.blockchain.value,
                    "balance": wallet_balance,
                    "is_primary": wallet.is_primary,
                })

            available_balance = total_confirmed - pending_withdrawals

            return {
                "user_id": user_id,
                "total_balance_usdt": total_confirmed,
                "pending_deposits_usdt": pending_deposits,
                "pending_withdrawals_usdt": pending_withdrawals,
                "available_balance_usdt": max(0, available_balance),
                "wallets": wallets_info,
            }, None

        except Exception as e:
            logger.error(f"Error getting user balance: {e}", exc_info=True)
            return None, str(e)

    @staticmethod
    async def get_payment_history(
        db: AsyncSession,
        user_id: UUID,
        limit: int = 10,
    ) -> Tuple[Optional[list], Optional[str]]:
        """Get recent deposit and withdrawal history."""
        try:
            result = await db.execute(
                select(Payment)
                .where(Payment.user_id == user_id)
                .order_by(Payment.created_at.desc())
                .limit(limit)
            )
            payments = result.scalars().all()

            history = [
                {
                    "id": str(p.id),
                    "type": p.payment_type.value,
                    "status": p.status.value,
                    "amount": p.amount,
                    "currency": p.currency,
                    "blockchain": p.blockchain,
                    "created_at": p.created_at.isoformat(),
                    "confirmed_at": p.confirmed_at.isoformat() if p.confirmed_at else None,
                    "fee": p.platform_fee or 0,
                }
                for p in payments
            ]

            return history, None

        except Exception as e:
            logger.error(f"Error getting payment history: {e}", exc_info=True)
            return None, str(e)
