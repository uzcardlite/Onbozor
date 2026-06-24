import uuid
from typing import Any, Sequence
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.shop import Shop
from app.models.listing import Listing
from app.models.favourite import Favourite
from app.models.payment import Payment
from app.models.broadcast import Broadcast
from app.models.notification import Notification
from app.models.enums import ListingStatusEnum, PaymentStatusEnum, SectionEnum


# ───────────────────────── generic helpers ─────────────────────────

async def _create(session: AsyncSession, instance) -> Any:
    session.add(instance)
    await session.flush()
    await session.refresh(instance)
    return instance


async def _get_by_id(session: AsyncSession, model, record_id: uuid.UUID):
    return await session.get(model, record_id)


async def _update(session: AsyncSession, model, record_id: uuid.UUID, **kwargs):
    await session.execute(
        update(model).where(model.id == record_id).values(**kwargs)
    )
    await session.flush()
    return await session.get(model, record_id)


async def _delete(session: AsyncSession, model, record_id: uuid.UUID) -> bool:
    result = await session.execute(delete(model).where(model.id == record_id))
    await session.flush()
    return result.rowcount > 0


# ─────────────────────────── USERS ────────────────────────────────

async def create_user(session: AsyncSession, **kwargs) -> User:
    return await _create(session, User(**kwargs))


async def get_user(session: AsyncSession, user_id: uuid.UUID) -> User | None:
    return await _get_by_id(session, User, user_id)


async def get_user_by_tg_id(session: AsyncSession, tg_id: int) -> User | None:
    result = await session.execute(select(User).where(User.tg_id == tg_id))
    return result.scalar_one_or_none()


async def get_user_by_ref_code(session: AsyncSession, ref_code: str) -> User | None:
    result = await session.execute(select(User).where(User.ref_code == ref_code))
    return result.scalar_one_or_none()


async def update_user(session: AsyncSession, user_id: uuid.UUID, **kwargs) -> User | None:
    return await _update(session, User, user_id, **kwargs)


async def delete_user(session: AsyncSession, user_id: uuid.UUID) -> bool:
    return await _delete(session, User, user_id)


async def count_users(session: AsyncSession) -> int:
    result = await session.execute(select(func.count(User.id)))
    return result.scalar()


async def get_all_user_tg_ids(session: AsyncSession, exclude_blocked: bool = True) -> Sequence[int]:
    query = select(User.tg_id)
    if exclude_blocked:
        query = query.where(User.is_blocked == False)
    result = await session.execute(query)
    return result.scalars().all()


# ─────────────────────────── SHOPS ────────────────────────────────

async def create_shop(session: AsyncSession, **kwargs) -> Shop:
    return await _create(session, Shop(**kwargs))


async def get_shop(session: AsyncSession, shop_id: uuid.UUID) -> Shop | None:
    return await _get_by_id(session, Shop, shop_id)


async def get_shops_by_category(
    session: AsyncSession,
    category: SectionEnum,
    viloyat: str | None = None,
    active_only: bool = True,
) -> Sequence[Shop]:
    query = select(Shop).where(Shop.category == category)
    if active_only:
        query = query.where(Shop.is_active == True)
    if viloyat:
        query = query.where(Shop.viloyat == viloyat)
    result = await session.execute(query.order_by(Shop.created_at.desc()))
    return result.scalars().all()


async def get_shops_by_owner(session: AsyncSession, owner_id: uuid.UUID) -> Sequence[Shop]:
    result = await session.execute(
        select(Shop).where(Shop.owner_id == owner_id).order_by(Shop.created_at.desc())
    )
    return result.scalars().all()


async def update_shop(session: AsyncSession, shop_id: uuid.UUID, **kwargs) -> Shop | None:
    return await _update(session, Shop, shop_id, **kwargs)


async def delete_shop(session: AsyncSession, shop_id: uuid.UUID) -> bool:
    return await _delete(session, Shop, shop_id)


async def count_shops(session: AsyncSession, active_only: bool = False) -> int:
    query = select(func.count(Shop.id))
    if active_only:
        query = query.where(Shop.is_active == True)
    result = await session.execute(query)
    return result.scalar()


