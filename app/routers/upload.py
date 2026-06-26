from fastapi import APIRouter, Depends, UploadFile, File, HTTPException

from app.dependencies import get_optional_user
from app.models.user import User
from app.services.cloudinary import upload_image, delete_image
from app.schemas.schemas import UploadResponse

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post("/image", response_model=UploadResponse)
async def upload_image_endpoint(
    file: UploadFile = File(...),
    user: User | None = Depends(get_optional_user),
):
    result = await upload_image(file)
    return UploadResponse(**result)


@router.delete("/image/{public_id}")
async def delete_image_endpoint(
    public_id: str,
    user: User | None = Depends(get_optional_user),
):
    ok = await delete_image(public_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Rasm topilmadi yoki o'chirib bo'lmadi")
    return {"status": "deleted"}
