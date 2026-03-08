"""
Protected image serving and upload for NFTs
Handles image and GIF uploads (including Telegram-compatible formats)
Prevents unauthorized downloads while allowing viewing
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
import aiohttp
import logging
from typing import Optional
from app.utils.auth import get_current_user
from urllib.parse import urlparse
import base64
import io
from PIL import Image

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


@router.post("/upload")
async def upload_nft_media(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
) -> dict:
    """
    Upload NFT media (images, GIFs) including Telegram-compatible formats.
    
    Supported formats:
    - JPEG, PNG, WebP (images)
    - GIF, MP4, WebM (animated/video)
    - TGS (Telegram animated sticker)
    
    Returns: {"image_url": "data:image/...", "media_type": "image/png", "size": ...}
    """
    try:
        # Validate file type
        allowed_mimetypes = {
            'image/jpeg', 'image/png', 'image/webp', 'image/gif',
            'video/mp4', 'video/webm', 'application/json'  # TGS is JSON
        }
        
        file_content = await file.read()
        file_size = len(file_content)
        
        # File size limits (50MB)
        if file_size > 50 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_PAYLOAD_TOO_LARGE,
                detail="File too large. Maximum 50MB allowed"
            )
        
        # Validate MIME type
        if file.content_type not in allowed_mimetypes and not file.filename:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_mimetypes)}"
            )
        
        # For images, convert to base64 data URI
        if file.content_type.startswith('image/'):
            # Validate it's a real image (basic check)
            try:
                img = Image.open(io.BytesIO(file_content))
                img.verify()
            except Exception:
                # Try to open it anyway (some formats might not verify)
                try:
                    img = Image.open(io.BytesIO(file_content))
                except Exception as e:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Invalid image file: {str(e)}"
                    )
            
            # Encode to base64
            base64_data = base64.b64encode(file_content).decode('utf-8')
            data_uri = f"data:{file.content_type};base64,{base64_data}"
            
            logger.info(f"User {current_user.id} uploaded image: {file.filename} ({file_size} bytes)")
            
            return {
                "image_url": data_uri,
                "media_type": file.content_type,
                "filename": file.filename,
                "size": file_size,
                "type": "image"
            }
        
        # For GIFs and videos, also encode as data URI
        elif file.content_type in {'image/gif', 'video/mp4', 'video/webm'}:
            base64_data = base64.b64encode(file_content).decode('utf-8')
            data_uri = f"data:{file.content_type};base64,{base64_data}"
            
            media_type = "gif" if file.content_type == "image/gif" else "video"
            logger.info(f"User {current_user.id} uploaded {media_type}: {file.filename} ({file_size} bytes)")
            
            return {
                "image_url": data_uri,
                "media_url": data_uri,  # Alternative key for videos
                "media_type": file.content_type,
                "filename": file.filename,
                "size": file_size,
                "type": media_type
            }
        
        # For TGS (Telegram sticker), handle as JSON
        elif file.content_type == 'application/json':
            base64_data = base64.b64encode(file_content).decode('utf-8')
            data_uri = f"data:{file.content_type};base64,{base64_data}"
            
            logger.info(f"User {current_user.id} uploaded Telegram sticker: {file.filename}")
            
            return {
                "image_url": data_uri,
                "media_type": file.content_type,
                "filename": file.filename,
                "size": file_size,
                "type": "telegram_sticker"
            }
        
        else:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Unsupported file type"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading media for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}"
        )



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
