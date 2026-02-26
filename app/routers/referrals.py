"""Referral system API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import secrets

from app.database import get_db
from app.models import (
    User, Referral, ReferralStatus, ReferralCommission, CommissionStatus, Payment
)
from app.schemas.auth import UserResponse
from app.security.auth import get_current_user
from app.utils.logger import logger

router = APIRouter(prefix="/api/v1/referrals", tags=["Referrals"])


def generate_referral_code(user_id: str, db: Session) -> str:
    """Generate a unique referral code."""
    base_code = f"REF{secrets.token_hex(3).upper()}"
    
    while db.query(User).filter(User.referral_code == base_code).first():
        base_code = f"REF{secrets.token_hex(3).upper()}"
    
    return base_code


@router.get("/me", response_model=dict)
async def get_my_referral_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's referral information and network."""
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    # Get or create referral code
    if not current_user.referral_code:
        current_user.referral_code = generate_referral_code(current_user.id, db)
        db.add(current_user)
        db.commit()
        db.refresh(current_user)
    
    # Get all referrals made by this user
    referrals = db.query(Referral).filter(
        Referral.referrer_id == current_user.id,
        Referral.status == ReferralStatus.ACTIVE
    ).all()
    
    # Calculate lifetime earnings
    lifetime_earnings = sum(ref.lifetime_earnings for ref in referrals)
    
    # Get referred user details
    referred_users = []
    for ref in referrals:
        referred_user = db.query(User).filter(User.id == ref.referred_user_id).first()
        if referred_user:
            referred_users.append({
                "user_id": str(referred_user.id),
                "user_name": referred_user.username,
                "user_avatar": referred_user.avatar_url,
                "earnings": ref.lifetime_earnings,
                "purchase_count": ref.referred_purchase_count,
                "purchase_amount": ref.referred_purchase_amount,
                "referred_at": ref.created_at.isoformat(),
                "first_purchase_at": ref.first_purchase_at.isoformat() if ref.first_purchase_at else None,
            })
    
    # Get pending commissions
    pending_commissions = db.query(ReferralCommission).filter(
        ReferralCommission.referral_id.in_([r.id for r in referrals]),
        ReferralCommission.status == CommissionStatus.PENDING
    ).all()
    
    pending_rewards = sum(c.commission_amount for c in pending_commissions)
    
    return {
        "code": current_user.referral_code,
        "lifetime_earnings": lifetime_earnings,
        "pending_commissions": pending_rewards,
        "referred_users": referred_users,
        "total_referrals": len(referrals),
    }


@router.get("/network")
async def get_referral_network(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get referral network and transaction history."""
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    # Get all referral commissions for this user's referrals
    referrals = db.query(Referral).filter(
        Referral.referrer_id == current_user.id
    ).all()
    
    commissions = db.query(ReferralCommission).filter(
        ReferralCommission.referral_id.in_([r.id for r in referrals])
    ).order_by(ReferralCommission.earned_at.desc()).all()
    
    transactions = []
    for commission in commissions:
        referral = db.query(Referral).filter(Referral.id == commission.referral_id).first()
        referred_user = db.query(User).filter(User.id == referral.referred_user_id).first() if referral else None
        
        transactions.append({
            "commission_id": str(commission.id),
            "amount": commission.commission_amount,
            "from_user": referred_user.username if referred_user else "Unknown",
            "type": "commission",
            "status": commission.status.value,
            "earned_at": commission.earned_at.isoformat(),
            "paid_at": commission.paid_at.isoformat() if commission.paid_at else None,
            "transaction_amount": commission.transaction_amount,
        })
    
    return {
        "transactions": transactions,
        "total_count": len(transactions),
    }


@router.post("/apply")
async def apply_referral_code(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Apply a referral code to the current user."""
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    referral_code = data.get("referral_code", "").strip()
    
    if not referral_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid referral code")
    
    # Check if user already has a referrer
    if current_user.referred_by_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has a referrer"
        )
    
    # Find the referrer
    referrer = db.query(User).filter(User.referral_code == referral_code).first()
    if not referrer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referral code not found"
        )
    
    if referrer.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot refer yourself"
        )
    
    # Create referral relationship
    referral = Referral(
        id=uuid.uuid4(),
        referrer_id=referrer.id,
        referred_user_id=current_user.id,
        referral_code=referral_code,
        status=ReferralStatus.ACTIVE,
    )
    
    # Update user
    current_user.referred_by_id = referrer.id
    
    db.add(referral)
    db.add(current_user)
    db.commit()
    
    logger.info(f"User {current_user.id} referred by {referrer.id}")
    
    return {
        "success": True,
        "message": "Referral code applied successfully",
        "referrer": referrer.username,
    }


@router.post("/commission/record")
async def record_referral_commission(
    data: dict,
    db: Session = Depends(get_db),
):
    """Record a referral commission (internal endpoint, requires special auth)."""
    # This endpoint should be called by the payment system after a successful transaction
    transaction_id = data.get("transaction_id")
    referred_user_id = data.get("referred_user_id")
    transaction_amount = data.get("transaction_amount", 0.0)
    commission_rate = data.get("commission_rate", 0.1)
    
    # Find the referral relationship
    referral = db.query(Referral).filter(
        Referral.referred_user_id == referred_user_id,
        Referral.status == ReferralStatus.ACTIVE
    ).first()
    
    if not referral:
        logger.warning(f"No active referral found for user {referred_user_id}")
        return {"success": False, "message": "No active referral"}
    
    # Calculate commission
    commission_amount = transaction_amount * commission_rate
    
    # Create commission record
    commission = ReferralCommission(
        id=uuid.uuid4(),
        referral_id=referral.id,
        transaction_id=transaction_id,
        commission_amount=commission_amount,
        commission_rate=commission_rate,
        transaction_amount=transaction_amount,
        status=CommissionStatus.PENDING,
    )
    
    # Update referral stats
    if not referral.first_purchase_at:
        referral.first_purchase_at = datetime.utcnow()
    referral.referred_purchase_count += 1
    referral.referred_purchase_amount += transaction_amount
    referral.lifetime_earnings += commission_amount
    
    # Update referrer's stars balance
    referrer = db.query(User).filter(User.id == referral.referrer_id).first()
    if referrer:
        referrer.stars_balance += commission_amount
        referrer.total_stars_earned += commission_amount
        db.add(referrer)
    
    db.add(commission)
    db.add(referral)
    db.commit()
    
    logger.info(f"Commission recorded: {commission_amount} stars for referral {referral.id}")
    
    return {
        "success": True,
        "commission_id": str(commission.id),
        "commission_amount": commission_amount,
    }


@router.get("/stats")
async def get_referral_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get referral statistics for the current user."""
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    referrals = db.query(Referral).filter(
        Referral.referrer_id == current_user.id
    ).all()
    
    total_earnings = sum(r.lifetime_earnings for r in referrals)
    total_referred = len(referrals)
    active_referrals = len([r for r in referrals if r.status == ReferralStatus.ACTIVE])
    total_purchases = sum(r.referred_purchase_count for r in referrals)
    
    return {
        "total_referred": total_referred,
        "active_referrals": active_referrals,
        "lifetime_earnings": total_earnings,
        "total_purchases_by_referrals": total_purchases,
        "average_earnings_per_referral": total_earnings / max(active_referrals, 1),
    }