# ──────────────────────── LISTINGS ────────────────────────────────

async def create_listing(session: AsyncSession, **kwargs) -> Listing:
    return await _create(session, Listing(**kwargs))


async def get_listing(session: AsyncSession, listing_id: uuid.UUID) -> Listing | None:
    return await _get_by_id(session, Listing, listing_id)


async def get_listings_by_filter(
    session: AsyncSession,
    section: SectionEnum | None = None,
    viloyat: str | None = None,
    status: ListingStatusEnum = ListingStatusEnum.ACTIVE,
    limit: int = 50,
    offset: int = 0,
) -> Sequence[Listing]:
    query = select(Listing).where(Listing.status == status)
    if section:
        query = query.where(Listing.section == section)
    if viloyat:
        query = query.where(Listing.viloyat == viloyat)
    query = query.order_by(
        Listing.is_promoted.desc(), Listing.created_at.desc()
    ).limit(limit).offset(offset)
    result = await session.execute(query)
    return result.scalars().all()


async def get_listings_by_user(session: AsyncSession, user_id: uuid.UUID) -> Sequence[Listing]:
    result = await session.execute(
        select(Listing).where(Listing.user_id == user_id).order_by(Listing.created_at.desc())
    )
    return result.scalars().all()


async def get_pending_listings(session: AsyncSession) -> Sequence[Listing]:
    result = await session.execute(
        select(Listing)
        .where(Listing.status == ListingStatusEnum.PENDING)
        .order_by(Listing.created_at.asc())
    )
    return result.scalars().all()


async def update_listing(session: AsyncSession, listing_id: uuid.UUID, **kwargs) -> Listing | None:
    return await _update(session, Listing, listing_id, **kwargs)


async def increment_views(session: AsyncSession, listing_id: uuid.UUID):
    await session.execute(
        update(Listing)
        .where(Listing.id == listing_id)
        .values(views=Listing.views + 1)
    )
    await session.flush()


async def delete_listing(session: AsyncSession, listing_id: uuid.UUID) -> bool:
    return await _delete(session, Listing, listing_id)


async def count_listings(session: AsyncSession, status: ListingStatusEnum | None = None) -> int:
    query = select(func.count(Listing.id))
    if status:
        query = query.where(Listing.status == status)
    result = await session.execute(query)
    return result.scalar()


# ─────────────────────── FAVOURITES ───────────────────────────────

async def create_favourite(session: AsyncSession, **kwargs) -> Favourite:
    return await _create(session, Favourite(**kwargs))


async def get_favourite(session: AsyncSession, fav_id: uuid.UUID) -> Favourite | None:
    return await _get_by_id(session, Favourite, fav_id)


async def get_user_favourite_shops(session: AsyncSession, user_id: uuid.UUID) -> Sequence[Favourite]:
    result = await session.execute(
        select(Favourite)
        .where(Favourite.user_id == user_id, Favourite.shop_id.isnot(None))
        .order_by(Favourite.created_at.desc())
    )
    return result.scalars().all()


async def get_user_favourite_listings(session: AsyncSession, user_id: uuid.UUID) -> Sequence[Favourite]:
    result = await session.execute(
        select(Favourite)
        .where(Favourite.user_id == user_id, Favourite.listing_id.isnot(None))
        .order_by(Favourite.created_at.desc())
    )
    return result.scalars().all()


async def is_favourite(
    session: AsyncSession,
    user_id: uuid.UUID,
    shop_id: uuid.UUID | None = None,
    listing_id: uuid.UUID | None = None,
) -> bool:
    query = select(Favourite).where(Favourite.user_id == user_id)
    if shop_id:
        query = query.where(Favourite.shop_id == shop_id)
    if listing_id:
        query = query.where(Favourite.listing_id == listing_id)
    result = await session.execute(query)
    return result.scalar_one_or_none() is not None


async def delete_favourite(session: AsyncSession, fav_id: uuid.UUID) -> bool:
    return await _delete(session, Favourite, fav_id)


