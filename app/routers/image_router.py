from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
import aiohttp
import logging
import base64
import io
from PIL import Image as PILImage

from app.utils.telegram_auth_dependency import get_current_user
from app.services.image_service import ImageService
from app.models.image import ImageType
from app.database.connection import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from urllib.parse import urlparse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/images", tags=["images"])


async def _validate_image_url(image_url: str) -> bool:
    """Validates that a URL points to a real, accessible image"""
    try:
        if not image_url:
            return False
        parsed = urlparse(image_url)
        if parsed.scheme not in ('http', 'https'):
            return False
        async with aiohttp.ClientSession() as session:
            async with session.head(image_url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
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
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Uploads image/media for NFT minting.
    
    Stores files in the Image table instead of returning massive data URIs.
    This prevents database bloat and allows proper image management.
    
    Returns:
        {
            "image_id": str,           # Image table record ID
            "image_url": str,          # Data URI for immediate use (small images)
            "image_ref": str,          # Reference path for large images
            "thumbnail": str,          # Optional thumbnail data URI
            "mime_type": str,
            "filename": str,
            "size": int,
            "width": int,
            "height": int,
            "type": str                # 'image', 'video', 'telegram_sticker'
        }
    """
    try:
        allowed_mimetypes = {
            'image/jpeg', 'image/png', 'image/webp', 'image/gif',
            'video/mp4', 'video/webm', 'application/json'  # JSON for Telegram stickers
        }

        file_content = await file.read()
        file_size = len(file_content)

        if file_size > 50 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_PAYLOAD_TOO_LARGE,
                detail="File too large. Maximum 50MB allowed"
            )

        if file.content_type not in allowed_mimetypes:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_mimetypes)}"
            )

        # Validate image files
        if file.content_type.startswith('image/') and file.content_type != 'image/gif':
            try:
                img = PILImage.open(io.BytesIO(file_content))
                img.verify()  # Basic validation
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid image file: {str(e)}"
                )

        # Determine image type
        if file.content_type.startswith('image/') and file.content_type != 'image/gif':
            image_type = ImageType.NFT_PREVIEW
            result_type = "image"
        elif file.content_type in {'image/gif', 'video/mp4', 'video/webm'}:
            image_type = ImageType.NFT_FULL
            result_type = "gif" if file.content_type == "image/gif" else "video"
        elif file.content_type == 'application/json':
            image_type = ImageType.NFT_FULL
            result_type = "telegram_sticker"
        else:
            image_type = ImageType.NFT_PREVIEW
            result_type = "image"

        # Use ImageService to upload
        image, error = await ImageService.upload_image(
            db=db,
            file_content=file_content,
            filename=file.filename or f"nft-{file_size}.{file.content_type.split('/')[-1]}",
            mime_type=file.content_type,
            user_id=current_user.id,
            image_type=image_type,
        )

        if error:
            logger.error(f"Image upload error: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error
            )

        # Get image URL
        image_url = await ImageService.get_image_url(image, include_data=True)

        logger.info(
            f"User {current_user.id} uploaded {result_type}: "
            f"{file.filename} ({file_size} bytes)"
        )

        return {
            "image_id": str(image.id),
            "image_url": image_url,
            "image_ref": f"/api/v1/images/{image.id}/data",
            "mime_type": image.mime_type,
            "filename": image.filename,
            "size": image.file_size,
            "width": image.width,
            "height": image.height,
            "type": result_type,
        }

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
    """Serves an image associated with an NFT"""
    try:
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
    """Proxies external image URLs for CORS and security"""
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

        is_valid = await _validate_image_url(url)
        if not is_valid:
            raise HTTPException(status_code=403, detail="Invalid or inaccessible image URL")

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    raise HTTPException(status_code=resp.status, detail="Failed to fetch image")

                content_type = resp.headers.get('content-type', 'application/octet-stream')
                return StreamingResponse(
                    resp.content.iter_chunked(4096),
                    media_type=content_type,
                    headers={
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "GET, OPTIONS",
                        "Access-Control-Allow-Headers": "Content-Type, Authorization",
                        "X-Content-Type-Options": "nosniff",
                        "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
                        "X-Frame-Options": "DENY",
                    }
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error proxying image: {e}")
        raise HTTPException(status_code=500, detail="Error proxying image")

