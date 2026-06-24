from sqlalchemy import select, func, or_, cast, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.listing import Listing
from app.models.shop import Shop
from app.models.enums import ListingStatusEnum, SectionEnum


async def search_listings(
    session: AsyncSession,
    q: str | None = None,
    section: SectionEnum | None = None,
    viloyat: str | None = None,
    price_min: int | None = None,
    price_max: int | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Listing], int]:
    query = select(Listing).where(Listing.status == ListingStatusEnum.ACTIVE)
    count_query = select(func.count(Listing.id)).where(Listing.status == ListingStatusEnum.ACTIVE)

    if q:
        pattern = f"%{q}%"
        text_filter = or_(
            Listing.description.ilike(pattern),
            Listing.category.ilike(pattern),
            Listing.subcategory.ilike(pattern),
        )
        query = query.where(text_filter)
        count_query = count_query.where(text_filter)

    if section:
        query = query.where(Listing.section == section)
        count_query = count_query.where(Listing.section == section)
    if viloyat:
        query = query.where(Listing.viloyat == viloyat)
        count_query = count_query.where(Listing.viloyat == viloyat)
    if price_min is not None:
        query = query.where(Listing.price >= price_min)
        count_query = count_query.where(Listing.price >= price_min)
    if price_max is not None:
        query = query.where(Listing.price <= price_max)
        count_query = count_query.where(Listing.price <= price_max)

    total = (await session.execute(count_query)).scalar()
    result = await session.execute(
        query.order_by(Listing.is_promoted.desc(), Listing.created_at.desc())
        .limit(limit).offset(offset)
    )
    return list(result.scalars().all()), total


async def search_shops(
    session: AsyncSession,
    q: str | None = None,
    section: SectionEnum | None = None,
    viloyat: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Shop], int]:
    query = select(Shop).where(Shop.is_active == True)
    count_query = select(func.count(Shop.id)).where(Shop.is_active == True)

    if q:
        pattern = f"%{q}%"
        text_filter = or_(
            Shop.name.ilike(pattern),
            Shop.description.ilike(pattern),
        )
        query = query.where(text_filter)
        count_query = count_query.where(text_filter)

    if section:
        query = query.where(Shop.category == section)
        count_query = count_query.where(Shop.category == section)
    if viloyat:
        query = query.where(Shop.viloyat == viloyat)
        count_query = count_query.where(Shop.viloyat == viloyat)

    total = (await session.execute(count_query)).scalar()
    result = await session.execute(query.order_by(Shop.created_at.desc()).limit(limit).offset(offset))
    return list(result.scalars().all()), total
