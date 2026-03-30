import logging
from typing import Optional, Dict, List, Any
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_, or_
from sqlalchemy.orm import joinedload
from app.models import NFT, User, Collection, ActivityLog
from app.models.marketplace import Listing, Offer, Order, ListingStatus, OfferStatus, OrderStatus
from app.models.activity import ActivityType

logger = logging.getLogger(__name__)


class TrendingService:
    """Service for fetching trending, activity, and market analytics data."""

    @staticmethod
    async def get_activity_feed(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        days: int = 7,
        activity_types: Optional[List[str]] = None,
    ) -> tuple[list[Dict[str, Any]], int]:
        """
        Get recent activity feed (sales, listings, transfers).
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Max records to return
            days: Activity from last N days
            activity_types: Filter by activity types (e.g., ['purchase_completed', 'nft_listed'])
        
        Returns:
            Tuple of (activities list, total count)
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Build query for marketplace orders/listings
            base_filters = [
                Order.created_at >= cutoff_date,
            ]
            
            # Get orders (purchases/sales)
            order_query = select(
                Order.id,
                Order.buyer_id,
                Order.seller_id,
                Order.nft_id,
                Order.amount,
                Order.currency,
                Order.status,
                Order.created_at,
                func.lit('purchase').label('activity_type'),
                NFT.name,
                NFT.image_url,
            ).join(NFT, Order.nft_id == NFT.id)
            
            if activity_types and 'purchase_completed' not in activity_types:
                # Skip if filtering and purchase not included
                orders = []
            else:
                order_result = await db.execute(
                    order_query.filter(Order.status == OrderStatus.COMPLETED)
                    .order_by(desc(Order.created_at))
                    .offset(skip)
                    .limit(limit)
                )
                orders = order_result.all()

            # Get listings
            listing_query = select(
                Listing.id,
                Listing.seller_id,
                func.lit(None).label('buyer_id'),
                Listing.nft_id,
                Listing.price,
                Listing.currency,
                Listing.status,
                Listing.created_at,
                func.lit('listing').label('activity_type'),
                NFT.name,
                NFT.image_url,
            ).join(NFT, Listing.nft_id == NFT.id)
            
            if activity_types and 'nft_listed' not in activity_types:
                listings = []
            else:
                listing_result = await db.execute(
                    listing_query.filter(Listing.status == ListingStatus.ACTIVE)
                    .order_by(desc(Listing.created_at))
                    .offset(skip)
                    .limit(limit)
                )
                listings = listing_result.all()

            # Combine and format results
            activities = []
            
            for order in orders:
                activities.append({
                    'id': str(order.id),
                    'type': 'sale',
                    'nft_name': order.name,
                    'nft_image': order.image_url,
                    'nft_id': str(order.nft_id),
                    'price': float(order.amount),
                    'currency': order.currency,
                    'seller_id': str(order.seller_id),
                    'buyer_id': str(order.buyer_id),
                    'timestamp': order.created_at.isoformat(),
                })
            
            for listing in listings:
                activities.append({
                    'id': str(listing.id),
                    'type': 'listing',
                    'nft_name': listing.name,
                    'nft_image': listing.image_url,
                    'nft_id': str(listing.nft_id),
                    'price': float(listing.price),
                    'currency': listing.currency,
                    'seller_id': str(listing.seller_id),
                    'timestamp': listing.created_at.isoformat(),
                })

            # Sort by timestamp
            activities.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Get total count
            total_count = len(orders) + len(listings)
            
            return activities[:limit], total_count
        except Exception as e:
            logger.error(f"Error fetching activity feed: {e}", exc_info=True)
            return [], 0

    @staticmethod
    async def get_trending_nfts(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        days: int = 7,
        sort_by: str = 'sales',  # 'sales', 'views', 'volume'
    ) -> tuple[list[Dict[str, Any]], int]:
        """
        Get trending NFTs based on sales/views/volume.
        
        Args:
            db: Database session
            skip: Offset
            limit: Max results
            days: Trend period in days
            sort_by: 'sales', 'views', or 'volume'
        
        Returns:
            Tuple of (trending NFTs, total count)
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Count completed sales per NFT
            sales_subquery = select(
                Order.nft_id,
                func.count(Order.id).label('sale_count'),
                func.sum(Order.amount).label('total_volume'),
            ).where(
                and_(
                    Order.status == OrderStatus.COMPLETED,
                    Order.created_at >= cutoff_date,
                )
            ).group_by(Order.nft_id).subquery()
            
            # Get trending NFTs with sales info
            trending_query = select(
                NFT.id,
                NFT.name,
                NFT.image_url,
                NFT.collection_id,
                NFT.owner_address,
                func.coalesce(sales_subquery.c.sale_count, 0).label('sale_count'),
                func.coalesce(sales_subquery.c.total_volume, 0).label('total_volume'),
            ).outerjoin(sales_subquery, NFT.id == sales_subquery.c.nft_id)
            
            # Filter by sort criteria
            if sort_by == 'volume':
                trending_query = trending_query.order_by(desc('total_volume'))
            else:  # Default to sales
                trending_query = trending_query.order_by(desc('sale_count'))
            
            result = await db.execute(
                trending_query.offset(skip).limit(limit)
            )
            
            nfts = result.all()
            
            # Format response
            trending_nfts = []
            for nft in nfts:
                trending_nfts.append({
                    'id': str(nft.id),
                    'name': nft.name,
                    'image_url': nft.image_url,
                    'collection_id': str(nft.collection_id) if nft.collection_id else None,
                    'owner_address': nft.owner_address,
                    'sale_count': int(nft.sale_count),
                    'total_volume': float(nft.total_volume or 0),
                })
            
            # Get total count
            total_result = await db.execute(
                select(func.count(NFT.id)).where(
                    select(NFT.id).where(NFT.id.in_(
                        select(Order.nft_id).where(
                            and_(
                                Order.status == OrderStatus.COMPLETED,
                                Order.created_at >= cutoff_date,
                            )
                        )
                    )).exists()
                )
            )
            total = total_result.scalar() or 0
            
            return trending_nfts, total
        except Exception as e:
            logger.error(f"Error fetching trending NFTs: {e}", exc_info=True)
            return [], 0

    @staticmethod
    async def get_trending_collections(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        days: int = 7,
        sort_by: str = 'volume',  # 'volume', 'sales', 'floor_price'
    ) -> tuple[list[Dict[str, Any]], int]:
        """
        Get trending collections by sales volume, count, or floor price.
        
        Args:
            db: Database session
            skip: Offset
            limit: Max results
            days: Trend period
            sort_by: Sort metric
        
        Returns:
            Tuple of (trending collections, total count)
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Subquery: get sales metrics per collection
            sales_metrics = select(
                NFT.collection_id,
                func.count(Order.id).label('sale_count'),
                func.sum(Order.amount).label('total_volume'),
                func.min(Order.amount).label('min_price'),
            ).join(NFT, Order.nft_id == NFT.id).where(
                and_(
                    NFT.collection_id.isnot(None),
                    Order.status == OrderStatus.COMPLETED,
                    Order.created_at >= cutoff_date,
                )
            ).group_by(NFT.collection_id).subquery()
            
            # Get collection info with metrics
            collection_query = select(
                Collection.id,
                Collection.name,
                Collection.image_url,
                Collection.creator_id,
                Collection.floor_price,
                func.coalesce(sales_metrics.c.sale_count, 0).label('sale_count'),
                func.coalesce(sales_metrics.c.total_volume, 0).label('total_volume'),
                func.coalesce(sales_metrics.c.min_price, Collection.floor_price).label('recent_floor'),
            ).outerjoin(sales_metrics, Collection.id == sales_metrics.c.collection_id)
            
            # Apply sorting
            if sort_by == 'sales':
                collection_query = collection_query.order_by(desc('sale_count'))
            elif sort_by == 'floor_price':
                collection_query = collection_query.order_by(desc('recent_floor'))
            else:  # Default to volume
                collection_query = collection_query.order_by(desc('total_volume'))
            
            result = await db.execute(
                collection_query.offset(skip).limit(limit)
            )
            
            collections = result.all()
            
            # Format response
            trending_collections = []
            for col in collections:
                trending_collections.append({
                    'id': str(col.id),
                    'name': col.name,
                    'image_url': col.image_url,
                    'creator_id': str(col.creator_id),
                    'floor_price': float(col.floor_price or col.recent_floor or 0),
                    'recent_floor_price': float(col.recent_floor or 0),
                    'sale_count': int(col.sale_count),
                    'total_volume': float(col.total_volume or 0),
                })
            
            # Get total count
            total_result = await db.execute(
                select(func.count(Collection.id.distinct())).select_from(Collection).join(
                    NFT, NFT.collection_id == Collection.id
                ).where(NFT.id.in_(
                    select(Order.nft_id).where(
                        and_(
                            Order.status == OrderStatus.COMPLETED,
                            Order.created_at >= cutoff_date,
                        )
                    )
                ))
            )
            total = total_result.scalar() or 0
            
            return trending_collections, total
        except Exception as e:
            logger.error(f"Error fetching trending collections: {e}", exc_info=True)
            return [], 0

    @staticmethod
    async def get_floor_prices(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Dict[str, Any]], int]:
        """
        Get current floor prices for all collections.
        
        Args:
            db: Database session
            skip: Offset
            limit: Max results
        
        Returns:
            Tuple of (collections with floor prices, total count)
        """
        try:
            # Get collections with their floor prices
            floor_query = select(
                Collection.id,
                Collection.name,
                Collection.image_url,
                Collection.floor_price,
                Collection.average_price,
                Collection.ceiling_price,
                Collection.total_sales,
                Collection.total_volume,
                func.count(NFT.id).label('nft_count'),
            ).outerjoin(NFT, NFT.collection_id == Collection.id).group_by(
                Collection.id
            ).order_by(desc(Collection.floor_price)).offset(skip).limit(limit)
            
            result = await db.execute(floor_query)
            collections = result.all()
            
            # Format response
            floor_prices = []
            for col in collections:
                floor_prices.append({
                    'id': str(col.id),
                    'name': col.name,
                    'image_url': col.image_url,
                    'floor_price': float(col.floor_price or 0),
                    'average_price': float(col.average_price or 0),
                    'ceiling_price': float(col.ceiling_price or 0),
                    'total_sales': int(col.total_sales or 0),
                    'total_volume': float(col.total_volume or 0),
                    'nft_count': int(col.nft_count or 0),
                })
            
            # Get total count
            total_result = await db.execute(select(func.count(Collection.id)))
            total = total_result.scalar() or 0
            
            return floor_prices, total
        except Exception as e:
            logger.error(f"Error fetching floor prices: {e}", exc_info=True)
            return [], 0

    @staticmethod
    async def get_market_volume(
        db: AsyncSession,
        days: int = 7,
        group_by: str = 'day',  # 'day', 'hour'
    ) -> list[Dict[str, Any]]:
        """
        Get trading volume over time.
        
        Args:
            db: Database session
            days: Number of days to analyze
            group_by: Group results by 'day' or 'hour'
        
        Returns:
            List of volume data points
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            if group_by == 'hour':
                # Group by hour
                volume_query = select(
                    func.date_trunc('hour', Order.created_at).label('period'),
                    func.count(Order.id).label('transaction_count'),
                    func.sum(Order.amount).label('total_volume'),
                    func.avg(Order.amount).label('average_price'),
                ).where(
                    and_(
                        Order.status == OrderStatus.COMPLETED,
                        Order.created_at >= cutoff_date,
                    )
                ).group_by(
                    func.date_trunc('hour', Order.created_at)
                ).order_by('period')
            else:
                # Group by day (default)
                volume_query = select(
                    func.date(Order.created_at).label('period'),
                    func.count(Order.id).label('transaction_count'),
                    func.sum(Order.amount).label('total_volume'),
                    func.avg(Order.amount).label('average_price'),
                ).where(
                    and_(
                        Order.status == OrderStatus.COMPLETED,
                        Order.created_at >= cutoff_date,
                    )
                ).group_by(
                    func.date(Order.created_at)
                ).order_by('period')
            
            result = await db.execute(volume_query)
            volumes = result.all()
            
            # Format response
            volume_data = []
            for vol in volumes:
                volume_data.append({
                    'period': vol.period.isoformat() if hasattr(vol.period, 'isoformat') else str(vol.period),
                    'transaction_count': int(vol.transaction_count),
                    'total_volume': float(vol.total_volume or 0),
                    'average_price': float(vol.average_price or 0),
                })
            
            return volume_data
        except Exception as e:
            logger.error(f"Error fetching market volume: {e}", exc_info=True)
            return []

    @staticmethod
    async def get_collection_stats(
        db: AsyncSession,
        collection_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed stats for a specific collection.
        
        Args:
            db: Database session
            collection_id: Collection ID
        
        Returns:
            Collection stats or None if not found
        """
        try:
            # Get collection info
            collection_result = await db.execute(
                select(Collection).where(Collection.id == collection_id)
            )
            collection = collection_result.scalar_one_or_none()
            
            if not collection:
                return None
            
            # Get NFT count
            nft_count_result = await db.execute(
                select(func.count(NFT.id)).where(NFT.collection_id == collection_id)
            )
            nft_count = nft_count_result.scalar() or 0
            
            # Get active listings count
            listings_result = await db.execute(
                select(func.count(Listing.id)).where(
                    and_(
                        Listing.status == ListingStatus.ACTIVE,
                        NFT.collection_id == collection_id,
                    )
                ).select_from(Listing).join(NFT, Listing.nft_id == NFT.id)
            )
            active_listings = listings_result.scalar() or 0
            
            # Get 7-day stats
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            stats_result = await db.execute(
                select(
                    func.count(Order.id).label('sales_7d'),
                    func.sum(Order.amount).label('volume_7d'),
                    func.avg(Order.amount).label('avg_price_7d'),
                    func.min(Order.amount).label('min_price_7d'),
                    func.max(Order.amount).label('max_price_7d'),
                ).where(
                    and_(
                        Order.status == OrderStatus.COMPLETED,
                        Order.created_at >= cutoff_date,
                        NFT.collection_id == collection_id,
                    )
                ).select_from(Order).join(NFT, Order.nft_id == NFT.id)
            )
            stats = stats_result.one()
            
            return {
                'id': str(collection.id),
                'name': collection.name,
                'image_url': collection.image_url,
                'floor_price': float(collection.floor_price or 0),
                'average_price': float(collection.average_price or 0),
                'ceiling_price': float(collection.ceiling_price or 0),
                'nft_count': nft_count,
                'active_listings': active_listings,
                'total_sales_all_time': int(collection.total_sales),
                'total_volume_all_time': float(collection.total_volume),
                'sales_7d': int(stats.sales_7d),
                'volume_7d': float(stats.volume_7d or 0),
                'avg_price_7d': float(stats.avg_price_7d or 0),
                'min_price_7d': float(stats.min_price_7d or 0),
                'max_price_7d': float(stats.max_price_7d or 0),
            }
        except Exception as e:
            logger.error(f"Error fetching collection stats: {e}", exc_info=True)
            return None
