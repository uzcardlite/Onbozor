import base64
import logging
from fastapi import UploadFile, HTTPException
from app.config import settings

logger = logging.getLogger(__name__)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE = 30 * 1024 * 1024

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
        logger.info("Cloudinary configured")
    except Exception as e:
        logger.warning("Cloudinary init failed: %s", e)


async def upload_image(file: UploadFile) -> dict:
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Faqat JPG, PNG, WEBP formatlar qabul qilinadi")

    contents = await file.read()
    if len(contents) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="Rasm hajmi 30MB dan oshmasligi kerak")

    if _cloudinary_ready:
        try:
            import cloudinary.uploader
            result = cloudinary.uploader.upload(
                contents,
                folder="onbozor",
                resource_type="image",
                transformation=[{"width": 1200, "height": 1200, "crop": "limit", "quality": "auto"}],
            )
            return {"url": result["secure_url"], "public_id": result["public_id"]}
        except Exception as e:
            logger.error("Cloudinary upload failed: %s", e)
            raise HTTPException(status_code=500, detail="Rasm yuklashda xatolik")

    b64 = base64.b64encode(contents).decode()
    data_url = f"data:{file.content_type};base64,{b64}"
    logger.info("Cloudinary not configured, using base64 fallback (%d bytes)", len(contents))
    return {"url": data_url, "public_id": "local"}
