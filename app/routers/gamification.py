from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.gamification import (
    level_progress, get_leaderboard, get_user_rank, get_user_badges,
)

router = APIRouter(prefix="/gamification", tags=["Gamification"])


@router.get("/my-stats")
async def my_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    progress = level_progress(user.points)
    rank = await get_user_rank(db, user.id)
    badges = await get_user_badges(db, user.id)

    return {
        **progress,
        "rank": rank,
        "badges": badges,
    }


@router.get("/leaderboard")
async def leaderboard(db: AsyncSession = Depends(get_db)):
    return await get_leaderboard(db, limit=20)
