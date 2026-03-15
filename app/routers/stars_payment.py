from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_DOWN
import uuid
import hashlib
import hmac
import json
from typing import Optional
from app.database import get_db
from app.models import User, Payment, PaymentStatus, PaymentType, Referral, ReferralStatus, ReferralCommission, CommissionStatus
from app.security.auth import get_current_user
from app.utils.logger import logger
from app.config import get_settings
router = APIRouter(prefix="/api/v1/stars", tags=["Telegram Stars"])
class StarsPurchaseRequest(BaseModel):
    invoice_id: str
    item_ids: list[str]
    total_amount: int
    currency: str = "XTR"
class StarsInvoiceResponse(BaseModel):
    invoice_id: str
    currency: str
    total_stars: int
    platform_commission: int
    referral_commission: int
    net_creator_payout: int
    invoice_link: str
class StarsPaymentConfirmation(BaseModel):
    invoice_id: str
    telegram_payment_charge_id: str
    provider_payment_charge_id: str
    total_amount: int
    currency: str = "XTR"
class WalletSignInRequest(BaseModel):
    wallet_address: str
    chain: str = "ethereum"
    message: str
    signature: str
class WalletSignInResponse(BaseModel):
    access_token: str
    user_id: str
    username: str
    is_new: bool
def generate_invoice_id() -> str:
    return f"inv_{uuid.uuid4().hex[:12]}"
def validate_telegram_signature(init_data: str, bot_token: str) -> bool:
    try:
        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(
                dict(param.split("=") for param in init_data.split("&")).items()
            ) if k != "hash"
        )
        secret_key = hashlib.sha256(bot_token.encode()).digest()
        hash_check = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        init_dict = dict(param.split("=") for param in init_data.split("&"))
        provided_hash = init_dict.get("hash", "")
        return hash_check == provided_hash
    except Exception as e:
        logger.warning(f"Signature validation failed: {e}")
        return False
def calculate_commissions(total_amount: int, referrer_exists: bool = True):
    amount_decimal = Decimal(str(total_amount))
    platform_fee_rate = Decimal("0.02")
    referral_fee_rate = Decimal("0.1")
    platform_commission_decimal = (amount_decimal * platform_fee_rate).quantize(
        Decimal("1"), rounding=ROUND_DOWN
    )
    platform_commission = int(platform_commission_decimal)
    referral_commission = 0
    if referrer_exists and platform_commission > 0:
        referral_decimal = (Decimal(platform_commission) * referral_fee_rate).quantize(
            Decimal("1"), rounding=ROUND_DOWN
        )
        referral_commission = int(referral_decimal)
        if referrer_exists and referral_commission == 0 and platform_commission >= 2:
            referral_commission = 1
    net_creator_payout = total_amount - platform_commission
    logger.debug(
        f"Commission calculation: total={total_amount} stars, "
        f"platform={platform_commission}, referral={referral_commission}, "
        f"payout={net_creator_payout}"
    )
    return {
        "platform_commission": platform_commission,
        "referral_commission": referral_commission,
        "net_creator_payout": net_creator_payout,
    }
