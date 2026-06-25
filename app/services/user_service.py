import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User


async def get_or_create_user(
    session: AsyncSession, telegram_id: int, full_name: str, username: str | None
) -> tuple[User, bool]:
    result = await session.execute(select(User).where(User.tg_id == telegram_id))
    user = result.scalar_one_or_none()
    if user:
        return user, False

    user = User(
        tg_id=telegram_id,
        full_name=full_name,
        username=username,
        ref_code=uuid.uuid4().hex[:8],
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user, True


async def get_user(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(select(User).where(User.tg_id == telegram_id))
    return result.scalar_one_or_none()


async def process_referral(session: AsyncSession, referrer_code: str, new_user: User):
    result = await session.execute(select(User).where(User.ref_code == referrer_code))
    referrer = result.scalar_one_or_none()
    if not referrer or referrer.tg_id == new_user.tg_id:
        return

    new_user.referred_by = referrer.id
    referrer.ref_count += 1
    await session.commit()


async def get_referral_count(session: AsyncSession, user_id) -> int:
    result = await session.execute(
        select(func.count(User.id)).where(User.referred_by == user_id)
    )
    return result.scalar() or 0
