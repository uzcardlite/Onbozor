import base64
import logging
from fastapi import UploadFile, HTTPException
from app.config import settings

logger = logging.getLogger(__name__)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE = 10 * 1024 * 1024

_cloudinary_ready = False

if settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY:
    try:
        import cloudinary
        import cloudinary.uploader
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
        )
        _cloudinary_ready = True
        logger.info("Cloudinary configured (cloud: %s)", settings.CLOUDINARY_CLOUD_NAME)
    except Exception as e:
        logger.warning("Cloudinary init failed: %s", e)


async def upload_image(file: UploadFile) -> dict:
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Faqat JPG, PNG, WEBP formatlar qabul qilinadi")

    contents = await file.read()
    if len(contents) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="Rasm hajmi 10MB dan oshmasligi kerak")

    if _cloudinary_ready:
        try:
            result = cloudinary.uploader.upload(
                contents,
                folder="onbozor",
                resource_type="image",
                eager=[{"width": 800, "crop": "limit", "quality": "auto", "fetch_format": "auto"}],
                eager_async=True,
            )
            url = result["secure_url"]
            public_id = result["public_id"]
            logger.info("Cloudinary upload OK: %s (%d bytes)", public_id, len(contents))
            return {"url": url, "public_id": public_id}
        except Exception as e:
            logger.error("Cloudinary upload failed: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail="Rasm yuklashda xatolik yuz berdi")

    b64 = base64.b64encode(contents).decode()
    data_url = f"data:{file.content_type};base64,{b64}"
    logger.info("Cloudinary not configured, base64 fallback (%d bytes)", len(contents))
    return {"url": data_url, "public_id": "local"}


def upload_image_bytes(contents: bytes, content_type: str = "image/jpeg") -> str | None:
    """Upload raw image bytes (e.g. a Telegram photo) and return the secure URL.

    Falls back to a base64 data URL when Cloudinary is not configured so the
    bot keeps working in local/dev environments.
    """
    if _cloudinary_ready:
        try:
            result = cloudinary.uploader.upload(
                contents,
                folder="onbozor",
                resource_type="image",
                eager=[{"width": 800, "crop": "limit", "quality": "auto", "fetch_format": "auto"}],
                eager_async=True,
            )
            logger.info("Cloudinary bot upload OK: %s (%d bytes)", result["public_id"], len(contents))
            return result["secure_url"]
        except Exception as e:
            logger.error("Cloudinary bot upload failed: %s", e, exc_info=True)
            return None

    b64 = base64.b64encode(contents).decode()
    logger.info("Cloudinary not configured, base64 fallback (%d bytes)", len(contents))
    return f"data:{content_type};base64,{b64}"


async def delete_image(public_id: str) -> bool:
    if not _cloudinary_ready or public_id == "local":
        return False
    try:
        result = cloudinary.uploader.destroy(public_id)
        ok = result.get("result") == "ok"
        logger.info("Cloudinary delete %s: %s", public_id, result.get("result"))
        return ok
    except Exception as e:
        logger.error("Cloudinary delete failed: %s", e)
        return False


def get_optimized_url(public_id: str, width: int = 800) -> str:
    if not _cloudinary_ready or public_id == "local":
        return ""
    return cloudinary.CloudinaryImage(public_id).build_url(
        width=width, crop="limit", quality="auto", fetch_format="auto",
    )
