from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.crud import get_user_notifications, mark_all_notifications_read, count_unread_notifications
from app.schemas.schemas import NotificationOut

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=list[NotificationOut])
async def list_notifications(
    unread_only: bool = False,
    limit: int = Query(50, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    notifs = await get_user_notifications(db, user.id, unread_only=unread_only, limit=limit)
    return [NotificationOut.model_validate(n) for n in notifs]


@router.get("/unread-count")
async def unread_count(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = await count_unread_notifications(db, user.id)
    return {"count": count}


@router.put("/read-all")
async def read_all_notifications(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await mark_all_notifications_read(db, user.id)
    return {"status": "ok"}
