import logging
from typing import Optional, Dict
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
from app.models import NFT, User, Wallet, Collection, RarityTier
from app.models.marketplace import Listing, Offer, Order, ListingStatus, OfferStatus, OrderStatus
from app.models.nft import NFTStatus
from app.config import get_settings
from app.utils.blockchain_utils import USDTHelper
from app.services.valuation_service import ValuationService

logger = logging.getLogger(__name__)
settings = get_settings()


class MarketplaceService:

    @staticmethod
    def validate_listing_currency(currency: str, blockchain: str) -> tuple[bool, Optional[str]]:
        if currency.upper() == "USDT":
            if not USDTHelper.is_usdt_supported(blockchain):
                return False, f"USDT is not supported on {blockchain}. Use Ethereum, Polygon, Arbitrum, Optimism, Avalanche, or Base."
            return True, None
        
        logger.warning(f"Non-USDT currency '{currency}' may have limited support")
        return True, None
    
    @staticmethod
    def validate_usdt_transaction(price: float) -> tuple[bool, Optional[str]]:
        return USDTHelper.validate_usdt_amount(price, settings.usdt_min_transaction)

    @staticmethod
    async def create_listing(
        db: AsyncSession,
        nft_id: UUID,
        seller_id: UUID,
        seller_address: str,
        price: float,
        currency: str,
        blockchain: str,
        expires_at: Optional[datetime] = None,
    ) -> tuple[Optional[Listing], Optional[str]]:

        is_valid, error = MarketplaceService.validate_listing_currency(currency, blockchain)
        if not is_valid:
            return None, error
        
        # Validate USDT amount if using USDT
        if currency.upper() == "USDT":
            is_valid, error = MarketplaceService.validate_usdt_transaction(price)
            if not is_valid:
                return None, error
        
        result = await db.execute(
            select(NFT).where(
                and_(
                    NFT.id == nft_id,
                    NFT.user_id == seller_id,
                    NFT.status == NFTStatus.MINTED,
                )
            )
        )
        nft = result.scalar_one_or_none()
        if not nft:
            return None, "NFT not found, not owned by user, or not minted"

        if nft.is_locked:
            return None, "NFT is locked and cannot be listed"

        listing = Listing(
            nft_id=nft_id,
            seller_id=seller_id,
            seller_address=seller_address,
            price=price,
            currency=currency,
            blockchain=blockchain,
            status=ListingStatus.ACTIVE,
            expires_at=expires_at,
        )
        db.add(listing)

        nft.is_locked = True
        nft.lock_reason = "marketplace"
        await db.commit()
        await db.refresh(listing)
        
        logger.info(f"Listed NFT {nft_id} for {price} {currency}")
        return listing, None

    @staticmethod
    async def cancel_listing(
        db: AsyncSession,
        listing_id: UUID,
        user_id: UUID,
    ) -> tuple[Optional[Listing], Optional[str]]:
        result = await db.execute(select(Listing).where(Listing.id == listing_id))
        listing = result.scalar_one_or_none()
        if not listing:
            return None, "Listing not found"

        if listing.seller_id != user_id:
            return None, "Unauthorized: not the listing seller"

        if listing.status != ListingStatus.ACTIVE:
            return None, f"Cannot cancel listing with status {listing.status}"

        listing.status = ListingStatus.CANCELLED
        nft_result = await db.execute(select(NFT).where(NFT.id == listing.nft_id))
        nft = nft_result.scalar_one_or_none()
        if nft:
            nft.is_locked = False
            nft.lock_reason = None

        await db.commit()
        await db.refresh(listing)
        return listing, None

    @staticmethod
    async def make_offer(
        db: AsyncSession,
        listing_id: UUID,
        buyer_id: UUID,
        buyer_address: str,
        offer_price: float,
        currency: str,
        expires_at: Optional[datetime] = None,
    ) -> tuple[Optional[Offer], Optional[str]]:
        result = await db.execute(select(Listing).where(Listing.id == listing_id))
        listing = result.scalar_one_or_none()
        if not listing:
            return None, "Listing not found"

        if listing.status != ListingStatus.ACTIVE:
            return None, "Listing is not active"

        if listing.seller_id == buyer_id:
            return None, "Cannot make offer on own listing"

        offer = Offer(
            listing_id=listing_id,
            nft_id=listing.nft_id,
            buyer_id=buyer_id,
            buyer_address=buyer_address,
            offer_price=offer_price,
            currency=currency,
            status=OfferStatus.PENDING,
            expires_at=expires_at,
        )
        db.add(offer)
        await db.commit()
        await db.refresh(offer)
        return offer, None

    @staticmethod
    async def accept_offer(
        db: AsyncSession,
        offer_id: UUID,
        seller_id: UUID,
        transaction_hash: str,
    ) -> tuple[Optional[Order], Optional[str]]:
        result = await db.execute(select(Offer).where(Offer.id == offer_id))
        offer = result.scalar_one_or_none()
        if not offer:
            return None, "Offer not found"

        if offer.status != OfferStatus.PENDING:
            return None, f"Cannot accept offer with status {offer.status}"

        listing_result = await db.execute(
            select(Listing).where(Listing.id == offer.listing_id)
        )
        listing = listing_result.scalar_one_or_none()
        if not listing or listing.seller_id != seller_id:
            return None, "Unauthorized: not the listing seller"

        nft_result = await db.execute(select(NFT).where(NFT.id == offer.nft_id))
        nft = nft_result.scalar_one_or_none()
        if not nft:
            return None, "NFT not found"

        royalty_amount = offer.offer_price * (nft.royalty_percentage / 100)
        platform_fee = offer.offer_price * 0.025

        order = Order(
            listing_id=listing_id,
            offer_id=offer_id,
            nft_id=offer.nft_id,
            seller_id=listing.seller_id,
            buyer_id=offer.buyer_id,
            amount=offer.offer_price,
            currency=offer.currency,
            blockchain=listing.blockchain,
            transaction_hash=transaction_hash,
            status=OrderStatus.CONFIRMED,
            royalty_amount=royalty_amount,
            platform_fee=platform_fee,
        )
        db.add(order)

        offer.status = OfferStatus.ACCEPTED
        listing.status = ListingStatus.ACCEPTED
        nft.owner_address = offer.buyer_address
        nft.status = NFTStatus.TRANSFERRED
        nft.is_locked = False
        nft.lock_reason = None
        await db.commit()
        await db.refresh(order)
        return order, None

    @staticmethod
    async def buy_now(
        db: AsyncSession,
        listing_id: UUID,
        buyer_id: UUID,
        buyer_address: str,
        transaction_hash: str,
    ) -> tuple[Optional[Order], Optional[str]]:
        result = await db.execute(select(Listing).where(Listing.id == listing_id))
        listing = result.scalar_one_or_none()
        if not listing:
            return None, "Listing not available"

        if listing.status != ListingStatus.ACTIVE:
            return None, "Listing is not active yet or has already been sold"

        if datetime.utcnow() > listing.expires_at if listing.expires_at else False:
            return None, "Listing has expired"

        if listing.seller_id == buyer_id:
            return None, "Cannot buy own listing"

        nft_result = await db.execute(select(NFT).where(NFT.id == listing.nft_id))
        nft = nft_result.scalar_one_or_none()
        if not nft:
            return None, "NFT not found"

        royalty_amount = listing.price * (nft.royalty_percentage / 100)
        platform_fee = listing.price * 0.025

        order = Order(
            listing_id=listing_id,
            nft_id=listing.nft_id,
            seller_id=listing.seller_id,
            buyer_id=buyer_id,
            amount=listing.price,
            currency=listing.currency,
            blockchain=listing.blockchain,
            transaction_hash=transaction_hash,
            status=OrderStatus.COMPLETED,
            royalty_amount=royalty_amount,
            platform_fee=platform_fee,
            completed_at=datetime.utcnow(),
        )
        db.add(order)

        listing.status = ListingStatus.ACCEPTED
        nft.owner_address = buyer_address
        nft.status = NFTStatus.TRANSFERRED
        nft.is_locked = False
        nft.lock_reason = None
        await db.commit()
        await db.refresh(order)
        return order, None

    @staticmethod
    async def get_active_listings(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        blockchain: Optional[str] = None,
    ) -> tuple[list[Listing], int]:
        
        query = select(Listing).where(Listing.status == ListingStatus.ACTIVE)

        if blockchain:
            query = query.where(Listing.blockchain == blockchain)

        count_result = await db.execute(
            select(Listing).where(Listing.status == ListingStatus.ACTIVE)
        )
        total = len(count_result.scalars().all())

        result = await db.execute(
            query.order_by(desc(Listing.created_at)).offset(skip).limit(limit)
        )
        listings = result.scalars().all()
        return listings, total

    @staticmethod
    async def get_user_listings(
        db: AsyncSession,
        user_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Listing], int]:
        
        query = select(Listing).where(Listing.seller_id == user_id)

        count_result = await db.execute(query)
        total = len(count_result.scalars().all())

        result = await db.execute(
            query.order_by(desc(Listing.created_at)).offset(skip).limit(limit)
        )
        listings = result.scalars().all()
        return listings, total

    @staticmethod
    async def get_listing_offers(
        db: AsyncSession,
        listing_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Offer], int]:
        
        query = select(Offer).where(Listing.id == listing_id)

        count_result = await db.execute(query)
        total = len(count_result.scalars().all())

        result = await db.execute(
            query.order_by(desc(Offer.created_at)).offset(skip).limit(limit)
        )
        offers = result.scalars().all()
        return offers, total

    @staticmethod
    async def get_order_by_id(db: AsyncSession, order_id: UUID) -> Optional[Order]:
        result = await db.execute(select(Order).where(Order.id == order_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_orders(
        db: AsyncSession,
        user_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Order], int]:
        
        """Get user's buy/sell orders."""
        query = select(Order).where(
            or_(Order.buyer_id == user_id, Order.seller_id == user_id)
        )

        count_result = await db.execute(query)
        total = len(count_result.scalars().all())

        result = await db.execute(
            query.order_by(desc(Order.created_at)).offset(skip).limit(limit)
        )
        orders = result.scalars().all()
        return orders, total

    @staticmethod
    async def get_price_suggestion(
        db: AsyncSession,
        nft_id: UUID,
    ) -> tuple[Optional[float], Optional[str]]:
        result = await db.execute(select(NFT).where(NFT.id == nft_id))
        nft = result.scalar_one_or_none()
        if not nft:
            return None, "NFT not found"
        
        collection = None
        if nft.collection_id:
            collection_result = await db.execute(
                select(Collection).where(Collection.id == nft.collection_id)
            )
            collection = collection_result.scalar_one_or_none()
        
        suggested_price = await ValuationService.suggest_listing_price(db, nft, collection)
        return suggested_price, None

    @staticmethod
    async def get_nft_valuation(
        db: AsyncSession,
        nft_id: UUID,
    ) -> tuple[Optional[Dict], Optional[str]]:
        result = await db.execute(select(NFT).where(NFT.id == nft_id))
        nft = result.scalar_one_or_none()
        if not nft:
            return None, "NFT not found"
        
        valuation = await ValuationService.get_nft_valuation(db, nft_id)
        return valuation, None

    @staticmethod
    async def get_collection_stats(
        db: AsyncSession,
        collection_id: UUID,
    ) -> tuple[Optional[Dict], Optional[str]]:
        result = await db.execute(
            select(Collection).where(Collection.id == collection_id)
        )
        collection = result.scalar_one_or_none()
        if not collection:
            return None, "Collection not found"
        
        stats = await ValuationService.get_collection_stats(db, collection_id)
        return stats, None

    @staticmethod
    async def create_collection(
        db: AsyncSession,
        creator_id: UUID,
        name: str,
        blockchain: str,
        description: Optional[str] = None,
        contract_address: Optional[str] = None,
        rarity_weights: Optional[Dict[str, float]] = None,
        image_url: Optional[str] = None,
        banner_url: Optional[str] = None,
    ) -> tuple[Optional[Collection], Optional[str]]:
        if contract_address:
            existing = await db.execute(
                select(Collection).where(Collection.contract_address == contract_address)
            )
            if existing.scalar_one_or_none():
                return None, f"Collection with contract {contract_address} already exists"
        
        collection = Collection(
            creator_id=creator_id,
            name=name,
            description=description,
            blockchain=blockchain,
            contract_address=contract_address,
            rarity_weights=rarity_weights or {},
            image_url=image_url,
            banner_url=banner_url,
        )
        db.add(collection)
        await db.commit()
        await db.refresh(collection)
        
        logger.info(f"Collection created: {name} on {blockchain}")
        return collection, None

    @staticmethod
    async def update_collection_rarity_weights(
        db: AsyncSession,
        collection_id: UUID,
        rarity_weights: Dict[str, float],
    ) -> tuple[Optional[Collection], Optional[str]]:
        result = await db.execute(
            select(Collection).where(Collection.id == collection_id)
        )
        collection = result.scalar_one_or_none()
        if not collection:
            return None, "Collection not found"
        
        collection.rarity_weights = rarity_weights
        await db.commit()
        await db.refresh(collection)
        
        logger.info(f"Updated rarity weights for collection {collection_id}")
        return collection, None

    @staticmethod
    async def get_listings_by_rarity(
        db: AsyncSession,
        collection_id: Optional[UUID] = None,
        rarity_tier: Optional[RarityTier] = None,
        blockchain: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Listing], int]:
        """Get active listings filtered by rarity tier."""
        query = select(Listing).where(Listing.status == ListingStatus.ACTIVE)
        
        if blockchain:
            query = query.where(Listing.blockchain == blockchain)
        
        if collection_id or rarity_tier:
            query = query.join(NFT)
            if collection_id:
                query = query.where(NFT.collection_id == collection_id)
            if rarity_tier:
                query = query.where(NFT.rarity_tier == rarity_tier)
        
        count_result = await db.execute(query)
        total = len(count_result.scalars().all())
        
        result = await db.execute(
            query.order_by(desc(Listing.created_at)).offset(skip).limit(limit)
        )
        listings = result.scalars().all()
        return listings, total

    @staticmethod
    async def get_listings_sorted_by_rarity(
        db: AsyncSession,
        collection_id: Optional[UUID] = None,
        sort_order: str = "asc",  # 'asc' for lowest rarity first, 'desc' for highest
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Listing], int]:
        """Get active listings sorted by rarity score."""
        query = select(Listing).where(Listing.status == ListingStatus.ACTIVE).join(NFT)
        
        if collection_id:
            query = query.where(NFT.collection_id == collection_id)
        
        count_result = await db.execute(query)
        total = len(count_result.scalars().all())
        
        # Sort by rarity score
        if sort_order.lower() == "desc":
            query = query.order_by(desc(NFT.rarity_score))
        else:
            query = query.order_by(NFT.rarity_score)
        
        result = await db.execute(query.offset(skip).limit(limit))
        listings = result.scalars().all()
        return listings, total

    @staticmethod
    async def get_listings_by_price_range(
        db: AsyncSession,
        min_price: float,
        max_price: float,
        collection_id: Optional[UUID] = None,
        blockchain: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Listing], int]:
        """Get active listings within a price range."""
        query = select(Listing).where(
            and_(
                Listing.status == ListingStatus.ACTIVE,
                Listing.price >= min_price,
                Listing.price <= max_price,
            )
        )
        
        if blockchain:
            query = query.where(Listing.blockchain == blockchain)
        
        if collection_id:
            query = query.join(NFT).where(NFT.collection_id == collection_id)
        
        count_result = await db.execute(query)
        total = len(count_result.scalars().all())
        
        result = await db.execute(
            query.order_by(Listing.price).offset(skip).limit(limit)
        )
        listings = result.scalars().all()
        return listings, total

    @staticmethod
    async def get_collection_listings(
        db: AsyncSession,
        collection_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Listing], int]:
        """Get all active listings for a collection."""
        query = select(Listing).where(
            and_(
                Listing.status == ListingStatus.ACTIVE,
                NFT.collection_id == collection_id,
            )
        ).join(NFT)
        
        count_result = await db.execute(query)
        total = len(count_result.scalars().all())
        
        result = await db.execute(
            query.order_by(desc(Listing.created_at)).offset(skip).limit(limit)
        )
        listings = result.scalars().all()
        return listings, total
