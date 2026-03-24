from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
import aiohttp
import logging
from typing import Optional
from app.utils.telegram_auth_dependency import get_current_user
from urllib.parse import urlparse
import base64
import io
from PIL import Image
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/images", tags=["images"])
async def _validate_image_url(image_url: str) -> bool:
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
) -> dict:
    try:
        allowed_mimetypes = {
            'image/jpeg', 'image/png', 'image/webp', 'image/gif',
            'video/mp4', 'video/webm', 'application/json'
        }
        file_content = await file.read()
        file_size = len(file_content)
        if file_size > 50 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_PAYLOAD_TOO_LARGE,
                detail="File too large. Maximum 50MB allowed"
            )
        if file.content_type not in allowed_mimetypes and not file.filename:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_mimetypes)}"
            )
        if file.content_type.startswith('image/'):
            try:
                img = Image.open(io.BytesIO(file_content))
                img.verify()
            except Exception:
                try:
                    img = Image.open(io.BytesIO(file_content))
                except Exception as e:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Invalid image file: {str(e)}"
                    )
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
        elif file.content_type in {'image/gif', 'video/mp4', 'video/webm'}:
            base64_data = base64.b64encode(file_content).decode('utf-8')
            data_uri = f"data:{file.content_type};base64,{base64_data}"
            media_type = "gif" if file.content_type == "image/gif" else "video"
            logger.info(f"User {current_user.id} uploaded {media_type}: {file.filename} ({file_size} bytes)")
            return {
                "image_url": data_uri,
                "media_url": data_uri,
                "media_type": file.content_type,
                "filename": file.filename,
                "size": file_size,
                "type": media_type
            }
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