async def remove_favourite(
    session: AsyncSession,
    user_id: uuid.UUID,
    shop_id: uuid.UUID | None = None,
    listing_id: uuid.UUID | None = None,
) -> bool:
    query = delete(Favourite).where(Favourite.user_id == user_id)
    if shop_id:
        query = query.where(Favourite.shop_id == shop_id)
    if listing_id:
        query = query.where(Favourite.listing_id == listing_id)
    result = await session.execute(query)
    await session.flush()
    return result.rowcount > 0


# ──────────────────────── PAYMENTS ────────────────────────────────

async def create_payment(session: AsyncSession, **kwargs) -> Payment:
    return await _create(session, Payment(**kwargs))


async def get_payment(session: AsyncSession, payment_id: uuid.UUID) -> Payment | None:
    return await _get_by_id(session, Payment, payment_id)


async def get_payment_by_transaction(session: AsyncSession, transaction_id: str) -> Payment | None:
    result = await session.execute(
        select(Payment).where(Payment.transaction_id == transaction_id)
    )
    return result.scalar_one_or_none()


async def get_payments_by_user(session: AsyncSession, user_id: uuid.UUID) -> Sequence[Payment]:
    result = await session.execute(
        select(Payment).where(Payment.user_id == user_id).order_by(Payment.created_at.desc())
    )
    return result.scalars().all()


async def update_payment(session: AsyncSession, payment_id: uuid.UUID, **kwargs) -> Payment | None:
    return await _update(session, Payment, payment_id, **kwargs)


async def delete_payment(session: AsyncSession, payment_id: uuid.UUID) -> bool:
    return await _delete(session, Payment, payment_id)


# ─────────────────────── BROADCASTS ───────────────────────────────

async def create_broadcast(session: AsyncSession, **kwargs) -> Broadcast:
    return await _create(session, Broadcast(**kwargs))


async def get_broadcast(session: AsyncSession, broadcast_id: uuid.UUID) -> Broadcast | None:
    return await _get_by_id(session, Broadcast, broadcast_id)


async def get_all_broadcasts(session: AsyncSession, limit: int = 50) -> Sequence[Broadcast]:
    result = await session.execute(
        select(Broadcast).order_by(Broadcast.created_at.desc()).limit(limit)
    )
    return result.scalars().all()


async def update_broadcast(session: AsyncSession, broadcast_id: uuid.UUID, **kwargs) -> Broadcast | None:
    return await _update(session, Broadcast, broadcast_id, **kwargs)


async def delete_broadcast(session: AsyncSession, broadcast_id: uuid.UUID) -> bool:
    return await _delete(session, Broadcast, broadcast_id)


# ────────────────────── NOTIFICATIONS ─────────────────────────────

async def create_notification(session: AsyncSession, **kwargs) -> Notification:
    return await _create(session, Notification(**kwargs))


async def get_notification(session: AsyncSession, notif_id: uuid.UUID) -> Notification | None:
    return await _get_by_id(session, Notification, notif_id)


async def get_user_notifications(
    session: AsyncSession,
    user_id: uuid.UUID,
    unread_only: bool = False,
    limit: int = 50,
) -> Sequence[Notification]:
    query = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        query = query.where(Notification.is_read == False)
    result = await session.execute(query.order_by(Notification.created_at.desc()).limit(limit))
    return result.scalars().all()


async def mark_notification_read(session: AsyncSession, notif_id: uuid.UUID) -> Notification | None:
    return await _update(session, Notification, notif_id, is_read=True)


async def mark_all_notifications_read(session: AsyncSession, user_id: uuid.UUID):
    await session.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read == False)
        .values(is_read=True)
    )
    await session.flush()


async def delete_notification(session: AsyncSession, notif_id: uuid.UUID) -> bool:
    return await _delete(session, Notification, notif_id)


async def count_unread_notifications(session: AsyncSession, user_id: uuid.UUID) -> int:
    result = await session.execute(
        select(func.count(Notification.id))
        .where(Notification.user_id == user_id, Notification.is_read == False)
    )
    return result.scalar()
