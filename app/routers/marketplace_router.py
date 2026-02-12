from __future__ import annotations
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.database import get_db_session
from app.utils.auth import get_current_user
from app.services.marketplace_service import MarketplaceService
from app.schemas.marketplace import (
    ListingRequest,
    ListingResponse,
    OfferRequest,
    OfferResponse,
    BuyNowRequest,
    AcceptOfferRequest,
    OrderResponse,
    ActiveListingsResponse,
    UserListingsResponse,
    ListingOffersResponse,
    UserOrdersResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/marketplace", tags=["marketplace"])


@router.post("/listings", response_model=ListingResponse, status_code=status.HTTP_201_CREATED)
async def create_listing(
    request: ListingRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user),
) -> ListingResponse:
    """Create a new NFT listing."""
    listing, error = await MarketplaceService.create_listing(
        db=db,
        nft_id=request.nft_id,
        seller_id=current_user.id,
        seller_address=current_user.wallet_address,
        price=request.price,
        currency=request.currency,
        blockchain="eth",
        expires_at=request.expires_at,
    )
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return ListingResponse.model_validate(listing)


@router.post("/listings/{listing_id}/cancel", response_model=ListingResponse)
async def cancel_listing(
    listing_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user),
) -> ListingResponse:
    """Cancel an active listing."""
    listing, error = await MarketplaceService.cancel_listing(
        db=db, listing_id=listing_id, user_id=current_user.id
    )
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return ListingResponse.model_validate(listing)


@router.get("/listings", response_model=ActiveListingsResponse)
async def get_active_listings(
    skip: int = 0,
    limit: int = 50,
    blockchain: str | None = None,
    db: AsyncSession = Depends(get_db_session),
) -> ActiveListingsResponse:
    """Get active listings."""
    listings, total = await MarketplaceService.get_active_listings(
        db=db, skip=skip, limit=limit, blockchain=blockchain
    )
    return ActiveListingsResponse(
        total=total,
        page=skip // limit + 1,
        per_page=limit,
        items=[ListingResponse.model_validate(l) for l in listings],
    )


@router.get("/listings/user", response_model=UserListingsResponse)
async def get_user_listings(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user),
) -> UserListingsResponse:
    """Get user's listings."""
    listings, total = await MarketplaceService.get_user_listings(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )
    return UserListingsResponse(
        total=total,
        page=skip // limit + 1,
        per_page=limit,
        items=[ListingResponse.model_validate(l) for l in listings],
    )


@router.post("/listings/{listing_id}/buy", response_model=OrderResponse)
async def buy_now(
    listing_id: UUID,
    request: BuyNowRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user),
) -> OrderResponse:
    """Instant buy at listing price."""
    order, error = await MarketplaceService.buy_now(
        db=db,
        listing_id=listing_id,
        buyer_id=current_user.id,
        buyer_address=current_user.wallet_address,
        transaction_hash=request.transaction_hash,
    )
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return OrderResponse.model_validate(order)


@router.post("/offers", response_model=OfferResponse, status_code=status.HTTP_201_CREATED)
async def make_offer(
    request: OfferRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user),
) -> OfferResponse:
    """Make an offer on a listing."""
    offer, error = await MarketplaceService.make_offer(
        db=db,
        listing_id=request.listing_id,
        buyer_id=current_user.id,
        buyer_address=current_user.wallet_address,
        offer_price=request.offer_price,
        currency=request.currency,
        expires_at=request.expires_at,
    )
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return OfferResponse.model_validate(offer)


@router.post("/offers/{offer_id}/accept", response_model=OrderResponse)
async def accept_offer(
    offer_id: UUID,
    request: AcceptOfferRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user),
) -> OrderResponse:
    """Accept an offer and create an order."""
    order, error = await MarketplaceService.accept_offer(
        db=db,
        offer_id=offer_id,
        seller_id=current_user.id,
        transaction_hash=request.transaction_hash,
    )
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return OrderResponse.model_validate(order)


@router.get("/listings/{listing_id}/offers", response_model=ListingOffersResponse)
async def get_listing_offers(
    listing_id: UUID,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db_session),
) -> ListingOffersResponse:
    """Get offers for a listing."""
    offers, total = await MarketplaceService.get_listing_offers(
        db=db, listing_id=listing_id, skip=skip, limit=limit
    )
    return ListingOffersResponse(
        total=total,
        page=skip // limit + 1,
        per_page=limit,
        items=[OfferResponse.model_validate(o) for o in offers],
    )


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user),
) -> OrderResponse:
    """Get order details."""
    order = await MarketplaceService.get_order_by_id(db=db, order_id=order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if order.buyer_id != current_user.id and order.seller_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")

    return OrderResponse.model_validate(order)


@router.get("/orders", response_model=UserOrdersResponse)
async def get_user_orders(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user),
) -> UserOrdersResponse:
    """Get user's buy/sell orders."""
    orders, total = await MarketplaceService.get_user_orders(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )
    return UserOrdersResponse(
        total=total,
        page=skip // limit + 1,
        per_page=limit,
        items=[OrderResponse.model_validate(o) for o in orders],
    )

