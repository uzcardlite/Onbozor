import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_admin_user
from app.models.user import User
from app.models.listing import Listing
from app.models.shop import Shop
from app.models.payment import Payment
from app.models.enums import (
    ListingStatusEnum, PaymentStatusEnum, NotificationTypeEnum,
)
from app.crud import (
    get_user, update_user, get_listing, update_listing,
    get_shop, update_shop, get_pending_listings, count_listings,
    count_shops, count_users, get_all_user_tg_ids,
    create_broadcast, create_notification, update_broadcast,
)
from app.schemas.schemas import (
    AdminStats, RejectRequest, BroadcastRequest, BroadcastOut,
    UserOut, ListingOut, ShopOut,
)

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/stats", response_model=AdminStats)
async def dashboard_stats(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    total_users = await count_users(db)
    total_listings = await count_listings(db)
    active_listings = await count_listings(db, ListingStatusEnum.ACTIVE)
    pending_listings = await count_listings(db, ListingStatusEnum.PENDING)
    total_shops = await count_shops(db)
    active_shops = await count_shops(db, active_only=True)

    revenue_result = await db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0))
        .where(Payment.status == PaymentStatusEnum.PAID)
    )
    total_revenue = revenue_result.scalar()

    payments_count = (await db.execute(
        select(func.count(Payment.id)).where(Payment.status == PaymentStatusEnum.PAID)
    )).scalar()

    return AdminStats(
        total_users=total_users,
        total_listings=total_listings,
        active_listings=active_listings,
        pending_listings=pending_listings,
        total_shops=total_shops,
        active_shops=active_shops,
        total_payments=payments_count,
        total_revenue=total_revenue,
    )


@router.get("/users", response_model=list[UserOut])
async def list_users(
    search: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(User)
    if search:
        pattern = f"%{search}%"
        query = query.where(or_(
            User.full_name.ilike(pattern),
            User.username.ilike(pattern),
            User.phone.ilike(pattern),
        ))
    query = query.order_by(User.created_at.desc()).limit(limit).offset((page - 1) * limit)
    result = await db.execute(query)
    return [UserOut.model_validate(u) for u in result.scalars().all()]


@router.post("/users/{user_id}/block")
async def block_user(
    user_id: uuid.UUID,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    await update_user(db, user_id, is_blocked=True)
    return {"status": "blocked"}


@router.post("/users/{user_id}/unblock")
async def unblock_user(
    user_id: uuid.UUID,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    await update_user(db, user_id, is_blocked=False)
    return {"status": "unblocked"}


@router.get("/listings", response_model=list[ListingOut])
async def admin_listings(
    status: ListingStatusEnum = ListingStatusEnum.PENDING,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Listing)
        .where(Listing.status == status)
        .order_by(Listing.created_at.asc())
        .limit(limit).offset((page - 1) * limit)
    )
    result = await db.execute(query)
    return [ListingOut.model_validate(l) for l in result.scalars().all()]


@router.post("/listings/{listing_id}/approve")
async def approve_listing(
    listing_id: uuid.UUID,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    listing = await get_listing(db, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="E'lon topilmadi")
    await update_listing(db, listing_id, status=ListingStatusEnum.ACTIVE)
    await create_notification(
        db,
        user_id=listing.user_id,
        type=NotificationTypeEnum.LISTING_APPROVED,
        title="E'lon tasdiqlandi",
        body=f"Sizning \"{listing.category}\" e'loningiz tasdiqlandi va endi barchaga ko'rinadi.",
    )
    return {"status": "approved"}


@router.post("/listings/{listing_id}/reject")
async def reject_listing(
    listing_id: uuid.UUID,
    body: RejectRequest,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    listing = await get_listing(db, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="E'lon topilmadi")
    await update_listing(db, listing_id, status=ListingStatusEnum.REJECTED, reject_reason=body.reason)
    await create_notification(
        db,
        user_id=listing.user_id,
        type=NotificationTypeEnum.LISTING_REJECTED,
        title="E'lon rad etildi",
        body=f"Sizning e'loningiz rad etildi. Sabab: {body.reason}",
    )
    return {"status": "rejected"}


@router.get("/shops", response_model=list[ShopOut])
async def admin_shops(
    is_active: bool | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Shop)
    if is_active is not None:
        query = query.where(Shop.is_active == is_active)
    query = query.order_by(Shop.created_at.desc()).limit(limit).offset((page - 1) * limit)
    result = await db.execute(query)
    return [ShopOut.model_validate(s) for s in result.scalars().all()]


@router.post("/shops/{shop_id}/approve")
async def approve_shop(
    shop_id: uuid.UUID,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    shop = await get_shop(db, shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Do'kon topilmadi")
    await update_shop(db, shop_id, is_active=True, is_verified=True)
    await create_notification(
        db,
        user_id=shop.owner_id,
        type=NotificationTypeEnum.SHOP_APPROVED,
        title="Do'kon tasdiqlandi",
        body=f"\"{shop.name}\" do'koningiz tasdiqlandi. To'lovni amalga oshirib, faollashtiring.",
    )
    return {"status": "approved"}


@router.post("/shops/{shop_id}/reject")
async def reject_shop(
    shop_id: uuid.UUID,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    shop = await get_shop(db, shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Do'kon topilmadi")
    await update_shop(db, shop_id, is_active=False)
    return {"status": "rejected"}


@router.post("/broadcast", response_model=BroadcastOut)
async def send_broadcast(
    body: BroadcastRequest,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    broadcast = await create_broadcast(
        db,
        admin_id=admin.id,
        message_text=body.text,
        image_url=body.image_url,
    )

    user_ids = await get_all_user_tg_ids(db)
    sent = 0

    import httpx
    bot_url = f"https://api.telegram.org/bot{__import__('app.config', fromlist=['settings']).settings.BOT_TOKEN}"
    async with httpx.AsyncClient() as client:
        for tg_id in user_ids:
            try:
                if body.image_url:
                    await client.post(f"{bot_url}/sendPhoto", json={
                        "chat_id": tg_id, "photo": body.image_url, "caption": body.text,
                    })
                else:
                    await client.post(f"{bot_url}/sendMessage", json={
                        "chat_id": tg_id, "text": body.text,
                    })
                sent += 1
            except Exception:
                pass

    await update_broadcast(db, broadcast.id, sent_count=sent)
    return BroadcastOut(id=broadcast.id, sent_count=sent)
