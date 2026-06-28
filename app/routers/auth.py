import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import create_jwt
from app.crud import get_user_by_tg_id, create_user
from app.services.telegram import verify_telegram_init_data
from app.schemas.schemas import TelegramAuthRequest, AuthResponse, UserOut

router = APIRouter(prefix="/auth", tags=["Auth"])


class DemoAuthRequest(BaseModel):
    tg_id: int
    username: str | None = None
    full_name: str | None = None


@router.post("/telegram", response_model=AuthResponse)
async def telegram_auth(body: TelegramAuthRequest, db: AsyncSession = Depends(get_db)):
    tg_user = verify_telegram_init_data(body.init_data)
    if not tg_user:
        raise HTTPException(status_code=401, detail="Telegram initData tekshiruvi muvaffaqiyatsiz")

    tg_id = tg_user["id"]
    user = await get_user_by_tg_id(db, tg_id)

    if not user:
        user = await create_user(
            db,
            tg_id=tg_id,
            username=tg_user.get("username"),
            full_name=tg_user.get("first_name", "") + " " + tg_user.get("last_name", ""),
            ref_code=uuid.uuid4().hex[:8],
        )

    token = create_jwt(user.id)
    return AuthResponse(token=token, user=UserOut.model_validate(user))


@router.post("/demo", response_model=AuthResponse)
async def demo_auth(body: DemoAuthRequest, db: AsyncSession = Depends(get_db)):
    """Demo/owner login by tg_id (no Telegram initData) — restricted to the
    configured admin IDs so it can't be used to impersonate arbitrary users.
    Returns a real JWT + user so the Mini App always has a valid user_id."""
    if settings.admin_ids_list and body.tg_id not in settings.admin_ids_list:
        raise HTTPException(status_code=403, detail="Demo login faqat admin uchun")

    user = await get_user_by_tg_id(db, body.tg_id)
    if not user:
        user = await create_user(
            db,
            tg_id=body.tg_id,
            username=body.username,
            full_name=body.full_name or "Demo",
            ref_code=uuid.uuid4().hex[:8],
        )

    token = create_jwt(user.id)
    return AuthResponse(token=token, user=UserOut.model_validate(user))
