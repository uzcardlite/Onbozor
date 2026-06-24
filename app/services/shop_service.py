from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.shop import Shop, ShopProduct
from app.constants import ShopStatus


async def create_shop(session: AsyncSession, **kwargs) -> Shop:
    shop = Shop(**kwargs)
    session.add(shop)
    await session.commit()
    await session.refresh(shop)
    return shop


async def get_shops_by_category(session: AsyncSession, category: str, region: str | None = None) -> list[Shop]:
    query = select(Shop).where(Shop.category == category, Shop.status == ShopStatus.ACTIVE)
    if region:
        query = query.where(Shop.region == region)
    result = await session.execute(query.order_by(Shop.created_at.desc()))
    return list(result.scalars().all())


async def get_shop(session: AsyncSession, shop_id: int) -> Shop | None:
    result = await session.execute(select(Shop).where(Shop.id == shop_id))
    return result.scalar_one_or_none()


async def get_shop_products(session: AsyncSession, shop_id: int) -> list[ShopProduct]:
    result = await session.execute(
        select(ShopProduct).where(ShopProduct.shop_id == shop_id).order_by(ShopProduct.created_at.desc())
    )
    return list(result.scalars().all())


async def approve_shop(session: AsyncSession, shop_id: int) -> Shop | None:
    shop = await get_shop(session, shop_id)
    if shop:
        shop.status = ShopStatus.ACTIVE
        shop.expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        await session.commit()
    return shop


async def reject_shop(session: AsyncSession, shop_id: int) -> Shop | None:
    shop = await get_shop(session, shop_id)
    if shop:
        shop.status = ShopStatus.REJECTED
        await session.commit()
    return shop


async def activate_shop_after_payment(session: AsyncSession, shop_id: int):
    shop = await get_shop(session, shop_id)
    if shop:
        shop.status = ShopStatus.ACTIVE
        shop.expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        await session.commit()


async def count_shops(session: AsyncSession, status: str | None = None) -> int:
    query = select(func.count(Shop.id))
    if status:
        query = query.where(Shop.status == status)
    result = await session.execute(query)
    return result.scalar()
