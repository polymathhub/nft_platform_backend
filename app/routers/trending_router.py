import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.database import get_db_session
from app.services.trending_service import TrendingService
from pydantic import BaseModel
from typing import Optional, List

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/trending", tags=["trending"])


# Response models
class ActivityItem(BaseModel):
    id: str
    type: str
    nft_name: str
    nft_image: Optional[str]
    nft_id: str
    price: float
    currency: str
    timestamp: str


class TrendingNFT(BaseModel):
    id: str
    name: str
    image_url: Optional[str]
    collection_id: Optional[str]
    owner_address: str
    sale_count: int
    total_volume: float


class TrendingCollection(BaseModel):
    id: str
    name: str
    image_url: Optional[str]
    creator_id: str
    floor_price: float
    recent_floor_price: float
    sale_count: int
    total_volume: float


class FloorPriceItem(BaseModel):
    id: str
    name: str
    image_url: Optional[str]
    floor_price: float
    average_price: float
    ceiling_price: float
    total_sales: int
    total_volume: float
    nft_count: int


class VolumeData(BaseModel):
    period: str
    transaction_count: int
    total_volume: float
    average_price: float


class CollectionStats(BaseModel):
    id: str
    name: str
    image_url: Optional[str]
    floor_price: float
    average_price: float
    ceiling_price: float
    nft_count: int
    active_listings: int
    total_sales_all_time: int
    total_volume_all_time: float
    sales_7d: int
    volume_7d: float
    avg_price_7d: float
    min_price_7d: float
    max_price_7d: float


class PaginatedResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: list


@router.get("/feed", response_model=PaginatedResponse)
async def get_activity_feed(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    days: int = Query(7, ge=1, le=90),
    activity_types: Optional[List[str]] = Query(None),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Get activity feed (recent sales, listings, transfers).
    
    Query Parameters:
    - skip: Number of records to skip (pagination)
    - limit: Max records to return (1-100)
    - days: Activity from last N days (1-90)
    - activity_types: Filter by activity type (purchase_completed, nft_listed, etc.)
    """
    try:
        activities, total = await TrendingService.get_activity_feed(
            db=db,
            skip=skip,
            limit=limit,
            days=days,
            activity_types=activity_types,
        )
        
        return {
            'total': total,
            'page': (skip // limit) + 1,
            'limit': limit,
            'items': activities,
        }
    except Exception as e:
        logger.error(f"Error getting activity feed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch activity feed: {str(e)}",
        )


@router.get("/nfts", response_model=PaginatedResponse)
async def get_trending_nfts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    days: int = Query(7, ge=1, le=90),
    sort_by: str = Query('sales', regex='^(sales|volume|views)$'),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Get trending NFTs based on sales, volume, or views.
    
    Query Parameters:
    - skip: Offset
    - limit: Max results (1-100)
    - days: Trend period in days (1-90)
    - sort_by: Sort by 'sales', 'volume', or 'views'
    """
    try:
        nfts, total = await TrendingService.get_trending_nfts(
            db=db,
            skip=skip,
            limit=limit,
            days=days,
            sort_by=sort_by,
        )
        
        return {
            'total': total,
            'page': (skip // limit) + 1,
            'limit': limit,
            'items': nfts,
        }
    except Exception as e:
        logger.error(f"Error getting trending NFTs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch trending NFTs: {str(e)}",
        )


@router.get("/collections", response_model=PaginatedResponse)
async def get_trending_collections(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    days: int = Query(7, ge=1, le=90),
    sort_by: str = Query('volume', regex='^(volume|sales|floor_price)$'),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Get trending collections by volume, sales, or floor price.
    
    Query Parameters:
    - skip: Offset
    - limit: Max results (1-100)
    - days: Trend period in days (1-90)
    - sort_by: Sort by 'volume', 'sales', or 'floor_price'
    """
    try:
        collections, total = await TrendingService.get_trending_collections(
            db=db,
            skip=skip,
            limit=limit,
            days=days,
            sort_by=sort_by,
        )
        
        return {
            'total': total,
            'page': (skip // limit) + 1,
            'limit': limit,
            'items': collections,
        }
    except Exception as e:
        logger.error(f"Error getting trending collections: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch trending collections: {str(e)}",
        )


@router.get("/floor-prices", response_model=PaginatedResponse)
async def get_floor_prices(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Get current floor prices for all collections.
    
    Query Parameters:
    - skip: Offset
    - limit: Max results (1-100)
    """
    try:
        prices, total = await TrendingService.get_floor_prices(
            db=db,
            skip=skip,
            limit=limit,
        )
        
        return {
            'total': total,
            'page': (skip // limit) + 1,
            'limit': limit,
            'items': prices,
        }
    except Exception as e:
        logger.error(f"Error getting floor prices: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch floor prices: {str(e)}",
        )


@router.get("/volume")
async def get_market_volume(
    days: int = Query(7, ge=1, le=90),
    group_by: str = Query('day', regex='^(day|hour)$'),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Get trading volume over time.
    
    Query Parameters:
    - days: Number of days to analyze (1-90)
    - group_by: Group by 'day' or 'hour'
    """
    try:
        volume_data = await TrendingService.get_market_volume(
            db=db,
            days=days,
            group_by=group_by,
        )
        
        return {
            'data': volume_data,
            'period_days': days,
            'group_by': group_by,
        }
    except Exception as e:
        logger.error(f"Error getting market volume: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch market volume: {str(e)}",
        )


@router.get("/collections/{collection_id}/stats")
async def get_collection_stats(
    collection_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Get detailed statistics for a specific collection.
    
    Path Parameters:
    - collection_id: UUID of the collection
    """
    try:
        stats = await TrendingService.get_collection_stats(
            db=db,
            collection_id=collection_id,
        )
        
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection not found",
            )
        
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting collection stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch collection stats: {str(e)}",
        )
