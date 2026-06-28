import logging
from fastapi import UploadFile, HTTPException
from app.config import settings

logger = logging.getLogger(__name__)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE = 10 * 1024 * 1024
PLACEHOLDER_IMAGE = "https://via.placeholder.com/400x300"

_cloudinary_ready = False

if settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY and settings.CLOUDINARY_API_SECRET:
    try:
        import cloudinary
        import cloudinary.uploader
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True,
        )
        _cloudinary_ready = True
        logger.info("Cloudinary configured (cloud: %s)", settings.CLOUDINARY_CLOUD_NAME)
    except Exception as e:
        logger.warning("Cloudinary init failed: %s", e)
else:
    logger.warning(
        "Cloudinary NOT configured (missing CLOUDINARY_* vars) — "
        "image upload is optional, placeholder will be used"
    )


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
            # Image upload must never block listing creation — fall back to a
            # placeholder instead of raising a 500.
            logger.error("Cloudinary upload failed, using placeholder: %s", e, exc_info=True)
            return {"url": PLACEHOLDER_IMAGE, "public_id": "placeholder"}

    logger.info("Cloudinary not configured — returning placeholder image URL")
    return {"url": PLACEHOLDER_IMAGE, "public_id": "placeholder"}


def upload_image_bytes(contents: bytes, content_type: str = "image/jpeg") -> str | None:
    """Upload raw image bytes (e.g. a Telegram photo) and return the secure URL.

    Returns the placeholder URL when Cloudinary is not configured or the upload
    fails, so listing creation in the bot never breaks because of an image.
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
            logger.error("Cloudinary bot upload failed, using placeholder: %s", e, exc_info=True)
            return PLACEHOLDER_IMAGE

    logger.info("Cloudinary not configured — bot photo stored as placeholder")
    return PLACEHOLDER_IMAGE

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
