from fastapi import APIRouter, Depends, UploadFile, File

from app.dependencies import get_current_user
from app.models.user import User
from app.services.cloudinary import upload_image
from app.schemas.schemas import UploadResponse

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post("/image", response_model=UploadResponse)
async def upload_image_endpoint(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    result = await upload_image(file)
    return UploadResponse(**result)
