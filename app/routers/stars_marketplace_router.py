"""Telegram Stars Marketplace Integration - handles NFT purchases using Telegram Stars."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime
import uuid
import logging
from typing import Optional
from decimal import Decimal

from app.database import get_db
from app.models import User, TONWallet, StarTransaction, NFT, Listing, Order
from app.security.auth import get_current_user
from app.utils.logger import logger

router = APIRouter(prefix="/api/v1/stars/marketplace", tags=["Stars Marketplace"])

# ========== SCHEMAS ==========

class StarsPurchaseRequest(BaseModel):
    """Request to purchase an NFT with Telegram Stars."""
    listing_id: str
    amount_stars: int  # Amount of Telegram Stars to send
    description: Optional[str] = None


class StarsPurchaseResponse(BaseModel):
    """Response with purchase details and payment request."""
    invoice_id: str
    nft_id: str
    listing_id: str
    amount_stars: int
    currency: str = "XTR"  # Telegram Stars currency code
    payment_link: Optional[str] = None
    message: str


class StarsPaymentConfirmation(BaseModel):
    """Confirmation of successful Telegram Stars payment."""
    invoice_id: str
    telegram_payment_charge_id: str
    provider_payment_charge_id: Optional[str] = None
    successful: bool


class NFTMarketplacePrice(BaseModel):
    """NFT price displayed in Stars on marketplace."""
    nft_id: str
    nft_name: str
    price_stars: int
    original_price_usdt: Optional[float] = None
    creator: str
    image_url: Optional[str] = None


# ========== CONSTANTS ==========

# Exchange rate: 1 USDT = ~100 Telegram Stars (configurable)
USDT_TO_STARS_RATE = 100

# Platform fee structure
PLATFORM_FEE_PERCENT = 5  # 5% platform fee
CREATOR_ROYALTY_PERCENT = 10  # 10% to original creator


# ========== HELPER FUNCTIONS ==========

def convert_usdt_to_stars(usdt_amount: float) -> int:
    """Convert USDT price to Telegram Stars."""
    return max(1, int(usdt_amount * USDT_TO_STARS_RATE))


def convert_stars_to_usdt(stars_amount: int) -> float:
    """Convert Telegram Stars to USDT."""
    return stars_amount / USDT_TO_STARS_RATE


# ========== ENDPOINTS ==========

@router.post("/buy-nft", response_model=StarsPurchaseResponse)
async def create_star_purchase(
    request: StarsPurchaseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StarsPurchaseResponse:
    """
    Create a purchase request for an NFT using Telegram Stars.
    Returns invoice details and payment link.
    """
    try:
        # Get listing details
        listing = db.execute(
            select(Listing).where(Listing.id == uuid.UUID(request.listing_id))
        ).scalar_one_or_none()
        
        if not listing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Listing not found"
            )
        
        # Check if user has TON wallet connected
        wallet = db.execute(
            select(TONWallet).where(
                (TONWallet.user_id == current_user.id) &
                (TONWallet.status == "connected")
            )
        ).scalar_one_or_none()
        
        if not wallet:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please connect your TON wallet first"
            )
        
        # Verify star amount
        expected_stars = convert_usdt_to_stars(float(listing.price))
        if request.amount_stars < expected_stars:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stars. Required: {expected_stars}, Provided: {request.amount_stars}"
            )
        
        # Generate invoice ID
        invoice_id = f"inv_stars_{uuid.uuid4().hex[:12]}"
        
        # Create star transaction record (pending status)
        star_transaction = StarTransaction(
            id=uuid.uuid4(),
            user_id=current_user.id,
            ton_wallet_id=wallet.id,
            amount_stars=str(request.amount_stars),
            transaction_type="buy_nft",
            related_nft_id=listing.nft_id,
            related_listing_id=uuid.UUID(request.listing_id),
            status="pending",
            description=request.description or f"Purchase NFT from listing {request.listing_id}",
            metadata={
                "invoice_id": invoice_id,
                "seller_id": str(listing.seller_id),
                "conversion_rate": USDT_TO_STARS_RATE,
                "platform_fee_percent": PLATFORM_FEE_PERCENT,
                "creator_royalty_percent": CREATOR_ROYALTY_PERCENT,
            }
        )
        
        db.add(star_transaction)
        db.commit()
        
        # In production, this would integrate with Telegram Bot API
        # to generate actual sticker pack or in-app payment link
        payment_link = (
            f"https://t.me/your_bot_username/marketplace"
            f"?startapp=pay_{invoice_id}"
        )
        
        return StarsPurchaseResponse(
            invoice_id=invoice_id,
            nft_id=str(listing.nft_id),
            listing_id=str(listing.id),
            amount_stars=request.amount_stars,
            payment_link=payment_link,
            message=f"Proceed to payment to purchase this NFT for {request.amount_stars} Telegram Stars"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating star purchase: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create purchase"
        )


@router.post("/payment-confirmation")
async def confirm_star_payment(
    confirmation: StarsPaymentConfirmation,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Confirm payment completion and finalize NFT purchase.
    Called by Telegram Bot after successful payment.
    """
    try:
        # Find the pending transaction
        star_transaction = db.execute(
            select(StarTransaction).where(
                (StarTransaction.metadata['invoice_id'].astext == confirmation.invoice_id) &
                (StarTransaction.user_id == current_user.id) &
                (StarTransaction.status == "pending")
            )
        ).scalar_one_or_none()
        
        if not star_transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found or already processed"
            )
        
        if not confirmation.successful:
            # Mark transaction as failed
            star_transaction.status = "failed"
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment was not successful"
            )
        
        # Update transaction with payment confirmation
        star_transaction.telegram_payment_charge_id = confirmation.telegram_payment_charge_id
        star_transaction.provider_payment_charge_id = confirmation.provider_payment_charge_id
        star_transaction.status = "completed"
        star_transaction.completed_at = datetime.utcnow()
        
        # Get the related listing
        listing = db.execute(
            select(Listing).where(Listing.id == star_transaction.related_listing_id)
        ).scalar_one_or_none()
        
        if not listing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Related listing not found"
            )
        
        # Create order to complete the purchase
        order = Order(
            id=uuid.uuid4(),
            listing_id=listing.id,
            buyer_id=current_user.id,
            seller_id=listing.seller_id,
            nft_id=listing.nft_id,
            status="completed",
            amount=float(star_transaction.amount_stars) / USDT_TO_STARS_RATE,  # Convert back to USDT for accounting
            currency="STARS",  # Mark currency as STARS
            created_at=datetime.utcnow()
        )
        
        # Update listing to sold
        listing.status = "sold"
        listing.sold_at = datetime.utcnow()
        listing.sold_to = current_user.id
        
        db.add(order)
        db.commit()
        
        return {
            "success": True,
            "message": "NFT purchased successfully",
            "order_id": str(order.id),
            "nft_id": str(listing.nft_id),
            "redirect": f"/dashboard?view=nft&id={listing.nft_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming star payment: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to confirm payment"
        )


