from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.listing import Listing
from app.constants import ListingStatus


async def create_listing(session: AsyncSession, **kwargs) -> Listing:
    listing = Listing(**kwargs)
    session.add(listing)
    await session.commit()
    await session.refresh(listing)
    return listing


async def get_pending_listings(session: AsyncSession) -> list[Listing]:
    result = await session.execute(
        select(Listing).where(Listing.status == ListingStatus.PENDING).order_by(Listing.created_at.desc())
    )
    return list(result.scalars().all())


async def get_user_listings(session: AsyncSession, user_id: int) -> list[Listing]:
    result = await session.execute(
        select(Listing).where(Listing.user_id == user_id).order_by(Listing.created_at.desc())
    )
    return list(result.scalars().all())


async def get_listings_by_category(session: AsyncSession, category: str, region: str | None = None) -> list[Listing]:
    query = select(Listing).where(
        Listing.category == category,
        Listing.status == ListingStatus.APPROVED,
    )
    if region:
        query = query.where(Listing.region == region)
    result = await session.execute(query.order_by(Listing.created_at.desc()))
    return list(result.scalars().all())


async def approve_listing(session: AsyncSession, listing_id: int) -> Listing | None:
    result = await session.execute(select(Listing).where(Listing.id == listing_id))
    listing = result.scalar_one_or_none()
    if listing:
        listing.status = ListingStatus.APPROVED
        await session.commit()
    return listing


async def reject_listing(session: AsyncSession, listing_id: int, reason: str) -> Listing | None:
    result = await session.execute(select(Listing).where(Listing.id == listing_id))
    listing = result.scalar_one_or_none()
    if listing:
        listing.status = ListingStatus.REJECTED
        listing.reject_reason = reason
        await session.commit()
    return listing


async def count_listings(session: AsyncSession, status: str | None = None) -> int:
    query = select(func.count(Listing.id))
    if status:
        query = query.where(Listing.status == status)
    result = await session.execute(query)
    return result.scalar()
