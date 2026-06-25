from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.favourite import Favourite


async def toggle_favourite_shop(session: AsyncSession, user_id, shop_id) -> bool:
    result = await session.execute(
        select(Favourite).where(Favourite.user_id == user_id, Favourite.shop_id == shop_id)
    )
    fav = result.scalar_one_or_none()
    if fav:
        await session.delete(fav)
        await session.commit()
        return False
    session.add(Favourite(user_id=user_id, shop_id=shop_id))
    await session.commit()
    return True


async def toggle_favourite_listing(session: AsyncSession, user_id, listing_id) -> bool:
    result = await session.execute(
        select(Favourite).where(Favourite.user_id == user_id, Favourite.listing_id == listing_id)
    )
    fav = result.scalar_one_or_none()
    if fav:
        await session.delete(fav)
        await session.commit()
        return False
    session.add(Favourite(user_id=user_id, listing_id=listing_id))
    await session.commit()
    return True


async def get_favourite_shops(session: AsyncSession, user_id) -> list[Favourite]:
    result = await session.execute(
        select(Favourite).where(Favourite.user_id == user_id, Favourite.shop_id.isnot(None))
    )
    return list(result.scalars().all())


async def get_favourite_listings(session: AsyncSession, user_id) -> list[Favourite]:
    result = await session.execute(
        select(Favourite).where(Favourite.user_id == user_id, Favourite.listing_id.isnot(None))
    )
    return list(result.scalars().all())


async def is_favourite_shop(session: AsyncSession, user_id, shop_id) -> bool:
    result = await session.execute(
        select(Favourite).where(Favourite.user_id == user_id, Favourite.shop_id == shop_id)
    )
    return result.scalar_one_or_none() is not None