@router.get("/marketplace-prices")
async def get_marketplace_prices(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> dict:
    """Get NFT prices displayed in Telegram Stars."""
    try:
        # Get active listings with NFT info
        listings = db.execute(
            select(Listing).where(Listing.status == "active").offset(skip).limit(limit)
        ).scalars().all()
        
        prices = []
        for listing in listings:
            nft = db.execute(
                select(NFT).where(NFT.id == listing.nft_id)
            ).scalar_one_or_none()
            
            if nft:
                stars_price = convert_usdt_to_stars(float(listing.price))
                prices.append({
                    "nft_id": str(nft.id),
                    "nft_name": nft.name,
                    "price_stars": stars_price,
                    "original_price_usdt": float(listing.price),
                    "creator": str(nft.creator_id),
                    "image_url": nft.image_url
                })
        
        return {
            "success": True,
            "exchange_rate": f"1 USDT = {USDT_TO_STARS_RATE} Telegram Stars",
            "platform_fee_percent": PLATFORM_FEE_PERCENT,
            "creator_royalty_percent": CREATOR_ROYALTY_PERCENT,
            "total": len(prices),
            "items": prices
        }
        
    except Exception as e:
        logger.error(f"Error getting marketplace prices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get prices"
        )


@router.get("/transaction-history")
async def get_star_transaction_history(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get user's Telegram Stars transaction history."""
    try:
        transactions = db.execute(
            select(StarTransaction).where(
                StarTransaction.user_id == current_user.id
            ).offset(skip).limit(limit)
        ).scalars().all()
        
        return {
            "success": True,
            "total": len(transactions),
            "transactions": [
                {
                    "id": str(t.id),
                    "amount_stars": t.amount_stars,
                    "type": t.transaction_type,
                    "status": t.status,
                    "description": t.description,
                    "created_at": t.created_at,
                    "completed_at": t.completed_at
                }
                for t in transactions
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting transaction history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get history"
        )
