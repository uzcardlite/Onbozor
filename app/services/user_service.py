import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.referral import Referral


async def get_or_create_user(session: AsyncSession, telegram_id: int, full_name: str, username: str | None) -> tuple[User, bool]:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user:
        return user, False

    user = User(
        telegram_id=telegram_id,
        full_name=full_name,
        username=username,
        referral_code=uuid.uuid4().hex[:8],
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user, True


async def get_user(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def process_referral(session: AsyncSession, referrer_code: str, new_user: User):
    result = await session.execute(select(User).where(User.referral_code == referrer_code))
    referrer = result.scalar_one_or_none()
    if not referrer or referrer.telegram_id == new_user.telegram_id:
        return

    new_user.referred_by = referrer.telegram_id
    referral = Referral(referrer_id=referrer.id, referred_id=new_user.id)
    session.add(referral)
    await session.commit()


async def get_referral_count(session: AsyncSession, user_id: int) -> int:
    result = await session.execute(select(Referral).where(Referral.referrer_id == user_id))
    return len(result.scalars().all())
