from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.favourite import FavouriteShop, FavouriteProduct


async def toggle_favourite_shop(session: AsyncSession, user_id: int, shop_id: int) -> bool:
    result = await session.execute(
        select(FavouriteShop).where(FavouriteShop.user_id == user_id, FavouriteShop.shop_id == shop_id)
    )
    fav = result.scalar_one_or_none()
    if fav:
        await session.delete(fav)
        await session.commit()
        return False
    session.add(FavouriteShop(user_id=user_id, shop_id=shop_id))
    await session.commit()
    return True


async def toggle_favourite_product(session: AsyncSession, user_id: int, product_id: int) -> bool:
    result = await session.execute(
        select(FavouriteProduct).where(FavouriteProduct.user_id == user_id, FavouriteProduct.product_id == product_id)
    )
    fav = result.scalar_one_or_none()
    if fav:
        await session.delete(fav)
        await session.commit()
        return False
    session.add(FavouriteProduct(user_id=user_id, product_id=product_id))
    await session.commit()
    return True


async def get_favourite_shops(session: AsyncSession, user_id: int) -> list[FavouriteShop]:
    result = await session.execute(select(FavouriteShop).where(FavouriteShop.user_id == user_id))
    return list(result.scalars().all())


async def get_favourite_products(session: AsyncSession, user_id: int) -> list[FavouriteProduct]:
    result = await session.execute(select(FavouriteProduct).where(FavouriteProduct.user_id == user_id))
    return list(result.scalars().all())


async def is_favourite_shop(session: AsyncSession, user_id: int, shop_id: int) -> bool:
    result = await session.execute(
        select(FavouriteShop).where(FavouriteShop.user_id == user_id, FavouriteShop.shop_id == shop_id)
    )
    return result.scalar_one_or_none() is not None