@router.post("/invoice/create")
async def create_stars_invoice(
    req: StarsPurchaseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    has_referrer = current_user.referred_by_id is not None
    commissions = calculate_commissions(req.total_amount, has_referrer)
    payment = Payment(
        id=uuid.uuid4(),
        user_id=current_user.id,
        payment_type=PaymentType.DEPOSIT,
        status=PaymentStatus.PENDING,
        blockchain="telegram",
        amount=req.total_amount,
        currency=req.currency,
        transaction_hash=req.invoice_id,
        description=f"Purchase {len(req.item_ids)} NFT(s)",
        platform_fee=commissions["platform_commission"],
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    logger.info(f"Invoice created: {req.invoice_id} for user {current_user.id}, amount: {req.total_amount}")
    return StarsInvoiceResponse(
        invoice_id=req.invoice_id,
        currency=req.currency,
        total_stars=req.total_amount,
        platform_commission=commissions["platform_commission"],
        referral_commission=commissions["referral_commission"],
        net_creator_payout=commissions["net_creator_payout"],
        invoice_link=f"https://t.me/stars?startapp=giftedforge_invoice_{req.invoice_id}",
    )
@router.post("/payment/success")
async def handle_payment_success(
    confirmation: StarsPaymentConfirmation,
    x_telegram_init_data: str = Header(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    settings = get_settings()
    if x_telegram_init_data and not validate_telegram_signature(
        x_telegram_init_data,
        settings.telegram_bot_token
    ):
        logger.warning(f"Invalid Telegram signature from user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Invalid payment signature"
        )
    from sqlalchemy import and_
    payment = db.query(Payment).filter(
        and_(
            Payment.transaction_hash == confirmation.invoice_id,
            Payment.user_id == current_user.id,
        )
    ).with_for_update().first()
    if not payment:
        logger.warning(f"Payment not found: {confirmation.invoice_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    if payment.status == PaymentStatus.CONFIRMED:
        logger.info(f"Payment already confirmed: {confirmation.invoice_id}")
        return {
            "success": True,
            "message": "Payment already processed",
            "payment_id": str(payment.id),
        }
    payment.status = PaymentStatus.CONFIRMED
    payment.confirmed_at = datetime.utcnow()
    payment.counterparty_address = confirmation.provider_payment_charge_id
    db.add(payment)
    current_user.stars_balance += confirmation.total_amount
    current_user.total_stars_earned += confirmation.total_amount
    db.add(current_user)
    if current_user.referred_by_id:
        referral = db.query(Referral).filter(
            Referral.referrer_id == current_user.referred_by_id,
            Referral.referred_user_id == current_user.id,
            Referral.status == ReferralStatus.ACTIVE,
        ).first()
        if referral:
            commissions = calculate_commissions(confirmation.total_amount, True)
            existing_commission = db.query(ReferralCommission).filter(
                ReferralCommission.transaction_id == payment.id,
                ReferralCommission.referral_id == referral.id,
            ).first()
            if not existing_commission:
                commission = ReferralCommission(
                    id=uuid.uuid4(),
                    referral_id=referral.id,
                    transaction_id=payment.id,
                    commission_amount=commissions["referral_commission"],
                    commission_rate=0.1,
                    transaction_amount=confirmation.total_amount,
                    status=CommissionStatus.PENDING,
                )
                referral.lifetime_earnings += commissions["referral_commission"]
                referral.referred_purchase_count += 1
                referral.referred_purchase_amount += confirmation.total_amount
                referrer = db.query(User).filter(User.id == current_user.referred_by_id).first()
                if referrer:
                    referrer.stars_balance += commissions["referral_commission"]
                    referrer.total_stars_earned += commissions["referral_commission"]
                    db.add(referrer)
                db.add(commission)
                db.add(referral)
                logger.info(
                    f"Referral commission created: {commissions['referral_commission']} stars "
                    f"for transaction {payment.id}"
                )
            else:
                logger.info(
                    f"Referral commission already exists for transaction {payment.id} - skipping"
                )
    db.commit()
    logger.info(
        f"Payment confirmed: {confirmation.invoice_id}, "
        f"user: {current_user.id}, "
        f"amount: {confirmation.total_amount}"
    )
    return {
        "success": True,
        "message": "Payment confirmed and stars credited",
        "payment_id": str(payment.id),
        "stars_balance": current_user.stars_balance,
    }
@router.post("/payment/failed")
async def handle_payment_failed(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    invoice_id = data.get("invoice_id")
    error_message = data.get("error_message", "Payment failed")
    payment = db.query(Payment).filter(
        Payment.transaction_hash == invoice_id,
        Payment.user_id == current_user.id
    ).first()
    if payment:
        payment.status = PaymentStatus.FAILED
        payment.error_message = error_message
        db.add(payment)
        db.commit()
        logger.warning(f"Payment failed: {invoice_id}, error: {error_message}")
    return {
        "success": False,
        "message": error_message,
    }
@router.post("/wallet/signin")
async def wallet_signin(
    req: WalletSignInRequest,
    db: Session = Depends(get_db),
):
    Sign in with wallet address (supports MetaMask, WalletConnect, etc).
    Flow:
    1. Frontend gets user's wallet address
    2. Generate message: "Sign in to GiftedForge as {address} at {timestamp}"
    3. User signs with wallet private key
    4. Send wallet_address + signature to this endpoint
    5. Server verifies signature and creates/updates user
    6. Return JWT token for authentication
    from eth_account.messages import encode_defunct
    from eth_account import Account
    wallet_address = req.wallet_address.lower()
    message_text = req.message
    try:
        message = encode_defunct(text=message_text)
        recovered_address = Account.recover_message(message, signature=req.signature).lower()
        if recovered_address != wallet_address:
            logger.warning(f"Signature mismatch: {recovered_address} != {wallet_address}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Signature verification failed"
            )
        user = db.query(User).filter(User.telegram_id == wallet_address).first()
        is_new = False
        if not user:
            is_new = True
            user = User(
                id=uuid.uuid4(),
                email=f"{wallet_address}@wallet.giftedforge",
                username=f"wallet_{wallet_address[:8]}",
                hashed_password="",
                telegram_id=wallet_address,
                telegram_username=f"wallet_{wallet_address[:8]}",
                is_verified=True,
                is_active=True,
            )
            import secrets
            referral_code = f"REF{secrets.token_hex(3).upper()}"
            while db.query(User).filter(User.referral_code == referral_code).first():
                referral_code = f"REF{secrets.token_hex(3).upper()}"
            user.referral_code = referral_code
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"New wallet user created: {wallet_address}")
        else:
            logger.info(f"Wallet user logged in: {wallet_address}")
        from app.security.auth import create_access_token
        access_token = create_access_token(data={"sub": str(user.id)})
        user.last_login = datetime.utcnow()
        db.add(user)
        db.commit()
        return WalletSignInResponse(
            access_token=access_token,
            user_id=str(user.id),
            username=user.username,
            is_new=is_new,
        )
    except Exception as e:
        logger.error(f"Wallet sign-in failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wallet sign-in failed"
        )
@router.post("/wallet/message")
async def get_signin_message():
    timestamp = datetime.utcnow().isoformat()
    message = (
        f"Sign in to GiftedForge\n\n"
        f"By signing this message, you confirm that you own this wallet.\n\n"
        f"Timestamp: {timestamp}"
    )
    return {
        "message": message,
        "timestamp": timestamp,
        "version": "1",
    }
