"""Payment router - deposit and withdrawal endpoints."""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
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

class WebAppDepositRequest(BaseModel):
    """Web app deposit request model."""
    user_id: str
    wallet_id: str
    amount: float
    blockchain: str | None = None
    init_data: str | None = None


class WebAppWithdrawalRequest(BaseModel):
    """Web app withdrawal request model."""
    user_id: str
    wallet_id: str
    amount: float
    destination_address: str
    blockchain: str | None = None
    init_data: str | None = None


@router.post("/web-app/deposit")
async def web_app_deposit(
    request: WebAppDepositRequest,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Web app deposit endpoint. Accepts request body with user_id, wallet_id, amount.
    Compatible with Telegram web app authentication.
    This is the PREFERRED endpoint for web app to use.
    """
    logger.info(f"[DEPOSIT] Received request: user_id={request.user_id}, wallet_id={request.wallet_id}, amount={request.amount}")
    
    try:
        # Convert string IDs to UUID
        try:
            user_id = UUID(request.user_id)
            wallet_id = UUID(request.wallet_id)
        except (ValueError, TypeError) as e:
            detail = f"Invalid user_id or wallet_id format: {str(e)}"
            logger.error(f"[DEPOSIT] UUID error: {detail}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=detail,
            )
        
        # Validate amount
        if not request.amount or request.amount <= 0:
            detail = "Amount must be greater than 0"
            logger.error(f"[DEPOSIT] Validation error: {detail}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=detail,
            )
        
        payment, error = await PaymentService.initiate_deposit(
            db=db,
            user_id=user_id,
            wallet_id=wallet_id,
            amount=request.amount,
        )

        if error:
            logger.error(f"[DEPOSIT] Service error: {error}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error,
            )

        settings = get_settings()
        # Use blockchain from request or get it from payment
        blockchain = request.blockchain or getattr(payment, "blockchain", "ethereum")
        platform_address = getattr(settings, "platform_wallets", {}).get(
            blockchain.lower(), "0x00000..." if blockchain == "ethereum" else "default_address"
        )

        response = {
            "success": True,
            "payment_id": str(payment.id),
            "deposit_address": platform_address,
            "amount": float(payment.amount) if hasattr(payment, "amount") else float(request.amount),
            "currency": getattr(payment, "currency", "USDT"),
            "blockchain": blockchain,
        }
        logger.info(f"[DEPOSIT] Success response: {response}")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DEPOSIT] Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deposit failed: {str(e)}",
        )


@router.post("/web-app/withdrawal")
async def web_app_withdrawal(
    request: WebAppWithdrawalRequest,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Web app withdrawal endpoint. Accepts request body with user_id, wallet_id, amount, destination_address.
    Compatible with Telegram web app authentication.
    This is the PREFERRED endpoint for web app to use.
    """
    logger.info(f"[WITHDRAWAL] Received request: user_id={request.user_id}, amount={request.amount}, dest={request.destination_address[:10]}...")
    
    try:
        # Convert string IDs to UUID
        try:
            user_id = UUID(request.user_id)
            wallet_id = UUID(request.wallet_id)
        except (ValueError, TypeError) as e:
            detail = f"Invalid user_id or wallet_id format: {str(e)}"
            logger.error(f"[WITHDRAWAL] UUID error: {detail}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=detail,
            )
        
        # Validate inputs
        if not request.amount or request.amount <= 0:
            detail = "Amount must be greater than 0"
            logger.error(f"[WITHDRAWAL] Validation error: {detail}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=detail,
            )
        
        if not request.destination_address or len(request.destination_address) < 26:
            detail = "Invalid destination address"
            logger.error(f"[WITHDRAWAL] Address validation error: {detail}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=detail,
            )
        
        payment, error = await PaymentService.initiate_withdrawal(
            db=db,
            user_id=user_id,
            wallet_id=wallet_id,
            amount=request.amount,
            destination_address=request.destination_address,
        )

        if error:
            logger.error(f"[WITHDRAWAL] Service error: {error}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error,
            )

        blockchain = request.blockchain or getattr(payment, "blockchain", "ethereum")
        response = {
            "success": True,
            "payment_id": str(payment.id),
            "amount": float(payment.amount) if hasattr(payment, "amount") else float(request.amount),
            "destination": request.destination_address,
            "status": payment.status.value if hasattr(payment.status, "value") else str(payment.status),
            "platform_fee": float(payment.platform_fee) if hasattr(payment, "platform_fee") and payment.platform_fee else 0,
            "blockchain": blockchain,
        }
        logger.info(f"[WITHDRAWAL] Success response: {response}")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[WITHDRAWAL] Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Withdrawal failed: {str(e)}",
        )


@router.get("/web-app/balance/{user_id}")
async def web_app_balance(
    user_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Get user balance for web app."""
    logger.info(f"[BALANCE] Fetching balance for user_id={user_id}")
    
    try:
        # Convert string ID to UUID
        try:
            uid = UUID(user_id)
        except (ValueError, TypeError) as e:
            detail = f"Invalid user_id format: {str(e)}"
            logger.error(f"[BALANCE] UUID error: {detail}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=detail,
            )
        
        balance_data, error = await PaymentService.get_user_balance(db, uid)

        if error:
            logger.error(f"[BALANCE] Service error: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error,
            )

        response = {
            "success": True,
            "balance": balance_data,
        }
        logger.info(f"[BALANCE] Success response retrieved")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[BALANCE] Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Balance fetch failed: {str(e)}",
        )
