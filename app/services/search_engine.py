from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.listing import Listing
from app.models.shop import Shop
from app.models.enums import ListingStatusEnum, SectionEnum

SORT_MAP = {
    "newest": Listing.created_at.desc(),
    "oldest": Listing.created_at.asc(),
    "cheapest": Listing.price.asc(),
    "expensive": Listing.price.desc(),
    "popular": Listing.views.desc(),
}


async def search_listings(
    session: AsyncSession,
    q: str | None = None,
    section: SectionEnum | None = None,
    viloyat: str | None = None,
    category: str | None = None,
    condition: str | None = None,
    payment_type: str | None = None,
    price_min: int | None = None,
    price_max: int | None = None,
    sort: str = "newest",
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Listing], int]:
    base = Listing.status == ListingStatusEnum.ACTIVE
    query = select(Listing).where(base)
    count_query = select(func.count(Listing.id)).where(base)

    if q:
        pattern = f"%{q}%"
        text_filter = or_(
            Listing.description.ilike(pattern),
            Listing.category.ilike(pattern),
            Listing.subcategory.ilike(pattern),
            Listing.seller_username.ilike(pattern),
            Listing.viloyat.ilike(pattern),
        )
        query = query.where(text_filter)
        count_query = count_query.where(text_filter)

    if section:
        query = query.where(Listing.section == section)
        count_query = count_query.where(Listing.section == section)
    if viloyat:
        query = query.where(Listing.viloyat == viloyat)
        count_query = count_query.where(Listing.viloyat == viloyat)
    if category:
        query = query.where(Listing.category == category)
        count_query = count_query.where(Listing.category == category)
    if condition:
        query = query.where(Listing.condition == condition)
        count_query = count_query.where(Listing.condition == condition)
    if payment_type:
        query = query.where(Listing.payment_type == payment_type)
        count_query = count_query.where(Listing.payment_type == payment_type)
    if price_min is not None:
        query = query.where(Listing.price >= price_min)
        count_query = count_query.where(Listing.price >= price_min)
    if price_max is not None:
        query = query.where(Listing.price <= price_max)
        count_query = count_query.where(Listing.price <= price_max)

    total = (await session.execute(count_query)).scalar()

    order = SORT_MAP.get(sort, Listing.created_at.desc())
    result = await session.execute(
        query.order_by(Listing.is_promoted.desc(), order).limit(limit).offset(offset)
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
    base = Shop.is_active == True
    query = select(Shop).where(base)
    count_query = select(func.count(Shop.id)).where(base)

    if q:
        pattern = f"%{q}%"
        text_filter = or_(Shop.name.ilike(pattern), Shop.description.ilike(pattern))
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
