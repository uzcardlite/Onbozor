from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.models.user import User
from app.models.listing import Listing
from app.models.shop import Shop

router = APIRouter(prefix="/api/admin")


@router.get("/stats")
async def get_stats(session: AsyncSession = Depends(get_session)):
    total_users = (await session.execute(select(func.count(User.id)))).scalar()
    total_listings = (await session.execute(select(func.count(Listing.id)))).scalar()
    pending_listings = (await session.execute(
        select(func.count(Listing.id)).where(Listing.status == "pending")
    )).scalar()
    total_shops = (await session.execute(select(func.count(Shop.id)))).scalar()

    return {
        "total_users": total_users,
        "total_listings": total_listings,
        "pending_listings": pending_listings,
        "total_shops": total_shops,
    }


@router.get("/users")
async def list_users(
    limit: int = 50, offset: int = 0,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
    )
    users = result.scalars().all()
    return [
        {
            "id": u.id, "telegram_id": u.telegram_id,
            "full_name": u.full_name, "username": u.username,
            "region": u.region, "is_blocked": u.is_blocked,
        }
        for u in users
    ]


@router.post("/users/{user_id}/block")
async def block_user(user_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return {"error": "User not found"}
    user.is_blocked = True
    await session.commit()
    return {"status": "blocked"}


@router.post("/users/{user_id}/unblock")
async def unblock_user(user_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return {"error": "User not found"}
    user.is_blocked = False
    await session.commit()
    return {"status": "unblocked"}
