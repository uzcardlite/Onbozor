from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.shop import Shop


async def create_shop(session: AsyncSession, **kwargs) -> Shop:
    shop = Shop(**kwargs)
    session.add(shop)
    await session.commit()
    await session.refresh(shop)
    return shop


async def get_shops_by_category(session: AsyncSession, category: str, viloyat: str | None = None) -> list[Shop]:
    query = select(Shop).where(Shop.is_active == True)
    if category:
        query = query.where(Shop.category == category)
    if viloyat:
        query = query.where(Shop.viloyat == viloyat)
    result = await session.execute(query.order_by(Shop.created_at.desc()))
    return list(result.scalars().all())


async def get_shop(session: AsyncSession, shop_id) -> Shop | None:
    return await session.get(Shop, shop_id)


async def approve_shop(session: AsyncSession, shop_id) -> Shop | None:
    shop = await get_shop(session, shop_id)
    if shop:
        shop.is_active = True
        shop.subscription_expires = datetime.now(timezone.utc) + timedelta(days=30)
        await session.commit()
    return shop


async def reject_shop(session: AsyncSession, shop_id) -> Shop | None:
    shop = await get_shop(session, shop_id)
    if shop:
        shop.is_active = False
        await session.commit()
    return shop


async def count_shops(session: AsyncSession, active_only: bool = False) -> int:
    query = select(func.count(Shop.id))
    if active_only:
        query = query.where(Shop.is_active == True)
    result = await session.execute(query)
    return result.scalar()
