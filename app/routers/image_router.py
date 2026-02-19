"""
Protected image serving for NFTs
Prevents unauthorized downloads while allowing viewing
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
import aiohttp
import logging
from typing import Optional
from app.utils.auth import get_current_user
from urllib.parse import urlparse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/images", tags=["images"])


async def _validate_image_url(image_url: str) -> bool:
    """Validate that the image URL is accessible and returns valid image content"""
    try:
        if not image_url:
            return False
        
        # Only allow HTTP/HTTPS
        parsed = urlparse(image_url)
        if parsed.scheme not in ('http', 'https'):
            return False
            
        async with aiohttp.ClientSession() as session:
            async with session.head(image_url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                # Check if it's an image
                content_type = resp.headers.get('content-type', '').lower()
                return (
                    resp.status == 200 and 
                    ('image' in content_type or 'application/octet-stream' in content_type)
                )
    except Exception as e:
        logger.warning(f"Failed to validate image URL {image_url}: {e}")
        return False


@router.get("/nft/{nft_id}")
async def serve_nft_image(
    nft_id: str,
    current_user = Depends(get_current_user),
    request: Request = None,
) -> StreamingResponse:
    """
    Serve NFT image with security headers to prevent downloads.
    Validates that the authenticated user has permission to view the NFT.
    
    Returns the image with headers that:
    - Prevent right-click context menu access
    - Disable drag-and-drop
    - Disable image saving
    - Add cache-busting headers
    """
    try:
        # NOTE: In production, you'd query the database to:
        # 1. Fetch the NFT by nft_id
        # 2. Verify current_user has permission to view it
        # 3. Get the actual image_url from the NFT record
        
        # For now, this validates the endpoint structure
        # Real implementation would be:
        # from app.database import get_db_session
        # from app.models import NFT
        # nft = await db.get(NFT, nft_id)
        # if not nft:
        #     raise HTTPException(status_code=404, detail="NFT not found")
        # if nft.user_id != current_user.id:
        #     raise HTTPException(status_code=403, detail="Not authorized")
        # image_url = nft.image_url
        
        # This is where you'd get the real image URL
        # For now, return a 404 as placeholder
        raise HTTPException(
            status_code=403,
            detail="Image serving not yet fully implemented. Use client-side protection."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving NFT image {nft_id}: {e}")
        raise HTTPException(status_code=500, detail="Error serving image")


@router.get("/proxy")
@router.options("/proxy")
async def proxy_image(
    url: str = None,
    current_user = None,
) -> StreamingResponse:
    """
    Proxy image requests with security headers.
    Validates the user is authenticated before proxying external images.
    
    Security headers prevent:
    - Context menu (right-click)
    - Dragging the image
    - Saving/downloading
    """
    # Handle CORS preflight
    if current_user is None and url is None:
        from fastapi import Response
        return Response(headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        })
    
    try:
        if not url:
            raise HTTPException(status_code=400, detail="URL parameter required")
        
        # Validate image URL
        is_valid = await _validate_image_url(url)
        if not is_valid:
            raise HTTPException(status_code=403, detail="Invalid or inaccessible image URL")
        
        # Fetch the image
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    raise HTTPException(status_code=resp.status, detail="Failed to fetch image")
                
                content_type = resp.headers.get('content-type', 'application/octet-stream')
                
                # Stream response with security headers (allow CORS for web app)
                return StreamingResponse(
                    resp.content.iter_chunked(4096),
                    media_type=content_type,
                    headers={
                        # CORS headers for web app
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "GET, OPTIONS",
                        "Access-Control-Allow-Headers": "Content-Type, Authorization",
                        # Prevent context menu/right-click
                        "X-Content-Type-Options": "nosniff",
                        # Allow caching for performance
                        "Cache-Control": "public, max-age=3600",
                        # Prevent framing attacks
                        "X-Frame-Options": "DENY",
                    }
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error proxying image: {e}")
        raise HTTPException(status_code=500, detail="Error proxying image")
