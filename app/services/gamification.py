import logging
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.achievement import Achievement
from app.models.listing import Listing
from app.models.review import Review
from app.models.enums import ListingStatusEnum

logger = logging.getLogger(__name__)

LEVELS = [
    (1, 0, "Yangi"),
    (2, 500, "Faol"),
    (3, 1500, "Tajribali"),
    (4, 3000, "Professional"),
    (5, 6000, "Ekspert"),
]

BADGES = {
    "first_listing":   {"emoji": "🥇", "name": "Birinchi e'lon", "desc": "Birinchi e'lonni bering"},
    "active_seller":   {"emoji": "🔥", "name": "Faol sotuvchi", "desc": "10 ta e'lon bering"},
    "top_seller":      {"emoji": "👑", "name": "Top sotuvchi", "desc": "50 ta e'lon bering"},
    "referrer":        {"emoji": "🤝", "name": "Do'stlarni jalb", "desc": "5 ta do'st taklif qiling"},
    "trusted":         {"emoji": "⭐", "name": "Ishonchli", "desc": "4.5+ reyting oling"},
    "shop_owner":      {"emoji": "🏪", "name": "Do'kon egasi", "desc": "Do'kon oching"},
    "loyal":           {"emoji": "🔄", "name": "Doimiy mijoz", "desc": "30 kun streak"},
}

POINT_RULES = {
    "register": 50,
    "first_listing": 100,
    "new_listing": 20,
    "referral": 200,
    "review": 30,
    "open_shop": 500,
    "daily_login": 10,
}


def calc_level(points: int) -> tuple[int, str]:
    for level, threshold, name in reversed(LEVELS):
        if points >= threshold:
            return level, name
    return 1, "Yangi"


def level_progress(points: int) -> dict:
    level, name = calc_level(points)
    current_threshold = LEVELS[level - 1][1]
    next_threshold = LEVELS[level][1] if level < len(LEVELS) else LEVELS[-1][1]
    progress = min(100, int((points - current_threshold) / max(1, next_threshold - current_threshold) * 100))
    return {"level": level, "name": name, "points": points, "next_level": next_threshold, "progress": progress}


async def award_points(session: AsyncSession, user_id, reason: str, amount: int | None = None):
    pts = amount if amount is not None else POINT_RULES.get(reason, 0)
    if pts <= 0:
        return

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return

    user.points += pts
    new_level, _ = calc_level(user.points)
    user.level = new_level
    await session.flush()

    await _check_badges(session, user)
    logger.info("Points awarded: user=%s reason=%s pts=%d total=%d", user_id, reason, pts, user.points)


async def _check_badges(session: AsyncSession, user: User):
    listing_count = (await session.execute(
        select(func.count(Listing.id)).where(Listing.user_id == user.id)
    )).scalar() or 0

    checks = []
    if listing_count >= 1:
        checks.append("first_listing")
    if listing_count >= 10:
        checks.append("active_seller")
    if listing_count >= 50:
        checks.append("top_seller")
    if user.ref_count >= 5:
        checks.append("referrer")

    avg_rating = (await session.execute(
        select(func.avg(Review.rating)).where(Review.seller_id == user.id)
    )).scalar()
    if avg_rating and float(avg_rating) >= 4.5:
        checks.append("trusted")

    for badge_type in checks:
        await _grant_badge(session, user.id, badge_type)


async def _grant_badge(session: AsyncSession, user_id, badge_type: str):
    existing = (await session.execute(
        select(Achievement).where(Achievement.user_id == user_id, Achievement.type == badge_type)
    )).scalar_one_or_none()

    if existing:
        return False

    session.add(Achievement(user_id=user_id, type=badge_type))
    await session.flush()
    logger.info("Badge granted: user=%s badge=%s", user_id, badge_type)
    return True


async def get_leaderboard(session: AsyncSession, limit: int = 20) -> list[dict]:
    result = await session.execute(
        select(User.id, User.full_name, User.username, User.points, User.level, User.is_verified)
        .where(User.is_blocked == False)
        .order_by(User.points.desc())
        .limit(limit)
    )
    return [
        {"id": str(r.id), "name": r.full_name, "username": r.username,
         "points": r.points, "level": r.level, "is_verified": r.is_verified}
        for r in result.all()
    ]


async def get_user_rank(session: AsyncSession, user_id) -> int:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return 0
    rank = (await session.execute(
        select(func.count(User.id)).where(User.points > user.points, User.is_blocked == False)
    )).scalar() or 0
    return rank + 1


async def get_user_badges(session: AsyncSession, user_id) -> list[dict]:
    result = await session.execute(
        select(Achievement).where(Achievement.user_id == user_id).order_by(Achievement.created_at)
    )
    earned = {a.type for a in result.scalars().all()}
    badges = []
    for key, info in BADGES.items():
        badges.append({**info, "type": key, "earned": key in earned})
    return badges
