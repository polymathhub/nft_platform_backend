"""Payment router - deposit and withdrawal endpoints."""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db_session
from app.models.user import User
from app.models.wallet import BlockchainType
from app.schemas.payment import (
    InitiateDepositRequest,
    DepositConfirmRequest,
    InitiateWithdrawalRequest,
    WithdrawalApprovalRequest,
    PaymentResponse,
    DepositInfoResponse,
    WithdrawalInfoResponse,
    BalanceSummaryResponse,
)
from app.services.payment_service import PaymentService
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


# ==================== BALANCE ENDPOINTS ====================


@router.get("/balance")
async def get_balance(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> BalanceSummaryResponse:
    """Get user's USDT balance across all wallets."""
    balance_data, error = await PaymentService.get_user_balance(db, current_user.id)

    if error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error,
        )

    return BalanceSummaryResponse(**balance_data)


@router.get("/history")
async def get_payment_history(
    limit: int = 10,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get deposit and withdrawal history."""
    history, error = await PaymentService.get_payment_history(
        db, current_user.id, limit
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error,
        )

    return {
        "user_id": str(current_user.id),
        "history": history,
    }


# ==================== DEPOSIT ENDPOINTS ====================


@router.post("/deposit/initiate")
async def initiate_deposit(
    req: InitiateDepositRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> DepositInfoResponse:
    """
    Initiate a deposit to a user's wallet.
    Returns platform wallet address to deposit to.
    """
    payment, error = await PaymentService.initiate_deposit(
        db=db,
        user_id=current_user.id,
        wallet_id=req.wallet_id,
        amount=req.amount,
        external_address=req.external_address,
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )

    # Get platform wallet for this blockchain
    platform_address = getattr(settings, "platform_wallets", {}).get(
        payment.blockchain.lower(), "0x..."
    )

    return DepositInfoResponse(
        payment_id=payment.id,
        deposit_address=platform_address,
        amount=payment.amount,
        currency=payment.currency,
        blockchain=payment.blockchain,
        status=payment.status.value,
        instructions=f"Send {payment.amount} USDT to the address above. After sending, confirm the transaction with its hash.",
    )


@router.post("/deposit/confirm")
async def confirm_deposit(
    req: DepositConfirmRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> PaymentResponse:
    """
    Confirm a deposit by providing the external transaction hash.
    """
    payment, error = await PaymentService.confirm_deposit(
        db=db,
        payment_id=req.payment_id,
        tx_hash=req.transaction_hash,
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )

    return PaymentResponse.from_orm(payment)


# ==================== WITHDRAWAL ENDPOINTS ====================


@router.post("/withdrawal/initiate")
async def initiate_withdrawal(
    req: InitiateWithdrawalRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> WithdrawalInfoResponse:
    """
    Initiate a withdrawal from a user's wallet.
    Requires approval before executing.
    """
    payment, error = await PaymentService.initiate_withdrawal(
        db=db,
        user_id=current_user.id,
        wallet_id=req.wallet_id,
        amount=req.amount,
        destination_address=req.destination_address,
        destination_blockchain=req.destination_blockchain,
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )

    return WithdrawalInfoResponse(
        payment_id=payment.id,
        destination_address=req.destination_address,
        amount=payment.amount,
        currency=payment.currency,
        blockchain=payment.blockchain,
        status=payment.status.value,
        network_fee=payment.network_fee or 0,
    )


@router.post("/withdrawal/approve")
async def approve_withdrawal(
    req: WithdrawalApprovalRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> PaymentResponse:
    """
    Approve a pending withdrawal.
    In production, this would trigger the actual on-chain transfer.
    """
    payment, error = await PaymentService.approve_withdrawal(
        db=db,
        payment_id=req.payment_id,
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )

    return PaymentResponse.from_orm(payment)


# ==================== WEB APP ENDPOINTS ====================


@router.post("/web-app/deposit")
async def web_app_deposit(
    user_id: str,
    wallet_id: str,
    amount: float,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Web app deposit endpoint."""
    payment, error = await PaymentService.initiate_deposit(
        db=db,
        user_id=UUID(user_id),
        wallet_id=UUID(wallet_id),
        amount=amount,
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )

    platform_address = getattr(settings, "platform_wallets", {}).get(
        payment.blockchain.lower(), "0x..."
    )

    return {
        "success": True,
        "payment_id": str(payment.id),
        "deposit_address": platform_address,
        "amount": payment.amount,
        "currency": payment.currency,
        "blockchain": payment.blockchain,
    }


@router.post("/web-app/withdrawal")
async def web_app_withdrawal(
    user_id: str,
    wallet_id: str,
    amount: float,
    destination_address: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Web app withdrawal endpoint."""
    payment, error = await PaymentService.initiate_withdrawal(
        db=db,
        user_id=UUID(user_id),
        wallet_id=UUID(wallet_id),
        amount=amount,
        destination_address=destination_address,
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )

    return {
        "success": True,
        "payment_id": str(payment.id),
        "amount": payment.amount,
        "destination": destination_address,
        "status": payment.status.value,
        "platform_fee": payment.platform_fee or 0,
    }


@router.get("/web-app/balance/{user_id}")
async def web_app_balance(
    user_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Get user balance for web app."""
    balance_data, error = await PaymentService.get_user_balance(
        db, UUID(user_id)
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error,
        )

    return {
        "success": True,
        "balance": balance_data,
    }
