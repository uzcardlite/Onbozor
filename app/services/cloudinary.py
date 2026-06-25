import cloudinary
import cloudinary.uploader
from fastapi import UploadFile, HTTPException

from app.config import settings

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE = 30 * 1024 * 1024


async def upload_image(file: UploadFile) -> dict:
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Faqat JPG, PNG, WEBP formatlar qabul qilinadi")

    contents = await file.read()
    if len(contents) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="Rasm hajmi 30MB dan oshmasligi kerak")

    result = cloudinary.uploader.upload(
        contents,
        folder="onbozor",
        resource_type="image",
        transformation=[{"width": 1200, "height": 1200, "crop": "limit", "quality": "auto"}],
    )

    return {"url": result["secure_url"], "public_id": result["public_id"]}