@router.get("/nfts/{nft_id}/valuation")
async def get_nft_valuation(
    nft_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    from app.schemas.collection import NFTValuation
    
    valuation, error = await MarketplaceService.get_nft_valuation(db=db, nft_id=nft_id)
    if error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error)
    
    return NFTValuation(**valuation)


@router.get("/nfts/{nft_id}/price-suggestion")
async def get_price_suggestion(
    nft_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    from app.schemas.collection import PriceSuggestion
    
    suggested_price, error = await MarketplaceService.get_price_suggestion(db=db, nft_id=nft_id)
    if error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error)
    
    return PriceSuggestion(
        nft_id=str(nft_id),
        suggested_price=suggested_price,
    )


@router.get("/collections/{collection_id}/stats")
async def get_collection_stats(
    collection_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    from app.schemas.collection import CollectionStats
    
    stats, error = await MarketplaceService.get_collection_stats(db=db, collection_id=collection_id)
    if error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error)
    
    return CollectionStats(**stats)


@router.post("/collections", status_code=status.HTTP_201_CREATED)
async def create_collection(
    request,
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user),
):
    from app.schemas.collection import CollectionCreate, CollectionResponse
    
    collection, error = await MarketplaceService.create_collection(
        db=db,
        creator_id=current_user.id,
        name=request.name,
        blockchain=request.blockchain,
        description=request.description,
        contract_address=request.contract_address,
        rarity_weights=request.rarity_weights,
        image_url=request.image_url,
        banner_url=request.banner_url,
    )
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return CollectionResponse.model_validate(collection)


@router.get("/listings/rarity/{rarity_tier}")
async def get_listings_by_rarity(
    rarity_tier: str,
    collection_id: UUID | None = None,
    blockchain: str | None = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db_session),
):
    from app.models import RarityTier
    from app.schemas.collection import ListingWithRarity
    
    try:
        tier = RarityTier(rarity_tier.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid rarity tier. Must be: common, rare, epic, legendary"
        )
    
    listings, total = await MarketplaceService.get_listings_by_rarity(
        db=db,
        collection_id=collection_id,
        rarity_tier=tier,
        blockchain=blockchain,
        skip=skip,
        limit=limit,
    )
    
    return {
        "total": total,
        "page": skip // limit + 1,
        "per_page": limit,
        "items": [ListingWithRarity.model_validate(l) for l in listings],
    }


@router.get("/listings/sorted-by-rarity")
async def get_listings_sorted_by_rarity(
    collection_id: UUID | None = None,
    sort_order: str = "asc",
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db_session),
):
    from app.schemas.collection import ListingWithRarity
    
    if sort_order.lower() not in ["asc", "desc"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="sort_order must be 'asc' or 'desc'"
        )
    
    listings, total = await MarketplaceService.get_listings_sorted_by_rarity(
        db=db,
        collection_id=collection_id,
        sort_order=sort_order,
        skip=skip,
        limit=limit,
    )
    
    return {
        "total": total,
        "page": skip // limit + 1,
        "per_page": limit,
        "items": [ListingWithRarity.model_validate(l) for l in listings],
    }


@router.get("/listings/price-range")
async def get_listings_by_price_range(
    min_price: float,
    max_price: float,
    collection_id: UUID | None = None,
    blockchain: str | None = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db_session),
):
    from app.schemas.marketplace import ListingResponse
    
    if min_price > max_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_price must be less than or equal to max_price"
        )
    
    listings, total = await MarketplaceService.get_listings_by_price_range(
        db=db,
        min_price=min_price,
        max_price=max_price,
        collection_id=collection_id,
        blockchain=blockchain,
        skip=skip,
        limit=limit,
    )
    
    return {
        "total": total,
        "page": skip // limit + 1,
        "per_page": limit,
        "items": [ListingResponse.model_validate(l) for l in listings],
    }


@router.get("/collections/{collection_id}/listings")
async def get_collection_listings(
    collection_id: UUID,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db_session),
):
    from app.schemas.collection import ListingWithRarity
    
    listings, total = await MarketplaceService.get_collection_listings(
        db=db,
        collection_id=collection_id,
        skip=skip,
        limit=limit,
    )
    
    return {
        "total": total,
        "page": skip // limit + 1,
        "per_page": limit,
        "items": [ListingWithRarity.model_validate(l) for l in listings],
    }
