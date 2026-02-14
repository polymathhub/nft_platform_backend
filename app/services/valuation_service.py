import logging
from typing import Optional, Dict, List, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.models import NFT, Collection, Order, RarityTier
from app.models.marketplace import Order as MarketOrder, OrderStatus

logger = logging.getLogger(__name__)


class ValuationService:
    """Calculates NFT rarity scores and suggests fair market prices."""

    @staticmethod
    def calculate_rarity_score(
        attributes: Dict[str, str],
        collection_weights: Optional[Dict[str, float]] = None,
    ) -> float:
        if not attributes:
            return 50.0
        
        weights = collection_weights or {}
        if not weights:
            weights = {key: 1.0 for key in attributes.keys()}
        
        total_weight = sum(weights.values()) or 1
        normalized_weights = {k: v / total_weight for k, v in weights.items()}
        
        score = 0.0
        for trait_name, trait_value in attributes.items():
            weight = normalized_weights.get(trait_name, 1.0 / len(attributes))
            trait_specificity = min(len(str(trait_value)) / 50, 1.0)
            score += weight * (trait_specificity * 100)
        
        return min(score, 100.0)

    @staticmethod
    def determine_rarity_tier(rarity_score: float) -> RarityTier:
        if rarity_score >= 80:
            return RarityTier.LEGENDARY
        elif rarity_score >= 60:
            return RarityTier.EPIC
        elif rarity_score >= 40:
            return RarityTier.RARE
        else:
            return RarityTier.COMMON

    @staticmethod
    async def update_nft_rarity(
        db: AsyncSession,
        nft: NFT,
        collection: Optional[Collection] = None,
    ) -> None:
        rarity_score = ValuationService.calculate_rarity_score(
            nft.attributes or {},
            collection.rarity_weights if collection else None,
        )
        
        nft.rarity_score = rarity_score
        nft.rarity_tier = ValuationService.determine_rarity_tier(rarity_score)
        await db.flush()

    @staticmethod
    async def get_comparable_sales(
        db: AsyncSession,
        collection_id: Optional[UUID] = None,
        rarity_tier: Optional[RarityTier] = None,
        days: int = 30,
        limit: int = 10,
    ) -> List[Tuple[float, datetime]]:
        """
        Get recent comparable sales for valuation.
        
        Returns:
            List of (price, completed_at) tuples
        """
        query = select(MarketOrder.amount, MarketOrder.completed_at).where(
            and_(
                MarketOrder.status == OrderStatus.COMPLETED,
                MarketOrder.completed_at >= datetime.utcnow() - timedelta(days=days),
            )
        )
        
        if collection_id:
            query = query.join(NFT).where(NFT.collection_id == collection_id)
        
        if rarity_tier:
            query = query.join(NFT).where(NFT.rarity_tier == rarity_tier)
        
        result = await db.execute(query.limit(limit))
        return result.all()

    @staticmethod
    async def suggest_listing_price(
        db: AsyncSession,
        nft: NFT,
        collection: Optional[Collection] = None,
    ) -> Optional[float]:
        """
        Suggest a fair listing price based on comparable sales.
        
        Returns:
            Suggested price or None if insufficient data
        """
        if not nft.rarity_tier:
            return collection.floor_price if collection else None
        
        # Get comparable sales for same rarity tier
        comparable = await ValuationService.get_comparable_sales(
            db,
            collection_id=nft.collection_id,
            rarity_tier=nft.rarity_tier,
            days=30,
            limit=20,
        )
        
        if not comparable:
            # Fall back to collection floor price
            return collection.floor_price if collection else None
        
        prices = [price for price, _ in comparable]
        
        # Use median as base, adjust for individual rarity score
        prices.sort()
        median_price = prices[len(prices) // 2]
        
        # Adjust based on rarity score relative to tier average
        if nft.rarity_score:
            tier_min = {
                RarityTier.COMMON: 0,
                RarityTier.RARE: 40,
                RarityTier.EPIC: 60,
                RarityTier.LEGENDARY: 80,
            }
            tier_max = {
                RarityTier.COMMON: 40,
                RarityTier.RARE: 60,
                RarityTier.EPIC: 80,
                RarityTier.LEGENDARY: 100,
            }
            
            min_score = tier_min.get(nft.rarity_tier, 0)
            max_score = tier_max.get(nft.rarity_tier, 100)
            tier_range = max_score - min_score or 1
            
            # Position within tier (0-1)
            position = (nft.rarity_score - min_score) / tier_range
            
            # Adjust price: 20% variance within tier
            adjustment = 0.9 + (position * 0.2)
            suggested_price = median_price * adjustment
        else:
            suggested_price = median_price
        
        return round(suggested_price, 2)

    @staticmethod
    async def update_collection_analytics(
        db: AsyncSession,
        collection_id: UUID,
    ) -> None:
        """Update collection floor price, average price, and total volume."""
        from sqlalchemy import and_
        from app.models.marketplace import Listing, ListingStatus
        
        # Get floor price (lowest active listing)
        floor_result = await db.execute(
            select(func.min(Listing.price)).where(
                and_(
                    Listing.status == ListingStatus.ACTIVE,
                    NFT.collection_id == collection_id,
                )
            ).join(NFT)
        )
        floor_price = floor_result.scalar()
        
        # Get average price of recent sales (last 30 days)
        avg_result = await db.execute(
            select(func.avg(MarketOrder.amount)).where(
                and_(
                    MarketOrder.status == OrderStatus.COMPLETED,
                    NFT.collection_id == collection_id,
                    MarketOrder.completed_at >= datetime.utcnow() - timedelta(days=30),
                )
            ).join(NFT)
        )
        average_price = avg_result.scalar()
        
        # Get total volume and sales count
        volume_result = await db.execute(
            select(func.sum(MarketOrder.amount), func.count(MarketOrder.id)).where(
                and_(
                    MarketOrder.status == OrderStatus.COMPLETED,
                    NFT.collection_id == collection_id,
                )
            ).join(NFT)
        )
        total_volume, total_sales = volume_result.one()
        total_volume = total_volume or 0.0
        total_sales = total_sales or 0
        
        # Get ceiling price (highest sale)
        ceiling_result = await db.execute(
            select(func.max(MarketOrder.amount)).where(
                and_(
                    MarketOrder.status == OrderStatus.COMPLETED,
                    NFT.collection_id == collection_id,
                )
            ).join(NFT)
        )
        ceiling_price = ceiling_result.scalar()
        
        # Update collection
        collection_result = await db.execute(
            select(Collection).where(Collection.id == collection_id)
        )
        collection = collection_result.scalar_one_or_none()
        
        if collection:
            collection.floor_price = floor_price
            collection.average_price = average_price
            collection.ceiling_price = ceiling_price
            collection.total_volume = float(total_volume)
            collection.total_sales = total_sales
            await db.flush()
            
            logger.info(
                f"Updated collection {collection_id} analytics: "
                f"floor={floor_price}, avg={average_price}, volume={total_volume}"
            )

    @staticmethod
    async def get_collection_stats(
        db: AsyncSession,
        collection_id: UUID,
    ) -> Dict:
        """Get collection statistics."""
        result = await db.execute(
            select(Collection).where(Collection.id == collection_id)
        )
        collection = result.scalar_one_or_none()
        
        if not collection:
            return {}
        
        return {
            "id": str(collection.id),
            "name": collection.name,
            "floor_price": collection.floor_price,
            "average_price": collection.average_price,
            "ceiling_price": collection.ceiling_price,
            "total_volume": collection.total_volume,
            "total_sales": collection.total_sales,
        }

    @staticmethod
    async def get_nft_valuation(
        db: AsyncSession,
        nft_id: UUID,
    ) -> Dict:
        """Get complete valuation data for an NFT."""
        result = await db.execute(
            select(NFT).where(NFT.id == nft_id)
        )
        nft = result.scalar_one_or_none()
        
        if not nft:
            return {}
        
        collection = None
        if nft.collection_id:
            collection_result = await db.execute(
                select(Collection).where(Collection.id == nft.collection_id)
            )
            collection = collection_result.scalar_one_or_none()
        
        suggested_price = await ValuationService.suggest_listing_price(db, nft, collection)
        
        return {
            "nft_id": str(nft.id),
            "name": nft.name,
            "rarity_score": nft.rarity_score,
            "rarity_tier": nft.rarity_tier,
            "attributes": nft.attributes,
            "suggested_price": suggested_price,
            "collection_floor_price": collection.floor_price if collection else None,
            "collection_average_price": collection.average_price if collection else None,
        }
